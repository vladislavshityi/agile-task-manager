import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { qk } from '@/lib/query-keys'
import { wikiApi, type WikiPageInput } from './api'

export function useWikiPages(wid: string) {
  return useQuery({ queryKey: qk.wiki(wid), queryFn: () => wikiApi.list(wid) })
}

export function useWikiSearch(wid: string, q: string) {
  return useQuery({ queryKey: qk.wikiSearch(wid, q), queryFn: () => wikiApi.list(wid, q), enabled: q.length > 0 })
}

export function useWikiPage(id: string) {
  return useQuery({ queryKey: qk.wikiPage(id), queryFn: () => wikiApi.get(id), enabled: !!id })
}

function useRefreshWiki(wid: string) {
  const qc = useQueryClient()
  return (pageId?: string) => {
    void qc.invalidateQueries({ queryKey: qk.wiki(wid) })
    if (pageId) void qc.invalidateQueries({ queryKey: qk.wikiPage(pageId) })
  }
}

export function useCreateWikiPage(wid: string) {
  const refresh = useRefreshWiki(wid)
  return useMutation({ mutationFn: (body: WikiPageInput) => wikiApi.create(wid, body), onSuccess: () => refresh() })
}

export function useUpdateWikiPage(wid: string, id: string) {
  const qc = useQueryClient()
  const refresh = useRefreshWiki(wid)
  return useMutation({
    mutationFn: (body: { title?: string; content?: string }) => wikiApi.update(id, body),
    onSuccess: (page) => {
      qc.setQueryData(qk.wikiPage(id), page)
      refresh()
    },
  })
}

export function useMoveWikiPage(wid: string, id: string) {
  const refresh = useRefreshWiki(wid)
  return useMutation({
    mutationFn: ({ parentId, position }: { parentId: string | null; position: number }) =>
      wikiApi.move(id, parentId, position),
    onSuccess: () => refresh(id),
  })
}

export function useDeleteWikiPage(wid: string) {
  const qc = useQueryClient()
  const refresh = useRefreshWiki(wid)
  return useMutation({
    mutationFn: wikiApi.remove,
    onSuccess: (_, id) => {
      qc.removeQueries({ queryKey: qk.wikiPage(id) })
      refresh()
    },
  })
}
