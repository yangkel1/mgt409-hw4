// Thin client for the FastAPI backend.

export const API_BASE: string = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export interface SizeStock {
  size: string
  quantity: number
}

export interface ProductSummary {
  product_id: string
  name: string
  garment_type: string
  price: number
  short_description: string
  colors: string[]
  image_url: string
  total_stock: number
  sizes_in_stock: string[]
}

export interface ProductDetail extends ProductSummary {
  description: string
  search_tags: string[]
  inventory: SizeStock[]
}

export interface User {
  id: number
  first_name: string
  last_name: string
  email: string
}

export interface SignupData {
  first_name: string
  last_name: string
  email: string
  password: string
}

// Matches the agent chose to show on the Products page (built from the database by the backend).
export interface PageResults {
  title: string
  search_id: string
  total: number
  products: ProductSummary[]
}

export interface ChatReply {
  reply: string
  products: ProductSummary[]
  page: PageResults | null
}

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

// credentials: 'include' sends the httpOnly session cookie set by the backend.
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    credentials: 'include',
    ...init,
    headers: init?.body ? { 'Content-Type': 'application/json', ...init.headers } : init?.headers,
  })
  if (!res.ok) {
    const body = await res.json().catch(() => null)
    const detail = typeof body?.detail === 'string' ? body.detail : res.status === 404 ? 'Not found' : `Request failed (${res.status})`
    throw new ApiError(res.status, detail)
  }
  return (res.status === 204 ? undefined : await res.json()) as T
}

const getJson = <T,>(path: string) => request<T>(path)
const postJson = <T,>(path: string, body?: unknown) =>
  request<T>(path, { method: 'POST', body: body === undefined ? undefined : JSON.stringify(body) })

export const fetchProducts = () => getJson<ProductSummary[]>('/api/products')

export const fetchProduct = (id: string) => getJson<ProductDetail>(`/api/products/${encodeURIComponent(id)}`)

export const fetchMe = () => getJson<User>('/api/auth/me')

export const login = (email: string, password: string) => postJson<User>('/api/auth/login', { email, password })

export const signup = (data: SignupData) => postJson<User>('/api/auth/signup', data)

export const logout = () => postJson<void>('/api/auth/logout')

export const imageSrc = (product: { image_url: string }) => `${API_BASE}${product.image_url}`

export const formatPrice = (price: number) => `$${price.toFixed(2)}`

export interface ChatTurn {
  role: 'user' | 'assistant'
  content: string
}

// Where the shopper is, so "do you have this in pink?" refers to the product on screen.
export interface PageContext {
  path: string
  product_id: string | null
  results_title: string | null
}

export interface StoredChatMessage extends ChatTurn {
  id: number
  products: ProductSummary[]
  page: PageResults | null
  created_at: string
}

// Guests send their earlier turns; signed-in history is loaded from the database by the server.
export const sendChatMessage = (message: string, history: ChatTurn[], page: PageContext) =>
  postJson<ChatReply>('/api/chat', { message, history: history.slice(-20), page })

export const fetchChatHistory = () => getJson<StoredChatMessage[]>('/api/chat/history')

export const clearChatHistory = () => request<void>('/api/chat/history', { method: 'DELETE' })
