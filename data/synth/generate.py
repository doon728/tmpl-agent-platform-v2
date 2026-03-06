#!/usr/bin/env python3
import csv
import json
import os
import random
from datetime import date, datetime, timedelta

try:
    import yaml  # pip install pyyaml
except ImportError:
    raise SystemExit("Missing dependency: pyyaml. Install with: pip install pyyaml")


# ---------- helpers ----------
def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def id_fmt(prefix: str, n: int, width: int) -> str:
    return f"{prefix}-{str(n).zfill(width)}"

def rand_date(start: date, end: date) -> date:
    # inclusive start, inclusive end
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))

def rand_phone() -> str:
    return f"{random.randint(200,999)}-{random.randint(200,999)}-{random.randint(1000,9999)}"

def rand_zip() -> str:
    return str(random.randint(10000, 99999))

def pick_weighted(items, weights):
    return random.choices(items, weights=weights, k=1)[0]

def write_csv(path: str, fieldnames: list[str], rows: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)

def write_jsonl(path: str, rows: list[dict]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def iso_dt(d: date) -> str:
    return d.isoformat()

def iso_ts(d: date) -> str:
    # simple timestamp at noon for readability
    return datetime(d.year, d.month, d.day, 12, 0, 0).isoformat() + "Z"


# ---------- synthetic vocab ----------
FIRST = ["Ava","Olivia","Emma","Noah","Liam","Mason","Sophia","Mia","Amelia","Ethan","Lucas","Isabella","Elijah","James","Harper"]
LAST = ["Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis","Rodriguez","Martinez","Hernandez","Lopez","Gonzalez","Wilson","Anderson"]
GENDER = ["M","F","X"]

# ICD-like codes (fake-ish but realistic looking)
ICD_POOL = ["E11.9","I10","J45.909","F41.1","E78.5","M54.5","K21.9","N18.3","I50.9","F32.9","G47.33","E66.9"]
PROC_POOL = ["99213","99214","93000","80053","83036","36415","71046","72148","J3490","A0425","G0477","D0120"]


def load_cfg(cfg_path: str) -> dict:
    with open(cfg_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main() -> None:
    repo_root = os.getcwd()
    cfg_path = os.path.join(repo_root, "data", "synth", "config", "generate.yaml")
    cfg = load_cfg(cfg_path)

    seed = int(cfg.get("seed", 42))
    random.seed(seed)

    counts = cfg["counts"]
    ucounts = cfg["unstructured_counts"]

    states = cfg["states"]
    programs = cfg["programs"]
    specialties = cfg["specialties"]
    service_types = cfg["service_types"]
    claim_types = cfg["claim_types"]

    # output dirs
    base = os.path.join(repo_root, "data", "synth")
    structured_dir = os.path.join(base, "structured")
    unstructured_dir = os.path.join(base, "unstructured")
    ensure_dir(structured_dir)
    ensure_dir(unstructured_dir)

    # date ranges
    today = date.today()
    start_2y = today - timedelta(days=730)
    start_10y = today - timedelta(days=3650)

    # ---------- 1) providers ----------
    providers = []
    provider_ids = []
    for i in range(1, counts["providers"] + 1):
        pid = id_fmt("p", i, 6)
        provider_ids.append(pid)
        st = random.choice(states)
        providers.append({
            "provider_id": pid,
            "npi": str(random.randint(10**9, 10**10 - 1)).zfill(10),
            "provider_name": f"{random.choice(LAST)} Clinic",
            "specialty": random.choice(specialties),
            "state": st,
            "network_status": pick_weighted(["IN","OUT"], [0.85, 0.15]),
            "phone": rand_phone(),
        })
    write_csv(
        os.path.join(structured_dir, "providers.csv"),
        ["provider_id","npi","provider_name","specialty","state","network_status","phone"],
        providers
    )

    # ---------- 2) members ----------
    members = []
    member_ids = []
    # high utilizers distribution helper
    high_utilizer_set = set()

    for i in range(1, counts["members"] + 1):
        mid = id_fmt("m", i, 6)
        member_ids.append(mid)

        # DOB 18-85
        dob = rand_date(today - timedelta(days=85*365), today - timedelta(days=18*365))
        st = random.choice(states)
        plan_id = f"plan-medicaid-{st.lower()}"

        # chronic conditions: 0-3, skewed
        n_cc = pick_weighted([0,1,2,3], [0.45, 0.30, 0.18, 0.07])
        ccs = random.sample(ICD_POOL, k=n_cc) if n_cc > 0 else []
        risk = round(min(5.0, max(0.1, random.gauss(1.8 + 0.6*n_cc, 0.7))), 2)

        # mark some as high utilizers (5%)
        if random.random() < 0.05:
            high_utilizer_set.add(mid)

        members.append({
            "member_id": mid,
            "first_name": random.choice(FIRST),
            "last_name": random.choice(LAST),
            "dob": iso_dt(dob),
            "gender": random.choice(GENDER),
            "state": st,
            "plan_id": plan_id,
            "pcp_provider_id": random.choice(provider_ids),
            "risk_score": risk,
            "chronic_conditions": "|".join(ccs),
            "address_zip": rand_zip(),
        })

    write_csv(
        os.path.join(structured_dir, "members.csv"),
        ["member_id","first_name","last_name","dob","gender","state","plan_id","pcp_provider_id","risk_score","chronic_conditions","address_zip"],
        members
    )

    # ---------- 3) care plans ----------
    care_plans = []
    care_plan_ids = []
    # allow multiple care plans per member; choose member per plan
    for i in range(1, counts["care_plans"] + 1):
        cpid = id_fmt("cp", i, 6)
        care_plan_ids.append(cpid)
        mid = random.choice(member_ids)
        prog = random.choice(programs)
        sd = rand_date(start_2y, today - timedelta(days=7))
        status = pick_weighted(["ACTIVE","CLOSED"], [0.75, 0.25])
        goals = {
            "ComplexCare": "Reduce avoidable ED visits; improve care coordination.",
            "Diabetes": "Improve A1c control; medication adherence; diet counseling.",
            "Maternity": "Prenatal visit adherence; postpartum follow-up.",
            "BehavioralHealth": "Engage in therapy; stabilize symptoms; safety planning.",
            "Asthma": "Reduce exacerbations; inhaler technique; trigger avoidance.",
        }.get(prog, "Improve outcomes and engagement.")
        care_plans.append({
            "care_plan_id": cpid,
            "member_id": mid,
            "program": prog,
            "start_date": iso_dt(sd),
            "status": status,
            "goals": goals,
        })
    write_csv(
        os.path.join(structured_dir, "care_plans.csv"),
        ["care_plan_id","member_id","program","start_date","status","goals"],
        care_plans
    )

    # index care plans by member
    cps_by_member = {}
    for cp in care_plans:
        cps_by_member.setdefault(cp["member_id"], []).append(cp["care_plan_id"])

    # ---------- 4) assessment questions (question bank) ----------
    # fixed-ish bank to keep it stable across runs
    domains = ["Medical","Behavioral","SDOH","MedAdherence"]
    answer_types = ["YESNO","SCALE_1_5","TEXT"]

    questions = []
    qids = []
    templates = [
        ("Medical","YESNO","Any ER visits in the last 30 days?"),
        ("Medical","SCALE_1_5","How would you rate pain today (1-5)?"),
        ("Medical","TEXT","List current top health concerns."),
        ("Behavioral","YESNO","Any recent anxiety/panic symptoms?"),
        ("Behavioral","SCALE_1_5","Stress level this week (1-5)?"),
        ("Behavioral","TEXT","Any barriers to following the care plan?"),
        ("SDOH","YESNO","Any food insecurity concerns?"),
        ("SDOH","YESNO","Any transportation issues for appointments?"),
        ("SDOH","TEXT","Housing situation summary."),
        ("MedAdherence","YESNO","Missed any doses in the last week?"),
        ("MedAdherence","SCALE_1_5","Confidence in managing meds (1-5)?"),
        ("MedAdherence","TEXT","Medication list notes."),
    ]

    # expand templates up to requested count by lightly varying wording
    base_list = templates[:]
    while len(base_list) < counts["assessment_questions"]:
        dom = random.choice(domains)
        at = random.choice(answer_types)
        text = {
            "YESNO": f"Any new issues related to {dom.lower()} in the past month?",
            "SCALE_1_5": f"Rate {dom.lower()} stability (1-5).",
            "TEXT": f"Provide additional details for {dom.lower()}.",
        }[at]
        base_list.append((dom, at, text))

    for i in range(1, counts["assessment_questions"] + 1):
        qid = id_fmt("q", i, 4)
        qids.append(qid)
        dom, at, qt = base_list[i-1]
        questions.append({
            "question_id": qid,
            "domain": dom,
            "question_text": qt,
            "answer_type": at,
        })

    write_csv(
        os.path.join(structured_dir, "assessment_questions.csv"),
        ["question_id","domain","question_text","answer_type"],
        questions
    )

    # ---------- 5) assessments (this is your CASE table) ----------
    assessments = []
    assessment_ids = []
    for i in range(1, counts["assessments"] + 1):
        aid = id_fmt("asmt", i, 6)
        assessment_ids.append(aid)

        # choose member with a care plan; if none, pick again
        mid = random.choice(member_ids)
        if mid not in cps_by_member:
            # rare but possible; fall back to random care plan to bind
            cp_id = random.choice(care_plan_ids)
            mid = next(cp["member_id"] for cp in care_plans if cp["care_plan_id"] == cp_id)
        cp_id = random.choice(cps_by_member[mid])

        atype = pick_weighted(["Initial","Reassessment","Discharge"], [0.55, 0.35, 0.10])
        status = pick_weighted(["OPEN","COMPLETE"], [0.25, 0.75])
        priority = pick_weighted(["LOW","MEDIUM","HIGH"], [0.55, 0.30, 0.15])

        created = rand_date(start_2y, today - timedelta(days=1))
        completed = "" if status == "OPEN" else iso_dt(rand_date(created, today))
        risk_level = pick_weighted(["LOW","MEDIUM","HIGH"], [0.55, 0.30, 0.15])

        summary = f"{atype} assessment for care plan {cp_id}. Focus on adherence and recent utilization."

        assessments.append({
            "assessment_id": aid,
            "member_id": mid,
            "care_plan_id": cp_id,
            "assessment_type": atype,
            "status": status,
            "priority": priority,
            "created_at": iso_dt(created),
            "completed_at": completed,
            "overall_risk_level": risk_level,
            "summary": summary,
        })

    write_csv(
        os.path.join(structured_dir, "assessments.csv"),
        ["assessment_id","member_id","care_plan_id","assessment_type","status","priority","created_at","completed_at","overall_risk_level","summary"],
        assessments
    )

    # index assessments by member
    asmt_by_member = {}
    for a in assessments:
        asmt_by_member.setdefault(a["member_id"], []).append(a["assessment_id"])

    # ---------- 6) assessment responses ----------
    responses = []
    rid_counter = 1
    per_asmt = int(counts["assessment_responses_per_assessment"])
    for a in assessments:
        aid = a["assessment_id"]
        # choose subset of questions
        chosen_qs = random.sample(qids, k=min(per_asmt, len(qids)))
        base_dt = datetime.fromisoformat(a["created_at"])
        for qid in chosen_qs:
            q = questions[int(qid.split("-")[1]) - 1]
            at = q["answer_type"]
            dom = q["domain"]

            if at == "YESNO":
                ans = pick_weighted(["Yes","No"], [0.30, 0.70])
                flag = 1 if (dom in ["Behavioral","SDOH","MedAdherence"] and ans == "Yes") else 0
            elif at == "SCALE_1_5":
                val = pick_weighted([1,2,3,4,5], [0.10,0.15,0.35,0.25,0.15])
                ans = str(val)
                flag = 1 if val >= 4 and dom in ["Behavioral","Medical"] else 0
            else:
                # TEXT
                snippets = {
                    "Medical": "Reports intermittent symptoms; monitoring; follow-up advised.",
                    "Behavioral": "Discussed coping strategies; consider referral if worsens.",
                    "SDOH": "Needs support with transportation; provided community resources.",
                    "MedAdherence": "Reviewed meds; set reminder plan; pharmacy sync suggested.",
                }
                ans = snippets.get(dom, "No additional details.")
                flag = 1 if dom == "SDOH" and "transportation" in ans else 0

            answered_at = (base_dt + timedelta(minutes=random.randint(5, 240))).isoformat() + "Z"

            responses.append({
                "response_id": id_fmt("r", rid_counter, 7),
                "assessment_id": aid,
                "question_id": qid,
                "answer_value": ans,
                "flag_risk": str(flag),
                "answered_at": answered_at,
            })
            rid_counter += 1

    write_csv(
        os.path.join(structured_dir, "assessment_responses.csv"),
        ["response_id","assessment_id","question_id","answer_value","flag_risk","answered_at"],
        responses
    )

    # ---------- 7) claims ----------
    claims = []
    claim_ids = []
    for i in range(1, counts["claims"] + 1):
        cid = id_fmt("clm", i, 7)
        claim_ids.append(cid)

        # skew claim volume for high utilizers
        mid = random.choice(member_ids if random.random() > 0.25 else list(high_utilizer_set) or member_ids)
        pid = random.choice(provider_ids)

        svc_from = rand_date(start_2y, today - timedelta(days=1))
        svc_to = svc_from + timedelta(days=random.randint(0, 3))

        ctype = random.choice(claim_types)
        status = pick_weighted(["PAID","DENIED","PENDED"], [0.70, 0.15, 0.15])
        total = round(max(25.0, random.gauss(450.0, 300.0)), 2)
        paid = 0.0 if status != "PAID" else round(total * random.uniform(0.6, 1.0), 2)

        dxs = random.sample(ICD_POOL, k=pick_weighted([1,2,3], [0.55,0.30,0.15]))
        procs = random.sample(PROC_POOL, k=pick_weighted([1,2,3,4], [0.40,0.35,0.20,0.05]))

        claims.append({
            "claim_id": cid,
            "member_id": mid,
            "provider_id": pid,
            "service_from_date": iso_dt(svc_from),
            "service_to_date": iso_dt(svc_to),
            "claim_type": ctype,
            "total_amount": f"{total:.2f}",
            "paid_amount": f"{paid:.2f}",
            "status": status,
            "diagnosis_codes": "|".join(dxs),
            "procedure_codes": "|".join(procs),
        })

    write_csv(
        os.path.join(structured_dir, "claims.csv"),
        ["claim_id","member_id","provider_id","service_from_date","service_to_date","claim_type","total_amount","paid_amount","status","diagnosis_codes","procedure_codes"],
        claims
    )

    # ---------- 8) auths ----------
    auths = []
    auth_ids = []
    for i in range(1, counts["auths"] + 1):
        auid = id_fmt("a", i, 6)
        auth_ids.append(auid)

        mid = random.choice(member_ids)
        req_pid = random.choice(provider_ids)
        req_date = rand_date(start_2y, today - timedelta(days=1))
        stype = random.choice(service_types)
        status = pick_weighted(["APPROVED","DENIED","PENDING"], [0.60, 0.15, 0.25])
        decision_date = "" if status == "PENDING" else iso_dt(rand_date(req_date, min(today, req_date + timedelta(days=14))))
        dxs = random.sample(ICD_POOL, k=pick_weighted([1,2], [0.7,0.3]))
        notes = f"Request for {stype}. Clinical rationale provided. Pending review." if status == "PENDING" else f"Decision: {status}. Rationale recorded."

        auths.append({
            "auth_id": auid,
            "member_id": mid,
            "requesting_provider_id": req_pid,
            "request_date": iso_dt(req_date),
            "service_type": stype,
            "status": status,
            "decision_date": decision_date,
            "diagnosis_codes": "|".join(dxs),
            "notes_summary": notes,
        })

    write_csv(
        os.path.join(structured_dir, "auths.csv"),
        ["auth_id","member_id","requesting_provider_id","request_date","service_type","status","decision_date","diagnosis_codes","notes_summary"],
        auths
    )

    # ---------- 9) case notes (nurse/agent notes tied to assessment) ----------
    notes = []
    note_ids = []
    for i in range(1, counts["case_notes"] + 1):
        nid = id_fmt("note", i, 6)
        note_ids.append(nid)

        mid = random.choice(member_ids)
        # pick an assessment for this member if available; else any assessment
        aid = random.choice(asmt_by_member.get(mid, assessment_ids))
        created = rand_date(start_2y, today)
        author = pick_weighted(["nurse-001","nurse-002","agent"], [0.45,0.45,0.10])

        note_text = pick_weighted(
            [
                "Reviewed assessment responses; provided education and follow-up plan.",
                "Discussed barriers to care; arranged transportation resources.",
                "Medication adherence reviewed; reminders and pharmacy sync recommended.",
                "Member reports improvement; continue monitoring and next touchpoint scheduled.",
                "Escalation noted; recommend provider follow-up and care team coordination.",
            ],
            [0.30,0.15,0.20,0.20,0.15]
        )

        notes.append({
            "note_id": nid,
            "member_id": mid,
            "assessment_id": aid,
            "author": author,
            "created_at": iso_ts(created),
            "note_text": note_text,
        })

    write_csv(
        os.path.join(structured_dir, "case_notes.csv"),
        ["note_id","member_id","assessment_id","author","created_at","note_text"],
        notes
    )

    # ---------- 10) unstructured docs ----------
    # clinical notes (often tie to member; sometimes to assessment)
    clinical = []
    for i in range(1, ucounts["clinical_notes"] + 1):
        doc_id = id_fmt("doc", i, 7)
        mid = random.choice(member_ids)
        maybe_asmt = ""
        if random.random() < 0.40 and mid in asmt_by_member:
            maybe_asmt = random.choice(asmt_by_member[mid])
        created = rand_date(start_2y, today)

        text = (
            f"CLINICAL NOTE\n"
            f"member_id: {mid}\n"
            f"assessment_id: {maybe_asmt}\n"
            f"Subjective: Reports intermittent symptoms; denies acute distress.\n"
            f"Assessment: Chronic conditions reviewed; adherence discussed.\n"
            f"Plan: Follow up in 2-4 weeks; reinforce care plan goals.\n"
        )

        clinical.append({
            "doc_id": doc_id,
            "doc_type": "CLINICAL_NOTE",
            "member_id": mid,
            "assessment_id": maybe_asmt,
            "created_at": iso_ts(created),
            "text": text
        })
    write_jsonl(os.path.join(unstructured_dir, "clinical_notes.jsonl"), clinical)

    # faxes (often tie to auth)
    faxes = []
    for i in range(1, ucounts["faxes"] + 1):
        doc_id = id_fmt("fax", i, 7)
        auth = random.choice(auths)
        mid = auth["member_id"]
        created = rand_date(start_2y, today)

        text = (
            f"FAX\n"
            f"member_id: {mid}\n"
            f"auth_id: {auth['auth_id']}\n"
            f"Requesting provider: {auth['requesting_provider_id']}\n"
            f"Service: {auth['service_type']}\n"
            f"Clinical rationale: Symptoms persist; requesting authorization.\n"
        )

        faxes.append({
            "doc_id": doc_id,
            "doc_type": "FAX",
            "member_id": mid,
            "auth_id": auth["auth_id"],
            "created_at": iso_ts(created),
            "text": text
        })
    write_jsonl(os.path.join(unstructured_dir, "faxes.jsonl"), faxes)

    # letters (tie to claim or auth)
    letters = []
    for i in range(1, ucounts["letters"] + 1):
        doc_id = id_fmt("ltr", i, 7)
        created = rand_date(start_2y, today)

        if random.random() < 0.60:
            clm = random.choice(claims)
            mid = clm["member_id"]
            decision = clm["status"]
            text = (
                f"LETTER\n"
                f"member_id: {mid}\n"
                f"claim_id: {clm['claim_id']}\n"
                f"Decision: {decision}\n"
                f"Summary: Your claim was processed. If denied, rationale is documented.\n"
            )
            letters.append({
                "doc_id": doc_id,
                "doc_type": "LETTER",
                "member_id": mid,
                "claim_id": clm["claim_id"],
                "auth_id": "",
                "created_at": iso_ts(created),
                "text": text
            })
        else:
            au = random.choice(auths)
            mid = au["member_id"]
            decision = au["status"]
            text = (
                f"LETTER\n"
                f"member_id: {mid}\n"
                f"auth_id: {au['auth_id']}\n"
                f"Decision: {decision}\n"
                f"Rationale: Medical necessity and benefit coverage were considered.\n"
            )
            letters.append({
                "doc_id": doc_id,
                "doc_type": "LETTER",
                "member_id": mid,
                "claim_id": "",
                "auth_id": au["auth_id"],
                "created_at": iso_ts(created),
                "text": text
            })

    write_jsonl(os.path.join(unstructured_dir, "letters.jsonl"), letters)

    # done
    print("✅ Synthetic data generated:")
    print(f"  Structured:  {structured_dir}")
    print(f"  Unstructured:{unstructured_dir}")
    print("  Files written:")
    for fn in [
        "providers.csv","members.csv","care_plans.csv","assessment_questions.csv",
        "assessments.csv","assessment_responses.csv","claims.csv","auths.csv","case_notes.csv"
    ]:
        print(f"   - {fn}")
    for fn in ["clinical_notes.jsonl","faxes.jsonl","letters.jsonl"]:
        print(f"   - {fn}")


if __name__ == "__main__":
    main()
