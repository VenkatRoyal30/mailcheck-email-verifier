import pytest
from pathlib import Path

def test_root_serves_react_index(client):
    """GET / should serve the React SPA index.html with 200 OK."""
    res = client.get("/")
    assert res.status_code == 200
    assert "text/html" in res.content_type
    html_text = res.data.decode("utf-8")
    assert 'id="root"' in html_text
    assert "MailCheck" in html_text

def test_frontend_client_routes_serve_index(client):
    """Client-side React routes (e.g. /history) should serve index.html with 200 OK."""
    res = client.get("/history")
    assert res.status_code == 200
    assert "text/html" in res.content_type
    html_text = res.data.decode("utf-8")
    assert 'id="root"' in html_text

def test_frontend_assets_served_correctly(client):
    """Static assets in /assets/ should be served with appropriate content-types."""
    dist_dir = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
    assets_dir = dist_dir / "assets"
    
    if assets_dir.exists():
        css_files = list(assets_dir.glob("*.css"))
        if css_files:
            css_name = css_files[0].name
            res = client.get(f"/assets/{css_name}")
            assert res.status_code == 200
            assert "text/css" in res.content_type

def test_api_health_endpoint(client):
    """GET /api/health should return 200 JSON status."""
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.is_json
    data = res.get_json()
    assert data["status"] == "healthy"
    assert data["service"] == "MailCheck SaaS API"
    assert data["database"] == "connected"

def test_unknown_api_routes_return_json_404(client):
    """Unknown /api/* routes must return JSON 404 responses, NOT HTML."""
    res_get = client.get("/api/nonexistent-route")
    assert res_get.status_code == 404
    assert res_get.is_json
    data_get = res_get.get_json()
    assert data_get.get("error") == "Resource not found"

    # Also test POST to unknown API route
    res_post = client.post("/api/another-unknown", json={"test": True})
    assert res_post.status_code == 404
    assert res_post.is_json
    data_post = res_post.get_json()
    assert data_post.get("error") == "Resource not found"
