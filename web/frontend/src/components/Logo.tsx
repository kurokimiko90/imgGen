interface LogoProps {
  size?: number
  className?: string
}

export function Logo({ size = 32, className }: LogoProps) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 32 32"
      fill="none"
      width={size}
      height={size}
      className={className}
    >
      {/* Card outline */}
      <rect x="2" y="5" width="22" height="24" rx="3" stroke="currentColor" strokeWidth="1.8" fill="none" />
      {/* Title line (bold) */}
      <rect x="6" y="11" width="12" height="2.2" rx="1.1" className="fill-accent" />
      {/* Summary line 1 */}
      <rect x="6" y="16" width="9" height="1.6" rx=".8" fill="currentColor" opacity=".35" />
      {/* Summary line 2 */}
      <rect x="6" y="20" width="12" height="1.6" rx=".8" fill="currentColor" opacity=".35" />
      {/* Sparkle (4-point star) */}
      <path d="M27 2l1.1 3.4L31.5 6.5l-3.4 1.1L27 11l-1.1-3.4L22.5 6.5l3.4-1.1z" className="fill-accent" />
    </svg>
  )
}
