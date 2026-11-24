import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.analysis.models import Analysis, AnalysisMember, SpecFragment


class AnalysisRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, analysis: Analysis, fragments: list[SpecFragment]) -> Analysis:
        self.session.add(analysis)
        await self.session.flush()
        for fragment in fragments:
            fragment.analysis_id = analysis.id
        self.session.add_all(fragments)
        await self.session.flush()
        return analysis

    async def get(self, analysis_id: uuid.UUID) -> Analysis | None:
        return await self.session.get(Analysis, analysis_id)

    async def get_full(self, analysis_id: uuid.UUID) -> Analysis | None:
        result = await self.session.execute(
            select(Analysis)
            .where(Analysis.id == analysis_id)
            .options(
                selectinload(Analysis.created_by),
                selectinload(Analysis.fragments),
                selectinload(Analysis.members).selectinload(AnalysisMember.user),
            )
            .execution_options(populate_existing=True)
        )
        return result.scalar_one_or_none()

    async def delete(self, analysis_id: uuid.UUID) -> None:
        await self.session.execute(delete(Analysis).where(Analysis.id == analysis_id))

    async def list_with_counts(self, workspace_id: uuid.UUID) -> list[tuple[Analysis, int]]:
        count = (
            select(func.count(SpecFragment.id))
            .where(SpecFragment.analysis_id == Analysis.id)
            .correlate(Analysis)
            .scalar_subquery()
        )
        result = await self.session.execute(
            select(Analysis, count)
            .where(Analysis.workspace_id == workspace_id)
            .options(selectinload(Analysis.created_by))
            .order_by(Analysis.created_at.desc())
        )
        return [(analysis, total) for analysis, total in result.all()]

    async def get_member(self, analysis_id: uuid.UUID, user_id: uuid.UUID) -> AnalysisMember | None:
        return await self.session.get(AnalysisMember, (analysis_id, user_id))

    async def member_flags(
        self, user_id: uuid.UUID, analysis_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, bool]:
        result = await self.session.execute(
            select(AnalysisMember.analysis_id, AnalysisMember.can_edit).where(
                AnalysisMember.user_id == user_id, AnalysisMember.analysis_id.in_(analysis_ids)
            )
        )
        return {analysis_id: can_edit for analysis_id, can_edit in result.all()}

    async def delete_member(self, analysis_id: uuid.UUID, user_id: uuid.UUID) -> None:
        await self.session.execute(
            delete(AnalysisMember).where(
                AnalysisMember.analysis_id == analysis_id, AnalysisMember.user_id == user_id
            )
        )
