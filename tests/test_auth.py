from flask import url_for

from app.models import User


def test_register_and_login_flow(client, app):
    # Register a new user
    response = client.post(
        "/auth/register",
        data={
            "email": "newuser@classifieds.io",
            "first_name": "New",
            "last_name": "User",
            "password": "strongpass",
            "password2": "strongpass",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        created = User.query.filter_by(email="newuser@classifieds.io").first()
        assert created is not None

    # Login with the new user
    response = client.post(
        "/auth/login",
        data={"email": "newuser@classifieds.io", "password": "strongpass"},
        follow_redirects=True,
    )
    assert response.status_code == 200

    # Logout should redirect back to login
    response = client.get(url_for("auth.logout"), follow_redirects=True)
    assert response.status_code == 200


def test_login_invalid_credentials(client):
    response = client.post(
        "/auth/login",
        data={"email": "missing@classifieds.io", "password": "nope"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Invalid credentials" in response.data or b"Sign in" in response.data
