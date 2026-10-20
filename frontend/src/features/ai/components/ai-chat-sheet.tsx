import { useEffect, useRef, useState } from 'react'
import { ArrowUp, RotateCcw, Sparkles, Square } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from '@/components/ui/sheet'
import { Textarea } from '@/components/ui/textarea'
import { errorMessage } from '@/lib/api-client'
import { cn } from '@/lib/utils'
import type { ChatMessage } from '@/types/api'
import { aiApi } from '../api'
import { useAIStatus } from '../hooks'
import { AIUnavailable } from './ai-unavailable'

const SUGGESTIONS = [
  'Сделай краткую сводку по доске',
  'Какие задачи просрочены или горят?',
  'Что взять в работу первым?',
  'У кого из исполнителей больше всего задач?',
]
// The API accepts at most 20 messages; keep the latest ones.
const HISTORY_LIMIT = 20

interface Props {
  boardId: string
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function AIChatSheet({ boardId, open, onOpenChange }: Props) {
  const status = useAIStatus()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [streaming, setStreaming] = useState(false)
  const abort = useRef<AbortController | null>(null)
  const bottom = useRef<HTMLDivElement>(null)

  useEffect(() => () => abort.current?.abort(), [])
  useEffect(() => {
    bottom.current?.scrollIntoView({ block: 'end' })
  }, [messages])

  const ask = async (text: string) => {
    const question = text.trim()
    if (!question || streaming) return
    const history: ChatMessage[] = [...messages, { role: 'user' as const, content: question }].slice(-HISTORY_LIMIT)
    setMessages([...history, { role: 'assistant', content: '' }])
    setInput('')
    setError(null)
    setStreaming(true)
    const controller = new AbortController()
    abort.current = controller
    try {
      for await (const delta of aiApi.chat(boardId, history, controller.signal)) {
        setMessages((prev) => {
          const last = prev[prev.length - 1]
          return [...prev.slice(0, -1), { ...last, content: last.content + delta }]
        })
      }
    } catch (err) {
      if (!controller.signal.aborted) setError(errorMessage(err))
    } finally {
      // Drop an assistant bubble that never received any text.
      setMessages((prev) => (prev[prev.length - 1]?.content === '' ? prev.slice(0, -1) : prev))
      setStreaming(false)
    }
  }

  const reset = () => {
    abort.current?.abort()
    setMessages([])
    setError(null)
  }

  const available = status.data?.available

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="flex w-full flex-col gap-0 sm:max-w-md">
        <SheetHeader className="border-b border-black/5 dark:border-white/10">
          <SheetTitle className="flex items-center gap-2">
            <Sparkles className="size-4 text-primary" /> ИИ-ассистент
          </SheetTitle>
          <SheetDescription>
            Локальная модель {status.data?.model ?? ''} видит задачи этой доски. Данные не покидают ваш компьютер.
          </SheetDescription>
        </SheetHeader>

        <div className="flex-1 overflow-y-auto px-4 py-4">
          {status.data && !available ? (
            <AIUnavailable status={status.data} />
          ) : messages.length === 0 ? (
            <div className="grid gap-2">
              <p className="text-sm text-muted-foreground">Спросите о задачах на доске, например:</p>
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => void ask(s)}
                  className="rounded-xl border border-black/5 bg-card px-3 py-2 text-left text-sm transition-colors duration-150 hover:bg-muted dark:border-white/10"
                >
                  {s}
                </button>
              ))}
            </div>
          ) : (
            <div className="grid gap-3" aria-live="polite">
              {messages.map((m, i) => (
                <div
                  key={i}
                  className={cn(
                    'max-w-[85%] rounded-2xl px-3.5 py-2 text-sm whitespace-pre-wrap',
                    m.role === 'user' ? 'justify-self-end bg-primary text-primary-foreground' : 'justify-self-start bg-muted',
                  )}
                >
                  {m.content || <span className="inline-block animate-pulse text-muted-foreground">Думаю…</span>}
                </div>
              ))}
              {error && <p role="alert" className="text-sm text-destructive">{error}</p>}
              <div ref={bottom} />
            </div>
          )}
        </div>

        <form
          className="grid gap-2 border-t border-black/5 p-4 dark:border-white/10"
          onSubmit={(e) => {
            e.preventDefault()
            void ask(input)
          }}
        >
          <Textarea
            value={input}
            rows={2}
            maxLength={4000}
            disabled={!available}
            placeholder="Задайте вопрос о доске…"
            className="resize-none"
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
                e.preventDefault()
                void ask(input)
              }
            }}
          />
          <div className="flex items-center justify-between">
            <Button type="button" variant="ghost" size="sm" disabled={messages.length === 0} onClick={reset}>
              <RotateCcw /> Новый диалог
            </Button>
            {streaming ? (
              <Button type="button" variant="secondary" size="sm" onClick={() => abort.current?.abort()}>
                <Square /> Остановить
              </Button>
            ) : (
              <Button type="submit" size="sm" disabled={!available || !input.trim()}>
                <ArrowUp /> Отправить
              </Button>
            )}
          </div>
        </form>
      </SheetContent>
    </Sheet>
  )
}
