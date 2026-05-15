import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { FieldError } from '../../components/FieldError'

describe('FieldError', () => {
  it('renders message with role="alert"', () => {
    render(<FieldError error={{ message: 'This field is required', type: 'required' }} />)
    const alert = screen.getByRole('alert')
    expect(alert).toBeInTheDocument()
    expect(alert).toHaveTextContent('This field is required')
  })

  it('renders nothing when error is undefined', () => {
    const { container } = render(<FieldError error={undefined} />)
    expect(container).toBeEmptyDOMElement()
  })

  it('renders nothing when message is empty', () => {
    const { container } = render(<FieldError error={{ message: '', type: 'required' }} />)
    expect(container).toBeEmptyDOMElement()
  })

  it('renders nothing when error has no message', () => {
    const { container } = render(<FieldError error={{ type: 'required' } as import('react-hook-form').FieldError} />)
    expect(container).toBeEmptyDOMElement()
  })
})
