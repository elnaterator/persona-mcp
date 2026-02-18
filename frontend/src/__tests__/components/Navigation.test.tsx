import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import Navigation from '../../components/Navigation'

describe('Navigation', () => {
  it('renders Resumes and Applications tabs', () => {
    render(<Navigation activeView="resumes" onNavigate={vi.fn()} />)

    expect(screen.getByRole('button', { name: /resumes/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /applications/i })).toBeInTheDocument()
  })

  it('marks resumes tab as active when activeView is resumes', () => {
    render(<Navigation activeView="resumes" onNavigate={vi.fn()} />)

    const resumesBtn = screen.getByRole('button', { name: /resumes/i })
    expect(resumesBtn).toHaveAttribute('aria-current', 'page')
    expect(screen.getByRole('button', { name: /applications/i })).not.toHaveAttribute('aria-current')
  })

  it('marks applications tab as active when activeView is applications', () => {
    render(<Navigation activeView="applications" onNavigate={vi.fn()} />)

    const appsBtn = screen.getByRole('button', { name: /applications/i })
    expect(appsBtn).toHaveAttribute('aria-current', 'page')
    expect(screen.getByRole('button', { name: /resumes/i })).not.toHaveAttribute('aria-current')
  })

  it('calls onNavigate with resumes when Resumes tab is clicked', async () => {
    const user = userEvent.setup()
    const onNavigate = vi.fn()
    render(<Navigation activeView="applications" onNavigate={onNavigate} />)

    await user.click(screen.getByRole('button', { name: /resumes/i }))
    expect(onNavigate).toHaveBeenCalledWith('resumes')
  })

  it('calls onNavigate with applications when Applications tab is clicked', async () => {
    const user = userEvent.setup()
    const onNavigate = vi.fn()
    render(<Navigation activeView="resumes" onNavigate={onNavigate} />)

    await user.click(screen.getByRole('button', { name: /applications/i }))
    expect(onNavigate).toHaveBeenCalledWith('applications')
  })
})
