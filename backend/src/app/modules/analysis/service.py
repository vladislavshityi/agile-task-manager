import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import Forbidden, NotFound, ValidationError
from app.modules.analysis.models import (
    Access,
    Analysis,
    AnalysisMember,
    FragmentKind,
    SpecFragment,
    Visibility,
)
from app.modules.analysis.repository import AnalysisRepository
from app.modules.analysis.schemas import (
    AnalysisCreate,
    AnalysisMemberRead,
    AnalysisRead,
    AnalysisSummary,
    AnalysisUpdate,
)
from app.modules.analysis.splitter import normalize, split
from app.modules.users.models import User
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserRead
from app.modules.workspaces.models import Role
from app.modules.workspaces.repository import WorkspaceRepository
from app.modules.workspaces.service import require_role

MAX_FRAGMENTS = 2000


def resolve_access(
    role: Role, analysis: Analysis, user_id: uuid.UUID, member_can_edit: bool | None
) -> Access | None:
    """Access level of a workspace member to an analysis, or None if it is hidden from them."""
    if role.rank >= Role.admin.rank:
        return Access.manage
    if analysis.created_by_id == user_id and role.rank >= Role.member.rank:
        return Access.manage
    if member_can_edit is not None:
        if member_can_edit and role.rank >= Role.member.rank:
            return Access.edit
        return Access.read
    if analysis.visibility == Visibility.workspace:
        return Access.read
    return None


def _not_found() -> NotFound:
    return NotFound("Analysis not found", "analysis_not_found")


class AnalysisService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = AnalysisRepository(session)

    async def _access(self, user: User, analysis_id: uuid.UUID, min_access: Access) -> Analysis:
        analysis, _ = await self._access_level(user, analysis_id, min_access)
        return analysis

    async def _access_level(
        self, user: User, analysis_id: uuid.UUID, min_access: Access
    ) -> tuple[Analysis, Access]:
        analysis = await self.repo.get(analysis_id)
        if analysis is None:
            raise _not_found()
        membership = await WorkspaceRepository(self.session).get_membership(
            analysis.workspace_id, user.id
        )
        if membership is None:
            raise _not_found()
        entry = await self.repo.get_member(analysis.id, user.id)
        access = resolve_access(
            membership.role, analysis, user.id, entry.can_edit if entry else None
        )
        if access is None:
            raise _not_found()
        if access.rank < min_access.rank:
            raise Forbidden("Insufficient access to this analysis", "analysis_access_denied")
        return analysis, access

    async def _read(self, analysis_id: uuid.UUID, access: Access) -> AnalysisRead:
        analysis = await self.repo.get_full(analysis_id)
        if analysis is None:
            raise _not_found()
        return AnalysisRead(
            id=analysis.id,
            workspace_id=analysis.workspace_id,
            title=analysis.title,
            visibility=analysis.visibility,
            created_by=UserRead.model_validate(analysis.created_by),
            created_at=analysis.created_at,
            fragment_count=len(analysis.fragments),
            access=access,
            text=analysis.text,
            fragments=analysis.fragments,  # type: ignore[arg-type]
            members=[AnalysisMemberRead.model_validate(m) for m in analysis.members],
        )

    async def create(
        self, user: User, workspace_id: uuid.UUID, data: AnalysisCreate
    ) -> AnalysisRead:
        await require_role(self.session, workspace_id, user.id, Role.member)
        text = normalize(data.text)
        fragments = split(text)
        if not any(f.kind != FragmentKind.heading for f in fragments):
            raise ValidationError("The specification has no text to analyze", "spec_empty")
        if len(fragments) > MAX_FRAGMENTS:
            raise ValidationError(
                f"The specification has more than {MAX_FRAGMENTS} fragments",
                "spec_too_many_fragments",
            )
        analysis = await self.repo.add(
            Analysis(
                workspace_id=workspace_id,
                title=data.title,
                text=text,
                created_by_id=user.id,
            ),
            [
                SpecFragment(
                    ordinal=index,
                    kind=FragmentKind(f.kind),
                    section=f.section,
                    heading_path=f.heading_path,
                    context=f.context,
                    text=f.text,
                    start=f.start,
                    end=f.end,
                )
                for index, f in enumerate(fragments, start=1)
            ],
        )
        await self.session.commit()
        return await self._read(analysis.id, Access.manage)

    async def list_analyses(self, user: User, workspace_id: uuid.UUID) -> list[AnalysisSummary]:
        membership = await require_role(self.session, workspace_id, user.id, Role.viewer)
        rows = await self.repo.list_with_counts(workspace_id)
        flags = await self.repo.member_flags(user.id, [a.id for a, _ in rows])
        summaries = []
        for analysis, count in rows:
            access = resolve_access(membership.role, analysis, user.id, flags.get(analysis.id))
            if access is None:
                continue
            summaries.append(
                AnalysisSummary(
                    id=analysis.id,
                    workspace_id=analysis.workspace_id,
                    title=analysis.title,
                    visibility=analysis.visibility,
                    created_by=UserRead.model_validate(analysis.created_by),
                    created_at=analysis.created_at,
                    fragment_count=count,
                    access=access,
                )
            )
        return summaries

    async def get(self, user: User, analysis_id: uuid.UUID) -> AnalysisRead:
        _, access = await self._access_level(user, analysis_id, Access.read)
        return await self._read(analysis_id, access)

    async def update(
        self, user: User, analysis_id: uuid.UUID, data: AnalysisUpdate
    ) -> AnalysisRead:
        analysis = await self._access(user, analysis_id, Access.manage)
        if data.title is not None:
            analysis.title = data.title
        if data.visibility is not None:
            analysis.visibility = data.visibility
        await self.session.commit()
        return await self._read(analysis_id, Access.manage)

    async def delete(self, user: User, analysis_id: uuid.UUID) -> None:
        await self._access(user, analysis_id, Access.manage)
        await self.repo.delete(analysis_id)
        await self.session.commit()

    async def set_member(
        self, user: User, analysis_id: uuid.UUID, member_id: uuid.UUID, can_edit: bool
    ) -> AnalysisMemberRead:
        analysis = await self._access(user, analysis_id, Access.manage)
        if member_id == analysis.created_by_id:
            raise ValidationError("The author already has full access", "author_is_member")
        target = await WorkspaceRepository(self.session).get_membership(
            analysis.workspace_id, member_id
        )
        if target is None:
            raise ValidationError("User is not a workspace member", "user_not_member")
        member = await self.repo.get_member(analysis_id, member_id)
        if member is None:
            self.session.add(
                AnalysisMember(analysis_id=analysis_id, user_id=member_id, can_edit=can_edit)
            )
        else:
            member.can_edit = can_edit
        await self.session.commit()
        member_user = await UserRepository(self.session).get(member_id)
        return AnalysisMemberRead(user=UserRead.model_validate(member_user), can_edit=can_edit)

    async def remove_member(self, user: User, analysis_id: uuid.UUID, member_id: uuid.UUID) -> None:
        await self._access(user, analysis_id, Access.manage)
        if await self.repo.get_member(analysis_id, member_id) is None:
            raise NotFound("Analysis member not found", "analysis_member_not_found")
        await self.repo.delete_member(analysis_id, member_id)
        await self.session.commit()
