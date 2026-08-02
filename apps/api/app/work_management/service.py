import uuid


def ensure_acyclic_dependencies(graph: dict[uuid.UUID, list[uuid.UUID]]) -> None:
    visiting: set[uuid.UUID] = set()
    visited: set[uuid.UUID] = set()

    def visit(node: uuid.UUID) -> None:
        if node in visiting:
            raise ValueError("Task dependency cycle detected")
        if node in visited:
            return
        visiting.add(node)
        for dependency in graph.get(node, []):
            if dependency not in graph:
                raise ValueError("Task dependency references an unknown task")
            visit(dependency)
        visiting.remove(node)
        visited.add(node)

    for node in graph:
        visit(node)


def allowed_task_transition(current: str, target: str) -> bool:
    allowed = {
        "BACKLOG": {"READY"},
        "READY": {"IN_PROGRESS", "BLOCKED"},
        "IN_PROGRESS": {"BLOCKED", "IN_REVIEW"},
        "BLOCKED": {"READY", "IN_PROGRESS"},
        "IN_REVIEW": {"IN_PROGRESS", "DONE"},
        "DONE": set(),
    }
    return target in allowed.get(current, set())
