import type { WikiPageSummary } from '@/types/api'

export interface WikiNode extends WikiPageSummary {
  children: WikiNode[]
}

/** Builds the page tree from the flat list (already sorted by position). */
export function buildTree(pages: WikiPageSummary[]): WikiNode[] {
  const nodes = new Map(pages.map((p) => [p.id, { ...p, children: [] as WikiNode[] }]))
  const roots: WikiNode[] = []
  for (const node of nodes.values()) {
    const parent = node.parent_id ? nodes.get(node.parent_id) : undefined
    if (parent) parent.children.push(node)
    else roots.push(node)
  }
  return roots
}

/** Ancestors of a page from the root down, not including the page itself. */
export function ancestors(pages: WikiPageSummary[], id: string): WikiPageSummary[] {
  const byId = new Map(pages.map((p) => [p.id, p]))
  const chain: WikiPageSummary[] = []
  let current = byId.get(id)?.parent_id
  while (current) {
    const page = byId.get(current)
    if (!page) break
    chain.unshift(page)
    current = page.parent_id
  }
  return chain
}

/** IDs of the page and everything nested under it. */
export function subtreeIds(pages: WikiPageSummary[], id: string): Set<string> {
  const ids = new Set([id])
  let grew = true
  while (grew) {
    grew = false
    for (const p of pages) {
      if (p.parent_id && ids.has(p.parent_id) && !ids.has(p.id)) {
        ids.add(p.id)
        grew = true
      }
    }
  }
  return ids
}
