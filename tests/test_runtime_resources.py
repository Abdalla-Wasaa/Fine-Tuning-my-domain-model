from pathlib import Path
import runtime_resources


def test_cgroup_reclaimable_cache_is_capped_by_host_available(tmp_path, monkeypatch):
    files = {'/proc/meminfo': 'MemAvailable: 20000000 kB\n',
             '/sys/fs/cgroup/memory.max': '32000000000',
             '/sys/fs/cgroup/memory.current': '24000000000',
             '/sys/fs/cgroup/memory.stat': 'inactive_file 16000000000\nanon 8000000000\n'}
    for name, text in files.items():
        target=tmp_path/name.lstrip('/');target.parent.mkdir(parents=True,exist_ok=True);target.write_text(text)
    monkeypatch.setattr(runtime_resources,'Path',lambda name: tmp_path/name.lstrip('/'))
    assert runtime_resources.available_memory_bytes()==20000000*1024
    (tmp_path/'sys/fs/cgroup/memory.stat').write_text('inactive_file 0\n')
    assert runtime_resources.available_memory_bytes()==8000000000
