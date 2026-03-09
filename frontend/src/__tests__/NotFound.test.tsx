import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import NotFound from '../components/NotFound'

function renderNotFound(props: { entityName: string; backTo: string; backLabel: string }) {
  return render(
    <MemoryRouter>
      <NotFound {...props} />
    </MemoryRouter>
  )
}

describe('NotFound', () => {
  it('renders the entity name in the heading', () => {
    renderNotFound({ entityName: 'Resume', backTo: '/resumes', backLabel: 'Back to Resumes' })
    expect(screen.getByRole('heading')).toHaveTextContent('Resume not found')
  })

  it('renders the back link with correct label', () => {
    renderNotFound({ entityName: 'Application', backTo: '/applications', backLabel: 'Back to Applications' })
    const link = screen.getByRole('link', { name: 'Back to Applications' })
    expect(link).toBeInTheDocument()
    expect(link).toHaveAttribute('href', '/applications')
  })

  it('renders with Accomplishment entity name', () => {
    renderNotFound({ entityName: 'Accomplishment', backTo: '/accomplishments', backLabel: 'Back to Accomplishments' })
    expect(screen.getByTestId('not-found')).toBeInTheDocument()
    expect(screen.getByRole('heading')).toHaveTextContent('Accomplishment not found')
  })

  it('renders a message referencing the entity name lowercased', () => {
    renderNotFound({ entityName: 'Resume', backTo: '/resumes', backLabel: 'Back to Resumes' })
    expect(screen.getByText(/resume you're looking for/i)).toBeInTheDocument()
  })
})
