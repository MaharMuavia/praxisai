from app.domain.enums import Role

INTERNSHIP_CAPABILITIES: dict[str, frozenset[str]] = {
    Role.STUDENT.value: frozenset(
        {
            "internships:applications:view",
            "internships:applications:create",
            "internships:applications:update_own",
            "internships:curriculum:view_own",
            "internships:assignments:view_own",
            "internships:assignments:start_own",
            "internships:uploads:create_own",
            "internships:submissions:manage_own",
            "internships:extensions:request",
            "internships:certificates:view_own",
        }
    ),
    Role.REVIEWER.value: frozenset(
        {"internships:reviews:view_assigned", "internships:reviews:finalize"}
    ),
    Role.TECHNICAL_LEAD.value: frozenset(
        {"internships:reviews:view_assigned", "internships:reviews:finalize"}
    ),
    Role.COORDINATOR.value: frozenset(
        {
            "internships:applications:view",
            "internships:applications:decide",
            "internships:programs:manage",
            "internships:cohorts:manage",
            "internships:curriculum:manage",
            "internships:assignments:manage",
            "internships:reviews:view_assigned",
            "internships:reviews:assign",
            "internships:reviews:finalize",
            "internships:extensions:decide",
            "internships:completion:decide",
            "internships:certificates:issue",
            "internships:analytics:view",
            "internships:domains:manage",
        }
    ),
    Role.PLATFORM_ADMIN.value: frozenset(
        {
            "internships:applications:view",
            "internships:applications:decide",
            "internships:programs:manage",
            "internships:cohorts:manage",
            "internships:curriculum:manage",
            "internships:assignments:manage",
            "internships:reviews:view_assigned",
            "internships:reviews:assign",
            "internships:reviews:finalize",
            "internships:extensions:decide",
            "internships:completion:decide",
            "internships:certificates:issue",
            "internships:certificates:revoke",
            "internships:analytics:view",
            "internships:domains:manage",
        }
    ),
}


def role_has_capability(role: str, capability: str) -> bool:
    return capability in INTERNSHIP_CAPABILITIES.get(role, frozenset())
