import { CircleOff } from 'lucide-react'
import type { AIStatus } from '@/types/api'

/** Explains why the assistant is off and how to turn it on. */
export function AIUnavailable({ status }: { status: AIStatus }) {
  return (
    <div className="grid justify-items-center gap-3 rounded-2xl border border-dashed border-black/10 px-6 py-10 text-center dark:border-white/15">
      <div className="flex size-12 items-center justify-center rounded-2xl bg-muted text-muted-foreground">
        <CircleOff className="size-6" />
      </div>
      {status.enabled ? (
        <>
          <p className="max-w-xs text-sm text-muted-foreground">
            Локальная модель недоступна. Запустите Ollama и установите модель:
          </p>
          <code className="rounded-lg bg-muted px-2 py-1 text-xs">ollama pull {status.model}</code>
        </>
      ) : (
        <p className="max-w-xs text-sm text-muted-foreground">ИИ-ассистент отключён администратором сервера.</p>
      )}
    </div>
  )
}
