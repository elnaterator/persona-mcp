import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import Breadcrumb from '../components/Breadcrumb'

function renderBreadcrumb(items: { label: string; to?: string }[]) {
  return render(
    <MemoryRouter>
      <Breadcrumb items={items} />
    </MemoryRouter>
  )
}

describe('Breadcrumb', () => {
  it('renders nothing for empty items', () => {
    const { container } = renderBreadcrumb([])
    expect(container.firstChild).toBeNull()
  })

  it('renders a single item as plain text (no link)', () => {
    renderBreadcrumb([{ label: 'Resumes' }])
    expect(screen.getByText('Resumes')).toBeInTheDocument()
    expect(screen.queryByRole('link')).toBeNull()
  })

  it('renders clickable link for non-last items with a to prop', () => {
    renderBreadcrumb([
      { label: 'Resumes', to: '/resumes' },
      { label: 'Version 1' },
    ])
    const link = screen.getByRole('link', { name: 'Resumes' })
    expect(link).toBeInTheDocument()
    expect(link).toHaveAttribute('href', '/resumes')
  })

  it('renders last item as plain text even with a to prop', () => {
    renderBreadcrumb([
      { label: 'Resumes', to: '/resumes' },
      { label: 'Version 1', to: '/resumes/1' },
    ])
    // "Resumes" should be a link, "Version 1" should be plain text
    expect(screen.getByRole('link', { name: 'Resumes' })).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'Version 1' })).toBeNull()
    expect(screen.getByText('Version 1')).toBeInTheDocument()
  })

  it('renders separators between items', () => {
    renderBreadcrumb([
      { label: 'Applications', to: '/applications' },
      { label: 'Acme Corp — Engineer' },
    ])
    expect(screen.getByText('>')).toBeInTheDocument()
  })

  it('renders multiple items with correct links', () => {
    renderBreadcrumb([
      { label: 'Accomplishments', to: '/accomplishments' },
      { label: 'Led migration' },
    ])
    expect(screen.getByRole('link', { name: 'Accomplishments' })).toHaveAttribute('href', '/accomplishments')
    expect(screen.getByText('Led migration')).toBeInTheDocument()
  })
})
