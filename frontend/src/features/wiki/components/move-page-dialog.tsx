import { useMemo, useState } from 'react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { errorMessage } from '@/lib/api-client'
import type { WikiPage, WikiPageSummary } from '@/types/api'
import { useMoveWikiPage } from '../hooks'
import { buildTree, subtreeIds, type WikiNode } from '../tree'

const ROOT = 'root'

interface Props {
  page: WikiPage
  pages: WikiPageSummary[]
  open: boolean
  onOpenChange: (open: boolean) => void
}

function flatten(nodes: WikiNode[], depth = 0): { node: WikiNode; depth: number }[] {
  return nodes.flatMap((node) => [{ node, depth }, ...flatten(node.children, depth + 1)])
}

export function MovePageDialog({ page, pages, open, onOpenChange }: Props) {
  const move = useMoveWikiPage(page.workspace_id, page.id)
  const [target, setTarget] = useState(page.parent_id ?? ROOT)

  const options = useMemo(() => {
    const excluded = subtreeIds(pages, page.id)
    return flatten(buildTree(pages)).filter(({ node }) => !excluded.has(node.id))
  }, [pages, page.id])

  const submit = () => {
    const parentId = target === ROOT ? null : target
    const position = pages.filter((p) => p.parent_id === parentId && p.id !== page.id).length
    move.mutate(
      { parentId, position },
      {
        onSuccess: () => {
          toast.success('Страница перемещена')
          onOpenChange(false)
        },
        onError: (e) => toast.error(errorMessage(e)),
      },
    )
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="rounded-2xl sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Переместить «{page.title}»</DialogTitle>
          <DialogDescription>Подстраницы переместятся вместе с ней.</DialogDescription>
        </DialogHeader>
        <Select value={target} onValueChange={setTarget}>
          <SelectTrigger className="w-full">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ROOT}>Верхний уровень</SelectItem>
            {options.map(({ node, depth }) => (
              <SelectItem key={node.id} value={node.id}>
                <span style={{ paddingLeft: (depth + 1) * 12 }}>{node.title}</span>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <DialogFooter>
          <Button type="button" variant="ghost" onClick={() => onOpenChange(false)}>
            Отмена
          </Button>
          <Button type="button" onClick={submit} disabled={move.isPending || target === (page.parent_id ?? ROOT)}>
            Переместить
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
