from unittest.mock import MagicMock, patch

from src.tools.bindings import search_kb


@patch("src.tools.bindings.requests.post")
def test_search_kb_success(mock_post):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "contract_version": "v1",
        "tool_name": "search_kb",
        "ok": True,
        "output": {"results": ["a", "b"]},
        "error": None,
    }
    mock_resp.raise_for_status.return_value = None
    mock_post.return_value = mock_resp

    out = search_kb("hi")
    assert out == ["a", "b"]


@patch("src.tools.bindings.requests.post")
def test_search_kb_error_envelope_raises(mock_post):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "contract_version": "v1",
        "tool_name": "search_kb",
        "ok": False,
        "output": None,
        "error": {
            "code": "UNKNOWN_TOOL",
            "message": "Unknown tool: search_kb",
        },
    }
    mock_resp.raise_for_status.return_value = None
    mock_post.return_value = mock_resp

    try:
        search_kb("hi")
        assert False, "Expected RuntimeError"
    except RuntimeError as e:
        assert "Unknown tool" in str(e)
