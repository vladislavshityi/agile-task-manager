import { useRef, useState } from 'react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Textarea } from '@/components/ui/textarea'
import { errorMessage } from '@/lib/api-client'
import type { WikiPage } from '@/types/api'
import { useUpdateWikiPage } from '../hooks'
import { WikiMarkdown } from './markdown'
import { MarkdownToolbar } from './markdown-toolbar'

interface Props {
  page: WikiPage
  onDone: () => void
}

export function WikiEditor({ page, onDone }: Props) {
  const update = useUpdateWikiPage(page.workspace_id, page.id)
  const [title, setTitle] = useState(page.title)
  const [content, setContent] = useState(page.content)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const dirty = title !== page.title || content !== page.content

  const save = () => {
    if (!title.trim()) {
      toast.error('Введите название страницы')
      return
    }
    update.mutate(
      { title: title.trim(), content },
      {
        onSuccess: () => {
          toast.success('Сохранено')
          onDone()
        },
        onError: (e) => toast.error(errorMessage(e)),
      },
    )
  }

  return (
    <div
      className="grid gap-4"
      onKeyDown={(e) => {
        if ((e.metaKey || e.ctrlKey) && e.key === 's') {
          e.preventDefault()
          save()
        }
      }}
    >
      <Input
        aria-label="Название страницы"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        maxLength={200}
        className="h-11 text-xl font-semibold"
      />
      <Tabs defaultValue="write">
        <TabsList>
          <TabsTrigger value="write">Текст</TabsTrigger>
          <TabsTrigger value="preview">Предпросмотр</TabsTrigger>
        </TabsList>
        <TabsContent value="write" className="grid gap-2">
          <MarkdownToolbar textareaRef={textareaRef} value={content} onChange={setContent} />
          <Textarea
            ref={textareaRef}
            aria-label="Содержимое страницы"
            autoFocus
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder={'# Заголовок\n\nПоддерживается Markdown: **жирный**, списки, таблицы, `код`, [ссылки](https://example.com)…'}
            className="min-h-[55svh] font-mono text-sm leading-relaxed"
          />
        </TabsContent>
        <TabsContent value="preview">
          <div className="min-h-[55svh] rounded-xl border px-4 py-3">
            {content.trim() ? (
              <WikiMarkdown content={content} />
            ) : (
              <p className="text-sm text-muted-foreground">Нечего показать</p>
            )}
          </div>
        </TabsContent>
      </Tabs>
      <div className="flex items-center justify-end gap-2">
        <span className="mr-auto hidden text-xs text-muted-foreground sm:inline">⌘/Ctrl + S — сохранить</span>
        <Button type="button" variant="ghost" onClick={onDone}>
          Отмена
        </Button>
        <Button type="button" onClick={save} disabled={!dirty || update.isPending}>
          Сохранить
        </Button>
      </div>
    </div>
  )
}
