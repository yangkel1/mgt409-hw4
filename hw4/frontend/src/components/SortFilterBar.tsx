import type { ProductSummary } from '../api'

export const SIZES = ['XS', 'S', 'M', 'L', 'XL', 'XXL'] as const

export type SortKey = 'featured' | 'price-asc' | 'price-desc' | 'name'

export interface SortFilter {
  sort: SortKey
  size: string // '' = any size
}

export const DEFAULT_SORT_FILTER: SortFilter = { sort: 'featured', size: '' }

export function applySortFilter(products: ProductSummary[], { sort, size }: SortFilter): ProductSummary[] {
  const filtered = size ? products.filter((p) => p.sizes_in_stock.includes(size)) : products
  if (sort === 'featured') return filtered
  return [...filtered].sort((a, b) =>
    sort === 'name' ? a.name.localeCompare(b.name) : sort === 'price-asc' ? a.price - b.price : b.price - a.price,
  )
}

// Sort by price/name and show only items in stock in the shopper's size.
// onChange receives only the field that changed, so quick successive changes can't resend stale values.
export default function SortFilterBar({ value, onChange }: { value: SortFilter; onChange: (change: Partial<SortFilter>) => void }) {
  return (
    <div className="sort-filter">
      <label>
        In stock in
        <select value={value.size} onChange={(e) => onChange({ size: e.target.value })}>
          <option value="">Any size</option>
          {SIZES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </label>
      <label>
        Sort by
        <select value={value.sort} onChange={(e) => onChange({ sort: e.target.value as SortKey })}>
          <option value="featured">Featured</option>
          <option value="price-asc">Price: low to high</option>
          <option value="price-desc">Price: high to low</option>
          <option value="name">Name: A to Z</option>
        </select>
      </label>
    </div>
  )
}
