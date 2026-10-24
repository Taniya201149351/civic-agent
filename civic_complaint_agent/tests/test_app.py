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
if __name__=="__main__": unittest.main()
