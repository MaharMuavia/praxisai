import uuid

import pytest

from app.change_orders.service import ScopeChangeInput, classify_scope_change
from app.work_management.service import ensure_acyclic_dependencies


def test_task_dependency_cycle_is_rejected() -> None:
    first, second = uuid.uuid4(), uuid.uuid4()
    with pytest.raises(ValueError, match="cycle"):
        ensure_acyclic_dependencies({first: [second], second: [first]})


def test_material_scope_change_requires_change_order() -> None:
    result = classify_scope_change(
        ScopeChangeInput(
            request_text="Add another provider integration",
            changes_deliverable=False,
            changes_acceptance_criterion=False,
            adds_integration=True,
            adds_environment=False,
            exceeds_effort_bound=False,
            corrects_verified_defect=False,
            remaining_revision_rounds=2,
        )
    )
    assert result == "new_scope"
