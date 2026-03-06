from typing import Callable, Dict, Any


class Tool:
    def __init__(
        self,
        name: str,
        description: str,
        mode: str,
        handler: Callable[[Dict[str, Any], Dict[str, Any]], Any],
    ):
        self.name = name
        self.description = description
        self.mode = mode
        self.handler = handler

    def invoke(self, tool_input: Dict[str, Any], ctx: Dict[str, Any]):
        return self.handler(tool_input, ctx)