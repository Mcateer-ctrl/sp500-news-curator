import { type ReactNode } from 'react'

interface CardProps {
  children: ReactNode
  className?: string
  padding?: 'compact' | 'default' | 'spacious'
  hover?: boolean
}

const PADDING_MAP = {
  compact: 'p-3',
  default: 'p-5',
  spacious: 'p-8',
}

export default function Card({ children, className = '', padding = 'default', hover = true }: CardProps) {
  return (
    <div
      className={`bg-white/40 ring-1 ring-black/[0.06] rounded-[1.25rem] p-[3px] ${
        hover ? 'hover:-translate-y-0.5 hover:shadow-card-hover' : ''
      } transition-all duration-200 ease-spring ${className}`}
    >
      <div
        className={`bg-white rounded-[calc(1.25rem-3px)] shadow-inner ${PADDING_MAP[padding]}`}
      >
        {children}
      </div>
    </div>
  )
}
