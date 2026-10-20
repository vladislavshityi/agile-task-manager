import { useState } from 'react'
import { Check, Sparkles } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { Textarea } from '@/components/ui/textarea'
import { FormField } from '@/components/form-field'
import { errorMessage } from '@/lib/api-client'
import { PRIORITY_META } from '@/lib/design'
import { cn } from '@/lib/utils'
import { useCreateTask } from '@/features/tasks/hooks'
import type { Board, TaskDraft } from '@/types/api'
import { useAIStatus, useGenerateTasks } from '../hooks'
import { AIUnavailable } from './ai-unavailable'

const COUNTS = [3, 5, 8]

interface Props {
  board: Board
  open: boolean
  onOpenChange: (open: boolean) => void
}

/** Describe a goal → the local model drafts tasks → the user picks which ones to add. */
export function GenerateTasksDialog({ board, open, onOpenChange }: Props) {
  const status = useAIStatus()
  const generate = useGenerateTasks(board.id)
  const create = useCreateTask(board.id)
  const [prompt, setPrompt] = useState('')
  const [count, setCount] = useState(5)
  const [columnId, setColumnId] = useState(board.columns[0]?.id ?? '')
  const [drafts, setDrafts] = useState<TaskDraft[] | null>(null)
  const [picked, setPicked] = useState<Set<number>>(new Set())
  const [saving, setSaving] = useState(false)

  // The chosen column may have been deleted since; fall back to the first one.
  const targetId = board.columns.some((c) => c.id === columnId) ? columnId : (board.columns[0]?.id ?? '')

  const close = () => {
    onOpenChange(false)
    setDrafts(null)
    generate.reset()
  }

  const run = () =>
    generate.mutate(
      { prompt: prompt.trim(), count },
      {
        onSuccess: ({ tasks }) => {
          setDrafts(tasks)
          setPicked(new Set(tasks.map((_, i) => i)))
        },
      },
    )

  const toggle = (index: number) =>
    setPicked((prev) => {
      const next = new Set(prev)
      if (next.has(index)) next.delete(index)
      else next.add(index)
      return next
    })

  const save = async () => {
    if (!drafts) return
    setSaving(true)
    let created = 0
    try {
      // One by one so tasks land in the column in the suggested order.
      for (const [index, draft] of drafts.entries()) {
        if (!picked.has(index)) continue
        await create.mutateAsync({ columnId: targetId, ...draft })
        created += 1
      }
      toast.success(`Добавлено задач: ${created}`)
      setPrompt('')
      close()
    } catch (err) {
      toast.error(created ? `Добавлено ${created}, затем ошибка: ${errorMessage(err)}` : errorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  const unavailable = status.data && !status.data.available

  return (
    <Dialog open={open} onOpenChange={(next) => !next && !saving && close()}>
      <DialogContent className="max-h-[90svh] overflow-y-auto rounded-2xl sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="size-4 text-primary" /> Задачи с помощью ИИ
          </DialogTitle>
          <DialogDescription>Опишите цель — локальная модель предложит задачи, а вы выберете нужные.</DialogDescription>
        </DialogHeader>

        {unavailable ? (
          <AIUnavailable status={status.data} />
        ) : drafts === null ? (
          <form
            id="ai-generate-form"
            className="grid gap-4"
            onSubmit={(e) => {
              e.preventDefault()
              run()
            }}
          >
            <FormField
              label="Цель"
              htmlFor="ai-goal"
              error={generate.error ? errorMessage(generate.error) : undefined}
              hint="Например: «Подготовить релиз мобильного приложения в App Store»"
            >
              <Textarea
                id="ai-goal"
                rows={3}
                autoFocus
                maxLength={1000}
                value={prompt}
                disabled={generate.isPending}
                onChange={(e) => setPrompt(e.target.value)}
              />
            </FormField>
            <FormField label="Сколько задач">
              <Select value={String(count)} onValueChange={(v) => setCount(Number(v))} disabled={generate.isPending}>
                <SelectTrigger className="h-9 w-full rounded-xl">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="rounded-xl">
                  {COUNTS.map((n) => (
                    <SelectItem key={n} value={String(n)}>
                      До {n}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </FormField>
            {generate.isPending && (
              <div className="grid gap-2" aria-label="Модель думает">
                {[0, 1, 2].map((i) => (
                  <Skeleton key={i} className="h-14 rounded-xl" />
                ))}
              </div>
            )}
          </form>
        ) : (
          <div className="grid gap-4">
            <ul className="grid gap-2">
              {drafts.map((draft, i) => {
                const on = picked.has(i)
                return (
                  <li key={i}>
                    <button
                      type="button"
                      aria-pressed={on}
                      onClick={() => toggle(i)}
                      className={cn(
                        'flex w-full gap-3 rounded-xl border p-3 text-left transition-colors duration-150',
                        on ? 'border-primary/40 bg-primary/5' : 'border-black/5 opacity-60 dark:border-white/10',
                      )}
                    >
                      <span
                        className={cn(
                          'mt-0.5 flex size-4 shrink-0 items-center justify-center rounded-[5px] border',
                          on ? 'border-primary bg-primary text-primary-foreground' : 'border-muted-foreground/40',
                        )}
                      >
                        {on && <Check className="size-3" />}
                      </span>
                      <span className="grid min-w-0 gap-1">
                        <span className="flex items-center gap-2 text-sm font-medium">
                          <span
                            className="size-2 shrink-0 rounded-full"
                            style={{ backgroundColor: PRIORITY_META[draft.priority].color }}
                            title={PRIORITY_META[draft.priority].label}
                          />
                          {draft.title}
                        </span>
                        {draft.description && (
                          <span className="text-xs text-muted-foreground">{draft.description}</span>
                        )}
                      </span>
                    </button>
                  </li>
                )
              })}
            </ul>
            <FormField label="Добавить в колонку">
              <Select value={targetId} onValueChange={setColumnId}>
                <SelectTrigger className="h-9 w-full rounded-xl">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="rounded-xl">
                  {board.columns.map((c) => (
                    <SelectItem key={c.id} value={c.id}>
                      <span className="size-2 rounded-full" style={{ backgroundColor: c.color }} />
                      {c.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </FormField>
          </div>
        )}

        <DialogFooter>
          {drafts === null ? (
            <>
              <Button type="button" variant="ghost" onClick={close}>
                Отмена
              </Button>
              <Button
                type="submit"
                form="ai-generate-form"
                disabled={!!unavailable || prompt.trim().length < 3 || generate.isPending}
              >
                <Sparkles /> {generate.isPending ? 'Модель думает…' : 'Предложить задачи'}
              </Button>
            </>
          ) : (
            <>
              <Button type="button" variant="ghost" disabled={saving} onClick={() => setDrafts(null)}>
                Назад
              </Button>
              <Button type="button" disabled={saving || picked.size === 0 || !targetId} onClick={() => void save()}>
                Добавить {picked.size}
              </Button>
            </>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
