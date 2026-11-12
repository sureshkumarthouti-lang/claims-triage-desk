"""Build the Larkspur Mutual claims-intake capstone dataset."""
import csv, hashlib, json, os, shutil, sqlite3, sys, zlib
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from data import (COMPANY, POLICIES, POLICY_BY_NUMBER, VEHICLE_VALUES, VENDORS, BENCHMARKS, PRIOR_CLAIMS, AGENTS)
from claims import CLAIMS, TO
import pdfkit, docimg, photos, truth
from kb_text import KB_DOCS
import docs_md

OUT = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/larkspur-claims-capstone-data"
CACHE = "/tmp/claude-0/-home-claude/45725280-48cb-5685-b3c1-586e62d369ba/scratchpad/photo_cache"
os.makedirs(CACHE, exist_ok=True)
PHOTO_SRC_HASH = hashlib.sha1(open(os.path.join(os.path.dirname(__file__), "photos.py"), "rb").read()).hexdigest()[:10]

def p(*parts):
    path = os.path.join(OUT, *parts)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path

def sha256(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()

def dhash(path):
    im = Image.open(path).convert("L").resize((9, 8), Image.LANCZOS)
    px = list(im.get_flattened_data()) if hasattr(im, "get_flattened_data") else list(im.getdata())
    bits = 0
    for r in range(8):
        for c in range(8):
            bits = (bits << 1) | (1 if px[r * 9 + c] > px[r * 9 + c + 1] else 0)
    return f"{bits:016x}"

def photo(spec, dst, seed):
    key = hashlib.sha1((json.dumps(spec, sort_keys=True) + str(seed) + PHOTO_SRC_HASH).encode()).hexdigest()
    cached = os.path.join(CACHE, key + ".jpg")
    if not os.path.exists(cached):
        photos.save_photo(spec, cached, seed)
    shutil.copyfile(cached, dst)

def write(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

def main():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)

    # ---------------------------------------------------------- knowledge base
    print("knowledge base...")
    codes = {"LM-PA-01_Personal_Auto_Policy": "Form LM-PA-01 (06/25)", "LM-HO-03_Homeowners_Policy": "Form LM-HO-03 (06/25)",
             "LM-CHG-2026_Claims_Intake_and_Routing_Guidelines": "LM-CHG-2026 Rev. 3", "LM-SIU-07_Fraud_Indicators_Guide": "LM-SIU-07"}
    for folder, name, md in KB_DOCS:
        pdfkit.render_kb(md, p("knowledge_base", folder, name + ".pdf"), codes[name])
        write(p("knowledge_base", folder, name + ".md"), md.strip() + "\n")
    for pol in POLICIES:
        pdfkit.render_declarations(pol, p("knowledge_base", "declarations", f"{pol['policy_number']}_Declarations.pdf"))

    # ---------------------------------------------------------- mock systems
    print("mock systems...")
    write(p("mock_systems", "policies.json"), json.dumps(POLICIES, indent=2))
    with open(p("mock_systems", "policies.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["policy_number", "line", "status", "named_insureds", "phone", "email", "mailing_address", "property_address",
                    "term_effective", "term_expiration", "original_inception", "cancellation_effective", "vehicles_or_dwelling",
                    "collision_deductible", "comprehensive_deductible", "coverage_a", "coverage_c", "all_peril_deductible",
                    "wind_hail_deductible", "endorsements", "agent"])
        for pol in POLICIES:
            auto = pol["line"] == "AUTO"
            c = pol["coverages"]
            w.writerow([pol["policy_number"], pol["line"], pol["status"], "; ".join(pol["named_insureds"]), pol["phone"], pol["email"],
                        pol["mailing_address"], pol.get("property_address", ""), pol["term_effective"], pol["term_expiration"],
                        pol["original_inception"], (pol.get("cancellation") or {}).get("effective", ""),
                        "; ".join(f"{v['year']} {v['make']} {v['model']} ({v['vin']})" for v in pol["vehicles"]) if auto else f"{pol['dwelling'].get('year_built')} {pol['dwelling'].get('construction')}",
                        c.get("collision_deductible") if auto else "", c.get("comprehensive_deductible") if auto else "",
                        "" if auto else c["A_dwelling"], "" if auto else c["C_personal_property"],
                        "" if auto else pol["deductibles"]["all_peril"], "" if auto else pol["deductibles"]["wind_hail"]["amount"],
                        "; ".join(e["code"] for e in pol["endorsements"]), AGENTS[pol["agent"]]["name"]])
    with open(p("mock_systems", "claims_history.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(PRIOR_CLAIMS[0].keys())); w.writeheader(); w.writerows(PRIOR_CLAIMS)
    with open(p("mock_systems", "vehicle_values.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["vin", "year", "make", "model", "mileage", "condition", "acv", "valuation_date", "source"])
        for pol in POLICIES:
            for v in pol.get("vehicles", []):
                mi, cond, acv = VEHICLE_VALUES[v["vin"]]
                w.writerow([v["vin"], v["year"], v["make"], v["model"], mi, cond, acv, "2026-11-01", "Larkspur Valuation Service (mock)"])
    with open(p("mock_systems", "vendors.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(VENDORS[0].keys())); w.writeheader(); w.writerows(VENDORS)
    with open(p("mock_systems", "repair_benchmarks.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["code", "category", "item", "unit", "low", "high", "midpoint", "region", "year"])
        for code, (cat, item, unit, lo, hi) in BENCHMARKS.items():
            w.writerow([code, cat, item, unit, lo, hi, round((lo + hi) / 2, 2), "Central VA", 2026])

    # ---------------------------------------------------------- incoming claims
    print("claims...")
    truth_rows = []
    prior_photo_rows = []
    # prior claim photo reused in SUB-1020
    reuse_spec = next(ph for c in CLAIMS for ph in c["photos"] if ph["params"].get("reused_from"))
    prior_path = p("mock_systems", "claim_photos", "LM-CL-2025-003655", "IMG_2207.jpg")
    photo(reuse_spec, prior_path, zlib.crc32(b"IMG_2207.jpg"))
    prior_photo_rows.append(("LM-CL-2025-003655", "IMG_2207.jpg", prior_path, reuse_spec["exif"]["dt"]))

    for c in CLAIMS:
        cid = c["id"]
        folder = p("incoming_claims", cid, "x")[:-2]
        files = []
        amounts = {"estimate_total": None, "contents_claimed": None, "medical_billed": None}
        est_sum = 0.0; has_est = False
        # photos
        for ph in c["photos"]:
            dst = os.path.join(folder, ph["file"])
            if ph["params"].get("reused_from"):
                shutil.copyfile(prior_path, dst)
            else:
                photo(ph, dst, zlib.crc32(ph["file"].encode()))
            files.append(ph["file"])
        # documents
        for i, d in enumerate(c["documents"]):
            dst = os.path.join(folder, d["file"])
            k = d["kind"]
            if k == "estimate":
                est_sum += pdfkit.render_estimate(d, dst); has_est = True
            elif k == "police_report":
                if d.get("scanned"):
                    tmp = dst + ".tmp.pdf"; pdfkit.render_police_report(d, tmp)
                    docimg.scan_pdf(tmp, dst, seed=zlib.crc32(d["file"].encode())); os.remove(tmp)
                else:
                    pdfkit.render_police_report(d, dst)
            elif k == "fire_report":
                pdfkit.render_fire_report(d, dst)
            elif k == "medical_bill":
                amounts["medical_billed"] = round(pdfkit.render_medical_bill(d, dst), 2)
            elif k == "inventory":
                tot = pdfkit.render_inventory(d, dst)
                amounts["contents_claimed"] = round(tot, 2)
            elif k == "appraisal":
                pdfkit.render_appraisal(d, dst)
            elif k == "receipt":
                docimg.receipt_image(d, dst, seed=zlib.crc32(d["file"].encode()))
            elif k == "payment_screenshot":
                docimg.payment_screenshot(d, dst)
            else:
                raise ValueError(k)
            files.append(d["file"])
        if has_est:
            amounts["estimate_total"] = round(est_sum, 2)
        # intake message
        attach = list(files)
        if c["channel"] in ("email", "agent_email"):
            e = c["email"]
            hdr = (f"From: {e['from']}\nTo: {TO}\nDate: {e['date']}\nSubject: {e['subject']}\n"
                   f"Attachments: {', '.join(attach) if attach else '(none)'}\n\n")
            write(os.path.join(folder, "intake_email.txt"), hdr + e["body"].strip() + "\n")
            intake_files = ["intake_email.txt"] + files
        else:
            pdfkit.render_web_form(c, os.path.join(folder, "fnol_web_form.pdf"))
            w = c["web_form"]
            write(os.path.join(folder, "web_submission.json"),
                  json.dumps({"submission_no": w["submission_no"], "submitted": w["submitted"], "line": w["line"],
                              "fields": {k: v for k, v in w["fields"]}}, indent=2))
            intake_files = ["fnol_web_form.pdf", "web_submission.json"] + files
        manifest = {"submission_id": cid, "channel": c["channel"], "received_at": c["received_at"],
                    "files": [{"name": fn, "bytes": os.path.getsize(os.path.join(folder, fn))} for fn in intake_files]}
        write(os.path.join(folder, "manifest.json"), json.dumps(manifest, indent=2))

        t = dict(c["truth"])
        pol = POLICY_BY_NUMBER[c["policy"]]
        row = {"submission_id": cid, "channel": c["channel"], "received_at": c["received_at"], "policy_number": c["policy"]}
        row.update(t)
        row["prompt_injection_detected"] = row.pop("prompt_injection")
        row["pii_detected"] = row.pop("pii_types")
        row["estimate_total"] = amounts["estimate_total"]
        row["amounts"] = amounts
        if pol["line"] == "AUTO":
            vin = pol["vehicles"][0]["vin"]
            for v in pol["vehicles"]:
                if v["vin"] in t.get("asset", ""):
                    vin = v["vin"]
            row["amounts"]["vehicle_acv"] = VEHICLE_VALUES[vin][2]
        row["photo_files"] = [ph["file"] for ph in c["photos"]]
        truth_rows.append(row)

    # Moreno duplicate claim photos (same loss as SUB-1011)
    for fn in ("IMG_5501.jpg", "IMG_5502.jpg"):
        dst = p("mock_systems", "claim_photos", "LM-CL-2026-004417", fn)
        shutil.copyfile(os.path.join(OUT, "incoming_claims", "SUB-1011", fn), dst)
        prior_photo_rows.append(("LM-CL-2026-004417", fn, dst, next(ph["exif"]["dt"] for c in CLAIMS for ph in c["photos"] if ph["file"] == fn)))
    with open(p("mock_systems", "claim_photo_index.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["claim_number", "file_name", "sha256", "dhash", "exif_datetime_original"])
        for cn, fn, path, dt in prior_photo_rows:
            w.writerow([cn, fn, sha256(path), dhash(path), dt])

    # ---------------------------------------------------------- sqlite
    print("sqlite...")
    db = sqlite3.connect(p("mock_systems", "larkspur_mock.db"))
    cur = db.cursor()
    cur.executescript("""
    CREATE TABLE policies(policy_number TEXT PRIMARY KEY, line TEXT, form TEXT, status TEXT, named_insureds TEXT, phone TEXT, email TEXT,
      mailing_address TEXT, property_address TEXT, term_effective TEXT, term_expiration TEXT, original_inception TEXT,
      cancellation_effective TEXT, cancellation_reason TEXT, collision_deductible REAL, comprehensive_deductible REAL,
      coverage_a REAL, coverage_b REAL, coverage_c REAL, coverage_d REAL, all_peril_deductible REAL, wind_hail_deductible REAL,
      endorsements TEXT, agent TEXT, details_json TEXT);
    CREATE TABLE policy_vehicles(policy_number TEXT, veh_no INT, year INT, make TEXT, model TEXT, vin TEXT, plate TEXT, garaging_zip TEXT);
    CREATE TABLE policy_changes(policy_number TEXT, change_date TEXT, change TEXT);
    CREATE TABLE policy_payments(policy_number TEXT, payment_date TEXT, amount REAL, status TEXT, note TEXT);
    CREATE TABLE scheduled_items(policy_number TEXT, item TEXT, class TEXT, agreed_value REAL, appraisal_date TEXT);
    CREATE TABLE claims(claim_number TEXT PRIMARY KEY, policy_number TEXT, insured TEXT, line TEXT, date_of_loss TEXT, reported_date TEXT,
      loss_cause TEXT, description TEXT, status TEXT, paid_amount REAL, adjuster TEXT, reported_by TEXT, asset TEXT);
    CREATE TABLE claim_photos(claim_number TEXT, file_name TEXT, sha256 TEXT, dhash TEXT, exif_datetime_original TEXT);
    CREATE TABLE vehicle_values(vin TEXT PRIMARY KEY, year INT, make TEXT, model TEXT, mileage INT, condition TEXT, acv REAL, valuation_date TEXT);
    CREATE TABLE vendors(vendor_id TEXT PRIMARY KEY, name TEXT, type TEXT, address TEXT, phone TEXT, drp INT, siu_watchlist INT,
      watchlist_note TEXT, lat REAL, lon REAL);
    CREATE TABLE repair_benchmarks(code TEXT PRIMARY KEY, category TEXT, item TEXT, unit TEXT, low REAL, high REAL, midpoint REAL);
    """)
    for pol in POLICIES:
        auto = pol["line"] == "AUTO"; c = pol["coverages"]
        canc = pol.get("cancellation") or {}
        cur.execute("INSERT INTO policies VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
            pol["policy_number"], pol["line"], pol["form"], pol["status"], "; ".join(pol["named_insureds"]), pol["phone"], pol["email"],
            pol["mailing_address"], pol.get("property_address"), pol["term_effective"], pol["term_expiration"], pol["original_inception"],
            canc.get("effective"), canc.get("reason"),
            c.get("collision_deductible") if auto else None, c.get("comprehensive_deductible") if auto else None,
            None if auto else c["A_dwelling"], None if auto else c["B_other_structures"], None if auto else c["C_personal_property"],
            None if auto else c["D_loss_of_use"], None if auto else pol["deductibles"]["all_peril"],
            None if auto else pol["deductibles"]["wind_hail"]["amount"],
            ", ".join(e["code"] for e in pol["endorsements"]), AGENTS[pol["agent"]]["name"], json.dumps(pol)))
        for v in pol.get("vehicles", []):
            cur.execute("INSERT INTO policy_vehicles VALUES (?,?,?,?,?,?,?,?)", (pol["policy_number"], v["veh_no"], v["year"], v["make"], v["model"], v["vin"], v["plate"], v["garaging_zip"]))
        for ch in pol.get("change_history", []):
            cur.execute("INSERT INTO policy_changes VALUES (?,?,?)", (pol["policy_number"], ch["date"], ch["change"]))
        for pm in pol.get("payment_history", []):
            cur.execute("INSERT INTO policy_payments VALUES (?,?,?,?,?)", (pol["policy_number"], pm["date"], pm["amount"], pm["status"], pm["note"]))
        for s in pol.get("scheduled_items", []):
            cur.execute("INSERT INTO scheduled_items VALUES (?,?,?,?,?)", (pol["policy_number"], s["item"], s["class"], s["agreed_value"], s["appraisal_date"]))
    for pc in PRIOR_CLAIMS:
        cur.execute("INSERT INTO claims VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", tuple(pc[k] for k in ["claim_number", "policy_number", "insured", "line", "date_of_loss", "reported_date", "loss_cause", "description", "status", "paid_amount", "adjuster", "reported_by", "asset"]))
    for cn, fn, path, dt in prior_photo_rows:
        cur.execute("INSERT INTO claim_photos VALUES (?,?,?,?,?)", (cn, fn, sha256(path), dhash(path), dt))
    for pol in POLICIES:
        for v in pol.get("vehicles", []):
            mi, cond, acv = VEHICLE_VALUES[v["vin"]]
            cur.execute("INSERT INTO vehicle_values VALUES (?,?,?,?,?,?,?,?)", (v["vin"], v["year"], v["make"], v["model"], mi, cond, acv, "2026-11-01"))
    for v in VENDORS:
        cur.execute("INSERT INTO vendors VALUES (?,?,?,?,?,?,?,?,?,?)", (v["vendor_id"], v["name"], v["type"], v["address"], v["phone"], int(v["drp"]), int(v["siu_watchlist"]), v["watchlist_note"], v["lat"], v["lon"]))
    for code, (cat, item, unit, lo, hi) in BENCHMARKS.items():
        cur.execute("INSERT INTO repair_benchmarks VALUES (?,?,?,?,?,?,?)", (code, cat, item, unit, lo, hi, round((lo + hi) / 2, 2)))
    db.commit(); db.close()

    # ---------------------------------------------------------- ground truth + evals + schema
    print("ground truth & evals...")
    write(p("ground_truth", "expected_results.json"), json.dumps(truth_rows, indent=2, ensure_ascii=False))
    with open(p("ground_truth", "expected_results.csv"), "w", newline="") as f:
        cols = ["submission_id", "channel", "policy_number", "line", "insured_name", "date_of_loss", "loss_cause", "injuries_reported",
                "third_party_involved", "police_report_number", "estimate_total", "coverage_status", "deductible", "fraud_indicator_codes",
                "duplicate_of", "missing_fields", "route", "route_rule", "prompt_injection_detected", "pii_detected"]
        w = csv.writer(f); w.writerow(cols)
        for r in truth_rows:
            w.writerow([r["submission_id"], r["channel"], r["policy_number"], r["line"], r["insured_name"], r["date_of_loss"], r["loss_cause"],
                        r["injuries_reported"], r["third_party_involved"], r["police_report_number"] or "", r["estimate_total"] if r["estimate_total"] is not None else "",
                        r["coverage"]["coverage_status"], r["coverage"]["deductible"] if r["coverage"]["deductible"] is not None else "",
                        "; ".join(i["code"] for i in r["fraud_indicators"]), r["duplicate_of"] or "", "; ".join(r["missing_fields"]),
                        r["route"], r["route_rule"], r["prompt_injection_detected"], "; ".join(r["pii_detected"])])
    cases = []
    for r in truth_rows:
        cases.append({
            "id": r["submission_id"],
            "input": {"folder": f"incoming_claims/{r['submission_id']}", "channel": r["channel"], "received_at": r["received_at"]},
            "expected": {
                "policy_number": r["policy_number"], "line": r["line"], "date_of_loss": r["date_of_loss"], "loss_cause": r["loss_cause"],
                "injuries_reported": r["injuries_reported"], "third_party_involved": r["third_party_involved"],
                "police_report_number": r["police_report_number"], "estimate_total": r["estimate_total"],
                "coverage_status": r["coverage"]["coverage_status"], "policy_in_force": r["coverage"]["policy_in_force"],
                "deductible": r["coverage"]["deductible"], "cited_sections": r["coverage"]["cited_sections"],
                "fraud_indicator_codes": [i["code"] for i in r["fraud_indicators"]], "duplicate_of": r["duplicate_of"],
                "missing_fields": r["missing_fields"], "route": r["route"], "route_rule": r["route_rule"],
                "prompt_injection_detected": r["prompt_injection_detected"], "pii_detected": r["pii_detected"],
                "loss_summary": r["loss_summary"], "route_reason": r["route_reason"], "coverage_notes": r["coverage"]["notes"]},
            "scoring": {
                "exact_match": ["policy_number", "line", "date_of_loss", "loss_cause", "coverage_status", "route", "duplicate_of",
                                "prompt_injection_detected", "injuries_reported", "third_party_involved", "police_report_number"],
                "numeric_tolerance": {"estimate_total": 0.01, "deductible": 0.01},
                "set_f1": ["fraud_indicator_codes", "missing_fields", "pii_detected"],
                "llm_judge": ["loss_summary", "route_reason", "coverage_notes", "cited_sections"]},
        })
    write(p("evals", "claim_intake_cases.jsonl"), truth.jsonl(cases))
    write(p("evals", "rag_golden_qa.jsonl"), truth.jsonl([
        {"id": f"QA-{i:02d}", "question": q, "expected_answer": a,
         "sources": [{"document": d, "section": s} for d, s in src]} for i, (q, a, src) in enumerate(truth.RAG_QA, 1)]))
    write(p("evals", "guardrail_injection_cases.jsonl"), truth.jsonl([
        {"id": f"INJ-{i:02d}", "text": t, "is_manipulation_attempt": inj, "expected_behavior": b} for i, (t, inj, b) in enumerate(truth.INJECTION_CASES, 1)]))
    write(p("evals", "pii_masking_cases.jsonl"), truth.jsonl([
        {"id": f"PII-{i:02d}", "input": a, "expected_output": b, "pii_types": t} for i, (a, b, t) in enumerate(truth.PII_CASES, 1)]))
    write(p("schemas", "claim_intake_result.schema.json"), json.dumps(truth.SCHEMA, indent=2, ensure_ascii=False))

    # ---------------------------------------------------------- docs
    print("readme...")
    write(p("README.md"), docs_md.readme(truth_rows))
    write(p("DATA_DICTIONARY.md"), docs_md.data_dictionary())
    write(p("ground_truth", "SCENARIOS.md"), docs_md.scenarios(truth_rows))
    gen_dir = os.path.dirname(os.path.abspath(__file__))
    for fn in ("data.py", "claims.py", "kb_text.py", "pdfkit.py", "photos.py", "docimg.py", "truth.py", "docs_md.py", "build.py"):
        shutil.copyfile(os.path.join(gen_dir, fn), p("tools", "generator", fn))
    write(p("tools", "generator", "README.md"), docs_md.generator_readme())
    print("done ->", OUT)

if __name__ == "__main__":
    main()
