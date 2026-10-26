import Markdown from 'react-markdown'
import remarkBreaks from 'remark-breaks'
import remarkGfm from 'remark-gfm'
import { cn } from '@/lib/utils'

/**
 * Forgives the most common slips of hand-written Markdown: a missing space after
 * `#`, `-` or `1.` at the start of a line (`#Title`, `-item`, `1.step`).
 * Fenced code blocks are left untouched.
 */
function normalizeMarkdown(source: string): string {
  let inFence = false
  return source
    .split('\n')
    .map((line) => {
      if (/^\s*(```|~~~)/.test(line)) {
        inFence = !inFence
        return line
      }
      if (inFence) return line
      return line
        .replace(/^(\s{0,3}#{1,6})(?=[^\s#])/, '$1 ')
        .replace(/^(\s*-)(?=\p{L})/u, '$1 ')
        .replace(/^(\s*\d+[.)])(?=\p{L})/u, '$1 ')
    })
    .join('\n')
}

/** Renders wiki Markdown (GitHub flavour: tables, task lists, strikethrough; single newlines break lines). */
export function WikiMarkdown({ content, className }: { content: string; className?: string }) {
  return (
    <div className={cn('wiki-prose', className)}>
      <Markdown
        remarkPlugins={[remarkGfm, remarkBreaks]}
        components={{
          a: ({ href, children }) => {
            const external = href?.startsWith('http')
            return (
              <a href={href} target={external ? '_blank' : undefined} rel={external ? 'noreferrer' : undefined}>
                {children}
              </a>
            )
          },
        }}
      >
        {normalizeMarkdown(content)}
      </Markdown>
    </div>
  )
}
