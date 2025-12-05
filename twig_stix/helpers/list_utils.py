from typing import Any, List, Optional


def ensure_list(x: Optional[Any]) -> List[Any]:
    """Normalize xmltodict nodes to lists.

    xmltodict returns a dict for single-node elements and a list for multi-node.
    This helper centralizes that behaviour.
    """
    if x is None:
        return []
    if isinstance(x, list):
        return x
    return [x]
