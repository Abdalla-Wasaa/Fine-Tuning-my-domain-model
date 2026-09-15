"""Conservative memory checks before loading the required unquantized 8B model."""
from pathlib import Path


def available_memory_bytes():
    entries = dict(line.split(':',1) for line in Path('/proc/meminfo').read_text().splitlines())
    available = int(entries['MemAvailable'].split()[0]) * 1024
    limit_path = Path('/sys/fs/cgroup/memory.max')
    used_path = Path('/sys/fs/cgroup/memory.current')
    if limit_path.exists() and used_path.exists():
        limit = limit_path.read_text().strip()
        if limit != 'max': available = min(available, max(0, int(limit)-int(used_path.read_text())))
    return available


def require_llama_memory():
    available = available_memory_bytes()
    if available < 40 * 1024**3:
        raise SystemExit(f'Unquantized LLaMA 8B needs at least 40 GiB available RAM for this float32 pipeline; {available/1024**3:.1f} GiB available. Use a larger CPU machine; do not restart GPU compute just to satisfy this check.')
