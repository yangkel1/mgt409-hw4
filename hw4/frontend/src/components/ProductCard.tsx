import { Link } from 'react-router-dom'
import { formatPrice, imageSrc, type ProductSummary } from '../api'
import { SIZES } from './SortFilterBar'

export default function ProductCard({ product }: { product: ProductSummary }) {
  const sizes = product.sizes_in_stock ?? []
  const fewSizes = sizes.length > 0 && sizes.length <= 3

  return (
    <Link to={`/products/${product.product_id}`} className="product-card">
      <div className="product-card-image">
        <img src={imageSrc(product)} alt={product.name} loading="lazy" />
        {fewSizes && <span className="card-badge">Few sizes left</span>}
        <span className="price-tag">{formatPrice(product.price)}</span>
      </div>
      <div className="product-card-body">
        <p className="card-type">{product.garment_type}</p>
        <h3>{product.name}</h3>
        <p className="product-card-desc">{product.short_description}</p>
        <ul className="size-dots" aria-label={`In stock: ${sizes.join(', ') || 'none'}`}>
          {SIZES.map((s) => (
            <li key={s} className={sizes.includes(s) ? 'in' : 'out'} title={sizes.includes(s) ? `${s} in stock` : `${s} sold out`}>
              {s}
            </li>
          ))}
        </ul>
      </div>
    </Link>
  )
}
