import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { fetchProduct, formatPrice, imageSrc, type ProductDetail } from '../api'
import { openChat } from '../chatEvents'
import { Bulldog } from '../components/Bulldog'
import { swatchFor } from '../colors'

const LOW_STOCK = 5

function stockLabel(quantity: number) {
  if (quantity === 0) return 'Sold out'
  if (quantity <= LOW_STOCK) return `Only ${quantity} left`
  return 'In stock'
}

export default function ProductPage() {
  const { productId = '' } = useParams()
  const [product, setProduct] = useState<ProductDetail | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setProduct(null)
    setError(null)
    fetchProduct(productId)
      .then(setProduct)
      .catch((e: Error) => setError(e.message === 'Not found' ? "We couldn't find that product." : "Couldn't load this product."))
  }, [productId])

  if (error)
    return (
      <div className="container section empty-state">
        <Bulldog size={120} mood="sleepy" />
        <h1>{error}</h1>
        <p className="muted">Dan sniffed everywhere but this item isn't in the catalogue.</p>
        <Link to="/products" className="btn">
          Back to all products
        </Link>
      </div>
    )
  if (!product)
    return (
      <div className="container section empty-state">
        <Bulldog size={80} className="loading-dog" />
        <p className="muted">Fetching…</p>
      </div>
    )

  const lowSizes = product.inventory.filter((s) => s.quantity > 0 && s.quantity <= LOW_STOCK)

  return (
    <div className="container section">
      <nav className="breadcrumbs" aria-label="Breadcrumb">
        <Link to="/">Home</Link>
        <span>/</span>
        <Link to="/products">Products</Link>
        <span>/</span>
        <span aria-current="page">{product.name}</span>
      </nav>

      <div className="product-detail">
        <div className="product-detail-image">
          <img src={imageSrc(product)} alt={product.name} />
          <span className="licensed-sticker">
            Officially
            <br />
            licensed
          </span>
        </div>

        <div className="product-detail-info">
          <p className="eyebrow varsity">{product.garment_type}</p>
          <h1>{product.name}</h1>
          <p className="price large">{formatPrice(product.price)}</p>
          <p className="detail-description">{product.description}</p>

          <h3>Colors</h3>
          <ul className="color-list">
            {product.colors.map((c) => (
              <li key={c}>
                <span className="swatch" style={{ background: swatchFor(c) }} />
                {c}
              </li>
            ))}
          </ul>

          <h3>Availability by size</h3>
          <ul className="size-tiles">
            {product.inventory.map((s) => (
              <li key={s.size} className={s.quantity === 0 ? 'sold-out' : s.quantity <= LOW_STOCK ? 'low' : 'in'}>
                <strong>{s.size}</strong>
                <span>{stockLabel(s.quantity)}</span>
                <small>{s.quantity} in stock</small>
              </li>
            ))}
          </ul>
          {lowSizes.length > 0 && (
            <p className="urgency">
              Going fast: only {lowSizes.map((s) => `${s.quantity} left in ${s.size}`).join(', ')}.
            </p>
          )}
          <p className="muted small">{product.total_stock} units across all sizes</p>

          <div className="ask-card">
            <Bulldog size={56} mood="wink" />
            <div>
              <strong>Not sure about the fit or color?</strong>
              <p className="muted small">Dan knows which item you're viewing. Ask about sizes, colors, or similar styles.</p>
            </div>
            <button className="btn" onClick={openChat}>
              Ask about this item
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
