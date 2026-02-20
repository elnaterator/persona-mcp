import { useAuth, UserButton } from '@clerk/clerk-react'

export default function UserMenu() {
  const { isSignedIn } = useAuth()

  if (!isSignedIn) {
    return null
  }

  return <UserButton afterSignOutUrl="/" />
}
