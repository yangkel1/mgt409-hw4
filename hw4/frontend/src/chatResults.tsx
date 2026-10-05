import { createContext, useContext, useState, type ReactNode } from 'react'
import type { PageResults } from './api'

// Products the chat put on the page, plus the shopper message that asked for them.
export interface ChatResults extends PageResults {
  question: string
  receivedAt: number
}

interface ChatResultsState {
  results: ChatResults | null
  showResults: (page: PageResults, question: string) => void
  clearResults: () => void
}

const ChatResultsContext = createContext<ChatResultsState | null>(null)

export function ChatResultsProvider({ children }: { children: ReactNode }) {
  const [results, setResults] = useState<ChatResults | null>(null)

  const value: ChatResultsState = {
    results,
    showResults: (page, question) => setResults({ ...page, question, receivedAt: Date.now() }),
    clearResults: () => setResults(null),
  }
  return <ChatResultsContext.Provider value={value}>{children}</ChatResultsContext.Provider>
}

export function useChatResults() {
  const ctx = useContext(ChatResultsContext)
  if (!ctx) throw new Error('useChatResults must be used inside <ChatResultsProvider>')
  return ctx
}
