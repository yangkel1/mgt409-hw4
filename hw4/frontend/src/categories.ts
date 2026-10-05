// The catalogue has 22 slightly different garment_type labels; group them into
// a few shopper-friendly categories.

export const CATEGORIES = ['Hoodies', 'Crewnecks', 'Quarter-zips', 'T-shirts', 'Long sleeves', 'Jackets & fleece'] as const

export type Category = (typeof CATEGORIES)[number]

export function categoryOf(garmentType: string): Category {
  const g = garmentType.toLowerCase()
  if (g.includes('quarter-zip')) return 'Quarter-zips'
  if (g.includes('jacket') || g.includes('fleece')) return 'Jackets & fleece'
  if (g.includes('hood')) return 'Hoodies'
  if (g.includes('t-shirt')) return 'T-shirts'
  if (g.includes('long-sleeve')) return 'Long sleeves'
  return 'Crewnecks'
}
