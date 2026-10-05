// Lets any page open the floating chat (e.g. "Ask about this item" on a product page).
const OPEN_CHAT = 'campus-customs:open-chat'

export function openChat() {
  window.dispatchEvent(new Event(OPEN_CHAT))
}

export function onOpenChat(handler: () => void) {
  window.addEventListener(OPEN_CHAT, handler)
  return () => window.removeEventListener(OPEN_CHAT, handler)
}
