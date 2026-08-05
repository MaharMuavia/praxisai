def can_edit_program(status: str) -> bool:
    return status == "DRAFT"


def can_publish_program(status: str) -> bool:
    return status == "DRAFT"
