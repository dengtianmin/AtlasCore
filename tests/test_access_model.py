from app.api.v1.graph import graph_overview
from app.api.v1.users import user_ping
from app.main import create_app


def _route_dependencies_by_path() -> dict[str, list]:
    app = create_app()
    return {
        route.path: getattr(route, "dependant").dependencies
        for route in app.routes
        if hasattr(route, "dependant")
    }


def test_anonymous_routes_have_no_auth_dependencies():
    dependencies = _route_dependencies_by_path()

    assert dependencies["/users/ping"] == []
    assert dependencies["/graph/overview"] == []
    assert dependencies["/graph/nodes/{node_id}"] == []
    assert dependencies["/graph/nodes/{node_id}/neighbors"] == []
    assert dependencies["/graph/nodes/{node_id}/hops"] == []


def test_admin_routes_still_require_auth_dependencies():
    dependencies = _route_dependencies_by_path()

    assert len(dependencies["/admin/ping"]) == 1
    assert len(dependencies["/api/admin/exports/qa-logs"]) == 1
    assert len(dependencies["/api/admin/exports"]) == 1
    assert len(dependencies["/api/admin/exports/download/{filename}"]) == 1
    assert len(dependencies["/auth/me"]) == 1


def test_user_ping_is_anonymous_payload():
    assert user_ping() == {"status": "ok", "scope": "anonymous"}


def test_graph_overview_signature_is_anonymous():
    assert "limit" in graph_overview.__annotations__
