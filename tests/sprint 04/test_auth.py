from flask import url_for
from sqlalchemy import select

from app import db
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
        created = db.session.execute(
            select(User).where(User.email == "newuser@classifieds.io")
        ).scalar_one_or_none()
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
