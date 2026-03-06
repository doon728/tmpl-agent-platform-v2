from unittest.mock import patch

from src.graph.build_graph import build_graph


@patch("src.graph.build_graph.build_chat_answer", return_value="ok")
@patch("src.graph.build_graph.execute", return_value={"results": [{"id": "doc-001"}]})
@patch("src.graph.build_graph.plan", return_value=["search_kb: hello"])
def test_graph_runs(mock_plan, mock_execute, mock_answer):
    graph = build_graph()
    out = graph.invoke({"prompt": "hello", "ctx": {}, "history": []})
    assert out is not None
    assert out.get("answer") == "ok"
