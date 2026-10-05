import { Link } from 'react-router-dom'
import { Bulldog, Paw } from './Bulldog'

export default function Footer() {
  return (
    <footer className="site-footer">
      <div className="footer-scallop" aria-hidden="true" />
      <div className="container footer-grid">
        <div className="footer-brand">
          <Bulldog size={64} mood="wink" />
          <strong className="varsity">Campus Customs</strong>
          <p>Officially licensed Yale gear from a shop on Broadway in New Haven.</p>
        </div>
        <div>
          <strong>Shop</strong>
          <Link to="/products">All products</Link>
          <Link to="/about">About us</Link>
        </div>
        <div>
          <strong>Visit or reach us</strong>
          <span>57 Broadway, New Haven, CT 06511</span>
          <span>orderdept@campuscustoms.com</span>
        </div>
      </div>
      <p className="container footer-note">
        <Paw size={12} /> Bulldog! Bulldog! Bow, wow, wow! · Class project for MGT 409. Not the official store.
      </p>
    </footer>
  )
}
