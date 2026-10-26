import uuid

from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.wiki.models import WikiPage


class WikiRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, page: WikiPage) -> WikiPage:
        self.session.add(page)
        await self.session.flush()
        return page

    async def get(self, page_id: uuid.UUID) -> WikiPage | None:
        return await self.session.get(WikiPage, page_id)

    async def get_full(self, page_id: uuid.UUID) -> WikiPage | None:
        result = await self.session.execute(
            select(WikiPage)
            .where(WikiPage.id == page_id)
            .options(selectinload(WikiPage.created_by), selectinload(WikiPage.updated_by))
            .execution_options(populate_existing=True)
        )
        return result.scalar_one_or_none()

    async def delete(self, page_id: uuid.UUID) -> None:
        await self.session.execute(delete(WikiPage).where(WikiPage.id == page_id))

    async def list_pages(self, workspace_id: uuid.UUID, query: str | None = None) -> list[WikiPage]:
        stmt = select(WikiPage).where(WikiPage.workspace_id == workspace_id)
        if query:
            pattern = f"%{query}%"
            stmt = stmt.where(or_(WikiPage.title.ilike(pattern), WikiPage.content.ilike(pattern)))
        result = await self.session.execute(stmt.order_by(WikiPage.position, WikiPage.created_at))
        return list(result.scalars())

    async def list_children(
        self, workspace_id: uuid.UUID, parent_id: uuid.UUID | None
    ) -> list[WikiPage]:
        parent = (
            WikiPage.parent_id.is_(None) if parent_id is None else WikiPage.parent_id == parent_id
        )
        result = await self.session.execute(
            select(WikiPage)
            .where(WikiPage.workspace_id == workspace_id, parent)
            .order_by(WikiPage.position, WikiPage.created_at)
        )
        return list(result.scalars())
