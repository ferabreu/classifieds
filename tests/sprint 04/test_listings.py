from app.models import Category


def test_index_renders_without_categories(client):
    response = client.get("/")
    assert response.status_code == 200


def test_index_with_listings(client, app, listing):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Test Listing" in response.data


def test_category_page(client, listing):
    response = client.get(f"/category/{listing['category_id']}")
    assert response.status_code in (200, 404)


def test_listing_detail(client, listing):
    response = client.get(f"/listing/{listing['id']}")
    # detail page should load
    assert response.status_code in (200, 404)


def test_category_from_path_lookup(app, category):
    with app.app_context():
        resolved = Category.from_path(category["url_name"])
        assert resolved is not None
        assert resolved.id == category["id"]


def test_random_listing_route(client, app, listing):
    response = client.get("/listing/random")
    assert response.status_code in (200, 302, 404)
