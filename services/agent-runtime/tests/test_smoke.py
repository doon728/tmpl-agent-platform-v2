from unittest.mock import patch

from src.graph.build_graph import run_graph

@patch("src.tools.bindings.requests.post")
def test_graph_runs(mock_post):
    mock_post.return_value.raise_for_status.return_value = None
    mock_post.return_value.json.return_value = {
      "contract_version": "v1",
      "tool_name": "search_kb",
      "ok": True,
      "output": {"results": [{"id":"doc-001","title":"x","score":1.0,"snippet":"ok"}]},
      "error": None
    }


    out = run_graph("hello")
    # Your current graph returns whatever execute() returns; if it's echo-like, adjust here.
    # For now we only assert it returns a non-empty value.
    assert out is not None
