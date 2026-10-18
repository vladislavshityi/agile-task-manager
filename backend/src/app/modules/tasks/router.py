import uuid
from datetime import date

from fastapi import APIRouter, Response, status

from app.core.deps import CurrentUser, SessionDep
from app.modules.tasks.schemas import (
    CommentCreate,
    CommentRead,
    LabelCreate,
    LabelRead,
    LabelUpdate,
    MyTask,
    TaskCreate,
    TaskDetail,
    TaskMove,
    TaskRead,
    TaskUpdate,
)
from app.modules.tasks.service import TaskService

router = APIRouter(tags=["tasks"])
NO_CONTENT = status.HTTP_204_NO_CONTENT
CREATED = status.HTTP_201_CREATED


@router.post("/columns/{column_id}/tasks", response_model=TaskRead, status_code=CREATED)
async def create_task(
    column_id: uuid.UUID, data: TaskCreate, user: CurrentUser, session: SessionDep
) -> TaskRead:
    return TaskRead.model_validate(await TaskService(session).create(user, column_id, data))


@router.get("/tasks/{task_id}", response_model=TaskDetail)
async def get_task(task_id: uuid.UUID, user: CurrentUser, session: SessionDep) -> TaskDetail:
    return TaskDetail.model_validate(await TaskService(session).get(user, task_id))


@router.patch("/tasks/{task_id}", response_model=TaskRead)
async def update_task(
    task_id: uuid.UUID, data: TaskUpdate, user: CurrentUser, session: SessionDep
) -> TaskRead:
    return TaskRead.model_validate(await TaskService(session).update(user, task_id, data))


@router.post("/tasks/{task_id}/move", response_model=TaskRead)
async def move_task(
    task_id: uuid.UUID, data: TaskMove, user: CurrentUser, session: SessionDep
) -> TaskRead:
    return TaskRead.model_validate(await TaskService(session).move(user, task_id, data))


@router.delete("/tasks/{task_id}", status_code=NO_CONTENT)
async def delete_task(task_id: uuid.UUID, user: CurrentUser, session: SessionDep) -> Response:
    await TaskService(session).delete(user, task_id)
    return Response(status_code=NO_CONTENT)


@router.get("/me/tasks", response_model=list[MyTask])
async def my_tasks(
    user: CurrentUser,
    session: SessionDep,
    workspace_id: uuid.UUID | None = None,
    due_from: date | None = None,
    due_to: date | None = None,
) -> list[MyTask]:
    return await TaskService(session).my_tasks(user, workspace_id, due_from, due_to)


@router.post("/tasks/{task_id}/comments", response_model=CommentRead, status_code=CREATED)
async def add_comment(
    task_id: uuid.UUID, data: CommentCreate, user: CurrentUser, session: SessionDep
) -> CommentRead:
    comment = await TaskService(session).add_comment(user, task_id, data.body)
    return CommentRead.model_validate(comment)


@router.delete("/comments/{comment_id}", status_code=NO_CONTENT)
async def delete_comment(comment_id: uuid.UUID, user: CurrentUser, session: SessionDep) -> Response:
    await TaskService(session).delete_comment(user, comment_id)
    return Response(status_code=NO_CONTENT)


@router.get("/workspaces/{workspace_id}/labels", response_model=list[LabelRead])
async def list_labels(
    workspace_id: uuid.UUID, user: CurrentUser, session: SessionDep
) -> list[LabelRead]:
    labels = await TaskService(session).list_labels(user, workspace_id)
    return [LabelRead.model_validate(label) for label in labels]


@router.post("/workspaces/{workspace_id}/labels", response_model=LabelRead, status_code=CREATED)
async def create_label(
    workspace_id: uuid.UUID, data: LabelCreate, user: CurrentUser, session: SessionDep
) -> LabelRead:
    label = await TaskService(session).create_label(user, workspace_id, data)
    return LabelRead.model_validate(label)


@router.patch("/labels/{label_id}", response_model=LabelRead)
async def update_label(
    label_id: uuid.UUID, data: LabelUpdate, user: CurrentUser, session: SessionDep
) -> LabelRead:
    return LabelRead.model_validate(await TaskService(session).update_label(user, label_id, data))


@router.delete("/labels/{label_id}", status_code=NO_CONTENT)
async def delete_label(label_id: uuid.UUID, user: CurrentUser, session: SessionDep) -> Response:
    await TaskService(session).delete_label(user, label_id)
    return Response(status_code=NO_CONTENT)
