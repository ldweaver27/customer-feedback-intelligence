import pytest

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client


def test_home_page_returns_success(client):
    response = client.get("/")

    assert response.status_code == 200


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