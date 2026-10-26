import { useState } from 'react'
import { Link } from 'react-router-dom'
import { ChevronRight, FileText, Plus } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { WikiNode } from '../tree'

interface Props {
  nodes: WikiNode[]
  basePath: string
  activeId?: string
  canEdit: boolean
  onAddChild: (parentId: string) => void
}

function TreeItem({ node, depth, ...props }: Omit<Props, 'nodes'> & { node: WikiNode; depth: number }) {
  const [open, setOpen] = useState(true)
  const active = node.id === props.activeId
  const hasChildren = node.children.length > 0

  return (
    <li>
      <div
        className={cn(
          'group flex items-center gap-1 rounded-lg pr-1 text-sm transition-colors duration-150 hover:bg-muted',
          active && 'bg-muted font-medium text-foreground',
        )}
        style={{ paddingLeft: depth * 12 }}
      >
        <button
          type="button"
          aria-label={open ? 'Свернуть' : 'Развернуть'}
          onClick={() => setOpen((v) => !v)}
          className={cn('flex size-6 shrink-0 items-center justify-center rounded text-muted-foreground', !hasChildren && 'invisible')}
        >
          <ChevronRight className={cn('size-3.5 transition-transform duration-150', open && 'rotate-90')} />
        </button>
        <Link to={`${props.basePath}/${node.id}`} className="flex min-w-0 flex-1 items-center gap-2 py-1.5">
          <FileText className="size-4 shrink-0 text-muted-foreground" />
          <span className="truncate">{node.title}</span>
        </Link>
        {props.canEdit && (
          <button
            type="button"
            title="Добавить подстраницу"
            onClick={() => {
              setOpen(true)
              props.onAddChild(node.id)
            }}
            className="flex size-6 shrink-0 items-center justify-center rounded text-muted-foreground opacity-0 transition-opacity hover:bg-background group-hover:opacity-100 focus-visible:opacity-100"
          >
            <Plus className="size-3.5" />
          </button>
        )}
      </div>
      {open && hasChildren && (
        <ul>
          {node.children.map((child) => (
            <TreeItem key={child.id} node={child} depth={depth + 1} {...props} />
          ))}
        </ul>
      )}
    </li>
  )
}

export function WikiTree({ nodes, ...props }: Props) {
  return (
    <ul className="grid gap-0.5">
      {nodes.map((node) => (
        <TreeItem key={node.id} node={node} depth={0} {...props} />
      ))}
    </ul>
  )
}
