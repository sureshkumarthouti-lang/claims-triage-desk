"""Procedurally drawn claim photos (stylized but recognizable) with phone-style EXIF."""
import math, random, io
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageChops
import piexif

W, H = 1600, 1200
SS = 2

def clamp(c):
    return tuple(max(0, min(255, int(v))) for v in c)

def shade(c, f):
    return clamp((c[0] * f, c[1] * f, c[2] * f))

def mix(a, b, t):
    return clamp((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t))

def vgrad(w, h, c1, c2):
    m = Image.linear_gradient("L").resize((max(1, w), max(1, h)))
    return Image.composite(Image.new("RGB", (w, h), c2), Image.new("RGB", (w, h), c1), m)

def qmap(q, u, v):
    tl, tr, br, bl = q
    tx, ty = tl[0] + (tr[0] - tl[0]) * u, tl[1] + (tr[1] - tl[1]) * u
    bx, by = bl[0] + (br[0] - bl[0]) * u, bl[1] + (br[1] - bl[1]) * u
    return (tx + (bx - tx) * v, ty + (by - ty) * v)


class Drawer:
    def __init__(self, img):
        self.img = img
        self.d = ImageDraw.Draw(img)

    def s(self, pts):
        return [(x * SS, y * SS) for x, y in pts]

    def poly(self, pts, fill=None, outline=None, width=1):
        self.d.polygon(self.s(pts), fill=fill, outline=outline, width=int(width * SS) if outline else 0)

    def rect(self, x0, y0, x1, y1, fill=None, outline=None, width=1, r=0):
        box = [x0 * SS, y0 * SS, x1 * SS, y1 * SS]
        if r:
            self.d.rounded_rectangle(box, radius=r * SS, fill=fill, outline=outline, width=int(width * SS) if outline else 0)
        else:
            self.d.rectangle(box, fill=fill, outline=outline, width=int(width * SS) if outline else 0)

    def ell(self, x0, y0, x1, y1, fill=None, outline=None, width=1):
        self.d.ellipse([x0 * SS, y0 * SS, x1 * SS, y1 * SS], fill=fill, outline=outline, width=int(width * SS) if outline else 0)

    def circ(self, cx, cy, r, fill=None, outline=None, width=1):
        self.ell(cx - r, cy - r, cx + r, cy + r, fill, outline, width)

    def line(self, pts, fill, width=2):
        self.d.line(self.s(pts), fill=fill, width=max(1, int(width * SS)), joint="curve")

    def arc(self, box, start, end, fill, width=2):
        self.d.arc([b * SS for b in box], start, end, fill=fill, width=max(1, int(width * SS)))


class Scene(Drawer):
    def __init__(self, seed, bg=(128, 128, 128)):
        super().__init__(Image.new("RGB", (W * SS, H * SS), bg))
        self.rnd = random.Random(seed)

    def grad(self, x0, y0, x1, y1, c1, c2):
        g = vgrad(int((x1 - x0) * SS), int((y1 - y0) * SS), c1, c2)
        self.img.paste(g, (int(x0 * SS), int(y0 * SS)))

    def grad_poly(self, pts, c1, c2, y0=None, y1=None):
        ys = [p[1] for p in pts]
        y0 = min(ys) if y0 is None else y0
        y1 = max(ys) if y1 is None else y1
        g = vgrad(W * SS, max(1, int((y1 - y0) * SS)), c1, c2)
        full = Image.new("RGB", (W * SS, H * SS))
        full.paste(g, (0, int(y0 * SS)))
        mask = Image.new("L", (W * SS, H * SS), 0)
        ImageDraw.Draw(mask).polygon(self.s(pts), fill=255)
        self.img.paste(full, (0, 0), mask)

    def layer(self):
        return Drawer(Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0)))

    def comp(self, lay, clip=None, blur=0, opacity=1.0):
        im = lay.img
        if blur:
            im = im.filter(ImageFilter.GaussianBlur(blur * SS))
        if clip is not None or opacity < 1:
            a = im.split()[3]
            if clip is not None:
                m = Image.new("L", im.size, 0)
                ImageDraw.Draw(m).polygon(self.s(clip), fill=255)
                a = ImageChops.multiply(a, m)
            if opacity < 1:
                a = a.point(lambda v: int(v * opacity))
            im.putalpha(a)
        base = self.img.convert("RGBA")
        base.alpha_composite(im)
        self.img = base.convert("RGB")
        self.d = ImageDraw.Draw(self.img)

    def soft_shadow(self, box, alpha=150, blur=18):
        lay = self.layer()
        lay.ell(*box, fill=(0, 0, 0, alpha))
        self.comp(lay, blur=blur)

    def noise_patch(self, pts, color, n=400, size=(1, 3), alpha=120):
        lay = self.layer()
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        for _ in range(n):
            x = self.rnd.uniform(min(xs), max(xs)); y = self.rnd.uniform(min(ys), max(ys))
            r = self.rnd.uniform(*size)
            c = shade(color, self.rnd.uniform(0.7, 1.3))
            lay.circ(x, y, r, fill=c + (alpha,))
        self.comp(lay, clip=pts)

    def crack(self, x, y, n=8, length=320, width=2.2, clip=None, color=(235, 238, 242), dark=(40, 44, 52), star=True):
        lay = self.layer()
        for i in range(n):
            ang = (i / n) * 2 * math.pi + self.rnd.uniform(-0.3, 0.3)
            L = self.rnd.uniform(0.35, 1.0) * length
            self._walk(lay, x, y, ang, L, width, color, dark, depth=0)
        if star:
            for r in (10, 22, 36):
                pts = []
                for k in range(14):
                    a = k / 14 * 2 * math.pi
                    rr = r * self.rnd.uniform(0.75, 1.2)
                    pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
                pts.append(pts[0])
                lay.line(pts, dark + (150,), width * 0.9)
                lay.line(pts, color + (220,), width * 0.6)
            lay.circ(x, y, 7, fill=(250, 250, 252, 230))
        self.comp(lay, clip=clip)

    def _walk(self, lay, x, y, ang, L, width, color, dark, depth):
        pts = [(x, y)]
        step = 14
        for _ in range(int(L / step)):
            ang += self.rnd.uniform(-0.32, 0.32)
            x += step * math.cos(ang); y += step * math.sin(ang)
            pts.append((x, y))
            if depth < 2 and self.rnd.random() < 0.06:
                self._walk(lay, x, y, ang + self.rnd.choice([-1, 1]) * self.rnd.uniform(0.4, 1.1), L * 0.35, width * 0.75, color, dark, depth + 1)
        lay.line(pts, dark + (160,), width + 1.6)
        lay.line(pts, color + (235,), width)

    def dent(self, cx, cy, rx, ry, depth=0.55, light_dir=(-1, -1), crease=True, clip=None):
        lay = self.layer()
        steps = 9
        for i in range(steps):
            t = i / steps
            a = int(30 + depth * 150 * t)
            lay.ell(cx - rx * (1 - t * 0.8), cy - ry * (1 - t * 0.8), cx + rx * (1 - t * 0.8), cy + ry * (1 - t * 0.8), fill=(0, 0, 0, a // 2))
        self.comp(lay, blur=max(2, rx * 0.12), clip=clip)
        hl = self.layer()
        lx, ly = light_dir
        hl.arc((cx - rx * 0.95, cy - ry * 0.95, cx + rx * 0.95, cy + ry * 0.95), 30, 160, fill=(255, 255, 255, 120), width=max(2, rx * 0.06))
        self.comp(hl, blur=max(1, rx * 0.04), clip=clip)
        if crease:
            cl = self.layer()
            for _ in range(4):
                a = self.rnd.uniform(0, math.pi)
                l = self.rnd.uniform(0.5, 1.0)
                p1 = (cx - rx * l * math.cos(a), cy - ry * l * math.sin(a))
                p2 = (cx + rx * l * math.cos(a), cy + ry * l * math.sin(a))
                cl.line([p1, (cx + self.rnd.uniform(-8, 8), cy + self.rnd.uniform(-8, 8)), p2], (20, 20, 22, 110), 2.2)
                cl.line([(p1[0] + 3, p1[1] - 3), (cx + 3, cy - 3), (p2[0] + 3, p2[1] - 3)], (255, 255, 255, 70), 1.5)
            self.comp(cl, clip=clip, blur=0.6)

    def shards(self, x0, y0, x1, y1, n=60, color=(220, 232, 240), size=(4, 14)):
        lay = self.layer()
        for _ in range(n):
            x = self.rnd.uniform(x0, x1); y = self.rnd.uniform(y0, y1)
            s = self.rnd.uniform(*size)
            pts = [(x + s * math.cos(a), y + s * 0.55 * math.sin(a)) for a in sorted(self.rnd.uniform(0, 2 * math.pi) for _ in range(3))]
            c = shade(color, self.rnd.uniform(0.75, 1.15))
            lay.poly(pts, fill=c + (230,), outline=(255, 255, 255, 200), width=0.6)
        self.comp(lay)

    def finish(self, crop=None, night=False, flash=False, warm=0.0, seed=0, rot=None):
        img = self.img
        if crop:
            x0, y0, x1, y1 = crop
            img = img.crop((int(x0 * SS), int(y0 * SS), int(x1 * SS), int(y1 * SS)))
        img = img.resize((W, H), Image.LANCZOS)
        r = random.Random(seed)
        angle = rot if rot is not None else r.uniform(-1.4, 1.4)
        img = img.rotate(angle, resample=Image.BICUBIC, expand=False)
        img = img.crop((24, 18, W - 24, H - 18)).resize((W, H), Image.LANCZOS)
        img = img.filter(ImageFilter.GaussianBlur(0.7))
        if night:
            img = ImageEnhance.Brightness(img).enhance(0.9)
        if flash:
            m = Image.radial_gradient("L").resize((W, H))
            m = m.point(lambda v: int(min(255, v * 1.05)))
            dark = ImageEnhance.Brightness(img).enhance(0.62)
            bright = ImageEnhance.Brightness(img).enhance(1.12)
            img = Image.composite(dark, bright, m)
        # vignette
        v = Image.radial_gradient("L").resize((W, H)).point(lambda p: int(p * (0.35 if night else 0.55)))
        img = Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), img, v)
        if warm:
            rch, gch, bch = img.split()
            rch = rch.point(lambda p: min(255, int(p * (1 + warm))))
            bch = bch.point(lambda p: int(p * (1 - warm)))
            img = Image.merge("RGB", (rch, gch, bch))
        # sensor noise
        sigma = 14 if night else 7
        n = Image.effect_noise((W, H), sigma).convert("L")
        n = Image.merge("RGB", (n, n, n))
        img = ImageChops.add(img, n, scale=1.0, offset=-128)
        return img


# =============================================================== backgrounds
def bg_lot(sc, sky=((150, 180, 210), (215, 225, 235)), horizon=430, asphalt=((92, 94, 98), (60, 62, 66))):
    sc.grad(0, 0, W, horizon, *sky)
    # distant buildings / trees
    x = -20
    while x < W:
        w = sc.rnd.uniform(90, 220); h = sc.rnd.uniform(60, 170)
        c = shade((120, 128, 136), sc.rnd.uniform(0.8, 1.1))
        sc.rect(x, horizon - h, x + w, horizon, fill=c)
        for wy in range(int(horizon - h + 14), int(horizon - 10), 26):
            for wx in range(int(x + 10), int(x + w - 14), 30):
                sc.rect(wx, wy, wx + 14, wy + 12, fill=shade(c, 0.75))
        x += w + sc.rnd.uniform(-10, 30)
    for _ in range(14):
        tx = sc.rnd.uniform(0, W); tr = sc.rnd.uniform(40, 80)
        sc.circ(tx, horizon - tr * 0.6, tr, fill=shade((70, 96, 62), sc.rnd.uniform(0.8, 1.15)))
    sc.grad(0, horizon, W, H, *asphalt)
    sc.noise_patch([(0, horizon), (W, horizon), (W, H), (0, H)], (110, 110, 112), n=2500, size=(0.8, 2.2), alpha=60)
    # parking lines in perspective
    vx = W / 2
    for k in range(-5, 7):
        xb = vx + k * 380
        sc.poly([(vx + k * 70, horizon + 8), (vx + k * 70 + 6, horizon + 8), (xb + 22, H), (xb, H)], fill=(225, 222, 205))

def bg_garage(sc):
    sc.grad(0, 0, W, 300, (70, 72, 76), (110, 112, 116))
    for x in (220, 760, 1300):
        sc.rect(x, 120, x + 160, 150, fill=(245, 248, 240))
        lay = sc.layer(); lay.rect(x - 80, 80, x + 240, 200, fill=(255, 255, 230, 60)); sc.comp(lay, blur=30)
    sc.grad(0, 300, W, 520, (150, 150, 148), (130, 130, 128))
    sc.grad(0, 520, W, H, (128, 126, 122), (98, 96, 92))
    sc.noise_patch([(0, 520), (W, 520), (W, H), (0, H)], (140, 138, 132), n=2500, size=(0.8, 2), alpha=50)
    for x in (80, 1400):
        sc.rect(x, 220, x + 130, 980, fill=(176, 174, 168))
        for y in range(840, 980, 34):
            sc.poly([(x, y), (x + 130, y - 30), (x + 130, y - 10), (x, y + 20)], fill=(220, 180, 30))
        sc.rect(x, 220, x + 130, 980, outline=(120, 118, 112), width=3)
    sc.rect(110, 330, 180, 400, fill=(30, 70, 140)); sc.d.text((126 * SS, 338 * SS), "2", fill=(255, 255, 255))
    for k in range(-4, 6):
        sc.line([(800 + k * 80, 530), (800 + k * 420, H)], (230, 225, 200), 5)

def bg_shop(sc):
    sc.grad(0, 0, W, 560, (176, 186, 196), (150, 160, 170))
    for x in (60, 560, 1060):
        sc.rect(x, 60, x + 440, 470, fill=(205, 210, 214), outline=(120, 126, 132), width=4)
        for y in range(90, 470, 46):
            sc.line([(x + 6, y), (x + 434, y)], (160, 166, 172), 3)
    sc.rect(1300, 300, 1560, 560, fill=(170, 30, 30)); sc.rect(1300, 300, 1560, 560, outline=(90, 10, 10), width=3)
    for y in range(330, 560, 44):
        sc.line([(1310, y), (1550, y)], (110, 15, 15), 3)
    sc.grad(0, 560, W, H, (120, 124, 128), (84, 88, 92))
    sc.noise_patch([(0, 560), (W, 560), (W, H), (0, H)], (130, 130, 130), n=1500, size=(1, 3), alpha=40)
    sc.rect(0, 556, W, 566, fill=(230, 190, 40))

def bg_road(sc):
    sc.grad(0, 0, W, 420, (120, 110, 140), (230, 170, 150))
    for _ in range(18):
        tx = sc.rnd.uniform(0, W); tr = sc.rnd.uniform(50, 110)
        sc.circ(tx, 420 - tr * 0.4, tr, fill=shade((40, 60, 46), sc.rnd.uniform(0.8, 1.2)))
    sc.grad(0, 420, W, 520, (70, 92, 60), (60, 80, 52))
    sc.grad(0, 520, W, H, (70, 72, 78), (44, 46, 52))
    lay = sc.layer()
    for _ in range(40):
        x = sc.rnd.uniform(0, W); y = sc.rnd.uniform(560, H)
        lay.ell(x - 80, y - 4, x + 80, y + 4, fill=(200, 160, 160, 40))
    sc.comp(lay, blur=4)
    # guardrail
    sc.poly([(0, 480), (W, 440), (W, 500), (0, 545)], fill=(170, 176, 182))
    sc.poly([(0, 495), (W, 455), (W, 470), (0, 510)], fill=(210, 214, 220))
    for x in range(40, W, 180):
        y = 545 - x * 0.028
        sc.rect(x, y - 10, x + 18, y + 120, fill=(120, 110, 96))

def bg_driveway(sc):
    sc.grad(0, 0, W, 420, (110, 140, 180), (190, 205, 220))
    for _ in range(10):
        tx = sc.rnd.uniform(0, W); tr = sc.rnd.uniform(60, 120)
        sc.circ(tx, 420 - tr * 0.3, tr, fill=shade((66, 92, 56), sc.rnd.uniform(0.8, 1.2)))
    sc.grad(0, 420, W, H, (98, 128, 70), (70, 98, 50))
    sc.poly([(500, 420), (1100, 420), (1500, H), (100, H)], fill=(150, 140, 125))
    sc.noise_patch([(500, 420), (1100, 420), (1500, H), (100, H)], (175, 165, 150), n=4000, size=(1, 3.5), alpha=140)
    # oak tree trunk on the right
    sc.poly([(1270, 120), (1350, 120), (1380, 760), (1240, 760)], fill=(88, 66, 48))
    for y in range(140, 760, 36):
        sc.line([(1255, y), (1365, y + 10)], (60, 44, 32), 4)
    sc.circ(1310, 80, 220, fill=(56, 84, 46))

def bg_night_street(sc):
    sc.grad(0, 0, W, 460, (24, 26, 40), (64, 62, 72))
    for x in range(-20, W, 260):
        h = sc.rnd.uniform(120, 260)
        sc.rect(x, 460 - h, x + 220, 460, fill=(40, 40, 50))
        for wy in range(int(460 - h + 20), 440, 40):
            for wx in range(x + 20, x + 200, 50):
                if sc.rnd.random() < 0.4:
                    sc.rect(wx, wy, wx + 22, wy + 18, fill=(230, 200, 120))
    for x in (200, 1100):
        sc.rect(x, 80, x + 14, 460, fill=(30, 30, 34))
        lay = sc.layer(); lay.circ(x + 7, 80, 120, fill=(255, 210, 140, 70)); sc.comp(lay, blur=40)
        sc.circ(x + 7, 80, 14, fill=(255, 230, 180))
    sc.grad(0, 460, W, H, (78, 78, 84), (44, 44, 48))
    lay = sc.layer()
    for _ in range(30):
        x = sc.rnd.uniform(0, W); y = sc.rnd.uniform(500, H)
        lay.ell(x - 60, y - 3, x + 60, y + 3, fill=(255, 200, 130, 40))
    sc.comp(lay, blur=4)

def bg_deck(sc):
    sc.grad(0, 0, W, 360, (60, 62, 66), (92, 94, 98))
    for x in (300, 900, 1400):
        sc.rect(x, 90, x + 140, 112, fill=(250, 250, 240))
        lay = sc.layer(); lay.rect(x - 70, 50, x + 210, 170, fill=(255, 255, 230, 70)); sc.comp(lay, blur=30)
    sc.grad(0, 360, W, H, (104, 104, 102), (70, 70, 70))
    sc.rect(0, 300, 120, 960, fill=(140, 140, 136)); sc.d.text((30 * SS, 400 * SS), "3", fill=(240, 240, 240))
    sc.noise_patch([(0, 360), (W, 360), (W, H), (0, H)], (120, 120, 118), n=2000, size=(1, 2), alpha=40)


# =============================================================== cars
def body_points(kind):
    if kind == "suv":
        return [(0.0, 0.66), (0.02, 0.50), (0.05, 0.45), (0.25, 0.40), (0.28, 0.39), (0.38, 0.06), (0.92, 0.05), (0.97, 0.10),
                (0.995, 0.40), (1.0, 0.75), (0.98, 0.88), (0.02, 0.88)], [(0.295, 0.38), (0.39, 0.10), (0.90, 0.09), (0.95, 0.38)], (0.56, 0.78), 0.36
    if kind == "truck":
        return [(0.0, 0.62), (0.02, 0.46), (0.05, 0.40), (0.27, 0.36), (0.36, 0.06), (0.55, 0.05), (0.57, 0.07), (0.57, 0.38),
                (0.995, 0.38), (1.0, 0.78), (0.98, 0.88), (0.02, 0.88)], [(0.285, 0.35), (0.37, 0.10), (0.54, 0.09), (0.545, 0.35)], (0.44,), 0.37
    return [(0.01, 0.86), (0.0, 0.70), (0.02, 0.58), (0.06, 0.52), (0.27, 0.46), (0.30, 0.45), (0.42, 0.10), (0.62, 0.08),
            (0.80, 0.40), (0.95, 0.43), (0.995, 0.55), (1.0, 0.72), (0.98, 0.86)], [(0.315, 0.44), (0.43, 0.15), (0.61, 0.13), (0.77, 0.41)], (0.53,), 0.30

def draw_car_side(sc, x0, ground, length, color, kind="sedan", flip=False, damage=None, sev="moderate"):
    pts, win, pillars, hr = body_points(kind)
    h = length * hr
    top = ground - h
    def P(u, v):
        uu = 1 - u if flip else u
        return (x0 + uu * length, top + v * h)
    r = length * 0.072
    wheels = [0.18, 0.80] if kind != "truck" else [0.17, 0.82]
    sc.soft_shadow((x0 - 20, ground - 28, x0 + length + 20, ground + 26), alpha=170, blur=14)
    body = [P(u, v) for u, v in pts]
    sc.grad_poly(body, shade(color, 1.35), shade(color, 0.55))
    # gloss band
    lay = sc.layer()
    lay.poly([P(0.05, 0.50), P(0.97, 0.47), P(0.97, 0.53), P(0.05, 0.56)], fill=(255, 255, 255, 55))
    sc.comp(lay, clip=body, blur=6)
    # windows
    wpts = [P(u, v) for u, v in win]
    sc.grad_poly(wpts, (70, 86, 104), (26, 32, 42))
    lay = sc.layer(); lay.poly([P(win[0][0] + 0.05, win[0][1]), P(win[1][0] + 0.08, win[1][1]), P(win[1][0] + 0.13, win[1][1]), P(win[0][0] + 0.10, win[0][1])], fill=(200, 220, 240, 60))
    sc.comp(lay, clip=wpts, blur=4)
    for pu in pillars:
        sc.line([P(pu, win[0][1] + 0.01), P(pu + 0.01, win[1][1] + 0.0)], shade(color, 0.35), length * 0.012)
    # door seams + handles
    seams = [0.33, 0.55, 0.76] if kind != "truck" else [0.29, 0.57]
    for su in seams:
        sc.line([P(su, 0.40), P(su - 0.01, 0.84)], shade(color, 0.45), 2.4)
    for hu in ([0.42, 0.63] if kind != "truck" else [0.47]):
        a = P(hu, 0.52); sc.rect(a[0] - 18, a[1] - 5, a[0] + 18, a[1] + 5, fill=shade(color, 0.6), r=4)
    # lights
    hl = [P(0.0, 0.56), P(0.07, 0.53), P(0.075, 0.60), P(0.005, 0.64)]
    sc.poly(hl, fill=(232, 236, 240), outline=(80, 84, 90), width=1.5)
    tl = [P(0.99, 0.50), P(0.93, 0.48), P(0.93, 0.56), P(0.995, 0.58)]
    sc.poly(tl, fill=(170, 24, 26), outline=(70, 10, 10), width=1.5)
    # mirror
    m = P(0.30 if kind != "suv" else 0.29, 0.40)
    sc.ell(m[0] - 22, m[1] - 14, m[0] + 22, m[1] + 14, fill=shade(color, 0.8), outline=shade(color, 0.4), width=1.5)
    # lower trim
    sc.poly([P(0.02, 0.82), P(0.98, 0.82), P(0.98, 0.88), P(0.02, 0.88)], fill=(36, 36, 38))
    # wheels
    for wu in wheels:
        c = P(wu, 1.0); cx, cy = c[0], ground - r
        sc.circ(cx, cy, r * 1.18, fill=(18, 18, 20))
        sc.circ(cx, cy, r, fill=(34, 34, 36))
        sc.circ(cx, cy, r * 0.62, fill=(178, 182, 188), outline=(110, 112, 118), width=2)
        for k in range(5):
            a = k / 5 * 2 * math.pi
            sc.line([(cx, cy), (cx + r * 0.58 * math.cos(a), cy + r * 0.58 * math.sin(a))], (120, 122, 128), 5)
        sc.circ(cx, cy, r * 0.14, fill=(90, 92, 96))
    geo = {"P": P, "body": body, "win": wpts, "h": h, "top": top, "r": r}
    if damage:
        damage_side(sc, geo, damage, color, sev, kind)
    return geo

def damage_side(sc, g, damage, color, sev, kind):
    P = g["P"]
    if damage in ("front_left", "front_right", "front_center", "front"):
        big = sev == "heavy"
        u1 = 0.26 if big else 0.18
        crush = [P(0.0, 0.48), P(u1 * 0.6, 0.44), P(u1, 0.50), P(u1 * 0.9, 0.66), P(u1, 0.84), P(0.0, 0.86)]
        sc.dent((crush[1][0] + crush[2][0]) / 2, P(0, 0.62)[1], abs(P(u1, 0)[0] - P(0, 0)[0]) * 0.65, g["h"] * 0.26, depth=0.9, clip=g["body"])
        lay = sc.layer()
        jag = [P(0.0, 0.50)]
        for k in range(10):
            jag.append(P(sc.rnd.uniform(0.02, u1 * 0.55), 0.50 + k * 0.035))
        jag.append(P(0.0, 0.86))
        lay.poly(jag, fill=(24, 22, 22, 235))
        sc.comp(lay, clip=g["body"])
        # radiator grid exposed
        gl = sc.layer()
        for k in range(8):
            gl.line([P(0.01, 0.55 + k * 0.035), P(u1 * 0.45, 0.55 + k * 0.035)], (130, 130, 130, 160), 2)
        sc.comp(gl, clip=jag)
        # broken headlight shards
        hlc = P(0.04, 0.58)
        sc.shards(hlc[0] - 40, hlc[1] - 20, hlc[0] + 40, hlc[1] + 30, n=18, color=(230, 235, 240), size=(5, 12))
        # hood buckled up
        sc.line([P(0.04, 0.50), P(u1 * 0.5, 0.40), P(u1, 0.47)], shade(color, 1.4), 4)
        sc.line([P(0.04, 0.52), P(u1 * 0.5, 0.43), P(u1, 0.49)], shade(color, 0.4), 3)
        # hanging bumper piece
        b = P(0.02, 0.86)
        sc.poly([b, (b[0] + 120 * (1 if P(1, 0)[0] > P(0, 0)[0] else -1), b[1] + 8), (b[0] + 110 * (1 if P(1, 0)[0] > P(0, 0)[0] else -1), b[1] + 34), (b[0] - 6, b[1] + 22)], fill=shade(color, 0.7))
        # debris + fluid
        gnd = P(0.05, 1.0)
        sc.shards(gnd[0] - 140, gnd[1] - 10, gnd[0] + 160, gnd[1] + 30, n=40, color=(200, 200, 205), size=(3, 9))
        lay = sc.layer(); lay.ell(gnd[0] - 120, gnd[1] - 6, gnd[0] + 150, gnd[1] + 24, fill=(20, 40, 30, 120)); sc.comp(lay, blur=6)
    elif damage == "door_intrusion":
        c = P(0.54, 0.60)
        sc.dent(c[0], c[1], g["h"] * 0.95, g["h"] * 0.38, depth=1.0, clip=g["body"])
        sc.dent(c[0] + 30, c[1] + 20, g["h"] * 0.55, g["h"] * 0.22, depth=0.9, clip=g["body"])
        # crumpled door skin: jagged dark crush zone with bright crease edges
        crush = []
        for k in range(12):
            a = k / 12 * 2 * math.pi
            rr = sc.rnd.uniform(0.75, 1.15)
            crush.append((c[0] + g["h"] * 0.62 * rr * math.cos(a), c[1] + g["h"] * 0.24 * rr * math.sin(a)))
        lay = sc.layer(); lay.poly(crush, fill=shade(color, 0.32) + (200,)); sc.comp(lay, clip=g["body"], blur=3)
        cl = sc.layer()
        for k in range(9):
            a = sc.rnd.uniform(0, 2 * math.pi); l1 = sc.rnd.uniform(0.15, 0.6)
            p1 = (c[0] + g["h"] * l1 * math.cos(a), c[1] + g["h"] * 0.25 * l1 * math.sin(a))
            p2 = (c[0] + g["h"] * 0.7 * math.cos(a + 0.4), c[1] + g["h"] * 0.28 * math.sin(a + 0.4))
            cl.line([p1, p2], shade(color, 1.9) + (190,), 3)
            cl.line([(p1[0] + 4, p1[1] + 4), (p2[0] + 4, p2[1] + 4)], (10, 10, 12, 190), 3)
        sc.comp(cl, clip=g["body"])
        # shattered side windows + deployed curtain airbag (puffy, translucent)
        sc.crack(P(0.50, 0.30)[0], P(0.50, 0.30)[1], n=12, length=g["h"] * 0.9, width=1.6, clip=g["win"])
        lay = sc.layer()
        for k in range(9):
            bx = P(0.38 + k * 0.055, 0.22)
            lay.ell(bx[0] - g["h"] * 0.16, bx[1] - g["h"] * 0.08, bx[0] + g["h"] * 0.16, bx[1] + g["h"] * 0.09, fill=(236, 236, 232, 170))
        sc.comp(lay, clip=g["win"], blur=2)
        sc.shards(P(0.4, 1.0)[0], P(0.4, 1.0)[1] - 6, P(0.7, 1.0)[0], P(0.7, 1.0)[1] + 30, n=50)
        # displaced mirror hanging
        m = P(0.30, 0.44)
        sc.line([m, (m[0] - 10, m[1] + 60)], (20, 20, 20), 3)
        sc.ell(m[0] - 38, m[1] + 50, m[0] + 8, m[1] + 80, fill=shade(color, 0.7))
    elif damage == "scrape":
        lay = sc.layer()
        for k in range(26):
            v = sc.rnd.uniform(0.55, 0.76)
            u0 = sc.rnd.uniform(0.28, 0.40); u1 = sc.rnd.uniform(0.62, 0.80)
            col = (240, 240, 240, sc.rnd.randint(90, 200)) if k % 3 else (shade(color, 1.8) + (150,))
            lay.line([P(u0, v), P((u0 + u1) / 2, v + sc.rnd.uniform(-0.01, 0.01)), P(u1, v + sc.rnd.uniform(-0.02, 0.02))], col, sc.rnd.uniform(1.5, 4.5))
        sc.comp(lay, clip=g["body"], blur=0.8)
        sc.dent(P(0.50, 0.66)[0], P(0.50, 0.66)[1], g["h"] * 0.6, g["h"] * 0.1, depth=0.5, clip=g["body"], crease=False)
        m = P(0.30, 0.40)
        sc.ell(m[0] - 26, m[1] - 4, m[0] + 22, m[1] + 30, fill=(28, 28, 30))
        sc.line([(m[0] - 20, m[1] + 6), (m[0] + 10, m[1] + 26)], (200, 200, 200), 2)
        sc.shards(m[0] - 60, P(0.3, 1.0)[1] - 4, m[0] + 80, P(0.3, 1.0)[1] + 20, n=24, color=(40, 40, 42), size=(4, 10))
    elif damage == "window_smashed":
        w = g["win"]
        # rear side window region (between pillar and rear)
        rw = [P(0.545, 0.16), P(0.61, 0.14), P(0.77, 0.41), P(0.545, 0.43)]
        lay = sc.layer()
        lay.poly(rw, fill=(12, 14, 18, 255))
        sc.comp(lay)
        edge = []
        for k in range(14):
            t = k / 13
            edge.append(qmap([rw[0], rw[1], rw[2], rw[3]], t * 0.2 + 0.05 * math.sin(k * 3), 0.1 + t * 0.8))
        sc.crack(P(0.57, 0.36)[0], P(0.57, 0.36)[1], n=10, length=90, width=1.4, clip=rw)
        lay = sc.layer(); lay.poly([rw[0]] + edge + [rw[3]], fill=(190, 205, 215, 150)); sc.comp(lay, clip=rw)
        gx = P(0.66, 1.0)
        sc.shards(gx[0] - 220, gx[1] - 10, gx[0] + 160, gx[1] + 50, n=120, color=(200, 225, 230), size=(3, 9))


def draw_car_front(sc, cx, ground, width, color, damage=None, airbags=True):
    h = width * 0.78
    top = ground - h
    X = lambda u: cx + (u - 0.5) * width
    Y = lambda v: top + v * h
    sc.soft_shadow((X(-0.05), ground - 30, X(1.05), ground + 34), alpha=180, blur=16)
    for u in (0.06, 0.94):
        sc.rect(X(u) - width * 0.07, Y(0.80), X(u) + width * 0.07, Y(1.0), fill=(22, 22, 24), r=18)
    green = [(X(0.20), Y(0.02)), (X(0.80), Y(0.02)), (X(0.93), Y(0.33)), (X(0.07), Y(0.33))]
    sc.grad_poly(green, shade(color, 1.1), shade(color, 0.8))
    ws = [(X(0.235), Y(0.05)), (X(0.765), Y(0.05)), (X(0.89), Y(0.31)), (X(0.11), Y(0.31))]
    sc.grad_poly(ws, (120, 140, 160), (40, 50, 62))
    lay = sc.layer(); lay.poly([(X(0.30), Y(0.05)), (X(0.42), Y(0.05)), (X(0.30), Y(0.31)), (X(0.16), Y(0.31))], fill=(230, 240, 255, 70)); sc.comp(lay, clip=ws, blur=6)
    hood = [(X(0.06), Y(0.33)), (X(0.94), Y(0.33)), (X(1.0), Y(0.52)), (X(0.0), Y(0.52))]
    sc.grad_poly(hood, shade(color, 1.4), shade(color, 0.95))
    fascia = [(X(0.0), Y(0.52)), (X(1.0), Y(0.52)), (X(0.99), Y(0.88)), (X(0.01), Y(0.88))]
    sc.grad_poly(fascia, shade(color, 1.0), shade(color, 0.55))
    for side in (0, 1):
        a, b = (0.03, 0.27) if side == 0 else (0.73, 0.97)
        sc.poly([(X(a), Y(0.55)), (X(b), Y(0.56)), (X(b - 0.02), Y(0.64)), (X(a + 0.01), Y(0.63))], fill=(236, 240, 244), outline=(70, 74, 80), width=2)
        sc.circ(X((a + b) / 2), Y(0.595), width * 0.025, fill=(255, 255, 250))
    sc.rect(X(0.32), Y(0.57), X(0.68), Y(0.71), fill=(26, 26, 28), r=12)
    for k in range(5):
        sc.line([(X(0.33), Y(0.59 + k * 0.025)), (X(0.67), Y(0.59 + k * 0.025))], (70, 70, 74), 3)
    sc.rect(X(0.20), Y(0.76), X(0.80), Y(0.86), fill=(30, 30, 32), r=10)
    sc.rect(X(0.40), Y(0.72), X(0.60), Y(0.80), fill=(240, 240, 236), outline=(40, 40, 40), width=2)
    for u in (0.02, 0.98):
        sc.ell(X(u) - width * 0.05, Y(0.26), X(u) + width * 0.05, Y(0.34), fill=shade(color, 0.8))
    geo = {"X": X, "Y": Y, "ws": ws, "hood": hood, "fascia": fascia, "w": width, "h": h}
    if damage == "windshield":
        sc.crack(X(0.66), Y(0.27), n=7, length=width * 0.28, width=2.0, clip=ws)
    elif damage == "heavy":
        crumple = [(X(0.06), Y(0.33)), (X(0.30), Y(0.24)), (X(0.52), Y(0.30)), (X(0.70), Y(0.22)), (X(0.94), Y(0.33)), (X(1.0), Y(0.52)), (X(0.0), Y(0.52))]
        sc.grad_poly(crumple, shade(color, 1.5), shade(color, 0.7))
        for u in (0.3, 0.52, 0.70):
            sc.line([(X(u), Y(0.25)), (X(u + 0.04), Y(0.50))], shade(color, 0.35), 4)
            sc.line([(X(u + 0.01), Y(0.25)), (X(u + 0.05), Y(0.50))], shade(color, 1.6), 2)
        lay = sc.layer()
        hole = [(X(0.0), Y(0.55))] + [(X(0.05 + k * 0.1), Y(sc.rnd.uniform(0.54, 0.62))) for k in range(10)] + [(X(1.0), Y(0.56)), (X(0.97), Y(0.86)), (X(0.03), Y(0.86))]
        lay.poly(hole, fill=(22, 20, 20, 240)); sc.comp(lay)
        gl = sc.layer()
        for k in range(10):
            gl.line([(X(0.12), Y(0.60 + k * 0.025)), (X(0.88), Y(0.60 + k * 0.025))], (120, 124, 128, 200), 3)
        for k in range(14):
            gl.line([(X(0.12 + k * 0.055), Y(0.60)), (X(0.12 + k * 0.055), Y(0.84))], (90, 94, 98, 160), 2)
        sc.comp(gl, clip=hole)
        sc.shards(X(0.0), Y(0.56), X(0.3), Y(0.66), n=30); sc.shards(X(0.7), Y(0.56), X(1.0), Y(0.66), n=30)
        sc.poly([(X(0.05), Y(0.86)), (X(0.55), Y(0.88)), (X(0.52), Y(0.97)), (X(0.02), Y(0.94))], fill=shade(color, 0.6))
        sc.crack(X(0.62), Y(0.22), n=10, length=width * 0.25, width=1.8, clip=ws)
        if airbags:
            lay = sc.layer()
            for bx in (0.33, 0.66):
                lay.ell(X(bx - 0.13), Y(0.12), X(bx + 0.13), Y(0.31), fill=(244, 244, 240, 220))
                lay.arc((X(bx - 0.10), Y(0.14), X(bx + 0.10), Y(0.29)), 200, 340, fill=(200, 200, 196, 220), width=3)
            sc.comp(lay, clip=ws)
        gx0, gx1 = X(0.0), X(1.0)
        sc.shards(gx0, ground - 10, gx1, ground + 40, n=90, color=(200, 200, 204), size=(3, 9))
        lay = sc.layer(); lay.ell(X(0.2), ground - 4, X(0.85), ground + 36, fill=(30, 50, 34, 140)); sc.comp(lay, blur=8)
    return geo


def draw_car_rear(sc, cx, ground, width, color, damage=None):
    h = width * 0.74
    top = ground - h
    X = lambda u: cx + (u - 0.5) * width
    Y = lambda v: top + v * h
    sc.soft_shadow((X(-0.05), ground - 30, X(1.05), ground + 34), alpha=180, blur=16)
    for u in (0.06, 0.94):
        sc.rect(X(u) - width * 0.07, Y(0.80), X(u) + width * 0.07, Y(1.0), fill=(22, 22, 24), r=18)
    green = [(X(0.22), Y(0.02)), (X(0.78), Y(0.02)), (X(0.92), Y(0.32)), (X(0.08), Y(0.32))]
    sc.grad_poly(green, shade(color, 1.15), shade(color, 0.8))
    rw = [(X(0.25), Y(0.05)), (X(0.75), Y(0.05)), (X(0.87), Y(0.30)), (X(0.13), Y(0.30))]
    sc.grad_poly(rw, (90, 108, 126), (30, 38, 48))
    trunk = [(X(0.06), Y(0.32)), (X(0.94), Y(0.32)), (X(1.0), Y(0.55)), (X(0.0), Y(0.55))]
    sc.grad_poly(trunk, shade(color, 1.35), shade(color, 0.9))
    bump = [(X(0.0), Y(0.55)), (X(1.0), Y(0.55)), (X(0.99), Y(0.88)), (X(0.01), Y(0.88))]
    sc.grad_poly(bump, shade(color, 0.95), shade(color, 0.55))
    tls = []
    for a, b in ((0.02, 0.26), (0.74, 0.98)):
        p = [(X(a), Y(0.40)), (X(b), Y(0.42)), (X(b), Y(0.52)), (X(a), Y(0.52))]
        sc.poly(p, fill=(176, 22, 26), outline=(60, 8, 8), width=2); tls.append(p)
    sc.rect(X(0.40), Y(0.60), X(0.60), Y(0.68), fill=(240, 240, 236), outline=(40, 40, 40), width=2)
    sc.rect(X(0.10), Y(0.80), X(0.90), Y(0.86), fill=(30, 30, 32), r=8)
    for u in (0.30, 0.50, 0.70):
        sc.circ(X(u), Y(0.75), width * 0.012, fill=(30, 30, 32))
    geo = {"X": X, "Y": Y, "bump": bump}
    if damage == "bumper":
        c = (X(0.36), Y(0.70))
        sc.dent(c[0], c[1], width * 0.18, h * 0.12, depth=0.9, clip=bump)
        sc.crack(X(0.30), Y(0.66), n=6, length=width * 0.16, width=2.0, clip=bump, color=(220, 220, 225), dark=(20, 20, 20), star=False)
        lay = sc.layer()
        for k in range(14):
            y = Y(sc.rnd.uniform(0.62, 0.80))
            lay.line([(X(0.20), y), (X(0.48), y + sc.rnd.uniform(-6, 6))], (225, 225, 225, sc.rnd.randint(80, 170)), sc.rnd.uniform(1.5, 3.5))
        sc.comp(lay, clip=bump, blur=0.6)
        p = tls[0]
        lay = sc.layer(); lay.poly([p[0], (X(0.14), Y(0.41)), (X(0.12), Y(0.52)), p[3]], fill=(30, 10, 10, 230)); sc.comp(lay)
        sc.shards(X(0.02), Y(0.88), X(0.30), ground + 30, n=30, color=(190, 30, 30), size=(4, 10))
        sc.rect(X(0.55), Y(0.69), X(0.58), Y(0.72), fill=(10, 10, 10))
    return geo


def draw_hail_top(sc, color):
    sc.grad(0, 0, W, H, (96, 100, 104), (70, 74, 78))
    roof = [(330, 40), (1270, 40), (1400, 700), (200, 700)]
    sc.grad_poly(roof, shade(color, 1.6), shade(color, 0.9))
    ws = [(200, 700), (1400, 700), (1480, 880), (120, 880)]
    sc.grad_poly(ws, (110, 126, 146), (50, 60, 74))
    hood = [(120, 880), (1480, 880), (1600, H), (0, H)]
    sc.grad_poly(hood, shade(color, 1.5), shade(color, 1.0))
    sun = [(520, 170), (1080, 170), (1130, 470), (470, 470)]
    sc.grad_poly(sun, (40, 48, 60), (18, 22, 28))
    lay = sc.layer(); lay.poly([(560, 180), (700, 180), (600, 460), (500, 460)], fill=(220, 230, 245, 50)); sc.comp(lay, clip=sun, blur=4)
    sc.crack(860, 330, n=9, length=260, width=1.8, clip=sun)
    for rail in ((300, 60, 350, 700), (1250, 60, 1300, 700)):
        pass
    sc.line([(330, 40), (200, 700)], (30, 30, 32), 10); sc.line([(1270, 40), (1400, 700)], (30, 30, 32), 10)
    lay = sc.layer()
    for k in range(5):
        x = 360 + k * 210
        lay.poly([(x, 40), (x + 60, 40), (x - 80, 700), (x - 140, 700)], fill=(255, 255, 255, 22))
    sc.comp(lay, clip=roof, blur=10)
    dl = sc.layer()
    for region, n, rmax in ((roof, 340, 15), (hood, 240, 20)):
        for _ in range(n):
            u, v = sc.rnd.random(), sc.rnd.random()
            x, y = qmap(region, u, v)
            if region is roof and 470 < x < 1130 and 170 < y < 470:
                continue
            r = sc.rnd.uniform(rmax * 0.45, rmax) * (0.7 + 0.5 * v)
            dl.ell(x - r, y - r * 0.75, x + r, y + r * 0.75, fill=(0, 0, 0, 70))
            dl.arc((x - r, y - r * 0.75, x + r, y + r * 0.75), 200, 320, fill=(255, 255, 255, 150), width=2)
            dl.arc((x - r * 0.8, y - r * 0.6, x + r * 0.8, y + r * 0.6), 20, 140, fill=(0, 0, 0, 90), width=2)
    sc.comp(dl, blur=1.2)


# =============================================================== interiors
def kitchen_base(sc, burned=False):
    wall = (226, 214, 190) if not burned else (120, 110, 100)
    sc.grad(0, 0, W, 760, shade(wall, 1.05), shade(wall, 0.92))
    up = (238, 236, 230) if not burned else (60, 50, 44)
    for i, x in enumerate(range(60, 1560, 250)):
        sc.rect(x, 60, x + 236, 380, fill=up, outline=shade(up, 0.75), width=3)
        sc.rect(x + 20, 80, x + 216, 360, outline=shade(up, 0.85), width=2)
        sc.rect(x + 200, 300, x + 208, 350, fill=(150, 150, 152))
    sc.rect(0, 560, W, 600, fill=(120, 120, 126) if not burned else (40, 38, 36))
    base = (240, 238, 232) if not burned else (70, 60, 52)
    for x in range(40, 1580, 255):
        sc.rect(x, 600, x + 245, 900, fill=base, outline=shade(base, 0.75), width=3)
        sc.rect(x + 20, 620, x + 225, 870, outline=shade(base, 0.85), width=2)
        sc.rect(x + 110, 640, x + 135, 650, fill=(150, 150, 152))
    sc.rect(0, 900, W, 930, fill=shade(base, 0.6))
    sc.rect(650, 540, 950, 580, fill=(176, 180, 186))
    sc.line([(800, 540), (800, 470), (850, 470)], (190, 192, 196), 10)
    floor = [(0, 930), (W, 930), (W, H), (0, H)]
    sc.grad_poly(floor, (176, 150, 116) if not burned else (90, 78, 64), (140, 116, 86) if not burned else (60, 52, 44))
    for y in (960, 1000, 1050, 1110, 1180):
        sc.line([(0, y), (W, y)], (110, 90, 66), 2)
    for k in range(30):
        y = sc.rnd.choice([930, 960, 1000, 1050, 1110])
        x = sc.rnd.uniform(0, W)
        sc.line([(x, y), (x, y + 40)], (110, 90, 66), 2)

def scene_kitchen_water(sc):
    kitchen_base(sc)
    for x in range(550, 1060, 255):
        lay = sc.layer()
        lay.rect(x, 820, x + 245, 900, fill=(110, 80, 50, 150))
        for k in range(6):
            lay.line([(x + 10, 830 + k * 12), (x + 235, 834 + k * 12 + sc.rnd.uniform(-4, 4))], (80, 60, 40, 120), 2)
        sc.comp(lay, blur=3)
        sc.poly([(x, 880), (x + 245, 878), (x + 250, 905), (x - 5, 905)], fill=(170, 150, 126))
    lay = sc.layer()
    pts = [(380, 935), (1300, 930), (1500, 1010), (1350, 1120), (700, 1170), (300, 1090)]
    lay.poly(pts, fill=(140, 170, 190, 90))
    for _ in range(30):
        x = sc.rnd.uniform(420, 1300); y = sc.rnd.uniform(950, 1120)
        lay.ell(x - 40, y - 3, x + 40, y + 3, fill=(255, 255, 255, 90))
    sc.comp(lay, blur=5)
    for k, x in enumerate((640, 760, 880, 1010)):
        sc.poly([(x, 1000), (x + 120, 994), (x + 122, 1004), (x + 2, 1010)], fill=(196, 172, 140))
        sc.line([(x, 1010), (x + 122, 1004)], (80, 60, 40), 2)

def scene_burst_line(sc):
    sc.grad(0, 0, W, H, (48, 44, 40), (30, 28, 26))
    sc.rect(0, 0, 160, H, fill=(230, 228, 222)); sc.rect(1440, 0, W, H, fill=(230, 228, 222))
    sc.rect(160, 0, 1440, 90, fill=(70, 66, 60))
    sc.poly([(160, 980), (1440, 980), (1440, H), (160, H)], fill=(96, 76, 54))
    lay = sc.layer(); lay.ell(300, 950, 1300, 1180, fill=(30, 22, 14, 170)); sc.comp(lay, blur=20)
    sc.rect(600, 90, 680, 520, fill=(190, 192, 196)); sc.rect(920, 90, 1000, 400, fill=(190, 192, 196))
    sc.line([(960, 400), (960, 620), (760, 640)], (200, 200, 200), 26)
    sc.rect(620, 760, 660, 980, fill=(186, 190, 196))
    sc.rect(600, 760, 680, 800, fill=(210, 160, 40))
    pts = [(640, 760), (650, 680), (720, 600), (820, 560), (900, 520), (960, 400)]
    for i in range(len(pts) - 1):
        sc.line([pts[i], pts[i + 1]], (150, 152, 156), 22)
    lay = sc.layer()
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        L = math.hypot(x1 - x0, y1 - y0)
        for k in range(int(L / 8)):
            t = k * 8 / L
            x = x0 + (x1 - x0) * t; y = y0 + (y1 - y0) * t
            lay.line([(x - 8, y - 8), (x + 8, y + 8)], (210, 212, 216, 200), 2)
    sc.comp(lay)
    bx, by = 740, 592
    sc.ell(bx - 34, by - 22, bx + 34, by + 22, fill=(40, 40, 42))
    for _ in range(26):
        a = sc.rnd.uniform(0, 2 * math.pi); l = sc.rnd.uniform(14, 46)
        sc.line([(bx, by), (bx + l * math.cos(a), by + l * math.sin(a))], (215, 215, 218), 2)
    lay = sc.layer()
    for _ in range(80):
        a = sc.rnd.uniform(-2.4, -0.5); l = sc.rnd.uniform(40, 340)
        lay.line([(bx, by), (bx + l * math.cos(a), by + l * math.sin(a) + 180)], (200, 225, 245, 110), 2)
    for _ in range(60):
        x = sc.rnd.uniform(500, 1000); y = sc.rnd.uniform(600, 980)
        lay.ell(x - 4, y - 7, x + 4, y + 7, fill=(210, 230, 250, 170))
    sc.comp(lay, blur=1)

def scene_basement_flood(sc):
    sc.grad(0, 0, W, 760, (210, 200, 180), (190, 180, 160))
    lay = sc.layer(); lay.rect(0, 520, W, 760, fill=(120, 96, 64, 150)); sc.comp(lay, blur=6)
    sc.line([(0, 520), (W, 516)], (100, 80, 52), 4)
    sc.rect(1160, 60, 1460, 220, fill=(170, 200, 220), outline=(90, 90, 90), width=6)
    sc.rect(80, 260, 300, 760, fill=(236, 236, 232), r=40)
    sc.line([(140, 260), (140, 60)], (190, 150, 90), 12); sc.line([(240, 260), (240, 60)], (180, 180, 184), 12)
    sc.rect(500, 520, 1350, 760, fill=(86, 88, 96), r=30)
    sc.rect(500, 430, 1350, 560, fill=(96, 98, 106), r=30)
    sc.rect(470, 470, 560, 760, fill=(80, 82, 90), r=20)
    water = [(0, 700), (W, 690), (W, H), (0, H)]
    sc.grad_poly(water, (120, 108, 82), (70, 62, 46))
    lay = sc.layer()
    for _ in range(120):
        x = sc.rnd.uniform(0, W); y = sc.rnd.uniform(710, H)
        lay.ell(x - 50, y - 3, x + 50, y + 3, fill=(220, 210, 180, 60))
    lay.rect(500, 700, 1350, 760, fill=(40, 40, 46, 120))
    sc.comp(lay, blur=3)
    for x0 in (300, 1000):
        sc.rect(x0, 780, x0 + 90, 800, fill=(200, 150, 90))
    sc.rect(900, 820, 980, 860, fill=(170, 40, 40))

def scene_bathroom_mold(sc, view):
    sc.grad(0, 0, W, 520, (200, 214, 220), (186, 200, 206))
    floor = [(0, 520), (W, 520), (W, H), (0, H)]
    sc.grad_poly(floor, (220, 218, 212), (196, 194, 188))
    q = [(240, 520), (1360, 520), (2000, H), (-400, H)]
    for i in range(11):
        sc.line([qmap(q, i / 10, 0), qmap(q, i / 10, 1)], (160, 158, 150), 3)
    for j in range(8):
        v = (j / 7) ** 1.4
        sc.line([qmap(q, 0, v), qmap(q, 1, v)], (160, 158, 150), 3)
    cx, cy = 800, 700
    stain = sc.layer()
    for _ in range(40):
        r = sc.rnd.uniform(60, 260)
        stain.ell(cx - r * 1.4 + sc.rnd.uniform(-40, 40), cy + 120 - r * 0.5, cx + r * 1.4 + sc.rnd.uniform(-40, 40), cy + 120 + r * 0.5, fill=(70, 50, 30, 18))
    sc.comp(stain, blur=12)
    sc.noise_patch([(cx - 380, cy + 40), (cx + 380, cy + 40), (cx + 440, cy + 300), (cx - 440, cy + 300)], (20, 34, 20), n=900, size=(1.5, 5), alpha=200)
    if view == "wide":
        sc.rect(640, 180, 960, 420, fill=(250, 250, 250), outline=(200, 200, 200), width=3, r=20)
        sc.ell(620, 400, 980, 640, fill=(252, 252, 252), outline=(200, 200, 200), width=3)
        sc.ell(680, 440, 920, 600, fill=(220, 226, 230))
        sc.poly([(700, 600), (900, 600), (870, 780), (730, 780)], fill=(246, 246, 246))
        sc.ell(700, 750, 900, 810, fill=(240, 240, 240))
        for x in (600, 1000):
            sc.line([(x, 860), (x + sc.rnd.uniform(-60, 60), 1000)], (90, 80, 70), 3)
    else:
        sc.ell(620, 520, 980, 760, fill=(98, 66, 38))
        wood = sc.layer()
        for k in range(30):
            y = 520 + k * 8
            wood.line([(620, y), (980, y + sc.rnd.uniform(-6, 6))], (60, 40, 22, 120), 2)
        sc.comp(wood, clip=[(620, 520), (980, 520), (980, 760), (620, 760)])
        sc.noise_patch([(620, 520), (980, 520), (980, 760), (620, 760)], (10, 20, 10), n=700, size=(2, 6), alpha=220)
        sc.circ(800, 640, 70, fill=(14, 14, 14))
        sc.circ(800, 640, 92, outline=(170, 130, 60), width=14)
        sc.circ(800, 640, 120, outline=(60, 80, 50), width=8)

def scene_kitchen_fire(sc, view):
    kitchen_base(sc, burned=True)
    lay = sc.layer()
    lay.poly([(560, 560), (1040, 560), (1500, 0), (100, 0)], fill=(10, 8, 6, 210))
    sc.comp(lay, blur=40)
    lay = sc.layer(); lay.rect(0, 0, W, 300, fill=(10, 10, 10, 180)); sc.comp(lay, blur=60)
    sc.poly([(620, 300), (980, 300), (1020, 420), (580, 420)], fill=(40, 36, 34))
    sc.poly([(640, 420), (700, 470), (740, 430), (820, 500), (880, 440), (960, 420)], fill=(30, 28, 26))
    sc.rect(640, 560, 960, 900, fill=(26, 26, 28))
    for k in range(4):
        sc.circ(700 + (k % 2) * 200, 580 + (k // 2) * 10, 30, outline=(80, 70, 60), width=4)
    sc.poly([(520, 0), (900, 0), (850, 90), (760, 60), (680, 120), (600, 70)], fill=(18, 16, 14))
    for x in range(560, 860, 40):
        sc.line([(x, 60), (x + sc.rnd.uniform(-20, 20), 160)], (60, 56, 50), 4)
    sc.noise_patch([(0, 0), (W, 0), (W, 900), (0, 900)], (20, 18, 16), n=3000, size=(1, 4), alpha=120)
    sc.shards(100, 940, 1500, 1180, n=140, color=(40, 36, 32), size=(6, 18))

def scene_smoke_room(sc):
    sc.grad(0, 0, W, 820, (120, 116, 110), (176, 170, 160))
    lay = sc.layer(); lay.rect(0, 0, W, 360, fill=(30, 28, 26, 170)); sc.comp(lay, blur=70)
    for (x, y, w, h) in ((220, 260, 260, 180), (620, 220, 360, 240), (1120, 280, 220, 160)):
        sc.rect(x, y, x + w, y + h, fill=(206, 200, 188))
    sc.grad(0, 820, W, H, (120, 100, 80), (90, 74, 60))
    sc.rect(300, 640, 1300, 900, fill=(110, 104, 96), r=30)
    sc.rect(300, 560, 1300, 680, fill=(120, 114, 106), r=30)
    sc.rect(1400, 500, 1440, 900, fill=(60, 56, 50)); sc.poly([(1360, 420), (1480, 420), (1450, 510), (1390, 510)], fill=(170, 160, 140))
    sc.noise_patch([(0, 0), (W, 0), (W, 820), (0, 820)], (40, 38, 36), n=2500, size=(1, 3), alpha=80)

def scene_roof(sc, view):
    sc.grad(0, 0, W, 300, (150, 180, 210), (210, 224, 236))
    q = [(160, 160), (1440, 160), (1700, H), (-100, H)]
    sc.poly(q, fill=(60, 60, 64))
    rows = 18
    rnd = sc.rnd
    missing = set()
    for _ in range(46):
        missing.add((rnd.randint(4, rows - 1), rnd.randint(2, 14)))
    for r in range(rows):
        v0 = (r / rows) ** 1.2; v1 = ((r + 1) / rows) ** 1.2
        cols = 16
        off = 0.5 if r % 2 else 0
        for c in range(-1, cols + 1):
            u0 = (c + off) / cols; u1 = (c + off + 1) / cols
            u0c, u1c = max(0, u0), min(1, u1)
            if u1c <= u0c:
                continue
            p = [qmap(q, u0c, v0), qmap(q, u1c, v0), qmap(q, u1c, v1), qmap(q, u0c, v1)]
            if (r, c) in missing or ((r - 1, c) in missing and rnd.random() < 0.5):
                sc.poly(p, fill=(28, 28, 30) if rnd.random() < 0.6 else (196, 160, 110))
                if rnd.random() < 0.5:
                    for k in range(4):
                        a = qmap(q, u0c, v0 + (v1 - v0) * k / 4); b = qmap(q, u1c, v0 + (v1 - v0) * k / 4)
                        sc.line([a, b], (150, 120, 80), 2)
            else:
                base = shade((92, 92, 98), rnd.uniform(0.8, 1.15))
                sc.poly(p, fill=base, outline=(40, 40, 44), width=1.5)
                if rnd.random() < 0.05:
                    sc.line([p[0], p[2]], (190, 190, 196), 3)
    sc.rect(-10, 1150, W + 10, H, fill=(220, 220, 214))
    sc.noise_patch(q, (130, 130, 130), n=3000, size=(0.8, 2), alpha=70)
    for _ in range(6):
        x = rnd.uniform(200, 1400); y = rnd.uniform(500, 1100)
        a = rnd.uniform(-0.6, 0.6)
        pts = [(x, y), (x + 140 * math.cos(a), y + 140 * math.sin(a)), (x + 140 * math.cos(a) - 30 * math.sin(a), y + 140 * math.sin(a) + 50), (x - 30 * math.sin(a), y + 50)]
        sc.poly(pts, fill=(84, 84, 90), outline=(30, 30, 34), width=2)

def scene_tree_garage(sc, view):
    sc.grad(0, 0, W, 560, (120, 126, 134), (170, 176, 182))
    sc.grad(0, 560, W, H, (86, 116, 64), (64, 92, 48))
    sc.rect(380, 380, 1280, 900, fill=(214, 206, 186))
    for y in range(390, 900, 22):
        sc.line([(380, y), (1280, y)], (180, 172, 152), 2)
    sc.rect(500, 560, 1160, 900, fill=(236, 236, 230), outline=(160, 160, 156), width=4)
    for y in range(600, 900, 70):
        sc.line([(500, y), (1160, y)], (180, 180, 176), 4)
    roof_l = [(330, 400), (830, 150), (830, 230), (430, 420)]
    sc.poly([(330, 400), (830, 150), (1330, 400)], fill=(80, 70, 66))
    sc.poly([(830, 150), (1330, 400), (1180, 430), (980, 300), (900, 340)], fill=(60, 52, 48))
    sc.poly([(900, 260), (1100, 330), (1060, 420), (930, 380)], fill=(22, 18, 16))
    for k in range(6):
        sc.line([(920 + k * 30, 300), (900 + k * 34, 420)], (150, 120, 80), 6)
    sc.poly([(-60, 1100), (60, 1180), (1120, 360), (1060, 300)], fill=(92, 70, 50))
    for t in range(0, 22):
        x = -40 + t * 52; y = 1120 - t * 38
        sc.line([(x, y), (x + 60, y + 30)], (62, 46, 34), 4)
    lay = sc.layer()
    for _ in range(180):
        x = sc.rnd.uniform(800, 1500); y = sc.rnd.uniform(80, 520)
        r = sc.rnd.uniform(20, 60)
        lay.circ(x, y, r, fill=shade((60, 96, 46), sc.rnd.uniform(0.7, 1.3)) + (230,))
    sc.comp(lay)
    for _ in range(14):
        x0 = sc.rnd.uniform(900, 1250); y0 = sc.rnd.uniform(260, 420)
        sc.line([(x0, y0), (x0 + sc.rnd.uniform(-180, 180), y0 + sc.rnd.uniform(-200, 60))], (82, 62, 44), 7)
    sc.line([(1180, 430), (1300, 470), (1360, 640)], (200, 200, 200), 10)
    sc.shards(380, 900, 1300, 1050, n=80, color=(90, 80, 70), size=(6, 16))

def scene_back_door(sc):
    sc.grad(0, 0, W, 980, (232, 228, 220), (214, 210, 200))
    sc.rect(470, 40, 1130, 980, fill=(244, 244, 240), outline=(190, 190, 186), width=6)
    sc.rect(530, 100, 1070, 620, fill=(230, 230, 226))
    panes = []
    for r in range(3):
        for c in range(3):
            x0 = 545 + c * 175; y0 = 115 + r * 165
            p = [(x0, y0), (x0 + 165, y0), (x0 + 165, y0 + 155), (x0, y0 + 155)]
            sc.grad_poly(p, (190, 220, 200), (140, 180, 150)); panes.append(p)
    broken = panes[5]
    lay = sc.layer(); hole = [(905, 290), (980, 300), (1010, 360), (960, 420), (900, 380)]
    lay.poly(hole, fill=(70, 110, 70, 255)); sc.comp(lay)
    sc.crack(955, 360, n=12, length=140, width=1.5, clip=broken)
    sc.rect(1000, 640, 1060, 700, fill=(200, 170, 70), r=8)
    floor = [(0, 980), (W, 980), (W, H), (0, H)]
    sc.grad_poly(floor, (200, 196, 186), (170, 166, 156))
    for x in range(0, W, 200):
        sc.line([(x, 980), (x - 100, H)], (150, 146, 136), 3)
    sc.shards(700, 990, 1250, 1150, n=110, color=(210, 230, 225), size=(4, 12))

def scene_jewelry_box(sc):
    sc.grad(0, 0, W, 520, (210, 200, 186), (190, 180, 166))
    sc.grad(0, 520, W, H, (120, 80, 50), (90, 58, 36))
    for k in range(18):
        sc.line([(0, 560 + k * 36), (W, 556 + k * 36)], (100, 66, 40), 2)
    sc.poly([(420, 180), (1180, 180), (1220, 520), (380, 520)], fill=(110, 70, 44))
    sc.poly([(450, 200), (1150, 200), (1180, 500), (420, 500)], fill=(34, 40, 76))
    sc.rect(380, 520, 1220, 820, fill=(130, 84, 52))
    sc.rect(410, 540, 1190, 800, fill=(30, 36, 70))
    for x in range(410, 1190, 130):
        sc.line([(x, 540), (x, 800)], (20, 24, 48), 8)
    sc.line([(410, 670), (1190, 670)], (20, 24, 48), 8)
    for (x, y) in ((470, 600), (730, 720), (990, 600)):
        sc.ell(x, y, x + 60, y + 30, fill=(24, 28, 56))
    sc.rect(200, 900, 700, 1100, fill=(140, 92, 58)); sc.rect(220, 920, 680, 1080, fill=(70, 46, 28))
    sc.rect(1000, 880, 1500, 1120, fill=(140, 92, 58)); sc.rect(1020, 900, 1480, 1100, fill=(70, 46, 28))

def scene_forced_door(sc):
    sc.grad(0, 0, W, H, (190, 186, 178), (160, 156, 148))
    sc.rect(300, 0, 980, H, fill=(46, 84, 62))
    for y in (120, 560):
        sc.rect(360, y, 920, y + 380, outline=(30, 60, 44), width=8)
    sc.rect(980, 0, 1160, H, fill=(236, 232, 222))
    sc.poly([(980, 420), (1060, 400), (1120, 450), (1090, 520), (1150, 600), (1060, 640), (980, 620)], fill=(222, 196, 150))
    for _ in range(26):
        x0 = sc.rnd.uniform(990, 1100); y0 = sc.rnd.uniform(420, 620)
        sc.line([(x0, y0), (x0 + sc.rnd.uniform(30, 90), y0 + sc.rnd.uniform(-30, 30))], (190, 160, 110), 4)
    sc.poly([(1040, 470), (1100, 460), (1110, 500), (1080, 580), (1050, 580)], fill=(170, 170, 172), outline=(90, 90, 90), width=2)
    sc.circ(900, 520, 34, fill=(196, 170, 80), outline=(120, 100, 40), width=3)
    sc.circ(900, 640, 44, fill=(196, 170, 80), outline=(120, 100, 40), width=3)
    for (x, y) in ((960, 470), (955, 560), (962, 610)):
        sc.ell(x - 10, y - 26, x + 12, y + 26, fill=(24, 46, 34))
    sc.shards(960, 900, 1300, 1150, n=50, color=(220, 196, 150), size=(6, 16))

def scene_tv_wall(sc):
    sc.grad(0, 0, W, 900, (150, 166, 180), (136, 152, 166))
    sc.rect(380, 160, 1220, 640, fill=(166, 182, 196))
    sc.rect(700, 300, 900, 500, fill=(30, 30, 32))
    for y in (320, 400, 480):
        sc.rect(660, y, 940, y + 18, fill=(40, 40, 44))
    for k, x in enumerate((770, 800, 830)):
        pts = [(x, 500)] + [(x + 30 * math.sin(t / 2 + k), 500 + t * 30) for t in range(1, 10)]
        sc.line(pts, (20, 20, 22), 6)
    sc.rect(360, 760, 1240, 900, fill=(90, 64, 44))
    sc.rect(520, 740, 1080, 762, fill=(110, 84, 64))
    sc.grad(0, 900, W, H, (120, 100, 80), (96, 80, 64))
    sc.circ(1300, 700, 30, fill=(230, 230, 226)); sc.rect(1290, 690, 1310, 710, fill=(40, 40, 40))

def scene_truck_ditch(sc, color, view):
    sc.grad(0, 0, W, 420, (16, 18, 26), (36, 38, 46))
    sc.grad(0, 420, W, H, (40, 58, 34), (22, 34, 20))
    sc.poly([(0, 700), (W, 640), (W, 820), (0, 900)], fill=(30, 26, 20))
    for x in range(-40, W, 230):
        lean = sc.rnd.uniform(-0.2, 0.2) if 400 < x < 1000 else 0
        sc.poly([(x, 520), (x + 26, 520), (x + 26 + lean * 200, 760), (x + lean * 200, 760)], fill=(110, 84, 56))
    for y in (560, 640):
        sc.line([(-40, y), (420, y - 10)], (140, 108, 70), 16)
        sc.line([(1040, y - 20), (W, y - 30)], (140, 108, 70), 16)
        sc.line([(430, y), (560, y + 160)], (140, 108, 70), 14)
        sc.line([(1010, y - 20), (900, y + 140)], (140, 108, 70), 14)
    sc.shards(420, 700, 1100, 900, n=60, color=(150, 116, 76), size=(10, 26))
    lay = Scene(0)
    geo = draw_car_side(sc, 260, 960, 1100, color, kind="truck", flip=False, damage="front", sev="moderate")
    lay = sc.layer()
    for _ in range(300):
        x = sc.rnd.uniform(0, W); y = sc.rnd.uniform(0, H)
        lay.line([(x, y), (x - 8, y + 40)], (200, 210, 230, 70), 1.5)
    sc.comp(lay)

def scene_empty_space(sc):
    bg_lot(sc, sky=((180, 196, 214), (236, 226, 210)), asphalt=((88, 90, 94), (56, 58, 62)))
    draw_car_side(sc, -700, 1000, 900, (40, 40, 44), kind="suv", flip=True)
    draw_car_side(sc, 1420, 1000, 900, (150, 150, 156), kind="sedan")
    sc.shards(520, 860, 1150, 1080, n=220, color=(200, 222, 228), size=(3, 9))
    sc.poly([(500, 1100), (520, 1100), (480, H), (455, H)], fill=(230, 226, 210))


# =============================================================== dispatcher
CROPS = {
    "windshield_crack": (560, 220, 1360, 820),
    "rear_bumper_damage": (380, 560, 1180, 1160),
    "front_corner_left": (100, 380, 900, 980),
    "front_corner_right": (700, 380, 1500, 980),
    "front_corner_center": (100, 380, 900, 980),
    "front_crush_heavy": (360, 380, 1240, 1040),
    "side_door_intrusion": (420, 380, 1220, 980),
    "side_scrape": (380, 520, 1180, 1120),
    "hail_top": (380, 120, 1180, 720),
    "kitchen_water": (360, 680, 1260, 1180),
    "basement_flood": (300, 380, 1300, 1130),
    "bathroom_mold": None,
    "kitchen_fire": (420, 0, 1240, 620),
    "roof_wind": (300, 420, 1100, 1020),
    "tree_on_garage": (700, 120, 1400, 645),
    "truck_ditch_fence": (150, 460, 950, 1060),
}

def render(spec, seed):
    scene = spec["scene"]; view = spec["view"]; p = spec["params"]
    sc = Scene(seed)
    color = tuple(p.get("color", (120, 120, 120)))
    night = p.get("night", False)
    crop = None
    warm = 0.0
    if scene == "windshield_crack":
        bg_lot(sc)
        draw_car_front(sc, 800, 1110, 1150, color, damage="windshield")
        crop = CROPS[scene] if view == "close" else None
    elif scene == "rear_bumper_damage":
        bg_garage(sc)
        draw_car_rear(sc, 800, 1130, 1100, color, damage="bumper")
        crop = CROPS[scene] if view == "close" else None
        warm = 0.04
    elif scene == "front_corner_damage":
        bgk = p.get("background")
        if night: bg_night_street(sc)
        elif bgk == "driveway": bg_driveway(sc)
        elif bgk == "shop": bg_shop(sc)
        else: bg_lot(sc)
        side = p.get("side", "left")
        kind = p.get("vehicle", "sedan")
        flip = side == "right"
        draw_car_side(sc, 180, 1040, 1240, color, kind=kind, flip=flip, damage="front", sev=p.get("severity", "moderate"))
        if view == "close":
            crop = CROPS["front_corner_right"] if flip else CROPS["front_corner_left"]
    elif scene == "front_crush_heavy":
        if p.get("background") == "shop": bg_shop(sc)
        else: bg_road(sc)
        draw_car_front(sc, 800, 1110, 1100, color, damage="heavy", airbags=p.get("airbags", True))
        crop = CROPS[scene] if view == "close" else None
    elif scene == "side_door_intrusion":
        bg_lot(sc, sky=((170, 176, 186), (205, 210, 216)))
        draw_car_side(sc, 140, 1040, 1320, color, kind=p.get("vehicle", "suv"), damage="door_intrusion")
        crop = CROPS[scene] if view == "close" else None
    elif scene == "side_scrape":
        bg_lot(sc)
        draw_car_side(sc, 160, 1040, 1280, color, kind=p.get("vehicle", "suv"), damage="scrape")
        crop = CROPS[scene] if view == "close" else None
    elif scene == "side_window_smashed":
        bg_deck(sc)
        draw_car_side(sc, 160, 1010, 1280, color, kind="sedan", damage="window_smashed")
        night = True
    elif scene == "hail_top":
        draw_hail_top(sc, color)
        crop = CROPS[scene] if view == "close" else None
    elif scene == "empty_space_glass":
        scene_empty_space(sc); warm = 0.05
    elif scene == "truck_ditch_fence":
        scene_truck_ditch(sc, color, view)
        crop = CROPS[scene] if view == "close" else None
        night = True
    elif scene == "kitchen_water":
        scene_kitchen_water(sc)
        crop = CROPS[scene] if view == "close" else None
        warm = 0.06
    elif scene == "burst_supply_line":
        scene_burst_line(sc); warm = 0.05
    elif scene == "basement_flood":
        scene_basement_flood(sc)
        crop = CROPS[scene] if view == "close" else None
    elif scene == "bathroom_mold":
        scene_bathroom_mold(sc, view)
    elif scene == "kitchen_fire":
        scene_kitchen_fire(sc, view)
        crop = CROPS[scene] if view == "close" else None
    elif scene == "smoke_room":
        scene_smoke_room(sc)
    elif scene == "roof_wind":
        scene_roof(sc, view)
        crop = CROPS[scene] if view == "close" else None
    elif scene == "tree_on_garage":
        scene_tree_garage(sc, view)
        crop = CROPS[scene] if view == "close" else None
    elif scene == "back_door_glass_broken":
        scene_back_door(sc); warm = 0.04
    elif scene == "empty_jewelry_box":
        scene_jewelry_box(sc); warm = 0.08
    elif scene == "forced_door":
        scene_forced_door(sc); warm = 0.03
    elif scene == "empty_tv_wall":
        scene_tv_wall(sc)
    else:
        raise ValueError(scene)
    return sc.finish(crop=crop, night=night, flash=night, warm=warm, seed=seed)


def exif_bytes(ex):
    dt = ex["dt"]
    zeroth = {piexif.ImageIFD.Make: ex["make"].encode(), piexif.ImageIFD.Model: ex["model"].encode(),
              piexif.ImageIFD.DateTime: dt.encode(), piexif.ImageIFD.Software: b"Camera"}
    exif = {piexif.ExifIFD.DateTimeOriginal: dt.encode(), piexif.ExifIFD.DateTimeDigitized: dt.encode()}
    if ex.get("comment"):
        exif[piexif.ExifIFD.UserComment] = b"ASCII\x00\x00\x00" + ex["comment"].encode()
    gps = {}
    if ex.get("gps"):
        lat, lon = ex["gps"]
        def dms(v):
            v = abs(v); d = int(v); m = int((v - d) * 60); s = round(((v - d) * 60 - m) * 60 * 100)
            return ((d, 1), (m, 1), (s, 100))
        gps = {piexif.GPSIFD.GPSLatitudeRef: b"N" if lat >= 0 else b"S", piexif.GPSIFD.GPSLatitude: dms(lat),
               piexif.GPSIFD.GPSLongitudeRef: b"E" if lon >= 0 else b"W", piexif.GPSIFD.GPSLongitude: dms(lon)}
    return piexif.dump({"0th": zeroth, "Exif": exif, "GPS": gps, "1st": {}, "thumbnail": None})


def save_photo(spec, path, seed):
    img = render(spec, seed)
    img.save(path, "JPEG", quality=84, exif=exif_bytes(spec["exif"]))
