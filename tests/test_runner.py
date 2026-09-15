"""Exercise shell cleanup with fake provider/storage commands, never cloud resources."""
import os
from pathlib import Path
import shutil
import subprocess
import pytest


@pytest.mark.parametrize('provider', ['nebius', 'vast'])
@pytest.mark.parametrize('failure', ['', 'training', 'upload', 'storage_preflight'])
def test_runner_stops_after_success_or_failure(tmp_path, failure, provider):
    project = tmp_path / 'project'
    (project / 'scripts').mkdir(parents=True)
    (project / 'artifacts/adapter').mkdir(parents=True)
    source = Path(__file__).resolve().parents[1] / f'scripts/train_{provider}.sh'
    shutil.copy(source, project / f'scripts/train_{provider}.sh')
    commands = tmp_path / 'commands'; commands.mkdir()
    fixtures = {
        'nebius': 'echo "nebius $*" >> "$TRACE"\necho \'{"status":{"state":"STOPPED"}}\'\n',
        'vastai': 'echo "vastai $*" >> "$TRACE"\necho \'{"actual_status":"stopped"}\'\n',
        'aws': 'echo "aws $*" >> "$TRACE"\nif [[ "$1 $2" == "s3 ls" && "$FAILURE" == storage_preflight ]]; then exit 25; fi\nif [[ "$1 $2" == "s3 cp" && "$FAILURE" == upload ]]; then exit 23; fi\n',
        'python': 'echo "training" >> "$TRACE"\nif [[ "$FAILURE" == training ]]; then exit 24; fi\n',
        'nohup': 'echo "watchdog armed" >> "$TRACE"\n',
    }
    for name, body in fixtures.items():
        file = commands / name
        file.write_text('#!/bin/bash\n' + body)
        file.chmod(0o755)
    trace = tmp_path / 'trace'
    env = {**os.environ, 'PATH': str(commands) + ':' + os.environ['PATH'], 'TRACE': str(trace),
           'FAILURE': failure, 'NEBIUS_INSTANCE_ID': 'test-instance', 'VAST_INSTANCE_ID': '50789605', 'MAX_RUN_SECONDS': '30',
           'ARTIFACT_URI': 's3://fixture-bucket/run', 'VAST_API_KEY': 'synthetic-test-key'}
    result = subprocess.run(['bash', str(project / f'scripts/train_{provider}.sh')], env=env, capture_output=True, timeout=10)
    assert result.returncode == {'': 0, 'training': 24, 'upload': 23, 'storage_preflight': 25}[failure]
    log = trace.read_text()
    stop = 'nebius compute instance stop --id test-instance' if provider == 'nebius' else 'vastai stop instance 50789605'
    assert stop in log
    if provider == 'vast':
        assert stop + ' --api-key synthetic-test-key --raw' in log
    if failure != 'storage_preflight':
        assert log.index('training') < log.index(stop)
