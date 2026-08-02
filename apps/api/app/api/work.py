import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.api.projects import _accessible_project
from app.auth.dependencies import DbSession, Principal, require_roles
from app.auth.service import SessionPrincipal
from app.domain.enums import Role
from app.domain.models import Milestone, ProjectAssignment, Task
from app.domain.schemas import TaskCreate, TaskTransitionRequest, TaskView
from app.work_management.service import allowed_task_transition, ensure_acyclic_dependencies

router = APIRouter(tags=["work management"])


@router.get("/projects/{project_id}/tasks", response_model=list[TaskView])
async def list_tasks(project_id: uuid.UUID, principal: Principal, session: DbSession) -> list[Task]:
    await _accessible_project(session, principal, project_id)
    return list(
        (
            await session.scalars(
                select(Task).where(Task.project_id == project_id).order_by(Task.created_at)
            )
        ).all()
    )


@router.post("/projects/{project_id}/tasks", response_model=TaskView, status_code=201)
async def create_task(
    project_id: uuid.UUID,
    body: TaskCreate,
    principal: Annotated[
        SessionPrincipal, Depends(require_roles(Role.COORDINATOR, Role.TECHNICAL_LEAD))
    ],
    session: DbSession,
) -> Task:
    await _accessible_project(session, principal, project_id)
    if body.milestone_id is not None:
        milestone = await session.get(Milestone, body.milestone_id)
        if milestone is None or milestone.project_id != project_id:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Invalid milestone")
    if body.assignee_id is not None:
        assignment = await session.scalar(
            select(ProjectAssignment).where(
                ProjectAssignment.project_id == project_id,
                ProjectAssignment.user_id == body.assignee_id,
            )
        )
        if assignment is None:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY, "Assignee is not on the project"
            )
    task = Task(
        project_id=project_id,
        milestone_id=body.milestone_id,
        assignee_id=body.assignee_id,
        title=body.title,
        definition_of_done=body.definition_of_done,
        state="BACKLOG",
        dependency_ids=[str(item) for item in body.dependency_ids],
        estimate_hours=body.estimate_hours,
    )
    session.add(task)
    await session.flush()
    current = list((await session.scalars(select(Task).where(Task.project_id == project_id))).all())
    graph = {
        item.id: [uuid.UUID(dependency) for dependency in item.dependency_ids] for item in current
    }
    try:
        ensure_acyclic_dependencies(graph)
    except ValueError as exc:
        await session.rollback()
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    await session.commit()
    await session.refresh(task)
    return task


@router.post("/projects/{project_id}/tasks/{task_id}/transition", response_model=TaskView)
async def transition_task(
    project_id: uuid.UUID,
    task_id: uuid.UUID,
    body: TaskTransitionRequest,
    principal: Principal,
    session: DbSession,
) -> Task:
    await _accessible_project(session, principal, project_id)
    task = await session.get(Task, task_id, with_for_update=True)
    if task is None or task.project_id != project_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")
    if principal.role == Role.STUDENT.value and task.assignee_id != principal.user_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Student is not assigned to this task")
    if principal.role not in {
        Role.STUDENT.value,
        Role.TECHNICAL_LEAD.value,
        Role.COORDINATOR.value,
    }:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Role cannot change tasks")
    if not allowed_task_transition(task.state, body.target):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Task transition {task.state} -> {body.target} is not allowed",
        )
    task.state = body.target
    await session.commit()
    await session.refresh(task)
    return task
