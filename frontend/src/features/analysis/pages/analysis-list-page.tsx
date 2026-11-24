import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { FileText, Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { EmptyState } from '@/components/empty-state'
import { PageHeader } from '@/components/page-header'
import { formatDateTime } from '@/lib/dates'
import { useWorkspace } from '@/features/workspaces/workspace-context'
import { CreateAnalysisDialog } from '../components/create-analysis-dialog'
import { useAnalyses } from '../hooks'

export default function AnalysisListPage() {
  const { id: workspaceId, can } = useWorkspace()
  const { data: analyses, isLoading, isError } = useAnalyses(workspaceId)
  const [creating, setCreating] = useState(false)
  const navigate = useNavigate()
  const base = `/w/${workspaceId}/analysis`

  return (
    <div className="grid gap-5">
      <PageHeader title="Анализ ТЗ" description="Разбор требований на структурированные фрагменты" actions={can('member') && <Button onClick={() => setCreating(true)}><Plus className="size-4" /> Новый анализ</Button>} />
      {isLoading && <div className="grid gap-3 sm:grid-cols-2">{[0, 1].map((i) => <Skeleton key={i} className="h-28 rounded-2xl" />)}</div>}
      {isError && <EmptyState icon={FileText} title="Не удалось загрузить анализы" />}
      {!isLoading && !isError && analyses?.length === 0 && <EmptyState icon={FileText} title="Анализов пока нет" action={can('member') && <Button onClick={() => setCreating(true)}>Создать анализ</Button>} />}
      {!isLoading && !isError && analyses && analyses.length > 0 && (
        <div className="grid gap-3 sm:grid-cols-2">
          {analyses.map((analysis) => (
            <Link key={analysis.id} to={`${base}/${analysis.id}`} className="grid gap-2 rounded-2xl bg-card p-4 ring-1 ring-black/5 transition-colors hover:bg-muted dark:ring-white/10">
              <div className="flex items-start justify-between gap-3"><h2 className="font-medium">{analysis.title}</h2><span className="text-xs text-muted-foreground">{analysis.access}</span></div>
              <p className="text-sm text-muted-foreground">{analysis.fragment_count} фрагментов · {formatDateTime(analysis.created_at)}</p>
              <p className="text-xs text-muted-foreground">{analysis.created_by.full_name}</p>
            </Link>
          ))}
        </div>
      )}
      <CreateAnalysisDialog workspaceId={workspaceId} open={creating} onOpenChange={setCreating} onCreated={(id) => navigate(`${base}/${id}`)} />
    </div>
  )
}
