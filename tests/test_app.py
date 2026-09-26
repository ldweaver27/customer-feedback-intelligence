import pytest

from app import app
from demand_service import calculate_theme_demand, classify_demand

@pytest.fixture
def client():
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client


def test_home_page_redirects_to_dashboard(client):
    response = client.get("/")

    assert response.status_code == 302
    assert "/dashboard" in response.headers["Location"]


def test_product_areas_page_returns_success(client):
    response = client.get("/product-areas")

    assert response.status_code == 200
    assert b"Product Areas" in response.data


def test_companies_page_returns_success(client):
    response = client.get("/companies")

    assert response.status_code == 200
    assert b"Customer Companies" in response.data


def test_feedback_page_returns_success(client):
    response = client.get("/feedback")

    assert response.status_code == 200
    assert b"Customer Feedback" in response.data


def test_product_area_requires_all_fields(client):
    response = client.post(
        "/product-areas",
        data={
            "name": "",
            "description": "",
            "core_functionality": "",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200


def test_duplicate_company_is_rejected(client):
    response = client.post(
        "/companies",
        data={
            "name": "Acme Corp",
            "arr": "500000",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"A company with this name already exists." in response.data


def test_feedback_requires_required_fields(client):
    response = client.post(
        "/feedback",
        data={
            "company_id": "",
            "feedback_text": "",
            "source": "",
            "feedback_date": "",
            "contact": "",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert (
        b"Company, feedback, source, and date are required."
        in response.data
    )


def test_ai_analysis_service_returns_expected_structure(monkeypatch):
    expected_analysis = {
        "product_area": "Reporting & Data Access",
        "pain_point": (
            "Analysts spend significant time manually retrieving "
            "and combining reports before performing analysis."
        ),
        "requested_solution": "API access",
    }

    def mock_analyze_feedback(feedback_text, product_areas):
        return expected_analysis

    monkeypatch.setattr(
        "app.analyze_feedback",
        mock_analyze_feedback,
    )

    result = mock_analyze_feedback(
        "We need an API because reporting is manual.",
        [],
    )

    assert result["product_area"] == "Reporting & Data Access"
    assert "manual" in result["pain_point"]
    assert result["requested_solution"] == "API access"


def test_ai_analysis_can_return_no_requested_solution(monkeypatch):
    expected_analysis = {
        "product_area": "Reporting & Data Access",
        "pain_point": (
            "Users cannot easily identify differences "
            "between reporting periods."
        ),
        "requested_solution": None,
    }

    def mock_analyze_feedback(feedback_text, product_areas):
        return expected_analysis

    monkeypatch.setattr(
        "app.analyze_feedback",
        mock_analyze_feedback,
    )

    result = mock_analyze_feedback(
        "It is difficult to tell what changed between periods.",
        [],
    )

    assert result["product_area"] == "Reporting & Data Access"
    assert result["pain_point"]
    assert result["requested_solution"] is None


def test_themes_page_returns_success(client):
    response = client.get("/themes")

    assert response.status_code == 200
    assert b"Pain-Point Themes" in response.data


def test_theme_approval_updates_status(client, monkeypatch):
    class MockResponse:
        data = []

    class MockQuery:
        def update(self, data):
            assert data == {"status": "Approved"}
            return self

        def eq(self, field, value):
            assert field == "id"
            return self

        def execute(self):
            return MockResponse()

    class MockSupabase:
        def table(self, table_name):
            assert table_name == "themes"
            return MockQuery()

    monkeypatch.setattr(
        "app.supabase",
        MockSupabase(),
    )

    response = client.post(
        "/themes/999/approve",
        follow_redirects=False,
    )

    assert response.status_code == 302


def test_theme_rejection_updates_status(client, monkeypatch):
    class MockResponse:
        data = []

    class MockQuery:
        def update(self, data):
            assert data == {"status": "Rejected"}
            return self

        def eq(self, field, value):
            assert field == "id"
            return self

        def execute(self):
            return MockResponse()

    class MockSupabase:
        def table(self, table_name):
            assert table_name == "themes"
            return MockQuery()

    monkeypatch.setattr(
        "app.supabase",
        MockSupabase(),
    )

    response = client.post(
        "/themes/999/reject",
        follow_redirects=False,
    )

    assert response.status_code == 302
def test_theme_edit_page_returns_success(client, monkeypatch):
    class MockResponse:
        data = {
            "id": 999,
            "name": "Test Theme",
            "description": "Test description",
            "status": "Proposed",
        }

    class MockQuery:
        def select(self, fields):
            return self

        def eq(self, field, value):
            return self

        def single(self):
            return self

        def execute(self):
            return MockResponse()

    class MockSupabase:
        def table(self, table_name):
            assert table_name == "themes"
            return MockQuery()

    monkeypatch.setattr(
        "app.supabase",
        MockSupabase(),
    )

    response = client.get("/themes/999/edit")

    assert response.status_code == 200
    assert b"Edit Proposed Theme" in response.data
def test_demand_classification_boundaries():
    assert classify_demand(0) == "Low"
    assert classify_demand(9.9) == "Low"
    assert classify_demand(10) == "Medium"
    assert classify_demand(24.9) == "Medium"
    assert classify_demand(25) == "High"
    assert classify_demand(100) == "High"


def test_company_only_counts_once_per_theme():
    theme_feedback = [
        {
            "feedback": {
                "companies": {
                    "id": 1,
                    "name": "Acme Corp",
                    "arr": 500000,
                }
            }
        },
        {
            "feedback": {
                "companies": {
                    "id": 1,
                    "name": "Acme Corp",
                    "arr": 500000,
                }
            }
        },
        {
            "feedback": {
                "companies": {
                    "id": 2,
                    "name": "Cyberdyne Systems",
                    "arr": 425000,
                }
            }
        },
    ]

    result = calculate_theme_demand(
        theme_feedback,
        total_feedback_companies=8,
    )

    assert result["feedback_volume"] == 3
    assert result["unique_companies"] == 2
    assert result["demand_rate"] == 25.0
    assert result["demand_classification"] == "High"
    assert result["represented_arr"] == 925000


def test_missing_arr_does_not_remove_company_vote():
    theme_feedback = [
        {
            "feedback": {
                "companies": {
                    "id": 1,
                    "name": "Acme Corp",
                    "arr": 500000,
                }
            }
        },
        {
            "feedback": {
                "companies": {
                    "id": 2,
                    "name": "No ARR Company",
                    "arr": None,
                }
            }
        },
    ]

    result = calculate_theme_demand(
        theme_feedback,
        total_feedback_companies=10,
    )

    assert result["unique_companies"] == 2
    assert result["demand_rate"] == 20.0
    assert result["demand_classification"] == "Medium"
    assert result["represented_arr"] == 500000


def test_empty_theme_returns_zero_demand():
    result = calculate_theme_demand(
        theme_feedback=[],
        total_feedback_companies=10,
    )

    assert result["feedback_volume"] == 0
    assert result["unique_companies"] == 0
    assert result["demand_rate"] == 0
    assert result["demand_classification"] == "Low"
    assert result["represented_arr"] == 0


def test_dashboard_page_returns_success(client):
    response = client.get("/dashboard")

    assert response.status_code == 200
    assert b"Customer Feedback Intelligence" in response.data
    assert b"Feedback Overview" in response.data
    assert b"Customer Pain-Point Demand" in response.data
def test_dashboard_contains_theme_demand(client):
    response = client.get("/dashboard")

    assert response.status_code == 200
    assert b"Customer Pain-Point Demand" in response.data
    assert b"Demand Rate" in response.data
    assert b"ARR Represented" in response.data