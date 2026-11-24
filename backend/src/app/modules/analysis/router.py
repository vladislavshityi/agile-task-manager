import uuid

from fastapi import APIRouter, Request, Response, status

from app.core.deps import CurrentUser, SessionDep
from app.core.errors import ValidationError
from app.modules.analysis.documents import extract_document
from app.modules.analysis.schemas import (
    AnalysisCreate,
    AnalysisMemberRead,
    AnalysisMemberUpdate,
    AnalysisRead,
    AnalysisSummary,
    AnalysisUpdate,
)
from app.modules.analysis.service import AnalysisService

router = APIRouter(tags=["analysis"])
NO_CONTENT = status.HTTP_204_NO_CONTENT


async def _create_data(request: Request) -> tuple[AnalysisCreate, dict[int, int] | None]:
    content_type = request.headers.get("content-type", "")
    if content_type.startswith("application/json"):
        try:
            return AnalysisCreate.model_validate(await request.json()), None
        except (ValueError, TypeError) as exc:
            raise ValidationError("Invalid analysis payload", "validation_error") from exc
    if content_type.startswith("multipart/form-data"):
        form = await request.form()
        title = form.get("title")
        upload = form.get("file")
        if not isinstance(title, str) or not title.strip() or not hasattr(upload, "read"):
            raise ValidationError("Multipart request requires title and file", "validation_error")
        content = await upload.read()
        document = extract_document(getattr(upload, "filename", None), content)
        try:
            data = AnalysisCreate(title=title, text=document.text)
        except ValueError as exc:
            raise ValidationError(
                "The extracted document has no usable text", "spec_empty"
            ) from exc
        return data, document.heading_hints
    raise ValidationError(
        "Content-Type must be application/json or multipart/form-data", "validation_error"
    )


@router.post(
    "/workspaces/{workspace_id}/analyses",
    response_model=AnalysisRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_analysis(
    workspace_id: uuid.UUID, request: Request, user: CurrentUser, session: SessionDep
) -> AnalysisRead:
    data, hints = await _create_data(request)
    return await AnalysisService(session).create(user, workspace_id, data, hints)


@router.get("/workspaces/{workspace_id}/analyses", response_model=list[AnalysisSummary])
async def list_analyses(
    workspace_id: uuid.UUID, user: CurrentUser, session: SessionDep
) -> list[AnalysisSummary]:
    return await AnalysisService(session).list_analyses(user, workspace_id)


@router.get("/analyses/{analysis_id}", response_model=AnalysisRead)
async def get_analysis(
    analysis_id: uuid.UUID, user: CurrentUser, session: SessionDep
) -> AnalysisRead:
    return await AnalysisService(session).get(user, analysis_id)


@router.patch("/analyses/{analysis_id}", response_model=AnalysisRead)
async def update_analysis(
    analysis_id: uuid.UUID, data: AnalysisUpdate, user: CurrentUser, session: SessionDep
) -> AnalysisRead:
    return await AnalysisService(session).update(user, analysis_id, data)


@router.delete("/analyses/{analysis_id}", status_code=NO_CONTENT)
async def delete_analysis(
    analysis_id: uuid.UUID, user: CurrentUser, session: SessionDep
) -> Response:
    await AnalysisService(session).delete(user, analysis_id)
    return Response(status_code=NO_CONTENT)


@router.put("/analyses/{analysis_id}/members/{user_id}", response_model=AnalysisMemberRead)
async def set_member(
    analysis_id: uuid.UUID,
    user_id: uuid.UUID,
    data: AnalysisMemberUpdate,
    user: CurrentUser,
    session: SessionDep,
) -> AnalysisMemberRead:
    return await AnalysisService(session).set_member(user, analysis_id, user_id, data.can_edit)


@router.delete("/analyses/{analysis_id}/members/{user_id}", status_code=NO_CONTENT)
async def remove_member(
    analysis_id: uuid.UUID, user_id: uuid.UUID, user: CurrentUser, session: SessionDep
) -> Response:
    await AnalysisService(session).remove_member(user, analysis_id, user_id)
    return Response(status_code=NO_CONTENT)
