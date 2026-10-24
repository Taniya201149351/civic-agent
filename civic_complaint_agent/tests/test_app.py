import json, tempfile, unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import app as civic

class CivicTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.old_db=civic.DB
        civic.DB=Path(self.temp.name)/"tickets.json"
        civic.DB.write_text("[]",encoding="utf-8")
    def tearDown(self):
        civic.DB=self.old_db
        self.temp.cleanup()
    def test_ward_alias(self):
        self.assertEqual(civic.lookup_ward("Commerce Six Roads")["id"],"W-01")
    def test_unknown_ward(self):
        self.assertIsNone(civic.lookup_ward("Unknown Place"))
    def test_department_routes(self):
        self.assertEqual(civic.department_for("garbage"),"Solid Waste Management")
        self.assertEqual(civic.department_for("pothole"),"Roads & Engineering")
    def test_ticket_create_and_fetch(self):
        t=civic.create_ticket({"area":"Navrangpura","issue_type":"pothole"})
        self.assertEqual(civic.fetch_status(t["tracking_id"])["area"],"Navrangpura")
    def test_api_validation_and_status(self):
        client=civic.app.test_client()
        response=client.post("/api/complaints",data={"area":"unknown","issue_type":"pothole"})
        self.assertEqual(response.status_code,400)
        response=client.get("/api/status/AMC-NOT-REAL")
        self.assertEqual(response.status_code,404)

    def test_status_advancement_lifecycle(self):
        t = civic.create_ticket({"area": "Navrangpura", "issue_type": "pothole"})
        tracking_id = t["tracking_id"]
        self.assertEqual(t["status"], "Submitted (mock)")
        
        # Advance 1: Assigned
        t1 = civic.advance_ticket_status(tracking_id)
        self.assertEqual(t1["status"], "Assigned to Ward Engineer")
        self.assertEqual(len(t1["status_history"]), 2)
        
        # Advance 2: In Progress
        t2 = civic.advance_ticket_status(tracking_id)
        self.assertEqual(t2["status"], "In Progress")
        
        # Advance 3: Resolved
        t3 = civic.advance_ticket_status(tracking_id)
        self.assertEqual(t3["status"], "Resolved")

    def test_unknown_ward_returns_suggestions(self):
        client = civic.app.test_client()
        response = client.post("/api/complaints", data={"area": "Mars Colony", "issue_type": "pothole"})
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn("suggestions", data)
        self.assertIn("Navrangpura", data["suggestions"])

    def test_api_wards_and_tickets_stats(self):
        client = civic.app.test_client()
        r_wards = client.get("/api/wards")
        self.assertEqual(r_wards.status_code, 200)
        self.assertIn("wards", r_wards.get_json())
        
        civic.create_ticket({"area": "Satellite", "issue_type": "garbage"})
        r_tickets = client.get("/api/tickets")
        self.assertEqual(r_tickets.status_code, 200)
        t_data = r_tickets.get_json()
        self.assertGreaterEqual(t_data["counts"]["total"], 1)

if __name__=="__main__": unittest.main()
