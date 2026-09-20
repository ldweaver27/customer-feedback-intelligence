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
    assert b"Company, feedback, source, and date are required." in response.data