import { useEffect, useRef, useState, type FormEvent } from 'react'
import { Link, matchPath, useLocation, useNavigate } from 'react-router-dom'
import {
  clearChatHistory,
  fetchChatHistory,
  formatPrice,
  imageSrc,
  sendChatMessage,
  type ChatTurn,
  type PageContext,
  type PageResults,
  type ProductSummary,
} from '../api'
import { useAuth } from '../auth'
import { useChatResults } from '../chatResults'
import { onOpenChat } from '../chatEvents'
import { Bulldog, Paw } from './Bulldog'

interface Message extends ChatTurn {
  products?: ProductSummary[]
  page?: PageResults | null
  // Shown in the panel but not sent to the agent (greeting, connection errors).
  local?: boolean
}

const GREETING: Message = {
  role: 'assistant',
  content: "Woof! I'm Dan, the Campus Customs shop pup. I can find Yale gear, check prices, and sniff out which sizes are in stock. What are you looking for?",
  local: true,
}

function greetingFor(firstName: string, hasHistory: boolean): Message {
  return {
    role: 'assistant',
    content: hasHistory
      ? `Welcome back, ${firstName}! *happy tail wag* Your earlier conversation is above. What can I fetch for you today?`
      : `Woof, hi ${firstName}! I'm Dan, the shop pup. I can find Yale gear, check prices, and sniff out sizes in stock. Your chat is saved to your account.`,
    local: true,
  }
}

function ChatProducts({ products }: { products: ProductSummary[] }) {
  return (
    <div className="chat-products">
      <p className="chat-products-label">
        Showing {products.length} item{products.length === 1 ? '' : 's'}
      </p>
      {products.map((p) => (
        <Link key={p.product_id} to={`/products/${p.product_id}`} className="chat-product">
          <img src={imageSrc(p)} alt="" />
          <span>
            <strong>{p.name}</strong>
            <small>
              {formatPrice(p.price)} · {p.total_stock > 0 ? 'In stock' : 'Sold out'}
            </small>
          </span>
        </Link>
      ))}
    </div>
  )
}

// One-tap questions that fit the page the shopper is on.
function suggestionsFor(productPage: boolean, resultsTitle: string | null): string[] {
  if (productPage) return ['Is this in stock in M?', 'What colors does this come in?', 'Show me something similar']
  if (resultsTitle) return ['Which of these is cheapest?', 'Any of these in XL?', 'Show me T-shirts instead']
  return ['What hoodies do you have?', 'Gifts under $40?', 'What is your return policy?']
}

function PageLink({ page }: { page: PageResults }) {
  const { showResults } = useChatResults()
  // Re-show these results on the page (useful for messages reloaded from history).
  return (
    <Link to="/products" className="chat-page-link" onClick={() => showResults(page, page.title)}>
      Showing {page.total} item{page.total === 1 ? '' : 's'} on the page →
    </Link>
  )
}

export default function ChatWidget() {
  const { user, loading } = useAuth()
  const { results, showResults } = useChatResults()
  const navigate = useNavigate()
  const { pathname } = useLocation()
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([GREETING])
  const [input, setInput] = useState('')
  const [thinking, setThinking] = useState(false)
  const endRef = useRef<HTMLDivElement>(null)

  // Signed in: reload saved history from the database. Logged out: start fresh as a guest.
  const userId = user?.id
  const firstName = user?.first_name ?? ''
  useEffect(() => {
    if (loading) return
    if (userId === undefined) {
      setMessages([GREETING])
      return
    }
    let cancelled = false
    fetchChatHistory()
      .then((saved) => {
        if (cancelled) return
        // Older saved replies used Markdown bold; the panel shows plain text.
        const cleaned = saved.map((m) => ({ ...m, content: m.content.replace(/\*\*/g, '') }))
        setMessages([...cleaned, greetingFor(firstName, saved.length > 0)])
      })
      .catch(() => {
        if (!cancelled) setMessages([greetingFor(firstName, false)])
      })
    return () => {
      cancelled = true
    }
  }, [userId, firstName, loading])

  const context = pageContext()
  const suggestions = suggestionsFor(context.product_id !== null, context.results_title)

  function pageContext(): PageContext {
    const productMatch = matchPath('/products/:productId', pathname)
    return {
      path: pathname,
      product_id: productMatch?.params.productId ?? null,
      results_title: pathname === '/products' && results ? results.title : null,
    }
  }

  async function handleClearHistory() {
    if (!window.confirm('Delete your saved chat history? This cannot be undone.')) return
    try {
      await clearChatHistory()
      setMessages([greetingFor(firstName, false)])
    } catch {
      setMessages((prev) => [...prev, { role: 'assistant', content: "Sorry, I couldn't clear your history just now.", local: true }])
    }
  }

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, thinking, open])

  useEffect(() => onOpenChat(() => setOpen(true)), [])

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    void send(input)
  }

  async function send(raw: string) {
    const text = raw.trim()
    if (!text || thinking) return

    // Only guests send history; for signed-in shoppers the server reads it from the database.
    const history = user ? [] : messages.filter((m) => !m.local).map(({ role, content }) => ({ role, content }))
    setMessages((prev) => [...prev, { role: 'user', content: text }])
    setInput('')
    setThinking(true)
    try {
      const { reply, products, page } = await sendChatMessage(text, history, pageContext())
      setMessages((prev) => [...prev, { role: 'assistant', content: reply, products, page }])
      if (page) {
        // Put the matches on the website itself: the Products page renders them as cards.
        showResults(page, text)
        navigate('/products')
      }
    } catch (e) {
      const detail = e instanceof Error ? e.message : ''
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: detail.startsWith('The shop assistant') ? detail : "Sorry, I couldn't reach the shop just now. Please try again.",
          local: true,
        },
      ])
    } finally {
      setThinking(false)
    }
  }

  return (
    <div className="chat-root">
      {open && (
        <section className="chat-panel" aria-label="Campus Customs chat">
          <header className="chat-header">
            <span className="chat-avatar">
              <Bulldog size={40} />
              <span className="online-dot" aria-hidden="true" />
            </span>
            <div>
              <strong>Dan · Campus Customs</strong>
              <small>
                {user ? `Signed in as ${user.first_name} ${user.last_name} · history saved` : 'Guest · sign in to save history'}
              </small>
            </div>
            {user && (
              <button className="chat-clear" onClick={handleClearHistory}>
                Clear history
              </button>
            )}
            <button className="chat-close" onClick={() => setOpen(false)} aria-label="Close chat">
              ×
            </button>
          </header>

          <div className="chat-messages">
            {messages.map((m, i) => (
              <div key={i} className={`chat-entry ${m.role}`}>
                <div className={`chat-bubble ${m.role}`}>
                  {m.role === 'assistant' && <Bulldog size={26} className="bubble-dog" />}
                  {m.content}
                </div>
                {m.products && m.products.length > 0 && <ChatProducts products={m.products} />}
                {m.page && <PageLink page={m.page} />}
              </div>
            ))}
            {thinking && (
              <div className="chat-bubble assistant typing" aria-label="Dan is looking that up">
                <Paw size={14} />
                <Paw size={14} />
                <Paw size={14} />
                <em>Dan is sniffing around…</em>
              </div>
            )}
            <div ref={endRef} />
          </div>

          {!thinking && (
            <div className="chat-suggestions" aria-label="Suggested questions">
              {suggestions.map((q) => (
                <button key={q} type="button" className="chat-suggestion" onClick={() => void send(q)}>
                  {q}
                </button>
              ))}
            </div>
          )}

          <form className="chat-input" onSubmit={handleSubmit}>
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about merch, sizes, prices…"
              aria-label="Chat message"
              maxLength={1000}
              autoFocus
            />
            <button type="submit" disabled={!input.trim() || thinking}>
              Send
            </button>
          </form>
        </section>
      )}

      <button
        className={open ? 'chat-launcher is-open' : 'chat-launcher'}
        onClick={() => setOpen((o) => !o)}
        aria-label={open ? 'Close chat' : 'Open chat'}
      >
        {open ? (
          '×'
        ) : (
          <>
            <Bulldog size={46} className="launcher-dog" />
            <span className="launcher-label">Ask Dan</span>
          </>
        )}
      </button>
    </div>
  )
}
