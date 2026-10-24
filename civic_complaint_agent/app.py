
import os, json, uuid, base64
from datetime import datetime, timezone
from pathlib import Path
from flask import Flask, request, jsonify, render_template, send_from_directory

ROOT=Path(__file__).parent
DATA=ROOT/"data"
UPLOADS=ROOT/"uploads"
DATA.mkdir(exist_ok=True); UPLOADS.mkdir(exist_ok=True)
app=Flask(__name__)
app.config["MAX_CONTENT_LENGTH"]=8*1024*1024
DB=DATA/"tickets.json"
AREAS= json.loads((DATA/"amc_mock.json").read_text(encoding="utf-8"))

def load_tickets():
    if not DB.exists(): DB.write_text("[]",encoding="utf-8")
    return json.loads(DB.read_text(encoding="utf-8"))
def save_tickets(items): DB.write_text(json.dumps(items,indent=2),encoding="utf-8")

# Tool 1: image analysis. Uses OpenAI vision only when explicitly configured; otherwise demo-safe mock.
def analyze_issue(image_path, user_hint=""):
    api_key=os.getenv("OPENAI_API_KEY")
    if api_key and image_path:
        try:
            from openai import OpenAI
            client=OpenAI(api_key=api_key)
            import mimetypes
            mime=mimetypes.guess_type(image_path)[0] or "image/jpeg"
            raw=Path(image_path).read_bytes()
            encoded=base64.b64encode(raw).decode()
            response=client.responses.create(
                model=os.getenv("OPENAI_VISION_MODEL","gpt-4.1-mini"),
                input=[{"role":"user","content":[
                    {"type":"input_text","text":"Classify this civic issue for a municipal complaint. Return JSON only with issue_type one of pothole, garbage, streetlight, waterlogging, other; short description; confidence 0-1. Do not infer location from the image. If unclear use other."},
                    {"type":"input_image","image_url":f"data:{mime};base64,{encoded}"}
                ]}],
                text={"format":{"type":"json_object"}}
            )
            result=json.loads(response.output_text)
            allowed={"pothole","garbage","streetlight","waterlogging","other"}
            kind=result.get("issue_type","other").lower()
            if kind not in allowed: kind="other"
            return {"issue_type":kind,"description":str(result.get("description","Civic issue reported"))[:300],
                    "confidence":max(0,min(1,float(result.get("confidence",0.5)))),"mode":"AI vision"}
        except Exception as e:
            return {"issue_type":"other","description":"Image analysis unavailable; please confirm the issue type.","confidence":0.0,"mode":"fallback","warning":"Vision API failed or is not configured."}
    # Fallback does not pretend to understand pixels; user hint drives the demo classification.
    hint=(user_hint or "").lower()
    mapping={"pothole":"pothole","road hole":"pothole","garbage":"garbage","waste":"garbage",
             "streetlight":"streetlight","light":"streetlight","waterlogging":"waterlogging","flood":"waterlogging"}
    kind=next((v for k,v in mapping.items() if k in hint),"other")
    return {"issue_type":kind,"description":f"Demo classification based on selected issue: {kind}.",
            "confidence":0.0,"mode":"demo fallback","warning":"Set OPENAI_API_KEY to enable actual image understanding."}

# Tool 2: ward and department lookup from local mock AMC data.
def lookup_ward(area):
    norm = (area or "").strip().lower()
    for ward in AREAS.get("wards", []):
        aliases = [x.lower() for x in ward.get("aliases", [])]
        if norm in aliases or norm == ward.get("name", "").lower():
            return ward
    return None

def department_for(kind):
    return {
        "pothole": "Roads & Engineering",
        "garbage": "Solid Waste Management",
        "streetlight": "Electrical / Street Lighting",
        "waterlogging": "Storm Water & Drainage",
        "other": "General Civic Grievances"
    }.get(kind, "General Civic Grievances")

STATUS_LIFECYCLE = [
    "Submitted (mock)",
    "Assigned to Ward Engineer",
    "In Progress",
    "Resolved"
]

# Tool 3: ticket creation in mock local JSON database.
def create_ticket(payload):
    tickets = load_tickets()
    now_iso = datetime.now(timezone.utc).isoformat()
    tracking_id = "AMC-" + datetime.now().strftime("%y%m%d") + "-" + uuid.uuid4().hex[:6].upper()
    ticket = {
        "tracking_id": tracking_id,
        **payload,
        "status": STATUS_LIFECYCLE[0],
        "created_at": now_iso,
        "status_history": [
            {
                "status": STATUS_LIFECYCLE[0],
                "at": now_iso,
                "note": "Complaint lodged in municipal mock registry. Pending ward engineer allocation."
            }
        ]
    }
    tickets.insert(0, ticket)
    save_tickets(tickets)
    return ticket

# Tool 4: status fetch from the local JSON database.
def fetch_status(tracking_id):
    normalized = (tracking_id or "").strip().lower()
    return next((t for t in load_tickets() if t.get("tracking_id", "").lower() == normalized), None)

# Tool 5: advance ticket status in mock lifecycle
def advance_ticket_status(tracking_id):
    tickets = load_tickets()
    normalized = (tracking_id or "").strip().lower()
    ticket = next((t for t in tickets if t.get("tracking_id", "").lower() == normalized), None)
    if not ticket:
        return None
    
    current_status = ticket.get("status", STATUS_LIFECYCLE[0])
    try:
        current_idx = STATUS_LIFECYCLE.index(current_status)
    except ValueError:
        current_idx = 0
    
    next_idx = (current_idx + 1) % len(STATUS_LIFECYCLE)
    next_status = STATUS_LIFECYCLE[next_idx]
    
    notes = {
        "Assigned to Ward Engineer": f"Assigned to AMC {ticket.get('ward_name', 'Local')} Ward Junior Engineer for site inspection.",
        "In Progress": f"Work order dispatched to {ticket.get('department', 'department')} maintenance crew.",
        "Resolved": f"Civic issue verified resolved on site by {ticket.get('ward_name', 'ward')} team. Ticket closed.",
        "Submitted (mock)": "Status reset to initial state for testing."
    }
    
    now_iso = datetime.now(timezone.utc).isoformat()
    ticket["status"] = next_status
    if "status_history" not in ticket:
        ticket["status_history"] = []
    ticket["status_history"].append({
        "status": next_status,
        "at": now_iso,
        "note": notes.get(next_status, f"Status updated to {next_status}.")
    })
    save_tickets(tickets)
    return ticket

@app.get("/")
def index():
    return render_template("index.html", wards=AREAS.get("wards", []))

@app.get("/api/wards")
def list_wards():
    return jsonify(city=AREAS.get("city", "Ahmedabad"), wards=AREAS.get("wards", []))

@app.post("/api/complaints")
def submit_complaint():
    area = request.form.get("area", "").strip()
    issue_hint = request.form.get("issue_type", "").strip().lower()
    
    if not area:
        return jsonify(
            error="Enter an area name so the mock ward lookup can route this complaint.",
            suggestions=[w["name"] for w in AREAS.get("wards", [])]
        ), 400
    
    ward = lookup_ward(area)
    if not ward:
        valid_names = [w["name"] for w in AREAS.get("wards", [])]
        return jsonify(
            error=f"Area '{area}' was not found in mock AMC data. Try: " + ", ".join(valid_names),
            suggestions=valid_names,
            wards=AREAS.get("wards", [])
        ), 400
    
    upload = request.files.get("photo")
    image_path = None
    image_name = None
    if upload and upload.filename:
        ext = Path(upload.filename).suffix.lower()
        if ext not in {".jpg", ".jpeg", ".png", ".webp"}:
            return jsonify(error="Upload a JPG, PNG, or WEBP image."), 400
        image_name = uuid.uuid4().hex + ext
        image_path = str(UPLOADS / image_name)
        upload.save(image_path)
    
    # Run vision or demo analysis
    raw_analysis = analyze_issue(image_path, issue_hint)
    ai_predicted_type = raw_analysis.get("issue_type", "other")
    has_image = bool(image_path)
    is_real_vision = raw_analysis.get("mode") == "AI vision"
    
    # Handle user confirmation & potential disagreement transparently (Requirement 3.B)
    allowed_categories = {"pothole", "garbage", "streetlight", "waterlogging", "other"}
    user_confirmed = issue_hint in allowed_categories
    
    has_disagreement = False
    disagreement_explanation = None
    
    if user_confirmed:
        final_issue_type = issue_hint
        if is_real_vision and ai_predicted_type != issue_hint:
            has_disagreement = True
            disagreement_explanation = (
                f"AI Vision detected '{ai_predicted_type}' ({int(raw_analysis.get('confidence', 0.5) * 100)}% confidence), "
                f"but resident explicitly specified '{issue_hint}'. Routed based on resident confirmation."
            )
        else:
            disagreement_explanation = None
    else:
        final_issue_type = ai_predicted_type
    
    routing_dept = department_for(final_issue_type)
    
    ticket_payload = {
        "area": area,
        "ward_id": ward["id"],
        "ward_name": ward["name"],
        "department": routing_dept,
        "issue_type": final_issue_type,
        "user_selected_issue": issue_hint if user_confirmed else None,
        "ai_predicted_issue": ai_predicted_type if (has_image or is_real_vision) else None,
        "has_disagreement": has_disagreement,
        "disagreement_explanation": disagreement_explanation,
        "routing_explanation": (
            f"Complaint routed to {routing_dept} based on verified {final_issue_type} category "
            f"({ 'resident confirmation overriding AI prediction' if has_disagreement else 'resident selection / classification' })."
        ),
        "description": raw_analysis.get("description", f"{final_issue_type.title()} reported by resident."),
        "analysis": {
            **raw_analysis,
            "final_routing_category": final_issue_type,
            "user_confirmed": user_confirmed
        },
        "photo": image_name,
        "location_source": "user-entered locality lookup",
        "reporter_note": request.form.get("note", "").strip()[:500]
    }
    
    ticket = create_ticket(ticket_payload)
    return jsonify(
        ticket=ticket,
        ward=ward,
        workflow=["1. Image analysis", "2. Ward resolution", "3. Department routing", "4. Ticket creation & tracking"]
    ), 201

@app.get("/api/status/<tracking_id>")
def status(tracking_id):
    ticket = fetch_status(tracking_id)
    if not ticket:
        return jsonify(error="Tracking ID not found in the local mock database."), 404
    return jsonify(ticket=ticket)

@app.post("/api/status/<tracking_id>/advance")
def advance_status(tracking_id):
    ticket = advance_ticket_status(tracking_id)
    if not ticket:
        return jsonify(error="Tracking ID not found in the local mock database."), 404
    return jsonify(ticket=ticket, message=f"Ticket status advanced to '{ticket['status']}'")

@app.get("/api/tickets")
def tickets():
    all_tickets = load_tickets()
    counts = {
        "total": len(all_tickets),
        "submitted": sum(1 for t in all_tickets if "submitted" in t.get("status", "").lower()),
        "assigned": sum(1 for t in all_tickets if "assigned" in t.get("status", "").lower()),
        "in_progress": sum(1 for t in all_tickets if "progress" in t.get("status", "").lower()),
        "resolved": sum(1 for t in all_tickets if "resolved" in t.get("status", "").lower()),
    }
    return jsonify(tickets=all_tickets, counts=counts)

@app.get("/uploads/<path:filename>")
def uploaded(filename):
    return send_from_directory(UPLOADS, filename)

@app.errorhandler(413)
def too_large(_):
    return jsonify(error="Image is too large. Maximum upload size is 8 MB."), 413

if __name__ == "__main__":
    app.run(debug=True, port=int(os.getenv("PORT", "5000")))

