import { SignInButton, SignUpButton } from '@clerk/nextjs'
import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'

export default async function Home() {
  const { userId } = await auth()
  if (userId) redirect('/dashboard')

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 flex items-center justify-center">
      <div className="text-center text-white p-8">
        <h1 className="text-5xl font-bold mb-4">Finance Assistant</h1>
        <p className="text-xl text-slate-300 mb-8">
          Your AI-powered personal finance companion
        </p>
        <div className="flex gap-4 justify-center">
          <SignInButton mode="modal">
            <button className="bg-white text-slate-900 px-8 py-3 rounded-lg font-semibold hover:bg-slate-100 transition">
              Sign In
            </button>
          </SignInButton>
          <SignUpButton mode="modal">
            <button className="bg-blue-500 text-white px-8 py-3 rounded-lg font-semibold hover:bg-blue-600 transition">
              Get Started
            </button>
          </SignUpButton>
        </div>
      </div>
    </main>
  )
}