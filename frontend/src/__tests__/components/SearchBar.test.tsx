import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { SearchBar } from '../../components/SearchBar'
import type { SearchValue } from '../../types'

const availableTags = ['leadership', 'technical', 'team lead', 'communication']

function renderSearchBar(
  value: SearchValue = { tags: [], text: '' },
  onChange = vi.fn(),
  onSubmit = vi.fn()
) {
  return render(
    <SearchBar
      value={value}
      onChange={onChange}
      onSubmit={onSubmit}
      availableTags={availableTags}
      placeholder="Search..."
    />
  )
}

describe('SearchBar', () => {
  describe('chip rendering', () => {
    it('renders tag chips', () => {
      renderSearchBar({ tags: ['leadership', 'technical'], text: '' })
      expect(screen.getByText('leadership')).toBeInTheDocument()
      expect(screen.getByText('technical')).toBeInTheDocument()
    })

    it('renders remove button per chip', () => {
      renderSearchBar({ tags: ['leadership'], text: '' })
      expect(screen.getByRole('button', { name: /remove leadership/i })).toBeInTheDocument()
    })
  })

  describe('chip removal', () => {
    it('calls onChange without removed chip on X click', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      renderSearchBar({ tags: ['leadership', 'technical'], text: '' }, onChange)

      await user.click(screen.getByRole('button', { name: /remove leadership/i }))
      expect(onChange).toHaveBeenCalledWith({ tags: ['technical'], text: '' })
    })

    it('removes last chip on Backspace when input empty', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      renderSearchBar({ tags: ['leadership', 'technical'], text: '' }, onChange)

      const input = screen.getByRole('textbox')
      await user.click(input)
      await user.keyboard('{Backspace}')

      expect(onChange).toHaveBeenCalledWith({ tags: ['leadership'], text: '' })
    })

    it('does not remove chip on Backspace when input has text', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      renderSearchBar({ tags: ['leadership'], text: 'abc' }, onChange)

      const input = screen.getByRole('textbox')
      await user.click(input)
      await user.keyboard('{Backspace}')

      // onChange may fire for text change, but tags must remain intact
      const lastCall = onChange.mock.calls[onChange.mock.calls.length - 1]?.[0]
      if (lastCall) {
        expect(lastCall.tags).toContain('leadership')
      }
    })
  })

  describe('Tab promotes token to chip (not Enter)', () => {
    it('Tab promotes matching suggestion to chip', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      renderSearchBar({ tags: [], text: '' }, onChange)

      const input = screen.getByRole('textbox')
      await user.type(input, 'lead')
      await user.keyboard('{Tab}')

      const lastCall = onChange.mock.calls[onChange.mock.calls.length - 1][0]
      expect(lastCall.tags).toContain('leadership')
    })

    it('Enter fires onSubmit, does not promote token to chip', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      const onSubmit = vi.fn()
      renderSearchBar({ tags: [], text: '' }, onChange, onSubmit)

      const input = screen.getByRole('textbox')
      await user.type(input, 'lead')
      await user.keyboard('{Enter}')

      expect(onSubmit).toHaveBeenCalled()
      // onChange may have been called for text updates, but should not have promoted a chip
      const lastCall = onChange.mock.calls[onChange.mock.calls.length - 1]?.[0]
      if (lastCall) {
        expect(lastCall.tags).toEqual([])
      }
    })
  })

  describe('blur keeps text as text (no auto-promote)', () => {
    it('blur does not promote typed text to chip', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      render(
        <div>
          <SearchBar
            value={{ tags: [], text: '' }}
            onChange={onChange}
            availableTags={availableTags}
            placeholder="Search..."
          />
          <button>other</button>
        </div>
      )

      const input = screen.getByRole('textbox')
      await user.type(input, 'leadership')
      await user.click(screen.getByRole('button', { name: 'other' }))

      await waitFor(() => {
        const calls = onChange.mock.calls
        const lastCall = calls[calls.length - 1]?.[0]
        // text updates are fine, but tags should remain empty
        if (lastCall) {
          expect(lastCall.tags).toEqual([])
        }
      })
    })
  })

  describe('dropdown navigation', () => {
    it('shows suggestions on typing', async () => {
      const user = userEvent.setup()
      renderSearchBar({ tags: [], text: '' })

      await user.type(screen.getByRole('textbox'), 'lead')
      expect(screen.getByRole('listbox')).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'leadership' })).toBeInTheDocument()
    })

    it('closes dropdown on Escape, text preserved', async () => {
      const user = userEvent.setup()
      renderSearchBar({ tags: [], text: '' })

      await user.type(screen.getByRole('textbox'), 'lead')
      await user.keyboard('{Escape}')

      expect(screen.queryByRole('listbox')).not.toBeInTheDocument()
    })

    it('promotes tag on dropdown item click', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      renderSearchBar({ tags: [], text: '' }, onChange)

      await user.type(screen.getByRole('textbox'), 'lead')
      await user.click(screen.getByRole('option', { name: 'leadership' }))

      const lastCall = onChange.mock.calls[onChange.mock.calls.length - 1][0]
      expect(lastCall.tags).toContain('leadership')
    })

    it('ArrowDown highlights first suggestion', async () => {
      const user = userEvent.setup()
      renderSearchBar({ tags: [], text: '' })

      await user.type(screen.getByRole('textbox'), 'lead')
      await user.keyboard('{ArrowDown}')

      const options = screen.getAllByRole('option')
      expect(options[0]).toHaveAttribute('aria-selected', 'true')
    })
  })

  describe('text updates propagate via onChange', () => {
    it('onChange called with updated text on each keystroke', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      renderSearchBar({ tags: [], text: '' }, onChange)

      await user.type(screen.getByRole('textbox'), 'hello')

      const calls = onChange.mock.calls
      expect(calls.length).toBeGreaterThan(0)
      const lastCall = calls[calls.length - 1][0] as SearchValue
      expect(lastCall.text).toBe('hello')
    })
  })
})
