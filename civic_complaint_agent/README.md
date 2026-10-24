# NagarSathi — Civic Complaint Agent (hackathon MVP)

A local Flask web app demonstrating the required agent sequence: image analysis → area/ward lookup → department routing → mock ticket creation → status fetch.

## Important honesty boundary
This is a **mock AMC system**, not a real municipal integration. Tickets are stored in `data/tickets.json`. Ward data is a small illustrative directory in `data/amc_mock.json`, not an authoritative AMC ward boundary dataset. Without an API key, the app **does not claim to understand image pixels**: the demo fallback uses the issue category selected by the user. With `OPENAI_API_KEY`, the server attempts OpenAI vision classification. The user-selected issue category remains an explicit confirmation and overrides the AI category for routing.

## Run on Windows (PowerShell)
```powershell
cd civic_complaint_agent
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000

If PowerShell blocks activation, run the commands without activation using:
```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

## Optional real image analysis
Set a valid key only in your terminal session; do not paste it into source code or commit it:
```powershell
$env:OPENAI_API_KEY="your-key"
$env:OPENAI_VISION_MODEL="gpt-4.1-mini"
python app.py
```
This may incur API charges. Do not enable it unless you have access/permission and understand provider pricing. If no key is set, local demo mode remains usable. The key is read server-side and never sent to the browser.

## Demo path
1. Upload a sample civic-issue photo (optional for the no-key fallback).
2. Choose/confirm an issue type.
3. Enter `Navrangpura` (or `Maninagar`, `Satellite`, `Bodakdev`, `Paldi`).
4. Click **Analyse & file complaint**. Show the tracking ID, ward, department, and mock status.
5. Paste the tracking ID into **Already reported?** and fetch the saved ticket.
6. Refresh the page and check status again; the JSON ticket persists locally.

## Test
```powershell
python -m unittest discover -s tests -v
```
Tests cover ward mapping, department routing, ticket persistence, and API validation/status lookup.

## Core design decisions
- Flask + plain HTML/CSS/JS keeps setup light for a 2.5-hour event.
- Tool-like functions in `app.py` separate analysis, ward lookup, department routing, create ticket, and fetch status.
- A JSON file is sufficient for the explicitly requested local mock system.
- No GPS/EXIF location is inferred. Area is entered by the user.
- Optional vision integration is isolated behind `OPENAI_API_KEY`; no API key is required to run the demo.
- Optional social posting is intentionally omitted: it is not needed for the core judged flow and external posting introduces permissions and privacy risk.

## Known limitations
- Ward/area mappings are mock examples and must be replaced with verified data for any realistic deployment.
- Vision model response is probabilistic; resident confirmation is retained for reliable routing.
- Status stays `Submitted (mock)`; no real municipal staff or status feed updates it.
- No authentication, duplicate detection, or real geocoding is included.
