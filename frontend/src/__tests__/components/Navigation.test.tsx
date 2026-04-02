import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import Navigation from '../../components/Navigation'

function renderNav(initialPath = '/resumes') {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Navigation />
    </MemoryRouter>
  )
}

describe('Navigation', () => {
  it('renders all nav items', () => {
    renderNav()
    expect(screen.getByRole('link', { name: /resumes/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /applications/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /accomplishments/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /connect/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /notes/i })).toBeInTheDocument()
  })

  it('links to correct paths', () => {
    renderNav()
    expect(screen.getByRole('link', { name: /resumes/i })).toHaveAttribute('href', '/resumes')
    expect(screen.getByRole('link', { name: /applications/i })).toHaveAttribute('href', '/applications')
    expect(screen.getByRole('link', { name: /accomplishments/i })).toHaveAttribute('href', '/accomplishments')
    expect(screen.getByRole('link', { name: /connect/i })).toHaveAttribute('href', '/connect')
    expect(screen.getByRole('link', { name: /notes/i })).toHaveAttribute('href', '/notes')
  })

  it('marks resumes link as active when on /resumes', () => {
    renderNav('/resumes')
    const resumesLink = screen.getByRole('link', { name: /resumes/i })
    expect(resumesLink).toHaveAttribute('aria-current', 'page')
  })

  it('marks applications link as active when on /applications', () => {
    renderNav('/applications')
    const appsLink = screen.getByRole('link', { name: /applications/i })
    expect(appsLink).toHaveAttribute('aria-current', 'page')
  })

  it('marks accomplishments link as active when on /accomplishments/1 (prefix match)', () => {
    renderNav('/accomplishments/1')
    const accLink = screen.getByRole('link', { name: /accomplishments/i })
    expect(accLink).toHaveAttribute('aria-current', 'page')
  })

  it('does not mark resumes as active when on /applications', () => {
    renderNav('/applications')
    const resumesLink = screen.getByRole('link', { name: /resumes/i })
    expect(resumesLink).not.toHaveAttribute('aria-current', 'page')
  })

  it('Connect NavLink has connectItem class', () => {
    renderNav()
    const connectLink = screen.getByRole('link', { name: /connect/i })
    expect(connectLink.className).toMatch(/connectItem/)
  })

  it('renders icons in all 5 nav items', () => {
    renderNav()
    // Each NavLink should contain an SVG (lucide-react icon)
    const navLinks = screen.getAllByRole('link')
    navLinks.forEach((link) => {
      expect(link.querySelector('svg')).not.toBeNull()
    })
  })
})
