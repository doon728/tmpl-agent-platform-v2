from typing import Dict, Any, List
import os

def _kb_provider_stub(query: str) -> List[Dict[str, Any]]:
    # TEMP: replace with Bedrock KB / OpenSearch / vector DB implementation
    if not query:
        return []
    return [
        {"id": "doc-001", "title": "Sample KB Doc", "score": 0.87, "snippet": f"Matched on: {query}"}
    ]

def search_kb(query: str) -> Dict[str, Any]:
    provider = os.getenv("KB_PROVIDER", "stub").lower()

    if provider == "stub":
        results = _kb_provider_stub(query)
        return {"results": results}

    # Future providers go here
    raise RuntimeError(f"Unsupported KB_PROVIDER: {provider}")