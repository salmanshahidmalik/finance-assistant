'use client'

import { useState, useEffect } from 'react'
import { getBudgets, createBudget } from '../lib/api'

interface Budget {
  id: string
  category: string
  amount: number
  spent: number
  remaining: number
  percentage: number
}

export default function BudgetPanel({ userId }: { userId: string }) {
  const [budgets, setBudgets] = useState<Budget[]>([])
  const [category, setCategory] = useState('')
  const [amount, setAmount] = useState('')
  const [loading, setLoading] = useState(false)

  const fetchBudgets = async () => {
    const data = await getBudgets(userId)
    setBudgets(data)
  }

  useEffect(() => {
    fetchBudgets()
  }, [userId])

  const handleCreate = async () => {
    if (!category || !amount) return
    setLoading(true)
    await createBudget(userId, category, parseFloat(amount))
    setCategory('')
    setAmount('')
    await fetchBudgets()
    setLoading(false)
  }

  return (
    <div className="bg-slate-800 rounded-xl border border-slate-700 p-6">
      <h2 className="text-lg font-semibold mb-4">Budget Tracker</h2>

      {/* Add budget */}
      <div className="flex gap-2 mb-6">
        <input
          type="text"
          placeholder="Category (e.g. Groceries)"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="flex-1 bg-slate-700 rounded-lg px-3 py-2 text-sm outline-none"
        />
        <input
          type="number"
          placeholder="Limit ($)"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          className="w-28 bg-slate-700 rounded-lg px-3 py-2 text-sm outline-none"
        />
        <button
          onClick={handleCreate}
          disabled={loading}
          className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg text-sm font-medium transition"
        >
          Add
        </button>
      </div>

      {/* Budget list */}
      <div className="space-y-4">
        {budgets.length === 0 && (
          <p className="text-slate-400 text-sm text-center">No budgets set yet.</p>
        )}
        {budgets.map((b) => (
          <div key={b.id}>
            <div className="flex justify-between text-sm mb-1">
              <span>{b.category}</span>
              <span className={b.percentage > 90 ? 'text-red-400' : b.percentage > 70 ? 'text-yellow-400' : 'text-green-400'}>
                ${b.spent.toFixed(0)} / ${b.amount.toFixed(0)}
              </span>
            </div>
            <div className="w-full bg-slate-700 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all ${
                  b.percentage > 90 ? 'bg-red-500' : b.percentage > 70 ? 'bg-yellow-500' : 'bg-green-500'
                }`}
                style={{ width: `${Math.min(b.percentage, 100)}%` }}
              />
            </div>
            {b.percentage > 90 && (
              <p className="text-red-400 text-xs mt-1">⚠️ Almost at limit!</p>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}