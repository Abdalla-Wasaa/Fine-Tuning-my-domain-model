"""Download this instance's artifacts over direct TLS pinned through authenticated SSH.

No Cloudflare tunnel is used. Session credentials remain in memory and are sent
only to the direct HTTPS endpoint of the same SSH-authenticated instance.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import ssl
import subprocess
import tempfile


def remote_python(ssh, code):
    return subprocess.check_output(ssh + ['/usr/bin/python3 -c ' + shlex.quote(code)], text=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', required=True)
    parser.add_argument('--ssh-port', type=int, required=True)
    parser.add_argument('--https-port', type=int, required=True)
    parser.add_argument('--instance-id', type=int, required=True)
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
                    with session.get(base + '/files/tmp/' + item['name'],
                        headers={'Authorization': 'Bearer ' + credentials['edge']},
                        params={'token': credentials['jupyter']}, stream=True,
                        allow_redirects=False, timeout=(20, 60)) as response:
                        if response.status_code != 200:
                            raise RuntimeError(f'Download returned HTTP {response.status_code}')
                        digest = hashlib.sha256()
                        with partial.open('wb') as stream:
                            for chunk in response.iter_content(1024 * 1024):
                                stream.write(chunk)
                                digest.update(chunk)
                    if partial.stat().st_size != item['size'] or digest.hexdigest() != item['sha256']:
                        raise RuntimeError('Downloaded artifact does not match remote size/hash')
                    partial.replace(path)
                    print(f"Verified {item['name']}: {item['size']} bytes; SHA256 {item['sha256']}", flush=True)
                except requests.RequestException as exc:
                    # Requests exceptions may contain URLs with session credentials.
                    raise SystemExit(f'Direct artifact transfer failed ({type(exc).__name__}); credentials omitted.') from None


if __name__ == '__main__':
    main()
