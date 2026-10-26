import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { BookOpen, ChevronRight, FilePlus, FolderInput, MoreHorizontal, Pencil, Plus, Search, SearchX, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { ConfirmDialog } from '@/components/confirm-dialog'
import { EmptyState } from '@/components/empty-state'
import { NameDialog } from '@/components/name-dialog'
import { PageHeader } from '@/components/page-header'
import { UserAvatar } from '@/components/user-avatar'
import { ApiError, errorMessage } from '@/lib/api-client'
import { formatDateTime } from '@/lib/dates'
import { cn } from '@/lib/utils'
import { useWorkspace } from '@/features/workspaces/workspace-context'
import type { WikiPage, WikiPageSummary } from '@/types/api'
import { WikiMarkdown } from '../components/markdown'
import { MovePageDialog } from '../components/move-page-dialog'
import { WikiEditor } from '../components/wiki-editor'
import { WikiTree } from '../components/wiki-tree'
import { useCreateWikiPage, useDeleteWikiPage, useWikiPage, useWikiPages, useWikiSearch } from '../hooks'
import { ancestors, buildTree, subtreeIds } from '../tree'

function useDebounced(value: string, ms = 250) {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), ms)
    return () => clearTimeout(t)
  }, [value, ms])
  return debounced
}

function PageActions({ page, pages, onAddChild }: { page: WikiPage; pages: WikiPageSummary[]; onAddChild: () => void }) {
  const navigate = useNavigate()
  const remove = useDeleteWikiPage(page.workspace_id)
  const [moving, setMoving] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const nested = subtreeIds(pages, page.id).size - 1

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" size="icon" aria-label="Действия со страницей">
            <MoreHorizontal className="size-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="rounded-xl">
          <DropdownMenuItem onSelect={onAddChild}>
            <FilePlus className="size-4" /> Подстраница
          </DropdownMenuItem>
          <DropdownMenuItem onSelect={() => setMoving(true)}>
            <FolderInput className="size-4" /> Переместить
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem variant="destructive" onSelect={() => setDeleting(true)}>
            <Trash2 className="size-4" /> Удалить
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
      <MovePageDialog key={`${page.id}-${moving}`} page={page} pages={pages} open={moving} onOpenChange={setMoving} />
      <ConfirmDialog
        open={deleting}
        onOpenChange={setDeleting}
        title={`Удалить страницу «${page.title}»?`}
        description={nested > 0 ? `Вместе с ней будут удалены вложенные страницы: ${nested}.` : 'Это действие нельзя отменить.'}
        onConfirm={() =>
          remove.mutate(page.id, {
            onSuccess: () => {
              toast.success('Страница удалена')
              navigate(`/w/${page.workspace_id}/wiki${page.parent_id ? `/${page.parent_id}` : ''}`, { replace: true })
            },
            onError: (e) => toast.error(errorMessage(e)),
          })
        }
      />
    </>
  )
}

function PageView({ pageId, pages, onAddChild }: { pageId: string; pages: WikiPageSummary[]; onAddChild: (parentId: string) => void }) {
  const { id: workspaceId, can } = useWorkspace()
  const [params, setParams] = useSearchParams()
  const { data: page, isLoading, error } = useWikiPage(pageId)
  const editing = params.get('edit') === '1' && can('member')
  const setEditing = (on: boolean) => setParams(on ? { edit: '1' } : {}, { replace: true })
  const base = `/w/${workspaceId}/wiki`

  if (isLoading) {
    return (
      <div className="grid gap-4">
        <Skeleton className="h-9 w-72 rounded-xl" />
        <Skeleton className="h-64 rounded-2xl" />
      </div>
    )
  }

  if (error || !page || page.workspace_id !== workspaceId) {
    const missing = error instanceof ApiError ? error.status === 404 : true
    return (
      <EmptyState
        icon={SearchX}
        title={missing ? 'Страница не найдена' : 'Не удалось загрузить страницу'}
        action={
          <Button asChild>
            <Link to={base}>К базе знаний</Link>
          </Button>
        }
      />
    )
  }

  if (editing) return <WikiEditor key={page.id} page={page} onDone={() => setEditing(false)} />

  const children = pages.filter((p) => p.parent_id === page.id)

  return (
    <article className="grid gap-5">
      <nav aria-label="Путь" className="flex flex-wrap items-center gap-1 text-xs text-muted-foreground">
        <Link to={base} className="hover:text-foreground">
          База знаний
        </Link>
        {ancestors(pages, page.id).map((a) => (
          <span key={a.id} className="flex items-center gap-1">
            <ChevronRight className="size-3" />
            <Link to={`${base}/${a.id}`} className="hover:text-foreground">
              {a.title}
            </Link>
          </span>
        ))}
      </nav>
      <PageHeader
        title={page.title}
        actions={
          can('member') && (
            <>
              <Button variant="outline" onClick={() => setEditing(true)}>
                <Pencil className="size-4" /> Редактировать
              </Button>
              <PageActions page={page} pages={pages} onAddChild={() => onAddChild(page.id)} />
            </>
          )
        }
      />
      <div className="-mt-3 flex items-center gap-2 text-xs text-muted-foreground">
        <UserAvatar user={page.updated_by} className="size-5" />
        <span>
          {page.updated_by.full_name} · {formatDateTime(page.updated_at)}
        </span>
      </div>
      {page.content.trim() ? (
        <WikiMarkdown content={page.content} />
      ) : (
        <EmptyState
          icon={BookOpen}
          title="Страница пока пустая"
          action={can('member') && <Button onClick={() => setEditing(true)}>Написать</Button>}
        />
      )}
      {children.length > 0 && (
        <section className="grid gap-2 border-t pt-4">
          <h2 className="text-sm font-semibold">Подстраницы</h2>
          <div className="grid gap-2 sm:grid-cols-2">
            {children.map((c) => (
              <Link
                key={c.id}
                to={`${base}/${c.id}`}
                className="rounded-xl bg-card px-3 py-2 text-sm font-medium ring-1 ring-black/5 transition-colors hover:bg-muted dark:ring-white/10"
              >
                {c.title}
              </Link>
            ))}
          </div>
        </section>
      )}
    </article>
  )
}

function WikiHome({ pages, onCreate }: { pages: WikiPageSummary[]; onCreate: () => void }) {
  const { id, can } = useWorkspace()
  const roots = pages.filter((p) => !p.parent_id)
  const recent = [...pages].sort((a, b) => b.updated_at.localeCompare(a.updated_at)).slice(0, 6)

  if (pages.length === 0) {
    return (
      <EmptyState
        icon={BookOpen}
        title={
          can('member')
            ? 'Соберите здесь знания команды: инструкции, регламенты, заметки и решения'
            : 'В базе знаний пока нет страниц'
        }
        action={can('member') && <Button onClick={onCreate}>Создать первую страницу</Button>}
      />
    )
  }

  return (
    <div className="grid gap-6">
      <PageHeader
        title="База знаний"
        description={`Страниц: ${pages.length} · разделов: ${roots.length}`}
        actions={
          can('member') && (
            <Button onClick={onCreate}>
              <Plus className="size-4" /> Новая страница
            </Button>
          )
        }
      />
      <section className="grid gap-3">
        <h2 className="text-sm font-semibold">Недавно обновлённые</h2>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {recent.map((p) => (
            <Link
              key={p.id}
              to={`/w/${id}/wiki/${p.id}`}
              className="rounded-2xl bg-card p-4 ring-1 ring-black/5 transition-all duration-150 ease-out hover:-translate-y-0.5 hover:shadow-lg dark:ring-white/10"
            >
              <h3 className="truncate font-semibold tracking-tight">{p.title}</h3>
              <p className="mt-1 text-xs text-muted-foreground">Обновлено {formatDateTime(p.updated_at)}</p>
            </Link>
          ))}
        </div>
      </section>
    </div>
  )
}

export default function WikiPageRoute() {
  const { pageId } = useParams()
  const { id: workspaceId, can } = useWorkspace()
  const navigate = useNavigate()
  const { data: pages, isLoading } = useWikiPages(workspaceId)
  const create = useCreateWikiPage(workspaceId)
  const [creatingIn, setCreatingIn] = useState<string | null | undefined>(undefined)
  const [query, setQuery] = useState('')
  const q = useDebounced(query.trim())
  const search = useWikiSearch(workspaceId, q)
  const tree = useMemo(() => buildTree(pages ?? []), [pages])
  const base = `/w/${workspaceId}/wiki`
  const parentTitle = pages?.find((p) => p.id === creatingIn)?.title

  return (
    <div className="mx-auto grid max-w-6xl gap-6 md:grid-cols-[16rem_minmax(0,1fr)]">
      <aside className={cn('grid content-start gap-3', pageId && 'hidden md:grid')}>
        <div className="flex items-center justify-between gap-2">
          <h2 className="text-sm font-semibold">Страницы</h2>
          {can('member') && (
            <Button variant="ghost" size="icon" className="size-7" title="Новая страница" onClick={() => setCreatingIn(null)}>
              <Plus className="size-4" />
            </Button>
          )}
        </div>
        <div className="relative">
          <Search className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Поиск по базе…"
            aria-label="Поиск по базе знаний"
            className="pl-8"
          />
        </div>
        {isLoading && [0, 1, 2].map((i) => <Skeleton key={i} className="h-7 rounded-lg" />)}
        {q ? (
          <ul className="grid gap-0.5">
            {search.data?.length === 0 && <li className="px-2 text-xs text-muted-foreground">Ничего не найдено</li>}
            {search.data?.map((p) => (
              <li key={p.id}>
                <Link
                  to={`${base}/${p.id}`}
                  className={cn('block truncate rounded-lg px-2 py-1.5 text-sm hover:bg-muted', p.id === pageId && 'bg-muted font-medium')}
                >
                  {p.title}
                </Link>
              </li>
            ))}
          </ul>
        ) : (
          <WikiTree nodes={tree} basePath={base} activeId={pageId} canEdit={can('member')} onAddChild={setCreatingIn} />
        )}
      </aside>
      <main className="min-w-0">
        {pageId ? (
          <PageView pageId={pageId} pages={pages ?? []} onAddChild={setCreatingIn} />
        ) : (
          !isLoading && <WikiHome pages={pages ?? []} onCreate={() => setCreatingIn(null)} />
        )}
      </main>
      <NameDialog
        open={creatingIn !== undefined}
        onOpenChange={(open) => !open && setCreatingIn(undefined)}
        title={parentTitle ? `Подстраница в «${parentTitle}»` : 'Новая страница'}
        submitLabel="Создать"
        onSubmit={async (title) => {
          const page = await create.mutateAsync({ title, parent_id: creatingIn ?? null })
          navigate(`${base}/${page.id}?edit=1`)
        }}
      />
    </div>
  )
}
