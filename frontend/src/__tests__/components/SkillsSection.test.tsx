import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import SkillsSection from '../../pages/resumes/SkillsSection'
import * as api from '../../services/api'
import type { Skill } from '../../types'
import { renderWithQuery } from '../test-utils'

vi.mock('../../services/api')

const skills: Skill[] = [
  { name: 'TypeScript', category: 'Languages' },
  { name: 'React', category: 'Frameworks' },
  { name: 'Bash', category: null },
]

function renderSection(list: Skill[] = skills) {
  const onUpdate = vi.fn()
  const { rerender } = renderWithQuery(<SkillsSection skills={list} onUpdate={onUpdate} />)
  /** Stands in for the parent refetch that follows a write. */
  const refetch = (next: Skill[]) =>
    rerender(<SkillsSection skills={next} onUpdate={onUpdate} />)
  return Object.assign(onUpdate, { refetch })
}

/** Enters edit mode for a persisted category and returns its skill input. */
async function openAdder(user: ReturnType<typeof userEvent.setup>, category: string) {
  await user.click(screen.getByRole('button', { name: `Edit ${category} skills` }))
  return screen.getByRole('textbox', { name: `Add skill to ${category}` })
}

beforeEach(() => {
  vi.clearAllMocks()
  vi.mocked(api.addEntry).mockResolvedValue({ success: true, message: 'ok' })
  vi.mocked(api.removeEntry).mockResolvedValue({ success: true, message: 'ok' })
})

describe('SkillsSection — category edit mode', () => {
  it('offers one edit button per category, and no per-skill controls in view mode', () => {
    renderSection()

    expect(screen.getByRole('button', { name: 'Edit Languages skills' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Edit Frameworks skills' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /^Remove / })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Edit React' })).not.toBeInTheDocument()
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument()
  })

  it('reveals removable chips and an adder for that category only', async () => {
    const user = userEvent.setup()
    renderSection()

    await openAdder(user, 'Languages')

    expect(screen.getByRole('button', { name: 'Remove TypeScript' })).toBeInTheDocument()
    // React lives in another category — untouched
    expect(screen.queryByRole('button', { name: 'Remove React' })).not.toBeInTheDocument()
    expect(screen.getAllByRole('textbox')).toHaveLength(1)
  })

  it('leaves edit mode via done', async () => {
    const user = userEvent.setup()
    renderSection()

    await openAdder(user, 'Languages')
    await user.click(screen.getByRole('button', { name: 'done' }))

    expect(screen.queryByRole('textbox')).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Remove TypeScript' })).not.toBeInTheDocument()
  })

  it('edits one category at a time', async () => {
    const user = userEvent.setup()
    renderSection()

    await openAdder(user, 'Languages')
    await openAdder(user, 'Frameworks')

    expect(screen.getAllByRole('textbox')).toHaveLength(1)
    expect(screen.getByRole('button', { name: 'Remove React' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Remove TypeScript' })).not.toBeInTheDocument()
  })

  it('persists a skill on Enter with the category it was typed under', async () => {
    const user = userEvent.setup()
    const onUpdate = renderSection()

    const input = await openAdder(user, 'Languages')
    await user.type(input, 'Go{Enter}')

    await waitFor(() =>
      expect(api.addEntry).toHaveBeenCalledWith('skills', { name: 'Go', category: 'Languages' })
    )
    await waitFor(() => expect(onUpdate).toHaveBeenCalled())
  })

  it('persists each comma-separated name and stays open for the next', async () => {
    const user = userEvent.setup()
    renderSection()

    const input = await openAdder(user, 'Languages')
    await user.type(input, 'Go,Rust,')

    await waitFor(() => expect(api.addEntry).toHaveBeenCalledTimes(2))
    expect(api.addEntry).toHaveBeenNthCalledWith(1, 'skills', { name: 'Go', category: 'Languages' })
    expect(api.addEntry).toHaveBeenNthCalledWith(2, 'skills', {
      name: 'Rust',
      category: 'Languages',
    })
    expect(screen.getByLabelText('Add skill to Languages')).toBeInTheDocument()
  })

  it('splits a pasted separated list into one request per skill', async () => {
    const user = userEvent.setup()
    renderSection()

    const input = await openAdder(user, 'Languages')
    await user.click(input)
    await user.paste('Go, Rust; Zig\nElixir')

    await waitFor(() => expect(api.addEntry).toHaveBeenCalledTimes(4))
    expect(api.addEntry.mock.calls.map((c) => (c[1] as Skill).name)).toEqual([
      'Go',
      'Rust',
      'Zig',
      'Elixir',
    ])
  })

  it('preserves skill-name casing', async () => {
    const user = userEvent.setup()
    renderSection()

    const input = await openAdder(user, 'Languages')
    await user.type(input, 'GraphQL{Enter}')

    await waitFor(() =>
      expect(api.addEntry).toHaveBeenCalledWith('skills', {
        name: 'GraphQL',
        category: 'Languages',
      })
    )
  })

  it('commits typed text on blur', async () => {
    const user = userEvent.setup()
    renderSection()

    const input = await openAdder(user, 'Languages')
    await user.type(input, 'Go')
    await user.tab()

    await waitFor(() => expect(api.addEntry).toHaveBeenCalledTimes(1))
  })

  it('sends a null category for the "Other" catch-all group', async () => {
    const user = userEvent.setup()
    renderSection()

    const input = await openAdder(user, 'Other')
    await user.type(input, 'Make{Enter}')

    await waitFor(() =>
      expect(api.addEntry).toHaveBeenCalledWith('skills', { name: 'Make', category: null })
    )
  })

  it('skips names already on the resume, case-insensitively', async () => {
    const user = userEvent.setup()
    renderSection()

    const input = await openAdder(user, 'Languages')
    await user.click(input)
    await user.paste('typescript, Go')

    await waitFor(() => expect(api.addEntry).toHaveBeenCalledTimes(1))
    expect(api.addEntry).toHaveBeenCalledWith('skills', { name: 'Go', category: 'Languages' })
    expect(await screen.findByText('Skipped 1 already on this resume')).toBeInTheDocument()
  })

  it('skips repeats within one pasted list', async () => {
    const user = userEvent.setup()
    renderSection()

    const input = await openAdder(user, 'Languages')
    await user.click(input)
    await user.paste('Go, go, GO')

    await waitFor(() => expect(api.addEntry).toHaveBeenCalledTimes(1))
  })

  it('reports failures without aborting the rest of the batch', async () => {
    const user = userEvent.setup()
    renderSection()
    vi.mocked(api.addEntry)
      .mockRejectedValueOnce(new Error('boom'))
      .mockResolvedValueOnce({ success: true, message: 'ok' })

    const input = await openAdder(user, 'Languages')
    await user.click(input)
    await user.paste('Go, Rust')

    await waitFor(() => expect(api.addEntry).toHaveBeenCalledTimes(2))
    expect(await screen.findByText('Failed to add: Go')).toBeInTheDocument()
  })

  it('leaves edit mode on Escape', async () => {
    const user = userEvent.setup()
    renderSection()

    const input = await openAdder(user, 'Languages')
    await user.type(input, '{Escape}')

    expect(screen.queryByRole('textbox')).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Edit Languages skills' })).toBeInTheDocument()
    expect(api.addEntry).not.toHaveBeenCalled()
  })
})

describe('SkillsSection — draft category', () => {
  it('adds a client-only category that persists nothing on its own', async () => {
    const user = userEvent.setup()
    const onUpdate = renderSection()

    await user.click(screen.getByRole('button', { name: '+ Add Category' }))
    await user.type(screen.getByLabelText('New category name'), 'Cloud')

    expect(screen.getByTestId('draft-category')).toBeInTheDocument()
    expect(api.addEntry).not.toHaveBeenCalled()
    expect(onUpdate).not.toHaveBeenCalled()
  })

  it('persists the category once its first skill is added', async () => {
    const user = userEvent.setup()
    const onUpdate = renderSection()

    await user.click(screen.getByRole('button', { name: '+ Add Category' }))
    await user.type(screen.getByLabelText('New category name'), 'Cloud')
    await user.type(screen.getByLabelText('Add skill to new category'), 'Terraform{Enter}')

    await waitFor(() =>
      expect(api.addEntry).toHaveBeenCalledWith('skills', {
        name: 'Terraform',
        category: 'Cloud',
      })
    )
    await waitFor(() => expect(onUpdate).toHaveBeenCalled())
  })

  it('keeps the draft mounted until the refetch shows the category', async () => {
    const user = userEvent.setup()
    const onUpdate = renderSection()

    await user.click(screen.getByRole('button', { name: '+ Add Category' }))
    await user.type(screen.getByLabelText('New category name'), 'Cloud')
    await user.type(screen.getByLabelText('Add skill to new category'), 'Terraform{Enter}')
    await waitFor(() => expect(onUpdate).toHaveBeenCalled())

    // Write is done but the new skill hasn't arrived yet — draft still holds focus
    expect(screen.getByTestId('draft-category')).toBeInTheDocument()
    expect(screen.getByLabelText('Add skill to new category')).toHaveFocus()

    onUpdate.refetch([...skills, { name: 'Terraform', category: 'Cloud' }])

    // Draft hands over to the real group, which stays in edit mode
    expect(screen.queryByTestId('draft-category')).not.toBeInTheDocument()
    expect(screen.getByRole('textbox', { name: 'Add skill to Cloud' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Remove Terraform' })).toBeInTheDocument()
  })

  it('moves focus from the name field to the skill input on Enter', async () => {
    const user = userEvent.setup()
    renderSection()

    await user.click(screen.getByRole('button', { name: '+ Add Category' }))
    await user.type(screen.getByLabelText('New category name'), 'Cloud{Enter}')

    expect(screen.getByLabelText('Add skill to new category')).toHaveFocus()
  })

  it('moves focus from the name field to the skill input on Tab', async () => {
    const user = userEvent.setup()
    renderSection()

    await user.click(screen.getByRole('button', { name: '+ Add Category' }))
    await user.type(screen.getByLabelText('New category name'), 'Cloud')
    await user.tab()

    expect(screen.getByLabelText('Add skill to new category')).toHaveFocus()
  })

  it('keeps focus on the name field when it is still empty', async () => {
    const user = userEvent.setup()
    renderSection()

    await user.click(screen.getByRole('button', { name: '+ Add Category' }))
    const nameInput = screen.getByLabelText('New category name')
    await user.type(nameInput, '{Enter}')

    expect(nameInput).toHaveFocus()
    expect(await screen.findByText('Name the category first')).toBeInTheDocument()
  })

  it('types a whole category without leaving the keyboard', async () => {
    const user = userEvent.setup()
    renderSection()

    await user.click(screen.getByRole('button', { name: '+ Add Category' }))
    await user.keyboard('Cloud{Enter}Terraform{Enter}Pulumi{Enter}')

    await waitFor(() => expect(api.addEntry).toHaveBeenCalledTimes(2))
    expect(api.addEntry.mock.calls.map((c) => c[1])).toEqual([
      { name: 'Terraform', category: 'Cloud' },
      { name: 'Pulumi', category: 'Cloud' },
    ])
  })

  it('discards the draft on Escape in the name field', async () => {
    const user = userEvent.setup()
    renderSection()

    await user.click(screen.getByRole('button', { name: '+ Add Category' }))
    await user.type(screen.getByLabelText('New category name'), 'Cloud{Escape}')

    expect(screen.queryByTestId('draft-category')).not.toBeInTheDocument()
    expect(api.addEntry).not.toHaveBeenCalled()
  })

  it('refuses to add a skill before the category is named', async () => {
    const user = userEvent.setup()
    renderSection()

    await user.click(screen.getByRole('button', { name: '+ Add Category' }))
    await user.type(screen.getByLabelText('Add skill to new category'), 'Terraform{Enter}')

    expect(await screen.findByText('Name the category first')).toBeInTheDocument()
    expect(api.addEntry).not.toHaveBeenCalled()
    expect(screen.getByTestId('draft-category')).toBeInTheDocument()
  })

  it('discards the draft without persisting anything', async () => {
    const user = userEvent.setup()
    renderSection()

    await user.click(screen.getByRole('button', { name: '+ Add Category' }))
    await user.type(screen.getByLabelText('New category name'), 'Cloud')
    await user.click(screen.getByRole('button', { name: 'Discard new category' }))

    expect(screen.queryByTestId('draft-category')).not.toBeInTheDocument()
    expect(api.addEntry).not.toHaveBeenCalled()
  })

  it('shows a draft group even when the resume has no skills yet', async () => {
    const user = userEvent.setup()
    renderSection([])

    await user.click(screen.getByRole('button', { name: '+ Add Category' }))

    expect(screen.getByTestId('draft-category')).toBeInTheDocument()
    expect(screen.getByLabelText('Add skill to new category')).toBeInTheDocument()
  })
})

describe('SkillsSection — remove with undo', () => {
  it('removes immediately with no confirmation dialog', async () => {
    const user = userEvent.setup()
    const onUpdate = renderSection()

    await openAdder(user, 'Frameworks')
    await user.click(screen.getByRole('button', { name: 'Remove React' }))

    await waitFor(() => expect(api.removeEntry).toHaveBeenCalledWith('skills', 1))
    await waitFor(() => expect(onUpdate).toHaveBeenCalled())
  })

  it('offers an Undo action that re-adds the removed skill', async () => {
    const user = userEvent.setup()
    renderSection()

    await openAdder(user, 'Frameworks')
    await user.click(screen.getByRole('button', { name: 'Remove React' }))
    await user.click(await screen.findByRole('button', { name: 'Undo' }))

    await waitFor(() =>
      expect(api.addEntry).toHaveBeenCalledWith('skills', {
        name: 'React',
        category: 'Frameworks',
      })
    )
  })

  it('surfaces an error and skips the undo toast when removal fails', async () => {
    const user = userEvent.setup()
    const onUpdate = renderSection()
    vi.mocked(api.removeEntry).mockRejectedValue(new Error('nope'))

    await openAdder(user, 'Frameworks')
    await user.click(screen.getByRole('button', { name: 'Remove React' }))

    expect(await screen.findByText('nope')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Undo' })).not.toBeInTheDocument()
    expect(onUpdate).not.toHaveBeenCalled()
  })
})

describe('SkillsSection — grouping', () => {
  it('pins the "Other" catch-all group last', () => {
    renderSection([
      { name: 'Bash', category: null },
      { name: 'Zig', category: 'Languages' },
      { name: 'Docker', category: 'Tooling' },
    ])

    const labels = screen.getAllByText(/^(Languages|Tooling|Other)$/).map((el) => el.textContent)
    expect(labels).toEqual(['Languages', 'Tooling', 'Other'])
  })
})
