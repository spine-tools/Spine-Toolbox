from spinetoolbox.frontend.user_mode_rpc import handle_request
from spinetoolbox.frontend.user_mode_service import UserModeService


def test_health_request_returns_application_status():
    result = handle_request(UserModeService(), {"method": "health"})

    assert result == {"status": "ok", "application": "Spine Toolbox"}


def test_project_request_uses_user_mode_service():
    service = UserModeService()

    result = handle_request(service, {"method": "project", "params": {"path": "execution_tests/active_by_default"}})

    assert result["items"][0]["name"] == "Test data"


def test_unknown_method_returns_clear_error():
    try:
        handle_request(UserModeService(), {"method": "not_supported"})
    except ValueError as error:
        assert str(error) == "Unknown method: not_supported"
    else:
        raise AssertionError("Unknown RPC methods must be rejected")


def test_execution_permits_selects_matching_tool():
    items = {"Input": {"type": "Data Store"}, "SpineOpt": {"type": "Tool"}, "Exporter": {"type": "Exporter"}}

    permits = UserModeService._execution_permits(items, "SpineOpt")

    assert permits == {"Input": False, "SpineOpt": True, "Exporter": False}


def test_import_excel_request_passes_workbook_to_service(monkeypatch):
    service = UserModeService()
    expected = {"filename": "input.xlsx", "imported": 2, "errors": []}
    monkeypatch.setattr(service, "import_excel", lambda *args: expected)

    result = handle_request(
        service,
        {
            "method": "import_excel",
            "params": {"path": "project", "filename": "input.xlsx", "content": "encoded"},
        },
    )

    assert result == expected