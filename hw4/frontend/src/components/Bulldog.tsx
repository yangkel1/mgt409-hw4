// Hand-drawn SVG mascot ("Dan, the shop pup") and a paw print, used across the site.

interface BulldogProps {
  size?: number
  mood?: 'happy' | 'wink' | 'sleepy'
  className?: string
  title?: string
}

export function Bulldog({ size = 64, mood = 'happy', className, title }: BulldogProps) {
  const navy = '#00356b'
  return (
    <svg
      viewBox="0 0 120 120"
      width={size}
      height={size}
      className={className}
      role={title ? 'img' : undefined}
      aria-label={title}
      aria-hidden={title ? undefined : true}
    >
      {/* folded "rose" ears, flopping outward */}
      <path d="M30 40 C18 30 6 36 8 50 C14 46 22 47 30 54 Z" fill={navy} />
      <path d="M90 40 C102 30 114 36 112 50 C106 46 98 47 90 54 Z" fill={navy} />
      {/* head: narrow brow, wide jowly cheeks */}
      <path
        d="M60 24 C84 24 98 36 101 54 C105 74 99 93 81 101 C71 105 49 105 39 101 C21 93 15 74 19 54 C22 36 36 24 60 24 Z"
        fill="#f7f0e3"
        stroke={navy}
        strokeWidth="4"
      />
      {/* brindle patch + forehead wrinkles */}
      <path d="M70 27 C83 29 93 38 96 50 C86 47 77 41 70 27 Z" fill="#c9a46a" opacity="0.55" />
      <path d="M46 36 Q60 31 74 36 M50 42 Q60 38 70 42" stroke={navy} strokeWidth="2.6" fill="none" strokeLinecap="round" />
      {/* eyes */}
      {mood === 'sleepy' ? (
        <>
          <path d="M36 57 Q43 62 50 57" stroke={navy} strokeWidth="3.5" fill="none" strokeLinecap="round" />
          <path d="M70 57 Q77 62 84 57" stroke={navy} strokeWidth="3.5" fill="none" strokeLinecap="round" />
        </>
      ) : (
        <>
          <circle cx="43" cy="56" r="7" fill={navy} />
          <circle cx="45.5" cy="53.5" r="2.4" fill="#fff" />
          {mood === 'wink' ? (
            <path d="M70 57 Q77 51 84 57" stroke={navy} strokeWidth="3.5" fill="none" strokeLinecap="round" />
          ) : (
            <>
              <circle cx="77" cy="56" r="7" fill={navy} />
              <circle cx="79.5" cy="53.5" r="2.4" fill="#fff" />
            </>
          )}
        </>
      )}
      {/* blush */}
      <ellipse cx="29" cy="70" rx="6.5" ry="4" fill="#f4a7b9" opacity="0.75" />
      <ellipse cx="91" cy="70" rx="6.5" ry="4" fill="#f4a7b9" opacity="0.75" />
      {/* droopy jowls */}
      <path
        d="M34 80 C34 66 48 64 60 71 C72 64 86 66 86 80 C86 93 73 98 60 92 C47 98 34 93 34 80 Z"
        fill="#fffaf2"
        stroke={navy}
        strokeWidth="3"
        strokeLinejoin="round"
      />
      {/* nose */}
      <path d="M50 69 Q60 63 70 69 Q67 77 60 78 Q53 77 50 69 Z" fill={navy} />
      <ellipse cx="56" cy="68.5" rx="3" ry="1.4" fill="#fff" opacity="0.6" />
      {/* mouth + underbite teeth */}
      <path d="M60 78 L60 83" stroke={navy} strokeWidth="3" strokeLinecap="round" />
      <path d="M50 88 Q60 96 70 88" stroke={navy} strokeWidth="3" fill="none" strokeLinecap="round" />
      <path d="M53 90.5 L54.5 85.5 L56.5 91.8 Z M63.5 91.8 L65.5 85.5 L67 90.5 Z" fill="#fff" stroke={navy} strokeWidth="1.3" strokeLinejoin="round" />
      {/* collar + Y tag */}
      <path d="M32 99 Q60 112 88 99" stroke="#286dc0" strokeWidth="7" fill="none" strokeLinecap="round" />
      <circle cx="60" cy="110" r="7" fill="#f2c94c" stroke={navy} strokeWidth="2" />
      {size >= 40 && (
        <text x="60" y="113.5" textAnchor="middle" fontSize="9" fontWeight="800" fill={navy} fontFamily="Georgia, serif">
          Y
        </text>
      )}
    </svg>
  )
}

export function Paw({ size = 16, className }: { size?: number; className?: string }) {
  return (
    <svg viewBox="0 0 24 24" width={size} height={size} className={className} aria-hidden="true">
      <ellipse cx="12" cy="16" rx="5.5" ry="4.5" fill="currentColor" />
      <circle cx="5" cy="10" r="2.4" fill="currentColor" />
      <circle cx="9.3" cy="5.8" r="2.4" fill="currentColor" />
      <circle cx="14.7" cy="5.8" r="2.4" fill="currentColor" />
      <circle cx="19" cy="10" r="2.4" fill="currentColor" />
    </svg>
  )
}
