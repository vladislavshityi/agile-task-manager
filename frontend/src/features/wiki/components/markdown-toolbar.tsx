import type { RefObject } from 'react'
import { Bold, Code, Heading1, Heading2, Italic, Link, List, ListChecks, ListOrdered, Quote, type LucideIcon } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface Props {
  textareaRef: RefObject<HTMLTextAreaElement | null>
  value: string
  onChange: (value: string) => void
}

type Edit = (text: string, start: number, end: number) => { text: string; start: number; end: number }

/** Wraps the selection, e.g. `**bold**`; with nothing selected inserts a placeholder. */
const wrap =
  (before: string, after: string, placeholder: string): Edit =>
  (text, start, end) => {
    const selected = text.slice(start, end) || placeholder
    return {
      text: text.slice(0, start) + before + selected + after + text.slice(end),
      start: start + before.length,
      end: start + before.length + selected.length,
    }
  }

/** Puts a prefix (`# `, `- `, `1. `…) at the start of every selected line. */
const prefixLines =
  (prefix: (index: number) => string): Edit =>
  (text, start, end) => {
    const lineStart = text.lastIndexOf('\n', start - 1) + 1
    const lines = text.slice(lineStart, end).split('\n')
    const block = lines.map((line, i) => prefix(i) + line).join('\n')
    return {
      text: text.slice(0, lineStart) + block + text.slice(end),
      start: lineStart,
      end: lineStart + block.length,
    }
  }

const ACTIONS: { icon: LucideIcon; label: string; edit: Edit }[] = [
  { icon: Heading1, label: 'Заголовок', edit: prefixLines(() => '# ') },
  { icon: Heading2, label: 'Подзаголовок', edit: prefixLines(() => '## ') },
  { icon: Bold, label: 'Жирный', edit: wrap('**', '**', 'жирный текст') },
  { icon: Italic, label: 'Курсив', edit: wrap('_', '_', 'курсив') },
  { icon: List, label: 'Список', edit: prefixLines(() => '- ') },
  { icon: ListOrdered, label: 'Нумерованный список', edit: prefixLines((i) => `${i + 1}. `) },
  { icon: ListChecks, label: 'Чек-лист', edit: prefixLines(() => '- [ ] ') },
  { icon: Quote, label: 'Цитата', edit: prefixLines(() => '> ') },
  { icon: Code, label: 'Код', edit: wrap('`', '`', 'код') },
  { icon: Link, label: 'Ссылка', edit: wrap('[', '](https://)', 'текст ссылки') },
]

export function MarkdownToolbar({ textareaRef, value, onChange }: Props) {
  const apply = (edit: Edit) => {
    const el = textareaRef.current
    if (!el) return
    const result = edit(value, el.selectionStart, el.selectionEnd)
    onChange(result.text)
    requestAnimationFrame(() => {
      el.focus()
      el.setSelectionRange(result.start, result.end)
    })
  }

  return (
    <div role="toolbar" aria-label="Форматирование" className="flex flex-wrap gap-0.5">
      {ACTIONS.map(({ icon: Icon, label, edit }) => (
        <Button
          key={label}
          type="button"
          variant="ghost"
          size="icon"
          className="size-8"
          title={label}
          aria-label={label}
          onMouseDown={(e) => e.preventDefault()}
          onClick={() => apply(edit)}
        >
          <Icon className="size-4" />
        </Button>
      ))}
    </div>
  )
}
