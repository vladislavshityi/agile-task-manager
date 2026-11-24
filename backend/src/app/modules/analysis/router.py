import uuid

from fastapi import APIRouter, Response, status

from app.core.deps import CurrentUser, SessionDep
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


@router.post(
    "/workspaces/{workspace_id}/analyses",
    response_model=AnalysisRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_analysis(
    workspace_id: uuid.UUID, data: AnalysisCreate, user: CurrentUser, session: SessionDep
) -> AnalysisRead:
    return await AnalysisService(session).create(user, workspace_id, data)


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
