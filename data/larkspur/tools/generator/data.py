"""Single source of truth for the Larkspur Mutual claims-intake capstone dataset.

Everything in the generated dataset (policies, claim packages, ground truth)
is derived from the structures in this file so the answer key always matches
the documents.
"""

COMPANY = {
    "name": "Larkspur Mutual Insurance Company",
    "short": "Larkspur Mutual",
    "address": "400 Commerce Way, Millbrook, VA 23990",
    "claims_email": "newclaims@larkspur-mutual.example",
    "claims_phone": "1-800-555-0199",
    "siu_email": "siu-intake@larkspur-mutual.example",
    "disclaimer": "SYNTHETIC TRAINING DATA - Larkspur Mutual is a fictional company. Not a real policy or record.",
}

# Fictional towns placed in central Virginia (lat, lon, zip)
TOWNS = {
    "Millbrook": (37.6189, -77.4934, "23990"),
    "Ashford": (37.7012, -77.3895, "23991"),
    "Riverton": (37.5402, -77.4361, "23992"),
    "Brookhaven": (37.4836, -77.5922, "23993"),
}

AGENTS = {
    "DIRECT": {"name": "Larkspur Direct", "contact": "Customer Service", "phone": "1-800-555-0198", "email": "service@larkspur-mutual.example"},
    "FR": {"name": "Foster & Reyes Insurance Agency", "contact": "Linda Foster", "phone": "(804) 555-0170", "email": "linda.foster@example.org"},
}

# ---------------------------------------------------------------------------
# POLICIES
# ---------------------------------------------------------------------------
STD_AUTO_LIAB = {"bodily_injury": "100,000/300,000", "property_damage": 100000,
                 "medical_payments": 5000, "uninsured_motorist": "100,000/300,000",
                 "uninsured_motorist_pd_deductible": 200}

def auto(pn, insureds, addr, town, phone, email, eff, exp, incept, vehicles, coll, comp,
         endorsements=(), agent="DIRECT", status="ACTIVE", **extra):
    cov = dict(STD_AUTO_LIAB)
    cov["collision_deductible"] = coll
    cov["comprehensive_deductible"] = comp
    p = {
        "policy_number": pn, "line": "AUTO", "form": "LM-PA-01 (06/25)", "status": status,
        "named_insureds": list(insureds), "mailing_address": f"{addr}, {town}, VA {TOWNS[town][2]}",
        "phone": phone, "email": email, "term_effective": eff, "term_expiration": exp,
        "original_inception": incept, "vehicles": vehicles, "coverages": cov,
        "endorsements": list(endorsements), "agent": agent,
        "cancellation": None, "payment_history": [], "change_history": [], "lienholders": [],
    }
    p.update(extra)
    return p

def veh(no, year, make, model, vin, town, plate):
    return {"veh_no": no, "year": year, "make": make, "model": model, "vin": vin,
            "garaging_zip": TOWNS[town][2], "plate": plate}

def home(pn, insureds, addr, town, phone, email, eff, exp, incept, a, ded, wind,
         endorsements=(), agent="DIRECT", dwelling=None, c=None, **extra):
    p = {
        "policy_number": pn, "line": "HOME", "form": "LM-HO-03 (06/25)", "status": "ACTIVE",
        "named_insureds": list(insureds), "property_address": f"{addr}, {town}, VA {TOWNS[town][2]}",
        "mailing_address": f"{addr}, {town}, VA {TOWNS[town][2]}",
        "phone": phone, "email": email, "term_effective": eff, "term_expiration": exp,
        "original_inception": incept,
        "dwelling": dwelling or {},
        "coverages": {"A_dwelling": a, "B_other_structures": round(a * 0.10),
                      "C_personal_property": c if c is not None else round(a * 0.50),
                      "D_loss_of_use": round(a * 0.20), "E_personal_liability": 300000,
                      "F_medical_payments": 5000},
        "deductibles": {"all_peril": ded, "wind_hail": wind},
        "endorsements": list(endorsements), "scheduled_items": [], "agent": agent,
        "cancellation": None, "payment_history": [], "change_history": [], "mortgagee": None,
    }
    p.update(extra)
    return p

FG = {"code": "LM-PA-FG", "name": "Full Glass Coverage"}
RR = {"code": "LM-PA-RR", "name": "Rental Reimbursement", "limit": "$40/day, $1,200 max"}
WB10 = {"code": "LM-HO-WB", "name": "Water Backup and Sump Discharge", "limit": 10000}
RCC = {"code": "LM-HO-RCC", "name": "Replacement Cost - Personal Property"}
SPP = {"code": "LM-HO-SPP", "name": "Scheduled Personal Property"}

POLICIES = [
    auto("LM-PA-2025-104233", ["Priya Raman"], "2207 Willow Bend Ct", "Ashford", "(804) 555-0112",
         "priya.raman@example.com", "2026-08-01", "2027-02-01", "2025-02-01",
         [veh(1, 2021, "Honda", "CR-V EX", "7FARW2H83ME014472", "Ashford", "VA UKP-2207")], 500, 250, [FG, RR]),
    auto("LM-PA-2024-088190", ["Marcus Bell"], "58 Carriage Hill Rd", "Millbrook", "(804) 555-0123",
         "mbell.home@example.net", "2026-07-10", "2027-01-10", "2024-07-10",
         [veh(1, 2019, "Toyota", "Camry SE", "4T1B11HK5KU238810", "Millbrook", "VA TBR-5814")], 500, 500, [RR]),
    auto("LM-PA-2023-071552", ["Elena Sokolova"], "911 Harbor View Dr", "Riverton", "(804) 555-0134",
         "elena.sokolova@example.com", "2026-09-05", "2027-03-05", "2023-03-05",
         [veh(1, 2022, "Subaru", "Outback Premium", "4S4BTACC2N3157726", "Riverton", "VA TXR-2290")], 500, 500, [RR]),
    auto("LM-PA-2025-112907", ["David Okafor", "Angela Okafor"], "4410 Stonegate Pl", "Millbrook", "(804) 555-0145",
         "d.okafor@example.com", "2026-05-20", "2026-11-20", "2025-05-20",
         [veh(1, 2020, "Toyota", "Highlander XLE", "5TDGZRBH8LS052291", "Millbrook", "VA KDO-4410")], 500, 500, [RR]),
    auto("LM-PA-2022-064410", ["Robert Chen"], "77 Laurel Ridge Way", "Ashford", "(804) 555-0156",
         "rchen77@example.net", "2026-06-01", "2026-12-01", "2022-06-01",
         [veh(1, 2014, "Honda", "Civic LX", "19XFB2F58EE063118", "Ashford", "VA RCX-7714")], 1000, 500, [],
         lienholders=[{"name": "Ashford Community Credit Union", "vehicle": 1}]),
    auto("LM-PA-2025-099318", ["Tasha Greene"], "1300 Parkside Ave Apt 4B", "Riverton", "(804) 555-0167",
         "tasha.greene@example.com", "2026-08-15", "2027-02-15", "2025-02-15",
         [veh(1, 2020, "Hyundai", "Elantra SEL", "5NPD84LF4LH512970", "Riverton", "VA LMN-8820")], 500, 500, [RR]),
    auto("LM-PA-2025-120044", ["Kevin Doyle"], "3 Quarry Rd", "Brookhaven", "(804) 555-0178",
         "kdoyle.va@example.com", "2026-07-01", "2027-01-01", "2025-07-01",
         [veh(1, 2017, "Chevrolet", "Malibu LT", "1G1ZE5ST3HF190452", "Brookhaven", "VA KDV-3301")], 500, 500, [],
         status="CANCELLED",
         cancellation={"effective": "2026-09-14 12:01 AM", "reason": "Nonpayment of premium",
                       "notice_mailed": "2026-09-01", "reinstated": False},
         payment_history=[
             {"date": "2026-07-01", "amount": 412.50, "status": "PAID", "note": "Installment 1 of 6"},
             {"date": "2026-08-01", "amount": 412.50, "status": "MISSED", "note": "Installment 2 due; not received"},
             {"date": "2026-09-01", "amount": None, "status": "NOTICE", "note": "Cancellation notice mailed; cancellation effective 2026-09-14 12:01 AM"},
             {"date": "2026-10-01", "amount": 412.50, "status": "RECEIVED_AFTER_CANCELLATION",
              "note": "Online payment received after cancellation date; not accepted for reinstatement; refund issued 2026-10-06"},
         ]),
    auto("LM-PA-2024-093371", ["Sandra Whitfield"], "18 Fox Hollow Rd", "Ashford", "(804) 555-0189",
         "swhitfield@example.org", "2026-10-10", "2027-04-10", "2024-10-10",
         [veh(1, 2011, "Ford", "Ranger XLT", "1FTKR1ED5BPA81920", "Ashford", "VA SWF-1811")], None, None, []),
    auto("LM-PA-2025-117760", ["Jamal Carter"], "620 Elm St Apt 12", "Millbrook", "(804) 555-0191",
         "jcarter.mb@example.com", "2026-06-25", "2026-12-25", "2025-06-25",
         [veh(1, 2018, "Nissan", "Altima 2.5 S", "1N4BL4BV6JC201145", "Millbrook", "VA JMC-6201")], 500, 500, [],
         agent="FR"),
    auto("LM-PA-2026-130512", ["Brandon Mills"], "245 Old Mill Rd", "Ashford", "(804) 555-0102",
         "bmills.auto@example.net", "2026-10-02", "2027-04-02", "2026-10-02",
         [veh(1, 2019, "Ford", "Fusion SE", "3FA6P0HD7KR170336", "Ashford", "VA BMF-2450")], 500, 500, [RR],
         change_history=[{"date": "2026-10-02", "change": "New business - policy issued online"}]),
    auto("LM-PA-2024-085526", ["Lisa Moreno"], "1522 Commons Blvd", "Riverton", "(804) 555-0113",
         "lisa.moreno@example.com", "2026-09-18", "2027-03-18", "2024-03-18",
         [veh(1, 2021, "Mazda", "CX-5 Touring", "JM3KFBCM1M0431087", "Riverton", "VA LMR-1522")], 500, 500, []),
    auto("LM-PA-2023-077804", ["Gregory Hall"], "9 Brookside Ln", "Brookhaven", "(804) 555-0124",
         "greg.hall@example.org", "2026-07-22", "2027-01-22", "2023-01-22",
         [veh(1, 2023, "Toyota", "RAV4 XLE", "2T3P1RFV0PW384629", "Brookhaven", "VA GHR-0904")], 500, 500, []),
    auto("LM-PA-2025-101876", ["Michael Brennan"], "87 Sawmill Rd", "Millbrook", "(804) 555-0147",
         "mike.brennan@example.com", "2026-08-03", "2027-02-03", "2025-08-03",
         [veh(1, 2018, "Ford", "F-150 XLT", "1FTEW1EP4JFB52618", "Millbrook", "VA MKB-8718"),
          veh(2, 2016, "Toyota", "Corolla LE", "2T1BURHE9GC605533", "Millbrook", "VA MKB-1633")], 500, 500, []),
    auto("LM-PA-2024-090017", ["Grace Liu"], "3301 Market St Apt 7C", "Millbrook", "(804) 555-0135",
         "grace.liu@example.net", "2026-09-01", "2027-03-01", "2024-09-01",
         [veh(1, 2022, "Kia", "Forte LXS", "3KPF24AD7NE472210", "Millbrook", "VA GLF-3301")], 500, 250, []),
    auto("LM-PA-2025-108845", ["James Whitaker"], "140 Ridgeline Dr", "Brookhaven", "(804) 555-0146",
         "jwhitaker@example.com", "2026-05-12", "2026-11-12", "2025-05-12",
         [veh(1, 2023, "Honda", "Accord EX", "1HGCY1F36PA011752", "Brookhaven", "VA JWA-1402")], 500, 500, [RR]),

    home("LM-HO-2024-210334", ["Nathan Park", "Julie Park"], "52 Juniper Ct", "Millbrook", "(804) 555-0157",
         "nathan.park@example.com", "2026-04-01", "2027-04-01", "2024-04-01", 380000, 1000,
         {"type": "percent_of_A", "percent": 1, "amount": 3800}, [WB10, RCC],
         dwelling={"year_built": 2008, "construction": "Frame", "roof": "Asphalt shingle", "roof_year": 2019, "sq_ft": 2350}),
    home("LM-HO-2023-198871", ["Carmen Delgado"], "16 Millers Creek Rd", "Brookhaven", "(804) 555-0168",
         "carmen.delgado@example.org", "2026-03-15", "2027-03-15", "2023-03-15", 310000, 1000,
         {"type": "same_as_all_peril", "amount": 1000}, [WB10],
         dwelling={"year_built": 1996, "construction": "Frame", "roof": "Asphalt shingle", "roof_year": 2015, "sq_ft": 2780,
                   "notes": "Finished basement; property backs onto Millers Creek"}),
    home("LM-HO-2025-224410", ["Thomas Wright"], "702 Cobblestone Way", "Riverton", "(804) 555-0179",
         "t.wright@example.net", "2026-02-10", "2027-02-10", "2025-02-10", 295000, 1000,
         {"type": "same_as_all_peril", "amount": 1000}, [],
         dwelling={"year_built": 1988, "construction": "Brick veneer", "roof": "Asphalt shingle", "roof_year": 2012, "sq_ft": 2100}),
    home("LM-HO-2022-187655", ["Linh Nguyen", "Bao Nguyen"], "1180 Sycamore Dr", "Millbrook", "(804) 555-0180",
         "linh.nguyen@example.com", "2026-06-01", "2027-06-01", "2022-06-01", 420000, 1000,
         {"type": "percent_of_A", "percent": 1, "amount": 4200}, [RCC],
         dwelling={"year_built": 2004, "construction": "Frame", "roof": "Architectural shingle", "roof_year": 2018, "sq_ft": 2400},
         mortgagee="Riverton Community Bank, ISAOA"),
    home("LM-HO-2024-205519", ["Harold Simmons", "Betty Simmons"], "33 Orchard Hill Rd", "Ashford", "(804) 555-0190",
         "harold.simmons@example.net", "2026-01-15", "2027-01-15", "2024-01-15", 350000, 1000,
         {"type": "percent_of_A", "percent": 2, "amount": 7000}, [],
         dwelling={"year_built": 1979, "construction": "Frame", "roof": "Asphalt shingle", "roof_year": 2006, "sq_ft": 1950}),
    home("LM-HO-2023-201147", ["Aisha Thompson"], "2416 Lakeview Ter", "Riverton", "(804) 555-0101",
         "aisha.thompson@example.com", "2026-05-05", "2027-05-05", "2023-05-05", 265000, 1000,
         {"type": "same_as_all_peril", "amount": 1000}, [SPP],
         dwelling={"year_built": 2001, "construction": "Frame", "roof": "Asphalt shingle", "roof_year": 2017, "sq_ft": 1680},
         scheduled_items=[{"item": "Engagement ring - platinum solitaire, 1.52 ct round brilliant diamond",
                           "class": "Jewelry", "agreed_value": 4000, "appraisal_date": "2023-02-14"}]),
    home("LM-HO-2024-209902", ["Derek Vaughn"], "905 Granite Ln", "Millbrook", "(804) 555-0114",
         "derek.vaughn@example.net", "2026-03-01", "2027-03-01", "2024-03-01", 240000, 1000,
         {"type": "same_as_all_peril", "amount": 1000}, [], c=175000,
         dwelling={"year_built": 1992, "construction": "Frame", "roof": "Asphalt shingle", "roof_year": 2016, "sq_ft": 1540},
         change_history=[{"date": "2026-10-04", "change": "Coverage C (personal property) increased from $100,000 to $175,000 - online self-service request"}]),
    home("LM-HO-2025-218863", ["Patricia O'Neill", "Samuel O'Neill"], "61 Hawthorn Rd", "Ashford", "(804) 555-0125",
         "pat.oneill@example.org", "2026-07-01", "2027-07-01", "2025-07-01", 280000, 1000,
         {"type": "percent_of_A", "percent": 1, "amount": 2800}, [],
         dwelling={"year_built": 1999, "construction": "Frame", "roof": "Asphalt shingle", "roof_year": 2014, "sq_ft": 2050,
                   "notes": "Detached two-car garage"}),
    home("LM-HO-2021-176540", ["Michael J. Brennan"], "12 Ferry Landing Rd", "Riverton", "(804) 555-0136",
         "mjbrennan.riverton@example.org", "2026-09-20", "2027-09-20", "2021-09-20", 330000, 1000,
         {"type": "percent_of_A", "percent": 1, "amount": 3300}, [],
         dwelling={"year_built": 2010, "construction": "Frame", "roof": "Asphalt shingle", "roof_year": 2010, "sq_ft": 2600}),
]

POLICY_BY_NUMBER = {p["policy_number"]: p for p in POLICIES}

# ---------------------------------------------------------------------------
# VEHICLE VALUES (mock valuation service)
# ---------------------------------------------------------------------------
VEHICLE_VALUES = {
    "7FARW2H83ME014472": (38200, "Good", 24800),
    "4T1B11HK5KU238810": (61400, "Good", 17900),
    "4S4BTACC2N3157726": (29800, "Excellent", 27300),
    "5TDGZRBH8LS052291": (52300, "Good", 27500),
    "19XFB2F58EE063118": (128900, "Fair", 9800),
    "5NPD84LF4LH512970": (47100, "Good", 15400),
    "1G1ZE5ST3HF190452": (88200, "Good", 12100),
    "1FTKR1ED5BPA81920": (164300, "Fair", 8600),
    "1N4BL4BV6JC201145": (79500, "Good", 13700),
    "3FA6P0HD7KR170336": (71200, "Good", 14200),
    "JM3KFBCM1M0431087": (33600, "Excellent", 22600),
    "2T3P1RFV0PW384629": (18900, "Excellent", 29900),
    "1FTEW1EP4JFB52618": (84700, "Good", 24300),
    "2T1BURHE9GC605533": (102300, "Good", 10900),
    "3KPF24AD7NE472210": (26400, "Excellent", 16200),
    "1HGCY1F36PA011752": (21800, "Excellent", 26400),
}

# ---------------------------------------------------------------------------
# VENDORS
# ---------------------------------------------------------------------------
VENDORS = [
    {"vendor_id": "V001", "name": "Millbrook Collision Center", "type": "Auto body", "address": "1880 Industrial Blvd, Millbrook, VA 23990",
     "phone": "(804) 555-0161", "drp": True, "siu_watchlist": False, "lat": 37.6102, "lon": -77.5011, "watchlist_note": ""},
    {"vendor_id": "V002", "name": "Riverton Auto Body", "type": "Auto body", "address": "455 Canal St, Riverton, VA 23992",
     "phone": "(804) 555-0162", "drp": True, "siu_watchlist": False, "lat": 37.5381, "lon": -77.4402, "watchlist_note": ""},
    {"vendor_id": "V003", "name": "Ashford Auto Glass", "type": "Auto glass", "address": "92 Station Rd, Ashford, VA 23991",
     "phone": "(804) 555-0163", "drp": True, "siu_watchlist": False, "lat": 37.6988, "lon": -77.3851, "watchlist_note": ""},
    {"vendor_id": "V004", "name": "QuickFix Auto Body & Paint", "type": "Auto body", "address": "3120 Turnpike Rd, Ashford, VA 23991",
     "phone": "(804) 555-0164", "drp": False, "siu_watchlist": True, "lat": 37.7244, "lon": -77.3530,
     "watchlist_note": "Added 2025-11: pattern of estimates priced well above regional benchmarks; two prior SIU referrals."},
    {"vendor_id": "V005", "name": "Brookhaven Body Works", "type": "Auto body", "address": "77 Mill Race Rd, Brookhaven, VA 23993",
     "phone": "(804) 555-0165", "drp": True, "siu_watchlist": False, "lat": 37.4859, "lon": -77.5874, "watchlist_note": ""},
    {"vendor_id": "V006", "name": "Cedar Lane Restoration", "type": "Water mitigation & restoration", "address": "210 Cedar Ln, Millbrook, VA 23990",
     "phone": "(804) 555-0172", "drp": True, "siu_watchlist": False, "lat": 37.6231, "lon": -77.4876, "watchlist_note": ""},
    {"vendor_id": "V007", "name": "Hometown Plumbing Co.", "type": "Plumbing", "address": "18 Front St, Riverton, VA 23992",
     "phone": "(804) 555-0173", "drp": False, "siu_watchlist": False, "lat": 37.5420, "lon": -77.4337, "watchlist_note": ""},
    {"vendor_id": "V008", "name": "Riverton Builders", "type": "General contractor", "address": "640 Mill St, Riverton, VA 23992",
     "phone": "(804) 555-0174", "drp": True, "siu_watchlist": False, "lat": 37.5446, "lon": -77.4389, "watchlist_note": ""},
    {"vendor_id": "V009", "name": "Oakridge Fire & Water Restoration", "type": "Fire & water restoration", "address": "1500 Oakridge Pkwy, Millbrook, VA 23990",
     "phone": "(804) 555-0175", "drp": True, "siu_watchlist": False, "lat": 37.6290, "lon": -77.5102, "watchlist_note": ""},
    {"vendor_id": "V010", "name": "Summit Peak Roofing", "type": "Roofing", "address": "802 Ridge Rd, Ashford, VA 23991",
     "phone": "(804) 555-0176", "drp": True, "siu_watchlist": False, "lat": 37.7090, "lon": -77.3922, "watchlist_note": ""},
    {"vendor_id": "V011", "name": "Ashford Tree Service", "type": "Tree removal", "address": "15 Timber Ln, Ashford, VA 23991",
     "phone": "(804) 555-0177", "drp": False, "siu_watchlist": False, "lat": 37.6955, "lon": -77.3990, "watchlist_note": ""},
]
VENDOR_BY_NAME = {v["name"]: v for v in VENDORS}

# ---------------------------------------------------------------------------
# REPAIR BENCHMARKS (region: Central VA, 2026). code -> (category, item, unit, low, high)
# ---------------------------------------------------------------------------
BENCHMARKS = {
    # auto labor rates
    "LAB-BODY": ("Auto labor", "Body labor rate", "per hour", 54, 62),
    "LAB-REFINISH": ("Auto labor", "Refinish (paint) labor rate", "per hour", 54, 62),
    "LAB-FRAME": ("Auto labor", "Frame labor rate", "per hour", 68, 80),
    "LAB-MECH": ("Auto labor", "Mechanical labor rate", "per hour", 105, 125),
    "MAT-PAINT": ("Auto materials", "Paint & materials", "per refinish hour", 36, 42),
    "SHOP-WASTE": ("Auto materials", "Hazardous waste / shop supplies", "flat", 15, 60),
    # auto parts
    "P-FBUMPER": ("Auto parts", "Front bumper cover", "each", 380, 520),
    "P-RBUMPER": ("Auto parts", "Rear bumper cover", "each", 360, 500),
    "P-REINF": ("Auto parts", "Bumper reinforcement bar", "each", 220, 340),
    "P-ABSORB": ("Auto parts", "Bumper energy absorber", "each", 70, 130),
    "P-HEAD-HAL": ("Auto parts", "Headlamp assembly - halogen", "each", 250, 420),
    "P-HEAD-LED": ("Auto parts", "Headlamp assembly - LED", "each", 650, 1100),
    "P-TAIL": ("Auto parts", "Tail lamp assembly", "each", 160, 300),
    "P-HOOD": ("Auto parts", "Hood panel", "each", 450, 650),
    "P-FENDER": ("Auto parts", "Front fender", "each", 230, 380),
    "P-LINER": ("Auto parts", "Fender liner", "each", 50, 110),
    "P-GRILLE": ("Auto parts", "Grille assembly", "each", 180, 320),
    "P-RADSUP": ("Auto parts", "Radiator support", "each", 380, 560),
    "P-RADIATOR": ("Auto parts", "Radiator", "each", 260, 420),
    "P-CONDENSER": ("Auto parts", "A/C condenser", "each", 290, 460),
    "P-FDOOR": ("Auto parts", "Front door shell", "each", 650, 950),
    "P-RDOOR": ("Auto parts", "Rear door shell", "each", 620, 900),
    "P-DOORGLASS": ("Auto parts", "Door glass (front or rear)", "each", 180, 340),
    "P-MIRROR": ("Auto parts", "Side mirror assembly", "each", 260, 480),
    "P-MOLDING": ("Auto parts", "Door body side molding", "each", 60, 120),
    "P-SENSOR": ("Auto parts", "Parking sensor", "each", 120, 220),
    "P-WINDSHIELD": ("Auto parts", "Windshield (with sensor/camera bracket)", "each", 320, 420),
    "P-GLASSKIT": ("Auto parts", "Urethane & molding kit", "each", 20, 45),
    "P-CLIPS": ("Auto parts", "Trim clip kit", "each", 10, 30),
    "P-SUNROOF": ("Auto parts", "Sunroof glass", "each", 900, 1400),
    "P-SUNSEAL": ("Auto parts", "Sunroof seal kit", "each", 40, 90),
    "P-AIRBAG-DRV": ("Auto parts", "Driver front airbag", "each", 650, 950),
    "P-AIRBAG-PASS": ("Auto parts", "Passenger front airbag", "each", 750, 1100),
    "P-AIRBAG-CURT": ("Auto parts", "Side curtain airbag", "each", 900, 1400),
    "P-PRETENS": ("Auto parts", "Seat belt pretensioner", "each", 280, 420),
    "P-ACM": ("Auto parts", "Airbag control module", "each", 350, 600),
    "P-WHEEL": ("Auto parts", "Alloy wheel", "each", 280, 450),
    "P-TIRE": ("Auto parts", "Tire", "each", 160, 240),
    "P-CTRLARM": ("Auto parts", "Lower control arm", "each", 180, 340),
    # auto sublet
    "S-ADAS": ("Auto sublet", "ADAS camera/radar calibration", "each", 180, 260),
    "S-ALIGN": ("Auto sublet", "Wheel alignment", "each", 100, 160),
    "S-SCAN": ("Auto sublet", "Pre/post repair diagnostic scan", "each", 100, 180),
    "S-TOW": ("Auto sublet", "Towing", "each", 125, 250),
    "S-STORAGE": ("Auto sublet", "Vehicle storage", "per day", 40, 65),
    "S-GLASSVAC": ("Auto sublet", "Glass cleanup / vacuum", "each", 30, 60),
    # hail PDR
    "PDR-ROOF-HVY": ("Hail PDR", "PDR roof panel - heavy", "each", 1100, 1700),
    "PDR-HOOD-MOD": ("Hail PDR", "PDR hood - moderate", "each", 450, 800),
    "PDR-FENDER": ("Hail PDR", "PDR fender", "each", 180, 320),
    "PDR-DOOR": ("Hail PDR", "PDR door", "each", 200, 350),
    "PDR-LIFTGATE": ("Hail PDR", "PDR liftgate/trunk lid", "each", 300, 480),
    "PDR-QUARTER": ("Hail PDR", "PDR quarter panel", "each", 250, 420),
    # home
    "H-EXTRACT-HARD": ("Home mitigation", "Water extraction - hard surface", "per sq ft", 0.75, 1.25),
    "H-EXTRACT-CARPET": ("Home mitigation", "Water extraction - carpet", "per sq ft", 0.90, 1.40),
    "H-DRYING": ("Home mitigation", "Drying equipment set", "per day", 450, 700),
    "H-ANTIMICROBIAL": ("Home mitigation", "Antimicrobial application", "per sq ft", 0.35, 0.60),
    "H-MOLD": ("Home mitigation", "Mold remediation", "per sq ft", 18, 30),
    "H-BASECAB": ("Home rebuild", "Base cabinets - remove & replace", "per LF", 280, 420),
    "H-WALLCAB": ("Home rebuild", "Wall cabinets - remove & replace", "per LF", 240, 380),
    "H-COUNTER-RESET": ("Home rebuild", "Countertop detach & reset", "per LF", 45, 75),
    "H-COUNTER-GRANITE": ("Home rebuild", "Granite countertop", "per sq ft", 55, 85),
    "H-LVP": ("Home rebuild", "LVP flooring installed", "per sq ft", 6.00, 8.50),
    "H-CARPET": ("Home rebuild", "Carpet & pad installed", "per sq ft", 4.00, 6.50),
    "H-CARPET-REMOVE": ("Home rebuild", "Carpet & pad removal", "per sq ft", 0.60, 1.10),
    "H-TILE": ("Home rebuild", "Tile floor remove & replace", "per sq ft", 12, 18),
    "H-SUBFLOOR": ("Home rebuild", "Subfloor replace", "per sq ft", 6.50, 9.00),
    "H-JOIST": ("Home rebuild", "Sister floor joist", "each", 220, 340),
    "H-DRYWALL": ("Home rebuild", "Drywall remove & replace", "per sq ft", 3.80, 5.50),
    "H-FLOODCUT": ("Home rebuild", "Drywall flood cut (2 ft)", "per LF", 18, 28),
    "H-INSUL": ("Home rebuild", "Insulation replace", "per sq ft", 1.50, 2.50),
    "H-PAINT": ("Home rebuild", "Interior paint", "per sq ft", 1.20, 1.90),
    "H-BASEBOARD": ("Home rebuild", "Baseboard", "per LF", 4.50, 7.00),
    "H-TOILET": ("Home rebuild", "Toilet detach & reset", "each", 180, 260),
    "H-VANITY": ("Home rebuild", "Bathroom vanity remove & replace", "each", 900, 1500),
    "H-WATERHEATER": ("Home rebuild", "Water heater replace (50 gal)", "each", 1400, 2000),
    "H-DEBRIS": ("Home rebuild", "Debris haul / dumpster", "each", 450, 750),
    "H-PLUMB-SUPPLY": ("Home plumbing", "Supply line replace (service call)", "each", 140, 240),
    "H-PLUMB-WAXRING": ("Home plumbing", "Toilet pull & wax ring replace", "each", 180, 280),
    "H-PLUMB-FLANGE": ("Home plumbing", "Closet flange replace", "each", 110, 190),
    "H-BOARDUP": ("Home fire", "Emergency board-up & tarp", "each", 350, 600),
    "H-PACKOUT": ("Home fire", "Content pack-out & storage", "each", 2000, 4000),
    "H-SMOKECLEAN": ("Home fire", "Smoke cleaning walls/ceilings", "per sq ft", 0.90, 1.60),
    "H-DEMO": ("Home fire", "Kitchen demolition & debris", "each", 1200, 2200),
    "H-RANGEHOOD": ("Home fire", "Range hood replace", "each", 400, 900),
    "H-ELECTRIC": ("Home fire", "Kitchen electrical circuits & fixtures", "each", 1800, 3200),
    "H-DUCTCLEAN": ("Home fire", "HVAC duct cleaning", "each", 450, 900),
    "H-DEODOR": ("Home fire", "Deodorization / thermal fogging", "each", 350, 700),
    "H-PERMIT-SUP": ("Home rebuild", "Permit & supervision", "each", 800, 1600),
    "H-PERMIT": ("Home rebuild", "Building permit (minor)", "each", 100, 250),
    "R-SHINGLE": ("Roofing", "Tear off & replace shingles", "per square", 450, 620),
    "R-UNDERLAY": ("Roofing", "Synthetic underlayment", "per square", 35, 60),
    "R-DRIPEDGE": ("Roofing", "Drip edge", "per LF", 3.50, 5.50),
    "R-RIDGE": ("Roofing", "Ridge cap", "per LF", 9, 14),
    "R-PIPEBOOT": ("Roofing", "Pipe boot", "each", 45, 90),
    "R-FRAMING": ("Structural", "Roof framing repair", "per sq ft", 9, 14),
    "R-SHEATHING": ("Structural", "Roof sheathing replace", "per sq ft", 2.50, 3.80),
    "R-GUTTER": ("Exterior", "Gutter replace", "per LF", 8, 13),
    "R-SIDING": ("Exterior", "Siding section repair", "each", 450, 900),
    "T-REMOVAL": ("Tree", "Tree removal from structure", "per tree", 600, 1500),
}

def L(desc, code, qty, unit_price, unit=""):
    return {"description": desc, "benchmark_code": code, "qty": qty, "unit_price": unit_price, "unit": unit}

# ---------------------------------------------------------------------------
# PRIOR CLAIMS (claims system)
# ---------------------------------------------------------------------------
PRIOR_CLAIMS = [
    {"claim_number": "LM-CL-2023-002210", "policy_number": "LM-PA-2022-064410", "insured": "Robert Chen", "line": "AUTO",
     "date_of_loss": "2023-04-18", "reported_date": "2023-04-18", "loss_cause": "collision",
     "description": "Rear-ended another vehicle in stop-and-go traffic on Route 33", "status": "CLOSED", "paid_amount": 2400,
     "adjuster": "M. Grant", "reported_by": "Insured (phone)", "asset": "2014 Honda Civic"},
    {"claim_number": "LM-CL-2024-002876", "policy_number": "LM-PA-2023-077804", "insured": "Gregory Hall", "line": "AUTO",
     "date_of_loss": "2024-05-02", "reported_date": "2024-05-03", "loss_cause": "glass",
     "description": "Windshield crack from road debris", "status": "CLOSED", "paid_amount": 610,
     "adjuster": "Fast-track desk", "reported_by": "Insured (web)", "asset": "2023 Toyota RAV4"},
    {"claim_number": "LM-CL-2024-001290", "policy_number": "LM-HO-2024-209902", "insured": "Derek Vaughn", "line": "HOME",
     "date_of_loss": "2024-03-12", "reported_date": "2024-03-13", "loss_cause": "theft",
     "description": "Bicycle and power tools stolen from detached shed", "status": "CLOSED", "paid_amount": 2100,
     "adjuster": "S. Patel", "reported_by": "Insured (email)", "asset": "905 Granite Ln"},
    {"claim_number": "LM-CL-2025-000318", "policy_number": "LM-HO-2024-209902", "insured": "Derek Vaughn", "line": "HOME",
     "date_of_loss": "2025-01-27", "reported_date": "2025-01-28", "loss_cause": "theft",
     "description": "Laptop and tablet stolen from vehicle parked in driveway", "status": "CLOSED", "paid_amount": 1600,
     "adjuster": "S. Patel", "reported_by": "Insured (email)", "asset": "905 Granite Ln"},
    {"claim_number": "LM-CL-2025-003655", "policy_number": "LM-HO-2024-209902", "insured": "Derek Vaughn", "line": "HOME",
     "date_of_loss": "2025-09-08", "reported_date": "2025-09-09", "loss_cause": "burglary",
     "description": "Rear door forced; television, game console and speakers taken", "status": "CLOSED", "paid_amount": 3900,
     "adjuster": "T. Okoro", "reported_by": "Insured (email)", "asset": "905 Granite Ln"},
    {"claim_number": "LM-CL-2024-003012", "policy_number": "LM-HO-2023-198871", "insured": "Carmen Delgado", "line": "HOME",
     "date_of_loss": "2024-08-19", "reported_date": "2024-08-19", "loss_cause": "water_backup",
     "description": "Sump pump failed during power outage; water backed up into basement (paid under LM-HO-WB)", "status": "CLOSED",
     "paid_amount": 3450, "adjuster": "Fast-track desk", "reported_by": "Insured (phone)", "asset": "16 Millers Creek Rd"},
    {"claim_number": "LM-CL-2026-004417", "policy_number": "LM-PA-2024-085526", "insured": "Lisa Moreno", "line": "AUTO",
     "date_of_loss": "2026-10-20", "reported_date": "2026-10-21", "loss_cause": "collision",
     "description": "Parked vehicle sideswiped by unknown driver at Riverton Commons (hit-and-run); police report RPD-26-120115",
     "status": "OPEN", "paid_amount": 0, "adjuster": "R. Alvarez", "reported_by": "Insured (phone)", "asset": "2021 Mazda CX-5"},
    {"claim_number": "LM-CL-2025-002230", "policy_number": "LM-PA-2025-108845", "insured": "James Whitaker", "line": "AUTO",
     "date_of_loss": "2025-11-14", "reported_date": "2025-11-14", "loss_cause": "collision",
     "description": "Low-speed backing collision in parking lot", "status": "CLOSED", "paid_amount": 1180,
     "adjuster": "Fast-track desk", "reported_by": "Insured (web)", "asset": "2023 Honda Accord"},
    {"claim_number": "LM-CL-2022-001845", "policy_number": "LM-HO-2021-176540", "insured": "Michael J. Brennan", "line": "HOME",
     "date_of_loss": "2022-04-07", "reported_date": "2022-04-08", "loss_cause": "wind",
     "description": "Wind damage to siding and gutters", "status": "CLOSED", "paid_amount": 2950,
     "adjuster": "M. Grant", "reported_by": "Insured (phone)", "asset": "12 Ferry Landing Rd"},
]
