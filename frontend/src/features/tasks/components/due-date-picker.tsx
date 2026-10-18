import { CalendarDays, X } from 'lucide-react'
import { ru } from 'react-day-picker/locale'
import { Button } from '@/components/ui/button'
import { Calendar } from '@/components/ui/calendar'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { formatLong, fromApiDate, toApiDate } from '@/lib/dates'

interface Props {
  value: string | null
  disabled?: boolean
  onChange: (value: string | null) => void
}

export function DueDatePicker({ value, disabled, onChange }: Props) {
  return (
    <div className="flex items-center gap-1">
      <Popover>
        <PopoverTrigger asChild>
          <Button variant="outline" disabled={disabled} className="h-9 flex-1 justify-start rounded-xl font-normal">
            <CalendarDays className="size-4 text-muted-foreground" />
            {value ? formatLong(value) : <span className="text-muted-foreground">Без срока</span>}
          </Button>
        </PopoverTrigger>
        <PopoverContent align="start" className="w-auto rounded-2xl p-0">
          <Calendar
            mode="single"
            locale={ru}
            weekStartsOn={1}
            selected={value ? fromApiDate(value) : undefined}
            defaultMonth={value ? fromApiDate(value) : undefined}
            onSelect={(d) => onChange(d ? toApiDate(d) : null)}
          />
        </PopoverContent>
      </Popover>
      {value && !disabled && (
        <Button variant="ghost" size="icon" aria-label="Убрать срок" onClick={() => onChange(null)}>
          <X className="size-4" />
        </Button>
      )}
    </div>
  )
}
