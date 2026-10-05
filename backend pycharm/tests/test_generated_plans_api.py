import os
import sys

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from fastapi.testclient import TestClient
from main import app
from app.services.generated_plans_manager import list_generated_plans, get_generated_plan

client = TestClient(app)


def test_list_generated_plans():
    response = client.get("/api/v1/generated-plans")
    assert response.status_code == 200
    plans = response.json()
    assert isinstance(plans, list)
    assert len(plans) >= 30, f"Expected at least 30 generated plans, got {len(plans)}"
    
    # Check fields in first plan
    first_plan = plans[0]
    assert "filename" in first_plan
    assert "grade" in first_plan
    assert "subject" in first_plan
    assert "competence_level" in first_plan
    assert "step_count" in first_plan


def test_filter_by_grade():
    response = client.get("/api/v1/generated-plans?grade=Grade 8")
    assert response.status_code == 200
    plans = response.json()
    assert len(plans) > 0
    for p in plans:
        assert "Grade 8" in p["grade"]


def test_get_specific_plan_detail():
    response = client.get("/api/v1/generated-plans/Grade_8_comp_8_1_1.json")
    assert response.status_code == 200
    data = response.json()
    assert "plan" in data
    assert data["filename"] == "Grade_8_comp_8_1_1.json"
    assert data["plan"]["competence_level"] == "8.1.1"
    assert "lesson_development_steps" in data["plan"]


def test_alias_route():
    response = client.get("/api/generated-plans")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_and_delete_plan_lifecycle():
    sample_plan = {
        "grade": "Grade 8",
        "subject": "Civic Education",
        "time_allocation": "40 Minutes (1 Period)",
        "competence": "Test Competence for LifeCycle Verification",
        "competence_level": "99.9.9",
        "lesson": "Lifecycle Test Lesson",
        "unique_learning_outcome": ["Test Outcome 1"],
        "the_entrance": "Test Entrance",
        "lesson_development_steps": [
            {
                "step_number": 1,
                "teacher_activities": "Test Teacher",
                "student_activities": "Test Student",
                "learning_teaching_method": "Discussion",
                "learning_teaching_aids": "Board",
                "assessment_and_feedback": "Oral",
                "time_minutes": 40
            }
        ],
        "summary": "Test Summary",
        "assessment_and_feedback_whole_lesson": "Test Assessment",
        "post_activity": "Test Post Activity"
    }

    # 1. Create
    create_resp = client.post("/api/v1/generated-plans", json={
        "plan": sample_plan,
        "filename": "Grade_8_comp_99_9_9_test.json"
    })
    assert create_resp.status_code == 201
    created_file = create_resp.json()["filename"]
    assert created_file == "Grade_8_comp_99_9_9_test.json"

    # 2. Verify it exists
    get_resp = client.get(f"/api/v1/generated-plans/{created_file}")
    assert get_resp.status_code == 200
    assert get_resp.json()["plan"]["competence_level"] == "99.9.9"

    # 3. Delete
    del_resp = client.delete(f"/api/v1/generated-plans/{created_file}")
    assert del_resp.status_code == 200
    assert del_resp.json()["success"] is True

    # 4. Verify 404 after delete
    get_after_del = client.get(f"/api/v1/generated-plans/{created_file}")
    assert get_after_del.status_code == 404
    print("test_create_and_delete_plan_lifecycle: PASSED")


if __name__ == "__main__":
    print("Running generated plans API tests...")
    test_list_generated_plans()
    print("test_list_generated_plans: PASSED")
    test_filter_by_grade()
    print("test_filter_by_grade: PASSED")
    test_get_specific_plan_detail()
    print("test_get_specific_plan_detail: PASSED")
    test_alias_route()
    print("test_alias_route: PASSED")
    test_create_and_delete_plan_lifecycle()
    print("ALL TESTS PASSED SUCCESSFULLY! [PASSED]")
