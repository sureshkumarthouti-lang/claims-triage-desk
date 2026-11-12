"""Image-type claim documents: receipts photographed on a table, payment screenshot, scanned PDFs."""
import math, random, subprocess, tempfile, os, glob
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops, ImageEnhance

FD = "/usr/share/fonts/truetype/dejavu/"
def font(name, size):
    return ImageFont.truetype(FD + name, size)

def receipt_image(d, path, seed=1):
    rnd = random.Random(seed)
    mono = font("DejaVuSansMono.ttf", 30); monob = font("DejaVuSansMono-Bold.ttf", 34); small = font("DejaVuSansMono.ttf", 22)
    lines = []
    lines.append(("C", d["store"], monob))
    lines.append(("C", d["store_address"], mono))
    lines.append(("C", "(804) 555-0187", mono))
    lines.append(("L", "", mono))
    date, time = d["datetime"].split(" ")
    lines.append(("L", f"DATE {date}   TIME {time}", mono))
    lines.append(("L", f"STORE 0412  REG 03  TRN {rnd.randint(1000, 9999)}", mono))
    lines.append(("L", "-" * 34, mono))
    sub = 0
    for name, price in d["items"]:
        lines.append(("L", name[:34], mono))
        lines.append(("R", f"1 @ {price:,.2f}   {price:,.2f}", mono))
        sub += price
    tax = round(sub * d["tax_rate"], 2)
    lines.append(("L", "-" * 34, mono))
    lines.append(("R", f"SUBTOTAL   {sub:,.2f}", mono))
    lines.append(("R", f"SALES TAX {d['tax_rate']*100:.1f}%   {tax:,.2f}", mono))
    lines.append(("R", f"TOTAL   {sub + tax:,.2f}", monob))
    lines.append(("L", "", mono))
    lines.append(("L", f"{d['payment']}   APPROVED", mono))
    lines.append(("L", f"AUTH {rnd.randint(100000, 999999)}", mono))
    lines.append(("L", "", mono))
    lines.append(("C", "THANK YOU FOR SHOPPING", mono))
    lines.append(("C", "RETURNS WITHIN 30 DAYS W/ RECEIPT", small))
    lines.append(("BAR", "", mono))
    lines.append(("C", "Synthetic training sample - fictional store", small))
    pw = 640; lh = 44
    ph = 80 + lh * len(lines) + 120
    paper = Image.new("RGB", (pw, ph), (246, 244, 236))
    d2 = ImageDraw.Draw(paper)
    y = 50
    for align, text, f in lines:
        if align == "BAR":
            x = 120
            while x < pw - 120:
                w = rnd.choice([2, 3, 5, 7]); d2.rectangle([x, y, x + w, y + 70], fill=(30, 30, 30)); x += w + rnd.choice([3, 4, 6])
            y += 90; continue
        tw = d2.textlength(text, font=f)
        x = (pw - tw) / 2 if align == "C" else (pw - 40 - tw if align == "R" else 40)
        d2.text((x, y), text, font=f, fill=(40, 40, 46))
        y += lh
    # paper texture & fade
    n = Image.effect_noise((pw, ph), 10).convert("L")
    paper = ImageChops.multiply(paper, Image.merge("RGB", (n.point(lambda v: 225 + v // 8),) * 3))
    # table background
    W, H = 1500, max(2000, ph + 300)
    bg = Image.new("RGB", (W, H), (120, 92, 66))
    bd = ImageDraw.Draw(bg)
    for k in range(0, H, 46):
        bd.line([(0, k + rnd.randint(-6, 6)), (W, k + rnd.randint(-6, 6))], fill=(104, 78, 54), width=3)
    shadow = Image.new("RGBA", (pw + 60, ph + 60), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rectangle([30, 30, pw + 30, ph + 30], fill=(0, 0, 0, 120))
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    ang = rnd.uniform(-4, 4)
    shadow = shadow.rotate(ang, expand=True)
    pr = paper.convert("RGBA").rotate(ang, expand=True, fillcolor=(0, 0, 0, 0))
    ox, oy = (W - pr.width) // 2, (H - pr.height) // 2
    bg = bg.convert("RGBA")
    bg.alpha_composite(shadow, (ox + 10, oy + 16))
    bg.alpha_composite(pr, (ox, oy))
    img = bg.convert("RGB").filter(ImageFilter.GaussianBlur(0.8))
    img = img.resize((1125, int(1125 * H / W)), Image.LANCZOS)
    img.save(path, "JPEG", quality=86)

def payment_screenshot(d, path):
    W, H = 1280, 860
    img = Image.new("RGB", (W, H), (244, 243, 248))
    dr = ImageDraw.Draw(img)
    dr.rectangle([0, 0, W, 90], fill=(59, 42, 107))
    dr.text((40, 26), "Larkspur Mutual", font=font("DejaVuSans-Bold.ttf", 34), fill="white")
    dr.text((W - 330, 34), "My Account  |  Sign out", font=font("DejaVuSans.ttf", 22), fill=(220, 214, 240))
    dr.rounded_rectangle([200, 150, W - 200, 760], radius=18, fill="white", outline=(220, 218, 228), width=2)
    dr.ellipse([590, 190, 690, 290], fill=(40, 150, 90))
    dr.line([(615, 242), (635, 262), (668, 222)], fill="white", width=10)
    t = "Payment received"
    f = font("DejaVuSans-Bold.ttf", 40); dr.text(((W - dr.textlength(t, font=f)) / 2, 310), t, font=f, fill=(30, 30, 40))
    rows = [("Confirmation number", d["confirmation"]), ("Policy", d["policy"]), ("Amount", d["amount"]),
            ("Payment date", d["date"]), ("Payment method", "Bank account ending 0331")]
    y = 400
    for k, v in rows:
        dr.text((280, y), k, font=font("DejaVuSans.ttf", 26), fill=(100, 100, 115))
        dr.text((640, y), v, font=font("DejaVuSans-Bold.ttf", 24), fill=(30, 30, 40))
        dr.line([(280, y + 44), (W - 280, y + 44)], fill=(232, 230, 238), width=2)
        y += 62
    dr.text((280, 712), "Receipt of payment does not reinstate a cancelled policy unless confirmed in writing.", font=font("DejaVuSans.ttf", 18), fill=(120, 120, 130))
    dr.text((40, H - 40), "Synthetic training sample - fictional company", font=font("DejaVuSans.ttf", 16), fill=(150, 150, 160))
    img.save(path, "PNG")

def scan_pdf(src_pdf, dst_pdf, seed=3):
    rnd = random.Random(seed)
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(["pdftoppm", "-r", "150", "-png", src_pdf, os.path.join(td, "pg")], check=True)
        pages = []
        for f in sorted(glob.glob(os.path.join(td, "pg*.png"))):
            im = Image.open(f).convert("L")
            im = ImageEnhance.Contrast(im).enhance(1.25)
            im = im.rotate(rnd.uniform(-1.2, 1.2), resample=Image.BICUBIC, expand=False, fillcolor=255)
            n = Image.effect_noise(im.size, 22)
            im = ImageChops.multiply(im, n.point(lambda v: 205 + v // 5))
            im = im.filter(ImageFilter.GaussianBlur(0.6))
            g = Image.linear_gradient("L").resize(im.size).point(lambda v: 255 - v // 14)
            im = ImageChops.multiply(im, g)
            pages.append(im.convert("RGB"))
        pages[0].save(dst_pdf, "PDF", resolution=150, save_all=True, append_images=pages[1:])
