import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { TagInput } from '../../components/TagInput'

const availableTags = ['leadership', 'technical', 'team lead', 'communication']

function renderInput(
  value: string[] = [],
  onChange = vi.fn(),
  options: { allowCreate?: boolean; placeholder?: string } = {}
) {
  return render(
    <TagInput
      value={value}
      onChange={onChange}
      availableTags={availableTags}
      allowCreate={options.allowCreate ?? true}
      placeholder={options.placeholder ?? 'Add tag...'}
    />
  )
}

describe('TagInput', () => {
  describe('chip rendering', () => {
    it('renders chips for initial value array', () => {
      renderInput(['leadership', 'technical'])
      expect(screen.getByText('leadership')).toBeInTheDocument()
      expect(screen.getByText('technical')).toBeInTheDocument()
    })

    it('renders remove button for each chip', () => {
      renderInput(['leadership', 'technical'])
      const removeButtons = screen.getAllByRole('button', { name: /remove/i })
      expect(removeButtons).toHaveLength(2)
    })

    it('renders empty without initial chips', () => {
      renderInput([])
      expect(screen.queryAllByRole('button', { name: /remove/i })).toHaveLength(0)
    })
  })

  describe('chip removal', () => {
    it('calls onChange without removed chip when x clicked', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      renderInput(['leadership', 'technical'], onChange)

      const removeButtons = screen.getAllByRole('button', { name: /remove leadership/i })
      await user.click(removeButtons[0])

      expect(onChange).toHaveBeenCalledWith(['technical'])
    })

    it('calls onChange with empty array when only chip removed', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      renderInput(['leadership'], onChange)

      const removeButton = screen.getByRole('button', { name: /remove leadership/i })
      await user.click(removeButton)

      expect(onChange).toHaveBeenCalledWith([])
    })
  })

  describe('commit via Enter', () => {
    it('commits typed text as chip on Enter and clears input', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      renderInput([], onChange)

      const input = screen.getByRole('textbox')
      await user.type(input, 'newskill')
      await user.keyboard('{Enter}')

      expect(onChange).toHaveBeenCalledWith(['newskill'])
    })

    it('normalizes to lowercase on Enter commit', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      renderInput([], onChange)

      const input = screen.getByRole('textbox')
      await user.type(input, 'Leadership')
      await user.keyboard('{Enter}')

      expect(onChange).toHaveBeenCalledWith(['leadership'])
    })

    it('does not commit empty string on Enter', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      renderInput([], onChange)

      const input = screen.getByRole('textbox')
      await user.click(input)
      await user.keyboard('{Enter}')

      expect(onChange).not.toHaveBeenCalled()
    })

    it('does not commit whitespace-only input on Enter', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      renderInput([], onChange)

      const input = screen.getByRole('textbox')
      await user.type(input, '   ')
      await user.keyboard('{Enter}')

      expect(onChange).not.toHaveBeenCalled()
    })
  })

  describe('commit via comma', () => {
    it('commits typed text as chip on comma', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      renderInput([], onChange)

      const input = screen.getByRole('textbox')
      await user.type(input, 'newskill,')

      expect(onChange).toHaveBeenCalledWith(['newskill'])
    })

    it('normalizes to lowercase on comma commit', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      renderInput([], onChange)

      const input = screen.getByRole('textbox')
      await user.type(input, 'Leadership,')

      expect(onChange).toHaveBeenCalledWith(['leadership'])
    })
  })

  describe('duplicate prevention', () => {
    it('does not add duplicate chip (exact match)', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      renderInput(['leadership'], onChange)

      const input = screen.getByRole('textbox')
      await user.type(input, 'leadership')
      await user.keyboard('{Enter}')

      expect(onChange).not.toHaveBeenCalled()
    })

    it('does not add duplicate chip (case-insensitive)', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      renderInput(['leadership'], onChange)

      const input = screen.getByRole('textbox')
      await user.type(input, 'LEADERSHIP')
      await user.keyboard('{Enter}')

      expect(onChange).not.toHaveBeenCalled()
    })
  })

  describe('multi-word tags', () => {
    it('allows spaces in tag text (Space does not commit)', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      renderInput([], onChange)

      const input = screen.getByRole('textbox')
      await user.type(input, 'team lead')
      // space should not have committed anything
      expect(onChange).not.toHaveBeenCalled()
      expect(input).toHaveValue('team lead')
    })

    it('commits multi-word tag on Enter', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      renderInput([], onChange)

      const input = screen.getByRole('textbox')
      await user.type(input, 'team lead')
      await user.keyboard('{Enter}')

      expect(onChange).toHaveBeenCalledWith(['team lead'])
    })
  })

  describe('autocomplete dropdown', () => {
    it('shows matching tags in dropdown on typing', async () => {
      const user = userEvent.setup()
      renderInput([])

      const input = screen.getByRole('textbox')
      await user.type(input, 'lead')

      expect(screen.getByText('leadership')).toBeInTheDocument()
      expect(screen.getByText('team lead')).toBeInTheDocument()
      // non-matching not shown in dropdown (but 'technical' and 'communication' shouldn't match 'lead')
      expect(screen.queryByRole('option', { name: 'technical' })).not.toBeInTheDocument()
    })

    it('hides dropdown when input is empty', async () => {
      const user = userEvent.setup()
      renderInput([])

      const input = screen.getByRole('textbox')
      await user.click(input)
      // no dropdown without text
      expect(screen.queryByRole('listbox')).not.toBeInTheDocument()
    })

    it('closes dropdown on Escape and keeps typed text', async () => {
      const user = userEvent.setup()
      renderInput([])

      const input = screen.getByRole('textbox')
      await user.type(input, 'lead')
      expect(screen.getByRole('listbox')).toBeInTheDocument()

      await user.keyboard('{Escape}')
      expect(screen.queryByRole('listbox')).not.toBeInTheDocument()
      expect(input).toHaveValue('lead')
    })

    it('commits tag on dropdown item click', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      renderInput([], onChange)

      const input = screen.getByRole('textbox')
      await user.type(input, 'lead')

      const option = screen.getByRole('option', { name: 'leadership' })
      await user.click(option)

      expect(onChange).toHaveBeenCalledWith(['leadership'])
    })

    it('excludes already-selected tags from dropdown', async () => {
      const user = userEvent.setup()
      renderInput(['leadership'])

      const input = screen.getByRole('textbox')
      await user.type(input, 'lead')

      // 'leadership' is already selected, should not appear as an option
      expect(screen.queryByRole('option', { name: 'leadership' })).not.toBeInTheDocument()
    })
  })

  describe('create new tag option', () => {
    it('shows "Create new tag" option when allowCreate=true and input non-empty', async () => {
      const user = userEvent.setup()
      renderInput([], vi.fn(), { allowCreate: true })

      const input = screen.getByRole('textbox')
      await user.type(input, 'brandnew')

      expect(screen.getByText(/create new tag.*brandnew/i)).toBeInTheDocument()
    })

    it('does not show "Create new tag" option when allowCreate=false', async () => {
      const user = userEvent.setup()
      renderInput([], vi.fn(), { allowCreate: false })

      const input = screen.getByRole('textbox')
      await user.type(input, 'brandnew')

      expect(screen.queryByText(/create new tag/i)).not.toBeInTheDocument()
    })

    it('commits new tag when "Create new tag" option clicked', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      renderInput([], onChange, { allowCreate: true })

      const input = screen.getByRole('textbox')
      await user.type(input, 'brandnew')

      const createOption = screen.getByText(/create new tag.*brandnew/i)
      await user.click(createOption)

      expect(onChange).toHaveBeenCalledWith(['brandnew'])
    })

    it('shows "Create new tag" even when input matches an existing tag exactly', async () => {
      const user = userEvent.setup()
      renderInput([], vi.fn(), { allowCreate: true })

      const input = screen.getByRole('textbox')
      await user.type(input, 'leadership')

      expect(screen.getByText(/create new tag.*leadership/i)).toBeInTheDocument()
    })
  })

  describe('backspace removal', () => {
    it('removes last chip when input is empty and Backspace pressed', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      renderInput(['leadership', 'technical'], onChange)

      const input = screen.getByRole('textbox')
      await user.click(input)
      await user.keyboard('{Backspace}')

      expect(onChange).toHaveBeenCalledWith(['leadership'])
    })

    it('does not remove chip when input has text and Backspace pressed', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      renderInput(['leadership'], onChange)

      const input = screen.getByRole('textbox')
      await user.type(input, 'abc')
      await user.keyboard('{Backspace}')

      expect(onChange).not.toHaveBeenCalled()
    })

    it('does nothing on Backspace when no chips exist', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      renderInput([], onChange)

      const input = screen.getByRole('textbox')
      await user.click(input)
      await user.keyboard('{Backspace}')

      expect(onChange).not.toHaveBeenCalled()
    })
  })

  describe('keyboard navigation', () => {
    it('ArrowDown highlights first suggestion', async () => {
      const user = userEvent.setup()
      renderInput([])

      const input = screen.getByRole('textbox')
      await user.type(input, 'lead')
      await user.keyboard('{ArrowDown}')

      const options = screen.getAllByRole('option')
      expect(options[0]).toHaveAttribute('aria-selected', 'true')
    })

    it('ArrowDown then ArrowUp returns to no selection', async () => {
      const user = userEvent.setup()
      renderInput([])

      const input = screen.getByRole('textbox')
      await user.type(input, 'lead')
      await user.keyboard('{ArrowDown}')
      await user.keyboard('{ArrowUp}')

      const options = screen.getAllByRole('option')
      options.forEach((opt) => expect(opt).toHaveAttribute('aria-selected', 'false'))
    })

    it('Enter commits highlighted suggestion (not typed text)', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      renderInput([], onChange)

      const input = screen.getByRole('textbox')
      await user.type(input, 'lead')
      await user.keyboard('{ArrowDown}') // highlights 'leadership'
      await user.keyboard('{Enter}')

      expect(onChange).toHaveBeenCalledWith(['leadership'])
    })

    it('Tab completes first suggestion when no item highlighted', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      renderInput([], onChange)

      const input = screen.getByRole('textbox')
      await user.type(input, 'lead')
      await user.keyboard('{Tab}')

      expect(onChange).toHaveBeenCalledWith(['leadership'])
    })

    it('Tab completes highlighted suggestion', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      renderInput([], onChange)

      const input = screen.getByRole('textbox')
      await user.type(input, 'lead')
      await user.keyboard('{ArrowDown}') // 'leadership'
      await user.keyboard('{ArrowDown}') // 'team lead'
      await user.keyboard('{Tab}')

      expect(onChange).toHaveBeenCalledWith(['team lead'])
    })

    it('ArrowDown resets when input text changes', async () => {
      const user = userEvent.setup()
      renderInput([])

      const input = screen.getByRole('textbox')
      await user.type(input, 'lead')
      await user.keyboard('{ArrowDown}')
      await user.type(input, 'x') // mutate input

      const options = screen.getAllByRole('option')
      options.forEach((opt) => expect(opt).toHaveAttribute('aria-selected', 'false'))
    })
  })

  describe('blur behavior', () => {
    it('commits non-empty typed text on blur', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      render(
        <div>
          <TagInput value={[]} onChange={onChange} availableTags={[]} />
          <button>other</button>
        </div>
      )

      const input = screen.getByRole('textbox')
      await user.type(input, 'newskill')
      await user.click(screen.getByRole('button', { name: 'other' }))

      await waitFor(() => {
        expect(onChange).toHaveBeenCalledWith(['newskill'])
      })
    })

    it('does not commit empty input on blur', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      render(
        <div>
          <TagInput value={[]} onChange={onChange} availableTags={[]} />
          <button>other</button>
        </div>
      )

      const input = screen.getByRole('textbox')
      await user.click(input)
      await user.click(screen.getByRole('button', { name: 'other' }))

      await waitFor(() => {
        expect(onChange).not.toHaveBeenCalled()
      })
    })
  })
})
