'use client'

import { useState } from 'react'
import { uploadCSV } from '../lib/api'
import { Upload } from 'lucide-react'

export default function CSVUpload({ userId }: { userId: string }) {
  const [status, setStatus] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setLoading(true)
    setStatus(null)

    try {
      const result = await uploadCSV(userId, file)
      setStatus(`✅ Successfully imported ${result.imported} transactions`)
    } catch (err) {
      setStatus('❌ Failed to import. Make sure it is a valid CSV file.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-slate-800 rounded-xl border border-slate-700 p-6">
      <h2 className="text-lg font-semibold mb-4">Import Transactions</h2>
      <label className="flex flex-col items-center justify-center border-2 border-dashed border-slate-600 rounded-lg p-8 cursor-pointer hover:border-blue-500 transition">
        <Upload size={32} className="text-slate-400 mb-2" />
        <span className="text-slate-400 text-sm">
          {loading ? 'Importing...' : 'Click to upload CSV file'}
        </span>
        <input type="file" accept=".csv" onChange={handleFile} className="hidden" />
      </label>
      {status && (
        <p className="mt-4 text-sm text-center">{status}</p>
      )}
    </div>
  )
}