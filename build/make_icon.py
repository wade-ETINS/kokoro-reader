"""Draw the Kokoro Reader icon (sound bars on a rounded tile) and write app/static/icon.ico + icon.png."""
import struct
import zlib
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "app" / "static"
BG, FG, HL = (11, 94, 107), (241, 242, 238), (251, 211, 141)
BARS = [0.30, 0.55, 0.85, 0.62, 0.40]  # bar heights as a share of the tile


def pixel(x, y):
    """Colour (r, g, b, a) at unit coordinates 0..1, or None for transparent."""
    r = 0.22
    cx, cy = min(max(x, r), 1 - r), min(max(y, r), 1 - r)
    if (x - cx) ** 2 + (y - cy) ** 2 > r * r:
        return None
    n, w, gap = len(BARS), 0.095, 0.045
    left = 0.5 - (n * w + (n - 1) * gap) / 2
    for i, h in enumerate(BARS):
        x0 = left + i * (w + gap)
        if x0 <= x <= x0 + w and abs(y - 0.5) <= h / 2:
            return HL if i == 2 else FG
    return BG


def render(size, ss=4):
    rows = []
    for py in range(size):
        row = bytearray([0])
        for px in range(size):
            acc, cov = [0, 0, 0], 0
            for sy in range(ss):
                for sx in range(ss):
                    c = pixel((px + (sx + 0.5) / ss) / size, (py + (sy + 0.5) / ss) / size)
                    if c:
                        cov += 1
                        for k in range(3):
                            acc[k] += c[k]
            if cov:
                row += bytes([acc[0] // cov, acc[1] // cov, acc[2] // cov, 255 * cov // (ss * ss)])
            else:
                row += bytes(4)
        rows.append(bytes(row))
    raw = b"".join(rows)

    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data))

    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


sizes = [256, 64, 48, 32, 16]
pngs = [render(s) for s in sizes]
header = struct.pack("<HHH", 0, 1, len(sizes))
offset = 6 + 16 * len(sizes)
entries = b""
for s, p in zip(sizes, pngs):
    entries += struct.pack("<BBBBHHII", s % 256, s % 256, 0, 0, 1, 32, len(p), offset)
    offset += len(p)
(OUT / "icon.ico").write_bytes(header + entries + b"".join(pngs))
(OUT / "icon.png").write_bytes(pngs[1])
print("wrote", OUT / "icon.ico")
