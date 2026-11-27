"""Generate a green-cheeked conure pet bundle for Orca (Codex sprite layout).

Draws the bird at 48x52 native pixels from parts, then scales each frame 4x to
the 192x208 Codex frame. Output: <out>/pet.json, <out>/spritesheet.webp, and
preview images in <out>/../preview/.
"""
import json
import os
import sys

from PIL import Image, ImageDraw

W, H, SCALE = 48, 52, 2
COLS = 96  # the calm "running" loop has 96 frames, like the built-in Claudino pet

K = (38, 44, 36, 255)
G = (108, 186, 72, 255)
GD = (70, 142, 52, 255)
GL = (150, 214, 100, 255)
GLINE = (48, 104, 42, 255)
CR = (92, 82, 80, 255)
CRL = (120, 108, 104, 255)
WT = (248, 246, 238, 255)
EY = (22, 22, 26, 255)
BK = (66, 66, 74, 255)
BKL = (124, 124, 134, 255)
BKLO = (98, 98, 108, 255)
MOUTH = (150, 60, 70, 255)
BR = (172, 150, 130, 255)
BRD = (120, 100, 90, 255)
R = (168, 42, 52, 255)
RL = (204, 74, 72, 255)
RD = (112, 26, 38, 255)
U = (72, 124, 212, 255)
UD = (44, 80, 160, 255)
FT = (156, 138, 138, 255)
FTD = (104, 90, 92, 255)

EXTRA_COLORS = {
    "N": (120, 110, 230, 255),  # music note
    "Q": (250, 210, 70, 255),   # question mark
    "E": (240, 80, 70, 255),    # exclamation
    "S": (130, 200, 250, 255),  # sweat drop
    "Y": (255, 222, 90, 255),   # sparkle
    "H": (255, 120, 160, 255),  # heart
}
EXTRAS = {
    "note": ["..XX.", "..XXX", "..X.X", "..X..", "XXX..", "XXX..", ".X..."],
    "q": [".XXX.", "XX.XX", "...XX", "..XX.", "..X..", ".....", "..X.."],
    "excl": ["XX", "XX", "XX", "XX", "..", "XX"],
    "drop": [".X.", ".X.", "XXX", "XXX", ".X."],
    "spark": ["..X..", "..X..", "XXXXX", "..X..", "..X.."],
    "heart": [".XX.XX.", "XXXXXXX", "XXXXXXX", ".XXXXX.", "..XXX..", "...X..."],
}
EXTRA_KIND_COLOR = {"note": "N", "q": "Q", "excl": "E", "drop": "S", "spark": "Y", "heart": "H"}

BEAK_CLOSED = [
    ".bbb...",
    "bbBBBb.",
    "BBBBBBB",
    "BBBBBBB",
    "lllBBBB",
    "llll.BB",
    ".ll...B",
]
BEAK_OPEN = [
    ".bbb...",
    "bbBBBb.",
    "BBBBBBB",
    "BBBBBBB",
    "MMMBBBB",
    "MMM..BB",
    "llll..B",
    ".ll....",
]
BEAK_COLORS = {"B": BK, "b": BKL, "l": BKLO, "M": MOUTH}
FOOT = [".ff.", "ffFf"]


def layer():
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))


def fill_ellipse(img, cx, cy, rx, ry, colfn):
    px = img.load()
    for y in range(H):
        for x in range(W):
            dx = (x + 0.5 - cx) / rx
            dy = (y + 0.5 - cy) / ry
            v = dx * dx + dy * dy
            if v <= 1:
                c = colfn(x, y, v) if callable(colfn) else colfn
                if c:
                    px[x, y] = c


def stamp(img, rows, x0, y0, colors):
    px = img.load()
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch in colors:
                x, y = x0 + i, y0 + j
                if 0 <= x < W and 0 <= y < H:
                    px[x, y] = colors[ch]


def outline(img, col):
    """Add a 1px outline outside the opaque area."""
    src = img.load()
    out = img.copy()
    dst = out.load()
    for y in range(H):
        for x in range(W):
            if src[x, y][3]:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < W and 0 <= ny < H and src[nx, ny][3]:
                    dst[x, y] = col
                    break
    return out


def edge_to(img, col):
    """Recolor opaque pixels on the silhouette edge."""
    src = img.load()
    out = img.copy()
    dst = out.load()
    for y in range(H):
        for x in range(W):
            if not src[x, y][3]:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if not (0 <= nx < W and 0 <= ny < H) or not src[nx, ny][3]:
                    dst[x, y] = col
                    break
    return out


def wing_layer(pvx, pvy, angle, mirror):
    L = layer()
    s = 1 if mirror else -1
    cx, cy = pvx + s * 1, pvy + 9

    cy = pvy + 8

    def col(x, y, v):
        Y = y + 0.5 - cy
        if Y > 4:
            return UD if v > 0.6 else U
        if Y < -4:
            return GL
        if v > 0.6 or 0 <= Y < 1:
            return GD
        return G

    fill_ellipse(L, cx, cy, 5, 8.5, col)
    d = ImageDraw.Draw(L)
    d.polygon([(cx - 3, cy + 5), (cx + 3, cy + 5), (cx + s * 4, cy + 12)], fill=UD)
    if angle:
        L = L.rotate(angle, resample=Image.NEAREST, center=(pvx, pvy))
    return outline(L, GLINE)


def bird(p):
    ox, oy = p.get("x", 0), p.get("y", 0)
    hx, hy = p.get("hx", 0), p.get("hy", 0)
    sq = p.get("sq", 0)
    tail = p.get("tail", 0)

    bottom = 45 + oy
    bry = 10 - sq
    brx = 10.5 + sq * 0.5
    bcx = 23.5 + ox
    bcy = bottom - bry

    out = layer()

    # tail
    T = layer()
    d = ImageDraw.Draw(T)
    d.polygon(
        [(bcx - 7, bcy + 3), (bcx - 2, bcy + 6), (bcx - 8 + tail, bcy + 16), (bcx - 12 + tail, bcy + 15)],
        fill=R,
    )
    d.line([(bcx - 5, bcy + 6), (bcx - 9 + tail, bcy + 14)], fill=RD)
    out.alpha_composite(outline(T, RD))

    # far wing (only visible when raised)
    if p.get("far") is not None:
        out.alpha_composite(wing_layer(bcx + 3, bcy - 6, p["far"], mirror=True))

    # body
    B = layer()

    def body_col(x, y, v):
        X = x + 0.5 - bcx
        Y = y + 0.5 - bcy
        if X > -2 and Y < 1:
            return BRD if (y % 2 == 0 and x % 3 == 0) else BR
        if ((X - 3) / 4.5) ** 2 + ((Y - 3.5) / 2.5) ** 2 <= 1:
            return RL if Y < 2 else R
        if v > 0.7 and X + Y > 4:
            return GD
        return G

    fill_ellipse(B, bcx, bcy, brx, bry, body_col)
    out.alpha_composite(outline(B, GLINE))

    # near wing
    out.alpha_composite(wing_layer(bcx - 4, bcy - 6, p.get("wing", 0), mirror=False))

    # feet
    F = layer()
    lift = p.get("feet", (0, 0))
    for i, fx in enumerate((int(bcx - 6), int(bcx + 1))):
        stamp(F, FOOT, fx, int(bottom) - 1 - lift[i], {"f": FT, "F": FTD})
    out.alpha_composite(outline(F, FTD))

    # head (with eye and beak), rotated as one piece
    Hd = layer()
    hcx = 25 + ox + hx
    hcy = bcy - 13 + hy

    def head_col(x, y, v):
        X = x + 0.5 - hcx
        Y = y + 0.5 - hcy
        if ((X + 4) / 10) ** 2 + ((Y + 9.5) / 7) ** 2 <= 1 or ((X + 10) / 5) ** 2 + ((Y + 2) / 6) ** 2 <= 1:
            return CRL if ((X + 4) / 4) ** 2 + ((Y + 8) / 1.5) ** 2 <= 1 else CR
        if ((X - 3) / 5) ** 2 + ((Y - 4) / 3.5) ** 2 <= 1:
            return GL
        if v > 0.75 and X + Y > 3:
            return GD
        return G

    fill_ellipse(Hd, hcx, hcy, 12, 11, head_col)

    ex, ey = int(hcx + 4), int(hcy - 1)
    fill_ellipse(Hd, ex + 1.0, ey + 0.5, 2.6, 3.0, WT)
    px = Hd.load()
    eye = p.get("eye", "open")

    def put(pts, c=EY):
        for x, y in pts:
            px[x, y] = c

    if eye == "open":
        put([(ex, ey - 1), (ex + 1, ey - 1), (ex, ey), (ex + 1, ey), (ex, ey + 1), (ex + 1, ey + 1)])
        put([(ex, ey - 1)], WT)
    elif eye == "wide":
        put([(ex, ey - 1), (ex + 1, ey - 1), (ex, ey), (ex + 1, ey), (ex, ey + 1), (ex + 1, ey + 1), (ex + 2, ey), (ex + 2, ey + 1)])
        put([(ex, ey - 1), (ex + 2, ey + 1)], WT)
    elif eye == "blink":
        put([(ex - 1, ey + 1), (ex, ey + 1), (ex + 1, ey + 1), (ex + 2, ey + 1)])
    elif eye == "happy":
        put([(ex - 1, ey + 1), (ex, ey), (ex + 1, ey), (ex + 2, ey + 1)])
    elif eye == "squint":
        put([(ex - 1, ey), (ex, ey), (ex + 1, ey), (ex + 2, ey)])
    elif eye == "sad":
        put([(ex, ey), (ex + 1, ey), (ex, ey + 1), (ex + 1, ey + 1)])
        put([(ex - 1, ey - 1), (ex, ey - 2), (ex + 1, ey - 2), (ex + 2, ey - 3)])
    elif eye == "x":
        put([(ex - 1, ey - 1), (ex + 2, ey - 1), (ex, ey), (ex + 1, ey), (ex - 1, ey + 1), (ex + 2, ey + 1)])

    beak = BEAK_OPEN if p.get("beak") else BEAK_CLOSED
    stamp(Hd, beak, int(hcx + 9), int(hcy - 3), BEAK_COLORS)

    if p.get("tilt"):
        Hd = Hd.rotate(p["tilt"], resample=Image.NEAREST, center=(hcx, hcy + 4))
    out.alpha_composite(outline(Hd, GLINE))

    out = edge_to(out, K)

    # shadow under the bird
    k = max(0.45, 1 + oy / 10)
    sh = layer()
    fill_ellipse(sh, 24 + ox, 47.5, 9 * k, 1.4, (0, 0, 0, 50))
    sh.alpha_composite(out)
    out = sh

    # extras (notes, sparkles, ...)
    for kind, x0, y0, *alpha in p.get("extras", []):
        X = layer()
        stamp(X, EXTRAS[kind], x0, y0, {"X": EXTRA_COLORS[EXTRA_KIND_COLOR[kind]]})
        X = outline(X, K)
        if alpha:
            X.putalpha(X.getchannel("A").point(lambda a: int(a * alpha[0])))
        out.alpha_composite(X)

    if p.get("flip"):
        out = out.transpose(Image.FLIP_LEFT_RIGHT)
    return out


HOP = [
    {"sq": 1},
    {"y": -2, "wing": -25, "tail": -1, "hx": 1},
    {"y": -4, "wing": -45, "tail": -2, "hx": 1, "feet": (1, 1)},
    {"y": -2, "wing": -20, "tail": -1},
    {"sq": 1},
    {"y": -2, "wing": -25, "tail": -1, "hx": 1},
    {"y": -4, "wing": -45, "tail": -2, "hx": 1, "eye": "happy", "feet": (1, 1)},
    {"y": -2, "wing": -20, "tail": -1},
]

# Claudino (Orca's built-in pet) is 96 frames at 82-84 ms each: an 8 s loop at about 12 fps.
CLAUDINO_DURATIONS = [83, 83, 84] * 32


def calm_singing():
    """96-frame working loop: two short sung phrases with a soft 1px nod and one
    slowly rising note, separated by stillness. No hopping or wing moves."""
    phrases = [(8, 40, 0), (56, 88, 6)]  # (start, end, head tilt)
    frames = []
    for t in range(96):
        f = {}
        for start, end, tilt in phrases:
            if start <= t < end:
                k = t - start
                f["eye"] = "happy"
                f["beak"] = 1 if k % 8 < 4 else 0
                f["hy"] = 1 if (k // 6) % 2 else 0
                if tilt:
                    f["tilt"] = tilt
                fade = min(1.0, k / 4, (end - start - k) / 8)
                f["extras"] = [("note", 38 + k // 16, 12 - k // 3, fade)]
        if 24 <= t < 72:
            f["tail"] = 1
        if t in (46, 47, 92):
            f["eye"] = "blink"
        frames.append(f)
    return frames


ANIMS = [
    ("idle", [
        {}, {"sq": 1}, {"eye": "blink"}, {"tilt": 8}, {"tilt": 8, "tail": 1, "sq": 1}, {},
    ], [1400, 700, 130, 900, 700, 1100]),
    ("running-right", HOP, [90, 90, 120, 90, 90, 90, 120, 90]),
    ("running-left", [dict(f, flip=True) for f in HOP], [90, 90, 120, 90, 90, 90, 120, 90]),
    ("waving", [
        {"wing": -120, "eye": "happy"},
        {"wing": -155, "eye": "happy", "beak": 1, "extras": [("heart", 37, 5)]},
        {"wing": -120, "eye": "happy", "extras": [("heart", 37, 3)]},
        {"wing": -155, "eye": "happy", "beak": 1, "extras": [("heart", 38, 1)]},
    ], [200, 200, 200, 260]),
    ("jumping", [
        {"sq": 2, "eye": "blink"},
        {"y": -5, "wing": -70, "far": 70, "tail": 2, "feet": (1, 1)},
        {"y": -7, "wing": -115, "far": 115, "eye": "happy", "beak": 1, "feet": (1, 1),
         "extras": [("spark", 4, 6), ("spark", 39, 4)]},
        {"y": -4, "wing": -80, "far": 80, "tail": 1},
        {"sq": 1},
    ], [170, 120, 260, 140, 220]),
    ("failed", [
        {"eye": "wide", "y": -1, "wing": -30, "extras": [("excl", 38, 2)]},
        {"eye": "x", "x": -1},
        {"eye": "x", "x": 1},
        {"eye": "x", "x": -1},
        {"eye": "sad", "hy": 2, "sq": 1, "wing": -8, "extras": [("drop", 37, 9)]},
        {"eye": "sad", "hy": 2, "sq": 1, "wing": -8, "extras": [("drop", 37, 10)]},
        {"eye": "blink", "hy": 2, "sq": 1, "wing": -8, "extras": [("drop", 37, 11)]},
        {"eye": "sad", "hy": 2, "sq": 1, "wing": -8, "tail": -1},
    ], [320, 90, 90, 90, 420, 420, 220, 600]),
    ("waiting", [
        {"extras": [("q", 38, 2)]},
        {"tilt": 12, "extras": [("q", 38, 1)]},
        {"tilt": 12, "eye": "blink", "extras": [("q", 38, 1)]},
        {"tilt": -8, "feet": (2, 0), "extras": [("q", 38, 2)]},
        {"tilt": -8, "extras": [("q", 38, 2)]},
        {"feet": (2, 0), "extras": [("q", 38, 2)]},
    ], [500, 500, 140, 260, 400, 260]),
    ("running", calm_singing(), CLAUDINO_DURATIONS),
    ("review", [
        {"hx": 1, "tilt": -10},
        {"hx": 2, "hy": 1, "tilt": -14, "eye": "squint"},
        {"hx": 2, "hy": 1, "tilt": -14, "eye": "squint", "feet": (0, 3)},
        {"hx": 1, "tilt": -6},
        {"eye": "happy", "beak": 1, "extras": [("spark", 38, 4)]},
        {"eye": "happy", "extras": [("spark", 39, 2), ("spark", 5, 8)]},
    ], [450, 450, 500, 220, 320, 520]),
]


def main(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    preview_dir = os.path.join(os.path.dirname(out_dir.rstrip("/")), "preview")
    os.makedirs(preview_dir, exist_ok=True)

    fw, fh = W * SCALE, H * SCALE
    sheet = Image.new("RGBA", (COLS * fw, len(ANIMS) * fh), (0, 0, 0, 0))
    native = Image.new("RGBA", (COLS * W, len(ANIMS) * H), (0, 0, 0, 0))
    animations = {}
    for row, (name, frames, durations) in enumerate(ANIMS):
        assert len(frames) == len(durations) <= COLS, name
        gif_frames = []
        for col, p in enumerate(frames):
            img = bird(p)
            native.alpha_composite(img, (col * W, row * H))
            big = img.resize((fw, fh), Image.NEAREST)
            sheet.alpha_composite(big, (col * fw, row * fh))
            bg = Image.new("RGBA", (fw, fh), (236, 240, 244, 255))
            bg.alpha_composite(big)
            gif_frames.append(bg.convert("RGB"))
        gif_frames[0].save(
            os.path.join(preview_dir, f"{name}.gif"), save_all=True, append_images=gif_frames[1:],
            duration=durations, loop=0,
        )
        animations[name] = {"row": row, "frames": len(frames), "frameDurationsMs": durations}

    sheet.save(os.path.join(out_dir, "spritesheet.webp"), lossless=True)
    manifest = {
        "id": "green-cheek-conure",
        "displayName": "Conure",
        "description": "A green-cheeked conure that head-bobs while your agents work.",
        "spritesheetPath": "spritesheet.webp",
        "frame": {"width": fw, "height": fh},
        "fps": 8,
        "defaultAnimation": "idle",
        "animations": animations,
    }
    with open(os.path.join(out_dir, "pet.json"), "w") as f:
        json.dump(manifest, f, indent=2)

    bg = Image.new("RGBA", native.size, (236, 240, 244, 255))
    bg.alpha_composite(native)
    bg.resize((native.width * 2, native.height * 2), Image.NEAREST).save(os.path.join(preview_dir, "contact.png"))
    print("wrote", out_dir, sheet.size)


if __name__ == "__main__":
    main(sys.argv[1])
