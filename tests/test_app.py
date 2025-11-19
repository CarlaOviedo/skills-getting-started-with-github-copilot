from fastapi.testclient import TestClient
import uuid

from src.app import app


client = TestClient(app)


def test_get_activities():
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    # Check a known activity exists
    assert "Chess Club" in data


def test_signup_and_unregister_flow():
    activity = "Chess Club"
    email = f"test_{uuid.uuid4().hex}@example.com"

    # Ensure email is not already present
    before = client.get("/activities").json()
    assert email not in before[activity]["participants"]

    # Sign up
    signup = client.post(f"/activities/{activity}/signup?email={email}")
    assert signup.status_code == 200
    assert "Signed up" in signup.json().get("message", "")

    # Verify participant present
    mid = client.get("/activities").json()
    assert email in mid[activity]["participants"]

    # Unregister
    delete = client.delete(f"/activities/{activity}/participants?email={email}")
    assert delete.status_code == 200
    assert "Unregistered" in delete.json().get("message", "")

    # Verify participant removed
    after = client.get("/activities").json()
    assert email not in after[activity]["participants"]
from fastapi.testclient import TestClient
import importlib.util
import os
from pathlib import Path

# Load the app module from src/app.py dynamically to avoid package import issues
ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "src" / "app.py"
spec = importlib.util.spec_from_file_location("app_module", str(APP_PATH))
app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_module)
app = getattr(app_module, "app")

client = TestClient(app)


def test_get_activities():
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    # expect some known activities from the in-memory DB
    assert "Chess Club" in data
    assert isinstance(data["Chess Club"]["participants"], list)


def test_signup_and_unregister_flow():
    activity = "Chess Club"
    email = "test_student@example.com"

    # Ensure the test email is not already present; if it is, remove it first
    client.delete(f"/activities/{activity}/participants?email={email}")

    # Sign up
    resp = client.post(f"/activities/{activity}/signup?email={email}")
    assert resp.status_code == 200
    json_resp = resp.json()
    assert "Signed up" in json_resp.get("message", "")

    # Verify participant appears in activity
    resp2 = client.get("/activities")
    assert resp2.status_code == 200
    data = resp2.json()
    assert email in data[activity]["participants"]

    # Unregister
    resp3 = client.delete(f"/activities/{activity}/participants?email={email}")
    assert resp3.status_code == 200
    assert "Unregistered" in resp3.json().get("message", "")

    # Verify participant removed
    resp4 = client.get("/activities")
    data2 = resp4.json()
    assert email not in data2[activity]["participants"]


def test_duplicate_signup_returns_400():
    activity = "Programming Class"
    email = "duplicate_test@example.com"

    # Clean up first
    client.delete(f"/activities/{activity}/participants?email={email}")

    # First signup should succeed
    r1 = client.post(f"/activities/{activity}/signup?email={email}")
    assert r1.status_code == 200

    # Second signup should fail with 400
    r2 = client.post(f"/activities/{activity}/signup?email={email}")
    assert r2.status_code == 400

    # Cleanup
    client.delete(f"/activities/{activity}/participants?email={email}")


def test_unregister_nonexistent_participant_returns_404():
    activity = "Math Olympiad"
    email = "no_such_student@example.com"

    # Ensure the participant is not present
    client.delete(f"/activities/{activity}/participants?email={email}")

    # Attempt to delete again should return 404
    r = client.delete(f"/activities/{activity}/participants?email={email}")
    assert r.status_code == 404
