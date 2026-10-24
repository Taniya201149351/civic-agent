# NagarSathi — Civic Complaint Agent (Hackathon MVP)

A responsive, agent-assisted civic complaint filing and tracking portal simulating the **Ahmedabad Municipal Corporation (AMC)** grievance workflow:
**Image Analysis ➔ Ward Resolution ➔ Department Routing ➔ Local JSON Store ➔ Lifecycle Tracking**.

---

## 🌟 Key Features

1. **4-Stage Agent Sequence**:
   - **Tool 1 (Visual Inspection)**: Optional OpenAI Vision model (`gpt-4.1-mini`) with transparent, clearly-labeled demo fallback when no key is set.
   - **Tool 2 (Ward Resolution)**: Locality to AMC ward lookup with alias matching (e.g. Navrangpura, Stadium, Satellite, Bodakdev, Maninagar, Paldi).
   - **Interactive Fallback (Section 3.C)**: If an unrecognized area is entered, clickable pills allow instant selection of valid AMC wards without retyping.
   - **Tool 3 (Department Routing)**: Automatic grievance cell routing (*Roads & Engineering*, *Solid Waste Management*, *Electrical / Street Lighting*, *Storm Water & Drainage*).
   - **Transparent Disagreement Handling (Section 3.B)**: If AI prediction and resident confirmation differ, both are recorded, and the resident's confirmation is prioritized and highlighted.
   - **Tool 4 (Ticket Issuance & Local Persistence)**: Generates unique tracking IDs (`AMC-YYMMDD-XXXXXX`) stored in `data/tickets.json`.
   - **Tool 5 (Lifecycle Status Progression)**: Simulates status progression through 4 stages: `Submitted` ➔ `Assigned to Ward Engineer` ➔ `In Progress` ➔ `Resolved` with full audit timestamps.

2. **Presentation-Ready UI**:
   - Modern civic-tech aesthetic built with clean CSS design tokens and Google Fonts (*Plus Jakarta Sans* & *Space Grotesk*).
   - Instant drag-and-drop photo upload with image preview.
   - **1-Click Demo Presets**: Test Pothole (Navrangpura), Waste (Satellite), Streetlight (Maninagar), or Drainage (Bodakdev) in 1 second.
   - Live animated agent pipeline tracker during submission.
   - Recent Community Reports drawer with live session stats.

---

## 🔒 Important Honesty Boundary
This is a **mock AMC system**, not an authoritative municipal integration.
- Without an `OPENAI_API_KEY`, the application **never fakes pixel understanding**: it uses the resident's selected issue category as an explicit confirmation and labels the mode as `demo fallback`.
- No GPS or EXIF data is inferred; localities are provided or confirmed by the resident.
- Local tickets are stored safely in local JSON (`data/tickets.json`).

---

## 🚀 How to Run Locally (PowerShell)

```powershell
cd civic_complaint_agent

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Start the Flask application
python app.py
```
Open **http://127.0.0.1:5000** in your web browser.

*Note: If PowerShell blocks script activation, run directly with:*
```powershell
.\.venv\Scripts\python.exe app.py
```

---

## 🧪 Running Automated Unit Tests

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```
Tests cover:
- Ward and alias resolution (`Navrangpura`, `Commerce Six Roads` ➔ `W-01`)
- Unknown ward rejection and interactive suggestions payload
- Department routing maps for all issue types
- Ticket creation, status lookup, and JSON database persistence
- Status advancement lifecycle (`Submitted` ➔ `Assigned` ➔ `In Progress` ➔ `Resolved`)
- API validation and error handling

---

## 🤖 Optional Real Image Analysis
To enable real OpenAI vision analysis:
```powershell
$env:OPENAI_API_KEY="your-openai-api-key"
$env:OPENAI_VISION_MODEL="gpt-4.1-mini"
.\.venv\Scripts\python.exe app.py
```
The key is kept secure server-side and is never sent to the browser.
