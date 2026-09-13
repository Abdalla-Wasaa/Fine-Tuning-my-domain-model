"""Download this instance's artifacts over direct TLS pinned through authenticated SSH.

No Cloudflare tunnel is used. Session credentials remain in memory and are sent
only to the direct HTTPS endpoint of the same SSH-authenticated instance.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import shlex
import ssl
import subprocess
import tempfile
import time


def remote_python(ssh, code):
    return subprocess.check_output(ssh + ['/usr/bin/python3 -c ' + shlex.quote(code)], text=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', required=True)
    parser.add_argument('--ssh-port', type=int, required=True)
    parser.add_argument('--https-port', type=int, required=True)
    parser.add_argument('--instance-id', type=int, required=True)
    parser.add_argument('--workers', type=int, default=32, choices=range(1,65))
    parser.add_argument('--include-base', action='store_true')
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parents[1] / 'artifacts')
    args = parser.parse_args()
    import ipaddress
    ipaddress.ip_address(args.host)  # Direct instance IP only, never a third-party hostname.
    if not all(1 <= p <= 65535 for p in (args.ssh_port, args.https_port)):
        parser.error('Ports must be between 1 and 65535')
    import requests
    from requests.adapters import HTTPAdapter
    ssh = ['ssh', '-p', str(args.ssh_port), '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
           '-o', 'ConnectTimeout=15', 'root@' + args.host]
    names = ['afyaplus-trained-adapter.tar.gz'] + (['afyaplus-base.tar'] if args.include_base else [])
    certificate = remote_python(ssh, 'import ssl; print(ssl.get_server_certificate(("localhost",8080)))')
    code = ('import os,json,subprocess,hashlib; from pathlib import Path; '
            f'd=json.loads(subprocess.check_output(["vastai","show","instance",{str(args.instance_id)!r},"--raw"])); '
            f'assert int(d["id"])=={args.instance_id}; '
            f'files=[{{"name":n,"size":Path("/tmp",n).stat().st_size,"sha256":subprocess.check_output(["sha256sum",str(Path("/tmp",n))],text=True).split()[0]}} for n in {names!r}]; '
            'print(json.dumps({"files":files,"jupyter":d["jupyter_token"],"edge":os.getenv("OPEN_BUTTON_TOKEN") or os.getenv("WEB_PASSWORD")}))')
    credentials = json.loads(remote_python(ssh, code))
    for item in credentials['files']:
        code = 'import hashlib,json; f=open(' + repr('/tmp/' + item['name']) + ',"rb"); print(json.dumps([hashlib.sha256(b).hexdigest() for b in iter(lambda:f.read(65536),b"")]))'
        item['chunks'] = json.loads(remote_python(ssh, code))
    args.output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='afyaplus-tls-') as directory:
        cert = Path(directory) / 'server.pem'
        cert.write_text(certificate)
        context = ssl.create_default_context(cafile=str(cert))
        context.check_hostname = False  # Trust the SSH-obtained certificate rather than its local DNS name.
        context.verify_flags |= ssl.VERIFY_X509_PARTIAL_CHAIN

        class PinnedAdapter(HTTPAdapter):
            def init_poolmanager(self, *a, **kw):
                kw.update(ssl_context=context, assert_hostname=False)
                return super().init_poolmanager(*a, **kw)

            def proxy_manager_for(self, *a, **kw):
                kw.update(ssl_context=context, assert_hostname=False)
                return super().proxy_manager_for(*a, **kw)

        base = f'https://{args.host}:{args.https_port}'
        with requests.Session() as session:
            session.mount(base + '/', PinnedAdapter())
            session.verify = str(cert)
            for item in credentials['files']:
                path = args.output / item['name']
                partial = path.with_name(path.name + '.part')
                try:
                    # Small parallel ranges avoid the stalled long streams observed on this host.
                    chunk_size = 64 * 1024
                    ranges = [(offset, min(offset + chunk_size, item['size']) - 1)
                              for offset in range(0, item['size'], chunk_size)]
                    if partial.exists():
                        with partial.open('rb') as existing:
                            remaining = []
                            for offset, end in ranges:
                                existing.seek(offset)
                                if hashlib.sha256(existing.read(end-offset+1)).hexdigest() != item['chunks'][offset//chunk_size]:
                                    remaining.append((offset,end))
                            ranges = remaining
                    print(f'Retrieving {len(ranges)} missing or invalid chunks', flush=True)
                    def fetch_once(bounds):
                        offset, end = bounds
                        with session.get(base + '/files/tmp/' + item['name'],
                            headers={'Authorization': 'Bearer ' + credentials['edge'],
                                     'Range': f'bytes={offset}-{end}', 'Connection': 'close'},
                            params={'token': credentials['jupyter']}, allow_redirects=False,
                            timeout=(15, 30)) as response:
                            if response.status_code != 206 or response.headers.get('Content-Range') != f'bytes {offset}-{end}/{item["size"]}':
                                raise RuntimeError(f'Expected exact byte range; HTTP {response.status_code}')
                            payload = response.content
                            if len(payload) != end - offset + 1:
                                raise RuntimeError('Incomplete byte range')
                            return offset, payload
                    def fetch(bounds):
                        for attempt in range(4):
                            try:
                                return fetch_once(bounds)
                            except requests.RequestException:
                                if attempt == 3:
                                    raise
                                time.sleep(attempt + 1)
                    completed = item['size'] - sum(end-offset+1 for offset,end in ranges)
                    with partial.open('r+b' if partial.exists() else 'w+b') as stream, ThreadPoolExecutor(max_workers=args.workers) as workers:
                        jobs = [workers.submit(fetch, bounds) for bounds in ranges]
                        for job in as_completed(jobs):
                            offset, payload = job.result()
                            stream.seek(offset); stream.write(payload)
                            completed += len(payload)
                            if completed // (1024 * 1024) > (completed - len(payload)) // (1024 * 1024):
                                print(f"Retrieved {completed // (1024 * 1024)} MiB of {item['name']}", flush=True)
                    with partial.open('rb') as stream:
                        digest = hashlib.file_digest(stream, 'sha256')
                    if partial.stat().st_size != item['size'] or digest.hexdigest() != item['sha256']:
                        raise RuntimeError('Downloaded artifact does not match remote size/hash')
                    partial.replace(path)
                    print(f"Verified {item['name']}: {item['size']} bytes; SHA256 {item['sha256']}", flush=True)
                except requests.RequestException as exc:
                    # Requests exceptions may contain URLs with session credentials.
                    raise SystemExit(f'Direct artifact transfer failed ({type(exc).__name__}); credentials omitted.') from None


if __name__ == '__main__':
    main()
