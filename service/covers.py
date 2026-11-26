"""주제 커버 이미지. 주제어에서 색 조합과 무늬를 정해 SVG로 그린다 (같은 주제는 항상 같은 그림)."""
import hashlib
import math

# (바탕 시작색, 바탕 끝색, 번짐 1, 번짐 2)
PALETTES = [
    ("#17504C", "#2F7F79", "#6FC4BB", "#F2A26B"),
    ("#153B5C", "#2C6E9B", "#7DC3E8", "#9BE0C9"),
    ("#A8401F", "#DB7445", "#F6C177", "#F28FA0"),
    ("#45295F", "#7A4BA0", "#C39BE0", "#F2A26B"),
    ("#2C4A2E", "#4F8046", "#B9D98A", "#F6D77A"),
    ("#1E2A38", "#44566C", "#8FB3D9", "#6FC4BB"),
    ("#7A1F45", "#B8436F", "#F2A0B5", "#F6C177"),
    ("#232B6B", "#4C5BC0", "#9AA8F2", "#7FE0D0"),
]
W, H = 800, 320


def _radar(r):
    cx, cy = 560 + r[0] % 120, 150 + r[1] % 60
    rings = "".join(f'<circle cx="{cx}" cy="{cy}" r="{k}" fill="none" stroke="#fff" stroke-opacity="{0.34 - i * 0.05:.2f}" '
                    f'stroke-width="2"/>' for i, k in enumerate((40, 85, 130, 175, 220)))
    a = math.radians(200 + r[2] % 120)
    x, y = cx + 220 * math.cos(a), cy + 220 * math.sin(a)
    blips = "".join(
        f'<circle cx="{cx + d * math.cos(math.radians(t)):.0f}" cy="{cy + d * math.sin(math.radians(t)):.0f}" r="{s}" '
        f'fill="#fff" fill-opacity=".85"/>'
        for d, t, s in ((85, r[3] * 1.4, 6), (130, r[4] * 1.4, 8), (175, r[5] * 1.4, 5), (60, r[6] * 1.4, 4)))
    return (rings + f'<line x1="{cx}" y1="{cy}" x2="{x:.0f}" y2="{y:.0f}" stroke="#fff" stroke-opacity=".6" stroke-width="3" '
            f'stroke-linecap="round"/><circle cx="{cx}" cy="{cy}" r="7" fill="#fff"/>' + blips)


def _bars(r):
    out = []
    for i in range(9):
        h = 50 + (r[i] % 150) + i * 9
        out.append(f'<rect x="{410 + i * 42}" y="{H - 34 - h}" width="26" height="{h}" rx="9" fill="#fff" '
                   f'fill-opacity="{0.16 + 0.07 * (i % 4):.2f}"/>')
    return "".join(out)


def _waves(r):
    out = []
    for i in range(5):
        y, amp = 90 + i * 44, 22 + r[i] % 26
        d = f"M-20 {y}" + "".join(
            f" Q{x + 50} {y + (amp if (x // 100 + i) % 2 else -amp)} {x + 100} {y}" for x in range(-20, W + 20, 100))
        out.append(f'<path d="{d}" fill="none" stroke="#fff" stroke-opacity="{0.42 - i * 0.07:.2f}" stroke-width="3" '
                   f'stroke-linecap="round"/>')
    return "".join(out)


def _dots(r):
    out = []
    for row in range(7):
        for col in range(11):
            on = (r[(row * 11 + col) % 16] + row * col) % 5 == 0
            out.append(f'<circle cx="{392 + col * 38}" cy="{40 + row * 40}" r="{9 if on else 4}" fill="#fff" '
                       f'fill-opacity="{0.8 if on else 0.24}"/>')
    return "".join(out)


def _network(r):
    pts = [(400 + (r[i] * 3) % 370, 36 + (r[i + 8] * 2) % 250) for i in range(8)]
    lines = "".join(f'<line x1="{pts[i][0]}" y1="{pts[i][1]}" x2="{pts[j][0]}" y2="{pts[j][1]}" stroke="#fff" '
                    f'stroke-opacity=".34" stroke-width="2"/>'
                    for i in range(8) for j in (i + 1, i + 3) if j < 8)
    nodes = "".join(f'<circle cx="{x}" cy="{y}" r="{6 + r[i] % 9}" fill="#fff" fill-opacity="{0.55 + (i % 3) * 0.15:.2f}"/>'
                    for i, (x, y) in enumerate(pts))
    return lines + nodes


MOTIFS = [_radar, _bars, _waves, _dots, _network]


def cover_svg(text):
    r = hashlib.md5((text or "").strip().lower().encode()).digest()
    c1, c2, b1, b2 = PALETTES[r[0] % len(PALETTES)]
    motif = MOTIFS[r[1] % len(MOTIFS)](r)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid slice">'
        f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{c1}"/>'
        f'<stop offset="1" stop-color="{c2}"/></linearGradient><filter id="b" x="-50%" y="-50%" width="200%" height="200%">'
        f'<feGaussianBlur stdDeviation="70"/></filter></defs>'
        f'<rect width="{W}" height="{H}" fill="url(#g)"/>'
        f'<g filter="url(#b)"><circle cx="{120 + r[2] % 200}" cy="{r[3] % 140}" r="150" fill="{b1}" fill-opacity=".6"/>'
        f'<circle cx="{520 + r[4] % 240}" cy="{220 + r[5] % 100}" r="170" fill="{b2}" fill-opacity=".5"/></g>'
        f'{motif}</svg>')
