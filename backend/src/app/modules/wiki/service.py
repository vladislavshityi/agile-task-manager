import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import utcnow
from app.core.errors import NotFound, ValidationError
from app.modules.users.models import User
from app.modules.wiki.models import WikiPage
from app.modules.wiki.repository import WikiRepository
from app.modules.wiki.schemas import WikiPageCreate, WikiPageUpdate
from app.modules.workspaces.models import Role
from app.modules.workspaces.service import require_role


class WikiService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = WikiRepository(session)

    async def _page(self, user: User, page_id: uuid.UUID, min_role: Role) -> WikiPage:
        page = await self.repo.get(page_id)
        if page is None:
            raise NotFound("Page not found", "wiki_page_not_found")
        await require_role(self.session, page.workspace_id, user.id, min_role)
        return page

    async def _full(self, page_id: uuid.UUID) -> WikiPage:
        page = await self.repo.get_full(page_id)
        if page is None:
            raise NotFound("Page not found", "wiki_page_not_found")
        return page

    async def _check_parent(self, workspace_id: uuid.UUID, parent_id: uuid.UUID | None) -> None:
        if parent_id is None:
            return
        parent = await self.repo.get(parent_id)
        if parent is None or parent.workspace_id != workspace_id:
            raise NotFound("Parent page not found", "wiki_parent_not_found")

    async def list_pages(
        self, user: User, workspace_id: uuid.UUID, query: str | None = None
    ) -> list[WikiPage]:
        await require_role(self.session, workspace_id, user.id, Role.viewer)
        return await self.repo.list_pages(workspace_id, query.strip() if query else None)

    async def create_page(
        self, user: User, workspace_id: uuid.UUID, data: WikiPageCreate
    ) -> WikiPage:
        await require_role(self.session, workspace_id, user.id, Role.member)
        await self._check_parent(workspace_id, data.parent_id)
        position = len(await self.repo.list_children(workspace_id, data.parent_id))
        page = await self.repo.add(
            WikiPage(
                workspace_id=workspace_id,
                parent_id=data.parent_id,
                title=data.title,
                content=data.content,
                position=position,
                created_by_id=user.id,
                updated_by_id=user.id,
            )
        )
        await self.session.commit()
        return await self._full(page.id)

    async def get_page(self, user: User, page_id: uuid.UUID) -> WikiPage:
        await self._page(user, page_id, Role.viewer)
        return await self._full(page_id)

    async def update_page(self, user: User, page_id: uuid.UUID, data: WikiPageUpdate) -> WikiPage:
        page = await self._page(user, page_id, Role.member)
        if data.title is not None:
            page.title = data.title
        if data.content is not None:
            page.content = data.content
        page.updated_by_id = user.id
        page.updated_at = utcnow()
        await self.session.commit()
        return await self._full(page_id)

    async def move_page(
        self, user: User, page_id: uuid.UUID, parent_id: uuid.UUID | None, position: int
    ) -> WikiPage:
        page = await self._page(user, page_id, Role.member)
        await self._check_parent(page.workspace_id, parent_id)
        ancestor_id = parent_id
        while ancestor_id is not None:
            if ancestor_id == page.id:
                raise ValidationError("A page cannot be moved inside itself", "wiki_cyclic_parent")
            ancestor = await self.repo.get(ancestor_id)
            ancestor_id = ancestor.parent_id if ancestor else None

        old_parent_id = page.parent_id
        page.parent_id = parent_id
        children = await self.repo.list_children(page.workspace_id, parent_id)
        siblings = [p for p in children if p.id != page.id]
        siblings.insert(min(position, len(siblings)), page)
        for index, sibling in enumerate(siblings):
            sibling.position = index
        if old_parent_id != parent_id:
            old_siblings = await self.repo.list_children(page.workspace_id, old_parent_id)
            for index, sibling in enumerate(p for p in old_siblings if p.id != page.id):
                sibling.position = index
        await self.session.commit()
        return await self._full(page_id)

    async def delete_page(self, user: User, page_id: uuid.UUID) -> None:
        page = await self._page(user, page_id, Role.member)
        await self.repo.delete(page_id)
        siblings = await self.repo.list_children(page.workspace_id, page.parent_id)
        for index, sibling in enumerate(siblings):
            sibling.position = index
        await self.session.commit()
