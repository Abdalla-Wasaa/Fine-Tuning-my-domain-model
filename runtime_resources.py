"""Conservative memory checks before loading the required unquantized 8B model."""
from pathlib import Path


def available_memory_bytes():
    entries = dict(line.split(':',1) for line in Path('/proc/meminfo').read_text().splitlines())
    available = int(entries['MemAvailable'].split()[0]) * 1024
    limit_path = Path('/sys/fs/cgroup/memory.max')
    used_path = Path('/sys/fs/cgroup/memory.current')
    if limit_path.exists() and used_path.exists():
        limit = limit_path.read_text().strip()
        if limit != 'max':
            stats_path = Path('/sys/fs/cgroup/memory.stat')
            stats = dict(line.split() for line in stats_path.read_text().splitlines()) if stats_path.exists() else {}
            # Inactive file pages are reclaimable; do not count model-download cache as live tensors.
            reclaimable = int(stats.get('inactive_file', 0))
            available = min(available, max(0, int(limit)-int(used_path.read_text())+reclaimable))
    return available


def require_llama_memory(precision="float32", minimum_gib=None):
    required = minimum_gib if minimum_gib is not None else (40 if precision == "float32" else 22)
    available = available_memory_bytes()
    if available < required * 1024**3:
        raise SystemExit(f'Unquantized LLaMA 8B needs at least {required} GiB available RAM for this {precision} pipeline; {available/1024**3:.1f} GiB available. Use a larger CPU machine; do not restart GPU compute just to satisfy this check.')
