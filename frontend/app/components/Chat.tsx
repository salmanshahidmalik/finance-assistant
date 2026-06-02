'use client'

import { useState, useEffect, useRef } from 'react'
import { sendMessage, getChatHistory } from '../lib/api'
import { Send, Paperclip } from 'lucide-react'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

export default function Chat({ userId }: { userId: string }) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [imageData, setImageData] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    getChatHistory(userId).then((history) => {
      setMessages(history)
    })
  }, [userId])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() && !imageData) return
    const userMessage = input.trim()
    setInput('')
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }])
    setLoading(true)

    try {
      const data = await sendMessage(userId, userMessage, imageData || undefined)
      setMessages((prev) => [...prev, { role: 'assistant', content: data.response }])
      setImageData(null)
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Sorry, something went wrong. Please try again.' },
      ])
    } finally {
      setLoading(false)
    }
  }

  const handleImage = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = () => {
      const base64 = (reader.result as string).split(',')[1]
      setImageData(base64)
    }
    reader.readAsDataURL(file)
  }

  return (
    <div className="flex flex-col h-[600px] bg-slate-800 rounded-xl border border-slate-700">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-slate-400 mt-20">
            <p className="text-2xl mb-2">👋</p>
            <p>Ask me anything about your finances!</p>
            <p className="text-sm mt-2">Try: "How much did I spend on groceries last month?"</p>
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-[80%] rounded-xl px-4 py-3 text-sm whitespace-pre-wrap ${
                msg.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-700 text-slate-100'
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-slate-700 rounded-xl px-4 py-3 text-sm text-slate-400">
              Thinking...
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Image preview */}
      {imageData && (
        <div className="px-4 py-2 bg-slate-750 border-t border-slate-700">
          <span className="text-xs text-green-400">✓ Image attached — ready to send</span>
          <button onClick={() => setImageData(null)} className="ml-2 text-xs text-red-400">Remove</button>
        </div>
      )}

      {/* Input */}
      <div className="border-t border-slate-700 p-4 flex gap-2">
        <input
          type="file"
          accept="image/*"
          ref={fileRef}
          onChange={handleImage}
          className="hidden"
        />
        <button
          onClick={() => fileRef.current?.click()}
          className="p-2 text-slate-400 hover:text-white transition"
          title="Upload receipt"
        >
          <Paperclip size={20} />
        </button>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Ask about your finances..."
          className="flex-1 bg-slate-700 rounded-lg px-4 py-2 text-sm outline-none text-white placeholder-slate-400"
        />
        <button
          onClick={handleSend}
          disabled={loading}
          className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 p-2 rounded-lg transition"
        >
          <Send size={20} />
        </button>
      </div>
    </div>
  )
}