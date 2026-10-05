import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchProducts, imageSrc, type ProductSummary } from '../api'
import ProductCard from '../components/ProductCard'
import { Bulldog, Paw } from '../components/Bulldog'
import { CATEGORIES, categoryOf } from '../categories'
import { useChatResults } from '../chatResults'
import { openChat } from '../chatEvents'

const FEATURED_IDS = ['basic-hoodie-big-yale', '2025-yale-vs-harvard-t-shirt', 'baseball-left-chest-crewneck', 'benjamin-franklin-fleece-jacket']

// One photo per category tile: a recognizable, well-stocked pick.
const CATEGORY_COVER: Record<string, string> = {
  Hoodies: 'basic-hoodie-big-yale',
  Crewnecks: 'baseball-left-chest-crewneck',
  'Quarter-zips': 'benjamin-franklin-1-4-zip',
  'T-shirts': '2025-yale-vs-harvard-t-shirt',
  'Long sleeves': 'dry-zone-long-sleeve',
  'Jackets & fleece': 'benjamin-franklin-fleece-jacket',
}

const CHEERS = ['Boola Boola', 'Bulldog! Bulldog! Bow, wow, wow!', 'For God, for Country & for Yale', 'Officially licensed', '57 Broadway, New Haven', 'Free advice from Dan the shop pup']

function FightSongBadge() {
  return (
    <div className="hero-badge">
      <svg viewBox="0 0 200 200" className="hero-badge-ring" aria-hidden="true">
        <defs>
          <path id="ring" d="M100,100 m-80,0 a80,80 0 1,1 160,0 a80,80 0 1,1 -160,0" />
        </defs>
        <text>
          <textPath href="#ring" startOffset="0" textLength="495" lengthAdjust="spacingAndGlyphs">
            BULLDOG! BULLDOG! BOW WOW WOW! ★ ELI YALE ★
          </textPath>
        </text>
      </svg>
      <Bulldog size={190} mood="happy" className="hero-dog" title="Dan, the Campus Customs bulldog" />
    </div>
  )
}

export default function Home() {
  const [all, setAll] = useState<ProductSummary[]>([])
  const { clearResults } = useChatResults()

  useEffect(() => {
    fetchProducts()
      .then(setAll)
      .catch(() => setAll([]))
  }, [])

  const featured = useMemo(() => {
    const picks = FEATURED_IDS.map((id) => all.find((p) => p.product_id === id)).filter((p): p is ProductSummary => Boolean(p))
    return picks.length ? picks : all.slice(0, 4)
  }, [all])

  const categories = useMemo(
    () =>
      CATEGORIES.map((name) => {
        const items = all.filter((p) => categoryOf(p.garment_type) === name)
        const cover = items.find((p) => p.product_id === CATEGORY_COVER[name]) ?? items[0]
        return { name, count: items.length, cover }
      }),
    [all],
  )

  return (
    <>
      <section className="hero">
        <div className="pennant-row" aria-hidden="true">
          {Array.from({ length: 14 }, (_, i) => (
            <span key={i} className="pennant-flag" style={{ animationDelay: `${(i % 7) * 0.18}s` }} />
          ))}
        </div>
        <div className="container hero-inner">
          <div className="hero-copy">
            <p className="eyebrow varsity">Yale Bulldog Blue · by Campus Customs</p>
            <h1>
              Bulldog pride,
              <br />
              <em>worn every day.</em>
            </h1>
            <p className="hero-sub">
              Cozy hoodies, game-day tees, and varsity crewnecks for students, alumni, and every proud Yale family.
              All officially licensed, all from our shop on Broadway.
            </p>
            <div className="hero-actions">
              <Link to="/products" className="btn btn-gold" onClick={clearResults}>
                Shop the collection
              </Link>
              <button className="btn btn-outline-light" onClick={openChat}>
                <Paw size={16} /> Ask Dan for help
              </button>
            </div>
          </div>
          <FightSongBadge />
        </div>
      </section>

      <div className="ticker" aria-label="Campus Customs cheers">
        <div className="ticker-track">
          {[...CHEERS, ...CHEERS].map((c, i) => (
            <span key={i}>
              {c} <Paw size={14} />
            </span>
          ))}
        </div>
      </div>

      <section className="container section">
        <div className="section-head">
          <h2>
            Shop by <span className="script">category</span>
          </h2>
        </div>
        <div className="category-grid">
          {categories.map(({ name, count, cover }) => (
            <Link
              key={name}
              to={`/products?category=${encodeURIComponent(name)}`}
              className="category-tile"
              onClick={clearResults}
            >
              <span className="category-photo">{cover && <img src={imageSrc(cover)} alt="" loading="lazy" />}</span>
              <span className="category-name">{name}</span>
              {count > 0 && <span className="category-count">{count} styles</span>}
            </Link>
          ))}
        </div>
      </section>

      <section className="container section">
        <div className="section-head">
          <h2>
            Campus <span className="script">favorites</span>
          </h2>
          <Link to="/products" className="link-arrow" onClick={clearResults}>
            View all →
          </Link>
        </div>
        <div className="product-grid">
          {featured.map((p) => (
            <ProductCard key={p.product_id} product={p} />
          ))}
        </div>
      </section>

      <section className="value-strip">
        <div className="container value-grid">
          <div>
            <span className="value-icon">✓</span>
            <strong>Officially licensed</strong>
            <span>Every item is official Yale merchandise.</span>
          </div>
          <div>
            <span className="value-icon">
              <Paw size={20} />
            </span>
            <strong>Steps from campus</strong>
            <span>Visit our store at 57 Broadway in New Haven.</span>
          </div>
          <div>
            <span className="value-icon">↺</span>
            <strong>Easy returns</strong>
            <span>Unworn items with tags come back within 30 days.</span>
          </div>
        </div>
      </section>
    </>
  )
}
