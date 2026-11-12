"""PDF rendering for the knowledge base, declarations pages and claim documents."""
import re
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table,
                                TableStyle, KeepTogether)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from data import COMPANY, POLICY_BY_NUMBER, AGENTS, VENDOR_BY_NAME

FD = "/usr/share/fonts/truetype/dejavu/"
pdfmetrics.registerFont(TTFont("Sans", FD + "DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("Sans-Bold", FD + "DejaVuSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Sans-Oblique", FD + "DejaVuSans-Oblique.ttf"))
pdfmetrics.registerFont(TTFont("Serif", FD + "DejaVuSerif.ttf"))
pdfmetrics.registerFont(TTFont("Serif-Bold", FD + "DejaVuSerif-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Mono", FD + "DejaVuSansMono.ttf"))
from reportlab.lib.fonts import addMapping
addMapping("Sans", 0, 0, "Sans"); addMapping("Sans", 1, 0, "Sans-Bold"); addMapping("Sans", 0, 1, "Sans-Oblique"); addMapping("Sans", 1, 1, "Sans-Bold")
addMapping("Serif", 0, 0, "Serif"); addMapping("Serif", 1, 0, "Serif-Bold"); addMapping("Serif", 0, 1, "Serif"); addMapping("Serif", 1, 1, "Serif-Bold")

INK = colors.HexColor("#1d2430")
MUTED = colors.HexColor("#5b6574")
RULE = colors.HexColor("#c9ced6")
BRAND = colors.HexColor("#3b2a6b")   # Larkspur purple

def S(name, **kw):
    base = dict(fontName="Sans", fontSize=9.5, leading=13, textColor=INK)
    base.update(kw)
    return ParagraphStyle(name, **base)

ST = {
    "title": S("title", fontName="Sans-Bold", fontSize=18, leading=22, spaceAfter=4, textColor=BRAND),
    "sub": S("sub", fontSize=9, textColor=MUTED, spaceAfter=10),
    "h2": S("h2", fontName="Sans-Bold", fontSize=12.5, leading=16, spaceBefore=12, spaceAfter=5, textColor=BRAND),
    "h3": S("h3", fontName="Sans-Bold", fontSize=10.5, leading=14, spaceBefore=8, spaceAfter=3),
    "h4": S("h4", fontName="Sans-Bold", fontSize=9.5, leading=13, spaceBefore=6, spaceAfter=2),
    "p": S("p", spaceAfter=5),
    "small": S("small", fontSize=8, leading=10, textColor=MUTED),
    "cell": S("cell", fontSize=8.5, leading=11),
    "cellb": S("cellb", fontName="Sans-Bold", fontSize=8.5, leading=11),
    "cellr": S("cellr", fontSize=8.5, leading=11, alignment=TA_RIGHT),
    "cellbr": S("cellbr", fontName="Sans-Bold", fontSize=8.5, leading=11, alignment=TA_RIGHT),
}

def esc(t):
    return (t or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def inline(t):
    t = esc(t)
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)

def money(v):
    return f"${v:,.2f}"

# ------------------------------------------------------------------ page frames
def make_doc(path, header_left, header_right="", footer=None, on_page_extra=None, margins=0.75, title=""):
    doc = BaseDocTemplate(path, pagesize=letter, leftMargin=margins * inch, rightMargin=margins * inch,
                          topMargin=0.85 * inch, bottomMargin=0.8 * inch, title=title, author=header_left)
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")
    foot = footer or COMPANY["disclaimer"]

    def on_page(c, d):
        c.saveState()
        w, h = letter
        c.setFont("Sans-Bold", 8); c.setFillColor(MUTED)
        c.drawString(d.leftMargin, h - 0.5 * inch, header_left)
        c.setFont("Sans", 8)
        if header_right:
            c.drawRightString(w - d.rightMargin, h - 0.5 * inch, header_right)
        c.setStrokeColor(RULE); c.setLineWidth(0.6)
        c.line(d.leftMargin, h - 0.56 * inch, w - d.rightMargin, h - 0.56 * inch)
        c.line(d.leftMargin, 0.62 * inch, w - d.rightMargin, 0.62 * inch)
        c.setFont("Sans", 7); c.setFillColor(MUTED)
        c.drawString(d.leftMargin, 0.45 * inch, foot)
        c.drawRightString(w - d.rightMargin, 0.45 * inch, f"Page {d.page}")
        if on_page_extra:
            on_page_extra(c, d)
        c.restoreState()

    doc.addPageTemplates([PageTemplate(id="p", frames=[frame], onPage=on_page)])
    return doc

def grid(rows, widths, header=True, zebra=True, font=8.5, box=True, bold_last=False):
    t = Table(rows, colWidths=widths, repeatRows=1 if header else 0)
    style = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("FONTNAME", (0, 0), (-1, -1), "Sans"),
             ("FONTSIZE", (0, 0), (-1, -1), font), ("TOPPADDING", (0, 0), (-1, -1), 3),
             ("BOTTOMPADDING", (0, 0), (-1, -1), 3), ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5)]
    if box:
        style += [("LINEBELOW", (0, 0), (-1, -1), 0.4, RULE)]
    if header:
        style += [("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eceaf3")), ("FONTNAME", (0, 0), (-1, 0), "Sans-Bold")]
    if zebra:
        for i in range(1 if header else 0, len(rows)):
            if i % 2 == 0:
                style.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#f7f7fa")))
    if bold_last:
        style += [("FONTNAME", (0, -1), (-1, -1), "Sans-Bold"), ("LINEABOVE", (0, -1), (-1, -1), 0.8, INK)]
    t.setStyle(TableStyle(style))
    return t

# ------------------------------------------------------------------ markdown renderer (KB)
ITEM_RE = re.compile(r"^(\s*)(\([0-9a-z]+\)|[0-9]+\.[0-9]+|[A-Z][0-9]+ -|[0-9]+\.)\s")

def md_to_flowables(md):
    out = []
    lines = md.strip("\n").split("\n")
    i = 0
    para = []
    def flush():
        nonlocal para
        if para:
            text = " ".join(x.strip() for x in para)
            out.append(Paragraph(inline(text), ST["p"]))
            para = []
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("# "):
            flush(); out.append(Paragraph(inline(ln[2:]), ST["title"]))
        elif ln.startswith("## "):
            flush(); out.append(Paragraph(inline(ln[3:]), ST["h2"]))
        elif ln.startswith("### "):
            flush(); out.append(Paragraph(inline(ln[4:]), ST["h3"]))
        elif ln.startswith("#### "):
            flush(); out.append(Paragraph(inline(ln[5:]), ST["h4"]))
        elif ln.startswith("**") and i < 3:
            flush(); out.append(Paragraph(inline(ln), ST["sub"]))
        elif ln.startswith("|"):
            flush()
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                rows.append(cells); i += 1
            n = len(rows[0])
            avail = 7.0 * inch
            if n == 2: widths = [avail * .35, avail * .65]
            elif n == 3: widths = [avail * .38, avail * .37, avail * .25]
            else: widths = [avail / n] * n
            data = [[Paragraph(inline(c), ST["cellb"] if r == 0 else ST["cell"]) for c in row] for r, row in enumerate(rows)]
            out.append(Spacer(1, 3)); out.append(grid(data, widths)); out.append(Spacer(1, 6))
            continue
        elif ln.startswith("- "):
            flush()
            out.append(Paragraph(inline(ln[2:]), S("bul", leftIndent=14, bulletIndent=4, spaceAfter=3), bulletText="•"))
        elif ln.strip() == "":
            flush()
        elif ITEM_RE.match(ln) and ln.startswith(" "):
            flush()
            lead = len(ln) - len(ln.lstrip(" "))
            out.append(Paragraph(inline(ln.strip()), S("item", leftIndent=12 * lead, spaceAfter=4)))
        else:
            para.append(ln)
        i += 1
    flush()
    return out

def render_kb(md, path, doc_code):
    title = md.strip().split("\n")[0][2:]
    doc = make_doc(path, f"{COMPANY['name']}", f"{doc_code}", title=title)
    doc.build(md_to_flowables(md))

# ------------------------------------------------------------------ declarations
def kv_table(pairs, widths=(2.0 * inch, 5.0 * inch)):
    data = [[Paragraph(f"<b>{esc(k)}</b>", ST["cell"]), Paragraph(esc(str(v)), ST["cell"])] for k, v in pairs]
    return grid(data, list(widths), header=False, zebra=True)

def render_declarations(p, path):
    is_auto = p["line"] == "AUTO"
    title = "Personal Auto Policy - Declarations" if is_auto else "Homeowners Policy - Declarations"
    doc = make_doc(path, COMPANY["name"], f"Declarations  |  {p['policy_number']}", title=title)
    agent = AGENTS[p["agent"]]
    fl = [Paragraph(title, ST["title"]),
          Paragraph(f"{COMPANY['name']}  |  {COMPANY['address']}  |  Claims: {COMPANY['claims_phone']}", ST["sub"])]
    pairs = [("Policy number", p["policy_number"]), ("Policy form", p["form"]),
             ("Named insured(s)", " and ".join(p["named_insureds"])),
             ("Mailing address", p["mailing_address"])]
    if not is_auto:
        pairs.append(("Residence premises", p["property_address"]))
    pairs += [("Policy period", f"{p['term_effective']} to {p['term_expiration']} (12:01 a.m. standard time)"),
              ("Customer since", p["original_inception"]),
              ("Policy status", p["status"] + (f" - cancelled effective {p['cancellation']['effective']} ({p['cancellation']['reason']})" if p.get("cancellation") else "")),
              ("Agent", f"{agent['name']} - {agent['contact']}, {agent['phone']}")]
    fl.append(kv_table(pairs)); fl.append(Spacer(1, 10))
    if is_auto:
        fl.append(Paragraph("Covered Autos", ST["h3"]))
        rows = [["Veh", "Year / Make / Model", "VIN", "Garaging ZIP"]]
        for v in p["vehicles"]:
            rows.append([str(v["veh_no"]), f"{v['year']} {v['make']} {v['model']}", v["vin"], v["garaging_zip"]])
        fl.append(grid(rows, [0.5 * inch, 2.6 * inch, 2.4 * inch, 1.5 * inch])); fl.append(Spacer(1, 10))
        c = p["coverages"]
        fl.append(Paragraph("Coverages and Limits (each covered auto)", ST["h3"]))
        rows = [["Coverage", "Limit / Deductible", "Status"],
                ["Part A - Bodily Injury Liability", f"${c['bodily_injury']} each person/each accident", "Included"],
                ["Part A - Property Damage Liability", f"${c['property_damage']:,} each accident", "Included"],
                ["Part B - Medical Payments", f"${c['medical_payments']:,} each person", "Included"],
                ["Part C - Uninsured Motorists (BI)", f"${c['uninsured_motorist']} each person/each accident", "Included"],
                ["Part C - Uninsured Motorists (PD)", f"Deductible ${c['uninsured_motorist_pd_deductible']}", "Included"],
                ["Part D - Collision", f"Deductible ${c['collision_deductible']:,}" if c["collision_deductible"] else "-", "Included" if c["collision_deductible"] else "NOT PURCHASED"],
                ["Part D - Other Than Collision (Comprehensive)", f"Deductible ${c['comprehensive_deductible']:,}" if c["comprehensive_deductible"] else "-", "Included" if c["comprehensive_deductible"] else "NOT PURCHASED"]]
        fl.append(grid([[Paragraph(esc(str(x)), ST["cell"]) for x in r] for r in rows], [2.7 * inch, 3.25 * inch, 1.05 * inch]))
    else:
        c = p["coverages"]; d = p["deductibles"]
        dw = p.get("dwelling", {})
        if dw:
            fl.append(Paragraph("Dwelling Information", ST["h3"]))
            fl.append(kv_table([("Year built", dw.get("year_built")), ("Construction", dw.get("construction")),
                                ("Roof", f"{dw.get('roof')} (installed {dw.get('roof_year')})"), ("Square feet", f"{dw.get('sq_ft'):,}")]
                               + ([("Notes", dw["notes"])] if dw.get("notes") else [])))
            fl.append(Spacer(1, 10))
        fl.append(Paragraph("Coverages and Limits", ST["h3"]))
        rows = [["Coverage", "Limit"],
                ["A - Dwelling", money(c["A_dwelling"])], ["B - Other Structures", money(c["B_other_structures"])],
                ["C - Personal Property", money(c["C_personal_property"])], ["D - Loss of Use", money(c["D_loss_of_use"])],
                ["E - Personal Liability (each occurrence)", money(c["E_personal_liability"])],
                ["F - Medical Payments to Others (each person)", money(c["F_medical_payments"])]]
        fl.append(grid(rows, [4.2 * inch, 2.8 * inch])); fl.append(Spacer(1, 10))
        fl.append(Paragraph("Deductibles", ST["h3"]))
        if d["wind_hail"]["type"] == "percent_of_A":
            wh = f"{d['wind_hail']['percent']}% of Coverage A = {money(d['wind_hail']['amount'])}"
        else:
            wh = f"Same as all-peril ({money(d['wind_hail']['amount'])})"
        fl.append(grid([["Deductible", "Amount"], ["All-peril (Section I)", money(d["all_peril"])], ["Windstorm or hail", wh]],
                       [4.2 * inch, 2.8 * inch]))
        if p.get("mortgagee"):
            fl.append(Spacer(1, 6)); fl.append(Paragraph(f"<b>Mortgagee:</b> {esc(p['mortgagee'])}", ST["p"]))
    fl.append(Spacer(1, 10))
    fl.append(Paragraph("Endorsements", ST["h3"]))
    if p["endorsements"]:
        rows = [["Form", "Endorsement", "Limit / Notes"]]
        for e in p["endorsements"]:
            lim = e.get("limit", "")
            rows.append([e["code"], e["name"], money(lim) if isinstance(lim, (int, float)) else lim])
        fl.append(grid(rows, [1.3 * inch, 3.3 * inch, 2.4 * inch]))
    else:
        fl.append(Paragraph("None.", ST["p"]))
    if p.get("scheduled_items"):
        fl.append(Spacer(1, 8)); fl.append(Paragraph("Schedule - LM-HO-SPP Scheduled Personal Property", ST["h3"]))
        rows = [["Class", "Description", "Agreed value"]]
        for s in p["scheduled_items"]:
            rows.append([s["class"], Paragraph(esc(s["item"]), ST["cell"]), money(s["agreed_value"])])
        fl.append(grid(rows, [1.0 * inch, 4.5 * inch, 1.5 * inch]))
    if p.get("lienholders"):
        fl.append(Spacer(1, 6)); fl.append(Paragraph("<b>Lienholder:</b> " + esc(", ".join(l["name"] + f" (veh {l['vehicle']})" for l in p["lienholders"])), ST["p"]))
    fl.append(Spacer(1, 12))
    fl.append(Paragraph("This Declarations page, together with the policy form and endorsements listed above, completes your policy. "
                        "Coverage applies only to losses occurring during the policy period while the policy is in force.", ST["small"]))
    doc.build(fl)

# ------------------------------------------------------------------ claim documents
VENDOR_COLORS = {
    "Ashford Auto Glass": "#0b6e8a", "Millbrook Collision Center": "#9c2a1e", "Riverton Auto Body": "#1f5a2e",
    "Brookhaven Body Works": "#30437a", "QuickFix Auto Body & Paint": "#c25e00", "Cedar Lane Restoration": "#2f6f5e",
    "Hometown Plumbing Co.": "#1b4f8c", "Riverton Builders": "#6b4a1f", "Oakridge Fire & Water Restoration": "#8a1c1c",
    "Summit Peak Roofing": "#3a3f45", "Ashford Tree Service": "#3e6b23",
}

def letterhead(name, address, phone, color, right_lines):
    left = Paragraph(f"<font name='Sans-Bold' size='15' color='{color}'>{esc(name)}</font><br/>"
                     f"<font size='8' color='#5b6574'>{esc(address)}  |  {esc(phone)}</font>", S("lh", leading=17))
    right = Paragraph("<br/>".join(right_lines), S("lhr", fontSize=8.5, leading=11.5, alignment=TA_RIGHT))
    t = Table([[left, right]], colWidths=[4.4 * inch, 2.6 * inch])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, 0), 1.6, colors.HexColor(color)),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
    return t

def render_estimate(d, path):
    v = VENDOR_BY_NAME[d["vendor"]]
    color = VENDOR_COLORS.get(d["vendor"], "#333333")
    hidden = d.get("hidden_text")

    def extra(c, doc):
        if hidden:
            c.setFillColorRGB(1, 1, 1); c.setFont("Sans", 1.5)
            c.drawString(doc.leftMargin, 0.70 * inch, hidden)

    doc = make_doc(path, d["vendor"], f"{d['title'].title()} {d['number']}",
                   footer="Synthetic training document - fictional business. Not a real estimate or invoice.",
                   on_page_extra=extra, title=f"{d['vendor']} {d['number']}")
    fl = [letterhead(d["vendor"], v["address"], v["phone"], color,
                     [f"<b>{esc(d['title'])}</b>", f"No. {esc(d['number'])}", f"Date: {esc(d['date'])}"]),
          Spacer(1, 10),
          kv_table([("Customer", d["customer"]), ("Vehicle / Property", d["asset"])], (1.6 * inch, 5.4 * inch)),
          Spacer(1, 10)]
    rows = [["#", "Description", "Qty", "Unit", "Unit price", "Amount"]]
    total = 0.0
    for i, ln in enumerate(d["lines"], 1):
        amt = round(ln["qty"] * ln["unit_price"], 2); total += amt
        q = ln["qty"]; qs = f"{q:g}" if isinstance(q, float) else str(q)
        rows.append([str(i), Paragraph(esc(ln["description"]), ST["cell"]), qs, ln["unit"] or "ea",
                     Paragraph(money(ln["unit_price"]), ST["cellr"]), Paragraph(money(amt), ST["cellr"])])
    total = round(total, 2)
    rows.append(["", Paragraph("<b>TOTAL</b>", ST["cell"]), "", "", "", Paragraph(f"<b>{money(total)}</b>", ST["cellr"])])
    fl.append(grid(rows, [0.3 * inch, 3.55 * inch, 0.55 * inch, 0.55 * inch, 0.95 * inch, 1.1 * inch], bold_last=True))
    fl.append(Spacer(1, 10))
    if d.get("notes"):
        fl.append(Paragraph("<b>Notes / Findings</b>", ST["h4"]))
        fl.append(Paragraph(esc(d["notes"]), ST["p"]))
    fl.append(Spacer(1, 16))
    fl.append(Paragraph("Prices valid 30 days. Hidden damage may require a supplement. Payment is the responsibility of the customer unless the "
                        "insurer has authorized direct payment in writing.", ST["small"]))
    doc.build(fl)
    return total

def render_police_report(d, path):
    doc = make_doc(path, d["agency"], f"Report No. {d['report_no']}",
                   footer="Synthetic training document - fictional agency. Not a real police record.", title=d["report_no"])
    fl = [Table([[Paragraph(f"<font name='Sans-Bold' size='14'>{esc(d['agency'].upper())}</font><br/>"
                            f"<font size='10'>{esc(d['report_type'])}</font>", S("ph", leading=17)),
                  Paragraph(f"<b>Report No.</b><br/><font size='12'>{esc(d['report_no'])}</font>", S("pn", alignment=TA_RIGHT, leading=15))]],
                colWidths=[4.8 * inch, 2.2 * inch],
                style=[("BOX", (0, 0), (-1, -1), 1.2, INK), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                       ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0f1f4")), ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]),
          Spacer(1, 8),
          kv_table([("Date/time reported", d["reported"]), ("Date/time of incident", d["occurred"]),
                    ("Location", d["location"]), ("Conditions", d.get("weather", "N/A"))], (1.8 * inch, 5.2 * inch)),
          Spacer(1, 8), Paragraph("Involved Units / Parties", ST["h3"])]
    rows = [["Unit", "Person", "Vehicle", "Insurance", "Direction / Damage"]]
    for u in d["units"]:
        person = u["driver"] + (f"<br/><font size='7'>{esc(u['dl'])}</font>" if u.get("dl") else "")
        rows.append([str(u["unit"]), Paragraph(person, ST["cell"]), Paragraph(esc(u["vehicle"]), ST["cell"]),
                     Paragraph(esc(u["insurer"]), ST["cell"]), Paragraph(esc((u["direction"] + " / " if u["direction"] else "") + u["damage"]), ST["cell"])])
    fl.append(grid(rows, [0.75 * inch, 1.45 * inch, 1.75 * inch, 1.45 * inch, 1.6 * inch]))
    fl.append(Spacer(1, 8)); fl.append(Paragraph("Injuries", ST["h3"])); fl.append(Paragraph(esc(d["injuries"]), ST["p"]))
    fl.append(Paragraph("Narrative", ST["h3"])); fl.append(Paragraph(esc(d["narrative"]), ST["p"]))
    fl.append(Paragraph("Citations", ST["h3"])); fl.append(Paragraph(esc(d["citations"]), ST["p"]))
    fl.append(Spacer(1, 14))
    fl.append(kv_table([("Reporting officer", d["officer"]), ("Approved", "Shift supervisor - electronically approved")], (1.8 * inch, 5.2 * inch)))
    doc.build(fl)

def render_fire_report(d, path):
    doc = make_doc(path, d["agency"], f"Incident No. {d['report_no']}",
                   footer="Synthetic training document - fictional agency. Not a real fire department record.", title=d["report_no"])
    fl = [Paragraph(f"{esc(d['agency'])} - Incident Report", ST["title"]),
          Paragraph(f"Incident No. {esc(d['report_no'])}", ST["sub"]),
          kv_table([("Incident address", d["address"]), ("Incident type", d["incident_type"]),
                    ("Alarm time", d["alarm"]), ("Arrival", d["arrival"]), ("Fire under control", d["controlled"]), ("Units cleared", d["cleared"]),
                    ("Cause", d["cause"]), ("Area of origin", d["origin"]), ("Fire/smoke extension", d["extension"]),
                    ("Injuries", d["injuries"]), ("Occupants", d["occupants"]), ("Estimated loss", d["est_loss"]),
                    ("Officer in charge", d["officer"])], (1.9 * inch, 5.1 * inch))]
    doc.build(fl)

def render_medical_bill(d, path):
    doc = make_doc(path, d["provider"], f"Account {d['account']}",
                   footer="Synthetic training document - fictional provider and patient. Not a real medical record.", title="Patient statement")
    fl = [letterhead(d["provider"], d["provider_address"], "(804) 555-0150", "#0f5c7a",
                     ["<b>ITEMIZED PATIENT STATEMENT</b>", f"Account: {esc(d['account'])}", f"Statement date: 10/19/2026"]),
          Spacer(1, 10),
          kv_table([("Patient", d["patient"]), ("Date of birth", d["dob"]), ("Medical record no.", d["mrn"]),
                    ("Insurance", d["insurance"]), ("Date of service", d["service_date"]),
                    ("Encounter", "Emergency department - arrived by ambulance")], (1.8 * inch, 5.2 * inch)),
          Spacer(1, 8), Paragraph("Diagnoses", ST["h3"])]
    fl.append(grid([["ICD-10", "Description"]] + [[c, Paragraph(esc(t), ST["cell"])] for c, t in d["diagnoses"]], [1.2 * inch, 5.8 * inch]))
    fl.append(Spacer(1, 8)); fl.append(Paragraph("Charges", ST["h3"]))
    rows = [["Code", "Description", "Charge"]]
    tot = 0
    for code, desc, amt in d["items"]:
        rows.append([code, Paragraph(esc(desc), ST["cell"]), Paragraph(money(amt), ST["cellr"])]); tot += amt
    rows.append(["", Paragraph("<b>Total charges</b>", ST["cell"]), Paragraph(f"<b>{money(tot)}</b>", ST["cellr"])])
    fl.append(grid(rows, [1.2 * inch, 4.6 * inch, 1.2 * inch], bold_last=True))
    fl.append(Spacer(1, 8)); fl.append(Paragraph(esc(d["note"]), ST["small"]))
    doc.build(fl)
    return tot

def render_web_form(claim, path):
    w = claim["web_form"]
    doc = make_doc(path, COMPANY["name"] + " - Online Claim Center", f"Submission {w['submission_no']}",
                   title=f"FNOL {w['submission_no']}")
    fl = [Paragraph(f"First Notice of Loss - {w['line']}", ST["title"]),
          Paragraph(f"Web submission {esc(w['submission_no'])}  |  Submitted {esc(w['submitted'])}  |  Source: larkspur-mutual.example/claims", ST["sub"])]
    data = [[Paragraph(f"<b>{esc(k)}</b>", ST["cell"]), Paragraph(esc(v), ST["cell"])] for k, v in w["fields"]]
    fl.append(grid(data, [2.0 * inch, 5.0 * inch], header=False))
    fl.append(Spacer(1, 10))
    fl.append(Paragraph("By submitting this form the reporter confirmed the information is true and complete to the best of their knowledge.", ST["small"]))
    doc.build(fl)

def render_inventory(d, path):
    doc = make_doc(path, d["owner"], d["date"], footer="Synthetic training document - fictional person.", title=d["title"])
    fl = [Paragraph(esc(d["title"]), ST["title"]), Paragraph(f"Prepared by {esc(d['owner'])}  |  {esc(d['date'])}", ST["sub"])]
    rows = [["#", "Item", "Qty", "Value each", "Total", "Purchased", "Notes / proof"]]
    tot = 0
    for i, (item, qty, val, yr, note) in enumerate(d["items"], 1):
        t = qty * val; tot += t
        rows.append([str(i), Paragraph(esc(item), ST["cell"]), str(qty), Paragraph(money(val), ST["cellr"]),
                     Paragraph(money(t), ST["cellr"]), yr, Paragraph(esc(note), ST["cell"])])
    rows.append(["", Paragraph("<b>Total claimed</b>", ST["cell"]), "", "", Paragraph(f"<b>{money(tot)}</b>", ST["cellr"]), "", ""])
    fl.append(grid(rows, [0.3 * inch, 2.4 * inch, 0.4 * inch, 0.9 * inch, 0.95 * inch, 0.8 * inch, 1.25 * inch], bold_last=True))
    doc.build(fl)
    return tot

def render_appraisal(d, path):
    doc = make_doc(path, d["jeweler"], "Appraisal for Insurance Replacement",
                   footer="Synthetic training document - fictional business.", title="Appraisal")
    fl = [letterhead(d["jeweler"], d["jeweler_address"], "(804) 555-0185", "#7a5c12",
                     ["<b>APPRAISAL</b>", "For insurance replacement value", esc(d["date"])]),
          Spacer(1, 12), Paragraph(f"<b>Prepared for:</b> {esc(d['client'])}", ST["p"]), Spacer(1, 6)]
    rows = [["Item description", "Replacement value"]]
    for desc, val in d["items"]:
        rows.append([Paragraph(esc(desc), ST["cell"]), Paragraph(money(val), ST["cellr"])])
    fl.append(grid(rows, [5.4 * inch, 1.6 * inch]))
    fl.append(Spacer(1, 12))
    fl.append(Paragraph("The values above represent the estimated cost to replace the items with new items of like kind and quality at the date of appraisal. "
                        "This appraisal was prepared after physical examination of the items.", ST["p"]))
    fl.append(Spacer(1, 18)); fl.append(Paragraph(f"Appraiser: {esc(d['appraiser'])}", ST["p"]))
    doc.build(fl)
