import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import Chat from '../components/Chat'
import CSVUpload from '../components/CSVUpload'
import BudgetPanel from '../components/BudgetPanel'

export default async function DashboardPage() {
  const { userId } = await auth()
  if (!userId) redirect('/')

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Chat — takes 2/3 width on large screens */}
      <div className="lg:col-span-2">
        <Chat userId={userId} />
      </div>

      {/* Right sidebar */}
      <div className="space-y-6">
        <CSVUpload userId={userId} />
        <BudgetPanel userId={userId} />
      </div>
    </div>
  )
}