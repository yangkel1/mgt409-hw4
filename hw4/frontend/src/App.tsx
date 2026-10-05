import { useEffect } from 'react'
import { BrowserRouter, Link, Route, Routes, useLocation } from 'react-router-dom'
import NavBar from './components/NavBar'
import Footer from './components/Footer'
import ChatWidget from './components/ChatWidget'
import Home from './pages/Home'
import Products from './pages/Products'
import ProductPage from './pages/ProductPage'
import About from './pages/About'
import AuthForm from './pages/AuthForm'
import { AuthProvider } from './auth'
import { ChatResultsProvider } from './chatResults'
import { Bulldog } from './components/Bulldog'

function ScrollToTop() {
  const { pathname } = useLocation()
  useEffect(() => {
    window.scrollTo(0, 0)
  }, [pathname])
  return null
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ChatResultsProvider>
          <ScrollToTop />
          <NavBar />
          <main>
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/products" element={<Products />} />
              <Route path="/products/:productId" element={<ProductPage />} />
              <Route path="/about" element={<About />} />
              <Route path="/login" element={<AuthForm mode="login" />} />
              <Route path="/signup" element={<AuthForm mode="signup" />} />
              <Route
                path="*"
                element={
                  <div className="container section empty-state">
                    <Bulldog size={140} mood="sleepy" />
                    <h1>Ruh-roh, page not found</h1>
                    <p className="muted">Dan dozed off and lost this page. Let's get you back to the good stuff.</p>
                    <Link to="/" className="btn">
                      Back to home
                    </Link>
                  </div>
                }
              />
            </Routes>
          </main>
          <Footer />
          <ChatWidget />
        </ChatResultsProvider>
      </AuthProvider>
    </BrowserRouter>
  )
}
