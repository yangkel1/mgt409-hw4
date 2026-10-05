import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'
import { Bulldog } from './Bulldog'

const MAIN_LINKS = [
  { to: '/', label: 'Home', end: true },
  { to: '/products', label: 'Products' },
  { to: '/about', label: 'About Us' },
]

export default function NavBar() {
  const { user, loading, logout } = useAuth()
  const navigate = useNavigate()

  async function handleLogout() {
    await logout()
    navigate('/')
  }

  return (
    <header className="site-header">
      <div className="announcement">
        <span className="varsity">Boola Boola!</span> Officially licensed Yale apparel · Visit us at 57 Broadway, New Haven
      </div>
      <nav className="navbar container">
        <Link to="/" className="brand">
          <span className="brand-mark">
            <Bulldog size={44} />
          </span>
          <span className="brand-text">
            <strong>Campus Customs</strong>
            <small>Yale Bulldog Blue</small>
          </span>
        </Link>

        <ul className="nav-links">
          {MAIN_LINKS.map((link) => (
            <li key={link.to}>
              <NavLink to={link.to} end={link.end}>
                {link.label}
              </NavLink>
            </li>
          ))}
        </ul>

        <div className="nav-account">
          {loading ? null : user ? (
            <>
              <span className="nav-greeting">Hi, {user.first_name}</span>
              <button className="btn btn-small btn-ghost" onClick={handleLogout}>
                Log out
              </button>
            </>
          ) : (
            <>
              <NavLink to="/login">Log in</NavLink>
              <NavLink to="/signup" className="btn btn-small">
                Create account
              </NavLink>
            </>
          )}
        </div>
      </nav>
    </header>
  )
}
