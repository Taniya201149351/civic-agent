
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
    norm=(area or "").strip().lower()
    for ward in AREAS["wards"]:
        if norm in [x.lower() for x in ward["aliases"]] or norm==ward["name"].lower():
            return ward
    return None
def department_for(kind):
    return {"pothole":"Roads & Engineering","garbage":"Solid Waste Management",
            "streetlight":"Electrical / Street Lighting","waterlogging":"Storm Water & Drainage",
            "other":"General Civic Grievances"}.get(kind,"General Civic Grievances")

# Tool 3: ticket creation in mock local JSON database.
def create_ticket(payload):
    tickets=load_tickets()
    ticket={"tracking_id":"AMC-"+datetime.now().strftime("%y%m%d")+"-"+uuid.uuid4().hex[:6].upper(),
            **payload,"status":"Submitted (mock)","created_at":datetime.now(timezone.utc).isoformat(),
            "status_history":[{"status":"Submitted (mock)","at":datetime.now(timezone.utc).isoformat()}]}
    tickets.insert(0,ticket); save_tickets(tickets)
    return ticket

# Tool 4: status fetch from the local JSON database.
def fetch_status(tracking_id):
    return next((t for t in load_tickets() if t["tracking_id"].lower()==tracking_id.strip().lower()),None)

@app.get("/")
def index(): return render_template("index.html", wards=AREAS["wards"])
@app.post("/api/complaints")
def submit_complaint():
    area=request.form.get("area","").strip()
    issue_hint=request.form.get("issue_type","")
    if not area: return jsonify(error="Enter an area name so the mock ward lookup can route this complaint."),400
    ward=lookup_ward(area)
    if not ward: return jsonify(error=f"Area '{area}' was not found in mock AMC data. Try: "+", ".join(w["name"] for w in AREAS["wards"])),400
    upload=request.files.get("photo")
    image_path=None; image_name=None
    if upload and upload.filename:
        ext=Path(upload.filename).suffix.lower()
        if ext not in {".jpg",".jpeg",".png",".webp"}: return jsonify(error="Upload a JPG, PNG, or WEBP image."),400
        image_name=uuid.uuid4().hex+ext; image_path=str(UPLOADS/image_name); upload.save(image_path)
    analysis=analyze_issue(image_path,issue_hint)
    # The selected issue is an explicit user confirmation, so it overrides uncertain analysis.
    if issue_hint in {"pothole","garbage","streetlight","waterlogging","other"}:
        analysis["issue_type"]=issue_hint
        analysis["description"]=f"{issue_hint.title()} reported by resident."
        analysis["user_confirmed"]=True
    ticket=create_ticket({"area":area,"ward_id":ward["id"],"ward_name":ward["name"],
        "department":department_for(analysis["issue_type"]),"issue_type":analysis["issue_type"],
        "description":analysis["description"],"analysis":analysis,"photo":image_name,
        "location_source":"user-entered area","reporter_note":request.form.get("note","").strip()[:500]})
    return jsonify(ticket=ticket,ward=ward,workflow=["Image analysis","Ward lookup","Department routing","Ticket creation"]),201

@app.get("/api/status/<tracking_id>")
def status(tracking_id):
    ticket=fetch_status(tracking_id)
    if not ticket: return jsonify(error="Tracking ID not found in the local mock database."),404
    return jsonify(ticket=ticket)
@app.get("/api/tickets")
def tickets(): return jsonify(tickets=load_tickets())
@app.get("/uploads/<path:filename>")
def uploaded(filename): return send_from_directory(UPLOADS,filename)
@app.errorhandler(413)
def too_large(_): return jsonify(error="Image is too large. Maximum upload size is 8 MB."),413
if __name__=="__main__": app.run(debug=True,port=int(os.getenv("PORT","5000")))
