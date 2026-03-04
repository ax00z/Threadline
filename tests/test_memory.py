import os
import tempfile
import psutil
import pytest
from threadline.parser import parse_file


def _make_large_chat(n: int) -> str:
    lines = []
    names = ["Rania", "Kofi", "Yusuf", "Selin", "Omar"]
    for i in range(n):
        h = 8 + (i % 12)
        ampm = "AM" if h < 12 else "PM"
        h12 = h if h <= 12 else h - 12
        m = i % 60
        sender = names[i % len(names)]
        lines.append(f"[1/{(i%28)+1}/25, {h12}:{m:02d} {ampm}] {sender}: message number {i}")
    return "\n".join(lines)


def test_memory_flat():
    content = _make_large_chat(50_000)
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8")
    f.write(content)
    f.close()

    proc = psutil.Process(os.getpid())
    samples = []

    try:
        gen = parse_file(f.name)
        for i, _ in enumerate(gen):
            if i % 5000 == 0:
                samples.append(proc.memory_info().rss // 1024)
    finally:
        os.unlink(f.name)

    assert len(samples) >= 5
    # peak should stay within 5x the first sample (O(1) memory)
    assert max(samples) < samples[0] * 5, f"memory grew too much: {samples}"
