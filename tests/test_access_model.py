import asyncio

from fastapi import HTTPException
from starlette.requests import Request

from app.auth.dependencies import bearer_scheme
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


def test_public_only_routes_have_no_auth_dependencies():
    dependencies = _route_dependencies_by_path()

    assert dependencies["/users/ping"] == []
    assert dependencies["/users/register"] == []
    assert dependencies["/users/login"] == []


def test_admin_routes_still_require_auth_dependencies():
    dependencies = _route_dependencies_by_path()

    assert len(dependencies["/admin/ping"]) == 1
    assert len(dependencies["/api/admin/graph/status"]) == 1
    assert len(dependencies["/api/admin/graph/reload"]) == 1
    assert len(dependencies["/api/admin/graph/export"]) == 1
    assert len(dependencies["/api/admin/graph/import"]) == 1
    assert len(dependencies["/api/admin/graph/download/{filename}"]) == 1
    assert len(dependencies["/api/admin/graph/clear"]) == 1
    assert len(dependencies["/api/admin/exports/qa-logs"]) == 1
    assert len(dependencies["/api/admin/exports"]) == 1
    assert len(dependencies["/api/admin/exports/download/{filename}"]) == 1
    assert len(dependencies["/auth/me"]) == 1
    assert len(dependencies["/users/me"]) == 1
    assert len(dependencies["/graph/summary"]) == 1
    assert len(dependencies["/graph/overview"]) == 1
    assert len(dependencies["/graph/nodes"]) == 1
    assert len(dependencies["/graph/nodes/{node_id}"]) == 1
    assert len(dependencies["/graph/nodes/{node_id}/neighbors"]) == 1
    assert len(dependencies["/graph/subgraph/{node_id}"]) == 1
    assert len(dependencies["/graph/nodes/{node_id}/hops"]) == 1
    assert len(dependencies["/chat/messages"]) == 2
    assert len(dependencies["/chat/messages/stream"]) == 2
    assert len(dependencies["/chat/messages/{message_id}/feedback"]) == 2
    assert len(dependencies["/review/evaluate"]) == 2


def test_user_ping_is_anonymous_payload():
    assert user_ping() == {"status": "ok", "scope": "anonymous"}


def test_graph_overview_signature_requires_principal_parameter():
    assert "limit" in graph_overview.__annotations__


def test_anonymous_access_to_protected_user_routes_is_blocked():
    request = Request({"type": "http", "headers": [], "method": "GET", "path": "/graph/summary"})

    try:
        asyncio.run(bearer_scheme(request))
    except HTTPException as exc:
        assert exc.status_code == 403
    else:
        raise AssertionError("Expected anonymous request to be rejected by bearer auth")
