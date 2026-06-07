interface Props { signal: string; size?: 'sm' | 'md' }

const LABELS: Record<string, string> = {
  STRONG_BUY: '⬆ Strong Buy',
  BUY: '↑ Buy',
  NEUTRAL: '→ Neutral',
  SELL: '↓ Sell',
  STRONG_SELL: '⬇ Strong Sell',
}

export default function SignalBadge({ signal, size = 'sm' }: Props) {
  const px = size === 'md' ? 'px-3 py-1 text-xs' : 'px-2 py-0.5 text-[10px]'
  return (
    <span className={`${px} rounded font-mono font-medium badge-${signal}`}>
      {LABELS[signal] ?? signal}
    </span>
  )
}
