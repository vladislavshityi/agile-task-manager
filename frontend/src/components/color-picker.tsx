import { Check } from 'lucide-react'
import { APPLE_COLORS } from '@/lib/design'
import { cn } from '@/lib/utils'

interface Props {
  value: string
  onChange: (color: string) => void
  disabled?: boolean
}

export function ColorPicker({ value, onChange, disabled }: Props) {
  return (
    <div className="flex flex-wrap gap-2" role="radiogroup" aria-label="Цвет">
      {APPLE_COLORS.map((c) => (
        <button
          key={c}
          type="button"
          role="radio"
          aria-checked={value.toLowerCase() === c.toLowerCase()}
          aria-label={c}
          disabled={disabled}
          onClick={() => onChange(c)}
          className={cn(
            'flex size-7 items-center justify-center rounded-full text-white transition-transform duration-150 ease-out hover:scale-110 focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none',
          )}
          style={{ backgroundColor: c }}
        >
          {value.toLowerCase() === c.toLowerCase() && <Check className="size-4" strokeWidth={3} />}
        </button>
      ))}
    </div>
  )
}
