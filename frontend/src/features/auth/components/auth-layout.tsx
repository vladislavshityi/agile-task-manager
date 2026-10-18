import type { ReactNode } from 'react'
import { LayoutDashboard } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

interface Props {
  title: string
  description: string
  children: ReactNode
}

export function AuthLayout({ title, description, children }: Props) {
  return (
    <div className="flex min-h-svh items-center justify-center px-4 py-10">
      <div className="w-full max-w-sm">
        <div className="mb-6 flex flex-col items-center gap-3">
          <div className="flex size-12 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-lg shadow-primary/30">
            <LayoutDashboard className="size-6" />
          </div>
        </div>
        <Card className="rounded-2xl border-0 shadow-sm ring-1 ring-black/5 dark:ring-white/10">
          <CardHeader className="text-center">
            <CardTitle className="text-xl tracking-tight">{title}</CardTitle>
            <CardDescription>{description}</CardDescription>
          </CardHeader>
          <CardContent>{children}</CardContent>
        </Card>
      </div>
    </div>
  )
}

/** Only allow same-origin relative redirects. */
export function safeNext(next: string | null): string {
  return next && next.startsWith('/') && !next.startsWith('//') ? next : '/'
}
