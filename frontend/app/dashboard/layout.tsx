import { UserButton } from '@clerk/nextjs'
import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const { userId } = await auth()
  if (!userId) redirect('/')

  return (
    <div className="min-h-screen bg-slate-900 text-white">
      <nav className="border-b border-slate-700 px-6 py-4 flex justify-between items-center">
        <h1 className="text-xl font-bold text-blue-400">💰 Finance Assistant</h1>
        <UserButton afterSignOutUrl="/" />
      </nav>
      <main className="max-w-7xl mx-auto p-6">
        {children}
      </main>
    </div>
  )
}