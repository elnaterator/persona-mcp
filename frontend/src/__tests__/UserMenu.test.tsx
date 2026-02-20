import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import UserMenu from '../components/UserMenu'

vi.mock('@clerk/clerk-react', () => ({
  useAuth: vi.fn(),
  UserButton: ({ afterSignOutUrl }: { afterSignOutUrl: string }) => (
    <div data-testid="user-button" data-after-sign-out-url={afterSignOutUrl} />
  ),
}))

const { useAuth } = await import('@clerk/clerk-react')

describe('UserMenu', () => {
  it('renders UserButton when signed in', () => {
    vi.mocked(useAuth).mockReturnValue({
      isSignedIn: true,
      isLoaded: true,
    } as ReturnType<typeof useAuth>)

    render(<UserMenu />)

    expect(screen.getByTestId('user-button')).toBeInTheDocument()
  })

  it('renders UserButton with afterSignOutUrl set to /', () => {
    vi.mocked(useAuth).mockReturnValue({
      isSignedIn: true,
      isLoaded: true,
    } as ReturnType<typeof useAuth>)

    render(<UserMenu />)

    expect(screen.getByTestId('user-button')).toHaveAttribute('data-after-sign-out-url', '/')
  })

  it('renders nothing when signed out', () => {
    vi.mocked(useAuth).mockReturnValue({
      isSignedIn: false,
      isLoaded: true,
    } as ReturnType<typeof useAuth>)

    const { container } = render(<UserMenu />)

    expect(container).toBeEmptyDOMElement()
    expect(screen.queryByTestId('user-button')).not.toBeInTheDocument()
  })
})
