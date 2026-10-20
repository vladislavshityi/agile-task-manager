import { Sparkles } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { errorMessage } from '@/lib/api-client'
import { useAIAvailable, useSuggestDescription } from '../hooks'

/** Asks the local model for a task description; the caller decides what to do with it. */
export function SuggestDescriptionButton({ taskId, onSuggest }: { taskId: string; onSuggest: (text: string) => void }) {
  const available = useAIAvailable()
  const suggest = useSuggestDescription(taskId)
  if (!available) return null

  return (
    <Button
      type="button"
      variant="ghost"
      size="xs"
      disabled={suggest.isPending}
      onClick={() =>
        suggest.mutate(undefined, {
          onSuccess: ({ description }) => onSuggest(description),
          onError: (e) => toast.error(errorMessage(e)),
        })
      }
    >
      <Sparkles className={suggest.isPending ? 'animate-pulse' : undefined} />
      {suggest.isPending ? 'Пишу…' : 'Описание с ИИ'}
    </Button>
  )
}
