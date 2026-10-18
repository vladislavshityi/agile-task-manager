import { useState } from 'react'
import { Check, Plus, Tag } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { ColorPicker } from '@/components/color-picker'
import { errorMessage } from '@/lib/api-client'
import { useWorkspace } from '@/features/workspaces/workspace-context'
import type { Label } from '@/types/api'
import { useCreateLabel, useLabels } from '../hooks'
import { LabelChip } from './task-badges'

interface Props {
  value: Label[]
  disabled?: boolean
  onChange: (ids: string[]) => void
}

function NewLabelForm({ workspaceId }: { workspaceId: string }) {
  const create = useCreateLabel(workspaceId)
  const [name, setName] = useState('')
  const [color, setColor] = useState('#007AFF')

  const submit = () => {
    const value = name.trim()
    if (!value) return
    create.mutate(
      { name: value, color },
      { onSuccess: () => setName(''), onError: (e) => toast.error(errorMessage(e)) },
    )
  }

  return (
    <div className="grid gap-2 border-t border-black/5 p-2 dark:border-white/10">
      <div className="flex gap-1.5">
        <Input
          value={name}
          placeholder="Новая метка"
          className="h-8 rounded-lg"
          onChange={(e) => setName(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), submit())}
        />
        <Button size="icon" variant="secondary" aria-label="Создать метку" onClick={submit} disabled={create.isPending}>
          <Plus className="size-4" />
        </Button>
      </div>
      <ColorPicker value={color} onChange={setColor} />
    </div>
  )
}

export function LabelPicker({ value, disabled, onChange }: Props) {
  const { id, can } = useWorkspace()
  const { data: labels = [] } = useLabels(id)
  const selected = new Set(value.map((l) => l.id))

  const toggle = (labelId: string) => {
    const next = new Set(selected)
    if (next.has(labelId)) next.delete(labelId)
    else next.add(labelId)
    onChange([...next])
  }

  return (
    <div className="flex flex-wrap items-center gap-1.5">
      {value.map((l) => (
        <LabelChip key={l.id} label={l} />
      ))}
      {!disabled && (
        <Popover>
          <PopoverTrigger asChild>
            <Button variant="outline" size="sm" className="rounded-full">
              <Tag className="size-3.5" /> {value.length ? 'Изменить' : 'Добавить'}
            </Button>
          </PopoverTrigger>
          <PopoverContent align="start" className="w-64 rounded-2xl p-0">
            <div className="max-h-56 overflow-y-auto p-1.5">
              {labels.length === 0 && <p className="px-2 py-3 text-sm text-muted-foreground">Меток пока нет</p>}
              {labels.map((l) => (
                <button
                  key={l.id}
                  type="button"
                  onClick={() => toggle(l.id)}
                  className="flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-left text-sm transition-colors duration-150 hover:bg-muted"
                >
                  <span className="size-3 rounded-full" style={{ backgroundColor: l.color }} />
                  <span className="flex-1 truncate">{l.name}</span>
                  {selected.has(l.id) && <Check className="size-4 text-primary" />}
                </button>
              ))}
            </div>
            {can('admin') && <NewLabelForm workspaceId={id} />}
          </PopoverContent>
        </Popover>
      )}
      {disabled && value.length === 0 && <span className="text-sm text-muted-foreground">Нет меток</span>}
    </div>
  )
}
