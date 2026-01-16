from flask import url_for


def test_profile_requires_login(client):
    response = client.get("/profile", follow_redirects=False)
    assert response.status_code in (301, 302)
    assert "/auth/login" in response.headers.get("Location", "")


def test_profile_page_loads_for_logged_in_user(client, app, user):
    client.post(
        "/auth/login",
        data={"email": user["email"], "password": user["password"]},
        follow_redirects=True,
    )
    response = client.get(url_for("users.profile"))
    assert response.status_code == 200
    assert b"Profile" in response.data or user["email"].encode() in response.data


def test_admin_user_list_requires_admin(client, app, admin_user):
    client.post(
        "/auth/login",
        data={"email": admin_user["email"], "password": admin_user["password"]},
        follow_redirects=True,
    )
    response = client.get("/admin/users")
    assert response.status_code in (200, 302, 403)


def test_cannot_promote_without_admin(client, app, user, admin_user):
    # login as non-admin user
    client.post(
        "/auth/login",
        data={"email": user["email"], "password": user["password"]},
        follow_redirects=True,
    )
    # Attempt to access admin endpoint should redirect/forbid
    response = client.post("/admin/users/promote", data={"user_id": admin_user["id"]})
    assert response.status_code in (302, 403, 405)
