class StaleAgentResultError(ValueError):
    pass


def require_current_resource_version(*, result_version: object, current_version: int) -> None:
    if not isinstance(result_version, int) or result_version != current_version:
        raise StaleAgentResultError("Agent result is stale for the current resource version")
