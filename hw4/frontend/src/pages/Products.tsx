import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { fetchProducts, type ProductSummary } from '../api'
import ProductCard from '../components/ProductCard'
import { CATEGORIES, categoryOf } from '../categories'
import { useChatResults, type ChatResults } from '../chatResults'
import SortFilterBar, { applySortFilter, type SortFilter, type SortKey } from '../components/SortFilterBar'

// Cards the chat agent found, shown in place of the full catalogue until cleared.
function ChatResultsView({
  results,
  onClear,
  sortFilter,
  onSortFilter,
}: {
  results: ChatResults
  onClear: () => void
  sortFilter: SortFilter
  onSortFilter: (change: Partial<SortFilter>) => void
}) {
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }, [results.receivedAt])
  const shown = applySortFilter(results.products, sortFilter)

  return (
    <div className="container section">
      <div className="chat-results-banner">
        <div>
          <p className="eyebrow">From your chat · “{results.question}”</p>
          <h1>{results.title}</h1>
          <p className="muted">
            {results.total} matching item{results.total === 1 ? '' : 's'}
          </p>
        </div>
        <button className="btn btn-ghost" onClick={onClear}>
          Show all products
        </button>
      </div>
      <div className="results-toolbar">
        <p className="muted">
          {shown.length === results.products.length
            ? `${shown.length} item${shown.length === 1 ? '' : 's'}`
            : `${shown.length} of ${results.products.length} in stock in ${sortFilter.size}`}
        </p>
        <SortFilterBar value={sortFilter} onChange={onSortFilter} />
      </div>
      <div className="product-grid chat-results-grid" key={results.receivedAt}>
        {shown.map((p) => (
          <ProductCard key={p.product_id} product={p} />
        ))}
      </div>
      {shown.length === 0 && <p className="muted">None of these are in stock in {sortFilter.size}. Try another size.</p>}
    </div>
  )
}

export default function Products() {
  const { results, clearResults } = useChatResults()
  const [products, setProducts] = useState<ProductSummary[]>([])
  const [status, setStatus] = useState<'loading' | 'ready' | 'error'>('loading')
  const [query, setQuery] = useState('')
  const [params, setParams] = useSearchParams()
  const category = params.get('category')
  // Sort and size live in the URL so they survive opening a product and pressing Back.
  const sortFilter: SortFilter = { sort: (params.get('sort') as SortKey) || 'featured', size: params.get('size') || '' }

  // Start from the live URL (not this render's copy), so two quick changes don't overwrite each other.
  function updateParams(changes: Record<string, string | null>) {
    setParams(
      () => {
        const next = new URLSearchParams(window.location.search)
        for (const [key, value] of Object.entries(changes)) {
          if (value) next.set(key, value)
          else next.delete(key)
        }
        return next
      },
      { replace: true },
    )
  }

  function setSortFilter(change: Partial<SortFilter>) {
    const updates: Record<string, string | null> = {}
    if (change.sort !== undefined) updates.sort = change.sort === 'featured' ? null : change.sort
    if (change.size !== undefined) updates.size = change.size || null
    updateParams(updates)
  }

  useEffect(() => {
    fetchProducts()
      .then((data) => {
        setProducts(data)
        setStatus('ready')
      })
      .catch(() => setStatus('error'))
  }, [])

  const visible = useMemo(() => {
    const q = query.trim().toLowerCase()
    const matches = products.filter(
      (p) =>
        (!category || categoryOf(p.garment_type) === category) &&
        (!q || `${p.name} ${p.garment_type} ${p.short_description}`.toLowerCase().includes(q)),
    )
    return applySortFilter(matches, { sort: (params.get('sort') as SortKey) || 'featured', size: params.get('size') || '' })
  }, [products, category, query, params])

  function chooseCategory(c: string | null) {
    updateParams({ category: c })
  }

  if (results)
    return <ChatResultsView results={results} onClear={clearResults} sortFilter={sortFilter} onSortFilter={setSortFilter} />

  return (
    <div className="container section">
      <h1>All products</h1>

      <div className="filters">
        <input
          className="search"
          type="search"
          placeholder="Search products"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <div className="chips">
          <button className={!category ? 'chip active' : 'chip'} onClick={() => chooseCategory(null)}>
            All
          </button>
          {CATEGORIES.map((c) => (
            <button key={c} className={category === c ? 'chip active' : 'chip'} onClick={() => chooseCategory(c)}>
              {c}
            </button>
          ))}
        </div>
      </div>

      {status === 'loading' && <p className="muted">Loading products…</p>}
      {status === 'error' && (
        <p className="error">Couldn't load products. Is the backend running on port 8000?</p>
      )}
      {status === 'ready' && (
        <>
          <div className="results-toolbar">
            <p className="muted">
              {visible.length} item{visible.length === 1 ? '' : 's'}
              {sortFilter.size && ` in stock in ${sortFilter.size}`}
            </p>
            <SortFilterBar value={sortFilter} onChange={setSortFilter} />
          </div>
          <div className="product-grid">
            {visible.map((p) => (
              <ProductCard key={p.product_id} product={p} />
            ))}
          </div>
        </>
      )}
    </div>
  )
}
