from flask import url_for


def test_admin_routes_require_login(client):
    response = client.get("/admin/dashboard")
    assert response.status_code in (301, 302)
    assert "/auth/login" in response.headers.get("Location", "")


def test_admin_users_requires_admin(client, user):
    # login as regular user
    client.post(
        "/auth/login",
        data={"email": user["email"], "password": user["password"]},
        follow_redirects=True,
    )
    response = client.get(url_for("admin.dashboard"))
    # Should redirect or forbid for non-admin depending on decorator behavior
    assert response.status_code in (302, 403)
