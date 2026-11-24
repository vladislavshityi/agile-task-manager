import { Link, useParams } from 'react-router-dom'
import { FileText, SearchX } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { EmptyState } from '@/components/empty-state'
import { PageHeader } from '@/components/page-header'
import { ApiError } from '@/lib/api-client'
import { formatDateTime } from '@/lib/dates'
import { useWorkspace } from '@/features/workspaces/workspace-context'
import { useAnalysis } from '../hooks'
import type { SpecFragment } from '@/types/api'

function FragmentGroup({ title, fragments }: { title: string; fragments: SpecFragment[] }) {
  return (
    <section className="grid gap-2">
      <h2 className="text-sm font-semibold">{title}</h2>
      <div className="grid gap-2">
        {fragments.map((fragment) => (
          <article key={fragment.id} className="rounded-xl bg-card p-3 ring-1 ring-black/5 dark:ring-white/10">
            <div className="mb-1 flex items-center gap-2 text-xs text-muted-foreground">
              <span>{fragment.kind === 'heading' ? 'Заголовок' : fragment.kind === 'list_item' ? 'Пункт' : 'Текст'}</span>
              {fragment.section && <span>· {fragment.section}</span>}
            </div>
            {fragment.context && <p className="mb-1 text-xs text-muted-foreground">{fragment.context}</p>}
            <p className={fragment.kind === 'heading' ? 'font-medium' : undefined}>{fragment.text}</p>
          </article>
        ))}
      </div>
    </section>
  )
}

export default function AnalysisPage() {
  const { analysisId = '' } = useParams()
  const { id: workspaceId } = useWorkspace()
  const { data: analysis, isLoading, error } = useAnalysis(analysisId)
  const base = `/w/${workspaceId}/analysis`

  if (isLoading) return <div className="grid gap-4"><Skeleton className="h-10 w-72 rounded-xl" /><Skeleton className="h-64 rounded-2xl" /></div>
  if (error || !analysis || analysis.workspace_id !== workspaceId) {
    const missing = error instanceof ApiError ? error.status === 404 : true
    return <EmptyState icon={SearchX} title={missing ? 'Анализ не найден' : 'Не удалось загрузить анализ'} action={<Button asChild><Link to={base}>К анализам</Link></Button>} />
  }

  const groups = new Map<string, SpecFragment[]>()
  for (const fragment of analysis.fragments) {
    const key = fragment.heading_path || fragment.section || 'Без раздела'
    const group = groups.get(key) ?? []
    group.push(fragment)
    groups.set(key, group)
  }

  return (
    <div className="grid gap-5">
      <Link to={base} className="text-sm text-muted-foreground hover:text-foreground">← Все анализы</Link>
      <PageHeader title={analysis.title} description={`Создан ${formatDateTime(analysis.created_at)} · ${analysis.created_by.full_name}`} />
      <div className="flex items-center gap-2 text-xs text-muted-foreground"><FileText className="size-4" />{analysis.fragment_count} фрагментов · Доступ: {analysis.access}</div>
      <div className="grid gap-6">{Array.from(groups, ([title, fragments]) => <FragmentGroup key={title} title={title} fragments={fragments} />)}</div>
    </div>
  )
}
