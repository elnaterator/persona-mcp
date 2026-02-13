import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ExperienceSection from '../../components/ExperienceSection'
import type { WorkExperience } from '../../types/resume'
import * as api from '../../services/api'

vi.mock('../../services/api')

const mockExperience: WorkExperience[] = [
  {
    title: 'Senior Engineer',
    company: 'Tech Corp',
    start_date: '2020-01',
    end_date: '2023-12',
    location: 'San Francisco, CA',
    highlights: ['Led team of 5', 'Built key features'],
  },
  {
    title: 'Software Developer',
    company: 'StartupCo',
    start_date: '2018-06',
    end_date: '2020-01',
    location: 'Austin, TX',
    highlights: ['Developed mobile app'],
  },
]

describe('ExperienceSection (edit/add/delete)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('view mode', () => {
    it('renders all experience entries', () => {
      render(<ExperienceSection experience={mockExperience} />)

      expect(screen.getByText('Senior Engineer')).toBeInTheDocument()
      expect(screen.getByText('Tech Corp')).toBeInTheDocument()
      expect(screen.getByText('Software Developer')).toBeInTheDocument()
      expect(screen.getByText('StartupCo')).toBeInTheDocument()
    })

    it('shows add button in view mode', () => {
      render(<ExperienceSection experience={mockExperience} />)

      expect(screen.getByRole('button', { name: /add experience/i })).toBeInTheDocument()
    })

    it('shows edit button for each entry', () => {
      render(<ExperienceSection experience={mockExperience} />)

      const editButtons = screen.getAllByRole('button', { name: /edit/i })
      expect(editButtons).toHaveLength(2)
    })

    it('shows delete button for each entry', () => {
      render(<ExperienceSection experience={mockExperience} />)

      const deleteButtons = screen.getAllByRole('button', { name: /delete/i })
      expect(deleteButtons).toHaveLength(2)
    })
  })

  describe('add mode', () => {
    it('shows entry form when add button clicked', async () => {
      const user = userEvent.setup()
      render(<ExperienceSection experience={mockExperience} />)

      await user.click(screen.getByRole('button', { name: /add experience/i }))

      expect(screen.getByLabelText(/title/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/company/i)).toBeInTheDocument()
    })

    it('hides add button when form is shown', async () => {
      const user = userEvent.setup()
      render(<ExperienceSection experience={mockExperience} />)

      await user.click(screen.getByRole('button', { name: /add experience/i }))

      expect(screen.queryByRole('button', { name: /add experience/i })).not.toBeInTheDocument()
    })

    it('calls addEntry API with correct data', async () => {
      const user = userEvent.setup()
      const mockAddEntry = vi.mocked(api.addEntry)
      mockAddEntry.mockResolvedValue({ message: 'Success' })

      const mockOnUpdate = vi.fn()
      render(<ExperienceSection experience={mockExperience} onUpdate={mockOnUpdate} />)

      await user.click(screen.getByRole('button', { name: /add experience/i }))

      await user.type(screen.getByLabelText(/title/i), 'New Position')
      await user.type(screen.getByLabelText(/company/i), 'New Company')
      await user.type(screen.getByLabelText(/start date/i), '2024-01')

      await user.click(screen.getByRole('button', { name: /save/i }))

      await waitFor(() => {
        expect(mockAddEntry).toHaveBeenCalledWith('experience', {
          title: 'New Position',
          company: 'New Company',
          start_date: '2024-01',
          end_date: null,
          location: null,
          highlights: [],
        })
      })
    })

    it('calls onUpdate callback after successful add', async () => {
      const user = userEvent.setup()
      const mockAddEntry = vi.mocked(api.addEntry)
      mockAddEntry.mockResolvedValue({ message: 'Success' })

      const mockOnUpdate = vi.fn()
      render(<ExperienceSection experience={mockExperience} onUpdate={mockOnUpdate} />)

      await user.click(screen.getByRole('button', { name: /add experience/i }))

      await user.type(screen.getByLabelText(/title/i), 'New Position')
      await user.type(screen.getByLabelText(/company/i), 'New Company')

      await user.click(screen.getByRole('button', { name: /save/i }))

      await waitFor(() => {
        expect(mockOnUpdate).toHaveBeenCalled()
      })
    })

    it('shows error message when add fails', async () => {
      const user = userEvent.setup()
      const mockAddEntry = vi.mocked(api.addEntry)
      mockAddEntry.mockRejectedValue(new Error('API Error'))

      render(<ExperienceSection experience={mockExperience} />)

      await user.click(screen.getByRole('button', { name: /add experience/i }))

      await user.type(screen.getByLabelText(/title/i), 'New Position')
      await user.type(screen.getByLabelText(/company/i), 'New Company')

      await user.click(screen.getByRole('button', { name: /save/i }))

      await waitFor(() => {
        expect(screen.getByText(/failed to add/i)).toBeInTheDocument()
      })
    })

    it('cancels add mode when cancel clicked', async () => {
      const user = userEvent.setup()
      render(<ExperienceSection experience={mockExperience} />)

      await user.click(screen.getByRole('button', { name: /add experience/i }))
      expect(screen.getByLabelText(/title/i)).toBeInTheDocument()

      await user.click(screen.getByRole('button', { name: /cancel/i }))

      expect(screen.queryByLabelText(/title/i)).not.toBeInTheDocument()
      expect(screen.getByRole('button', { name: /add experience/i })).toBeInTheDocument()
    })
  })

  describe('edit mode', () => {
    it('shows entry form when edit button clicked', async () => {
      const user = userEvent.setup()
      render(<ExperienceSection experience={mockExperience} />)

      const editButtons = screen.getAllByRole('button', { name: /edit/i })
      await user.click(editButtons[0])

      expect(screen.getByLabelText(/title/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/company/i)).toBeInTheDocument()
    })

    it('pre-fills form with entry data', async () => {
      const user = userEvent.setup()
      render(<ExperienceSection experience={mockExperience} />)

      const editButtons = screen.getAllByRole('button', { name: /edit/i })
      await user.click(editButtons[0])

      expect(screen.getByLabelText(/title/i)).toHaveValue('Senior Engineer')
      expect(screen.getByLabelText(/company/i)).toHaveValue('Tech Corp')
      expect(screen.getByLabelText(/start date/i)).toHaveValue('2020-01')
      expect(screen.getByLabelText(/end date/i)).toHaveValue('2023-12')
      expect(screen.getByLabelText(/location/i)).toHaveValue('San Francisco, CA')
    })

    it('pre-fills highlights from entry data', async () => {
      const user = userEvent.setup()
      render(<ExperienceSection experience={mockExperience} />)

      const editButtons = screen.getAllByRole('button', { name: /edit/i })
      await user.click(editButtons[0])

      const highlightInputs = screen.getAllByPlaceholderText(/highlight/i)
      expect(highlightInputs).toHaveLength(2)
      expect(highlightInputs[0]).toHaveValue('Led team of 5')
      expect(highlightInputs[1]).toHaveValue('Built key features')
    })

    it('calls updateEntry API with correct index and data', async () => {
      const user = userEvent.setup()
      const mockUpdateEntry = vi.mocked(api.updateEntry)
      mockUpdateEntry.mockResolvedValue({ message: 'Success' })

      const mockOnUpdate = vi.fn()
      render(<ExperienceSection experience={mockExperience} onUpdate={mockOnUpdate} />)

      const editButtons = screen.getAllByRole('button', { name: /edit/i })
      await user.click(editButtons[1])

      const titleInput = screen.getByLabelText(/title/i)
      await user.clear(titleInput)
      await user.type(titleInput, 'Updated Title')

      await user.click(screen.getByRole('button', { name: /save/i }))

      await waitFor(() => {
        expect(mockUpdateEntry).toHaveBeenCalledWith('experience', 1, expect.objectContaining({
          title: 'Updated Title',
        }))
      })
    })

    it('calls onUpdate callback after successful edit', async () => {
      const user = userEvent.setup()
      const mockUpdateEntry = vi.mocked(api.updateEntry)
      mockUpdateEntry.mockResolvedValue({ message: 'Success' })

      const mockOnUpdate = vi.fn()
      render(<ExperienceSection experience={mockExperience} onUpdate={mockOnUpdate} />)

      const editButtons = screen.getAllByRole('button', { name: /edit/i })
      await user.click(editButtons[0])

      await user.click(screen.getByRole('button', { name: /save/i }))

      await waitFor(() => {
        expect(mockOnUpdate).toHaveBeenCalled()
      })
    })

    it('shows error message when update fails', async () => {
      const user = userEvent.setup()
      const mockUpdateEntry = vi.mocked(api.updateEntry)
      mockUpdateEntry.mockRejectedValue(new Error('API Error'))

      render(<ExperienceSection experience={mockExperience} />)

      const editButtons = screen.getAllByRole('button', { name: /edit/i })
      await user.click(editButtons[0])

      await user.click(screen.getByRole('button', { name: /save/i }))

      await waitFor(() => {
        expect(screen.getByText(/failed to update/i)).toBeInTheDocument()
      })
    })

    it('cancels edit mode when cancel clicked', async () => {
      const user = userEvent.setup()
      render(<ExperienceSection experience={mockExperience} />)

      const editButtons = screen.getAllByRole('button', { name: /edit/i })
      await user.click(editButtons[0])

      expect(screen.getByLabelText(/title/i)).toBeInTheDocument()

      await user.click(screen.getByRole('button', { name: /cancel/i }))

      expect(screen.queryByLabelText(/title/i)).not.toBeInTheDocument()
      expect(screen.getByText('Senior Engineer')).toBeInTheDocument()
    })
  })

  describe('delete mode', () => {
    it('shows confirmation dialog when delete button clicked', async () => {
      const user = userEvent.setup()
      render(<ExperienceSection experience={mockExperience} />)

      const deleteButtons = screen.getAllByRole('button', { name: /delete/i })
      await user.click(deleteButtons[0])

      expect(screen.getByText(/are you sure/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /confirm/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument()
    })

    it('calls removeEntry API with correct index when confirmed', async () => {
      const user = userEvent.setup()
      const mockRemoveEntry = vi.mocked(api.removeEntry)
      mockRemoveEntry.mockResolvedValue({ message: 'Success' })

      const mockOnUpdate = vi.fn()
      render(<ExperienceSection experience={mockExperience} onUpdate={mockOnUpdate} />)

      const deleteButtons = screen.getAllByRole('button', { name: /delete/i })
      await user.click(deleteButtons[1])

      await user.click(screen.getByRole('button', { name: /confirm/i }))

      await waitFor(() => {
        expect(mockRemoveEntry).toHaveBeenCalledWith('experience', 1)
      })
    })

    it('calls onUpdate callback after successful delete', async () => {
      const user = userEvent.setup()
      const mockRemoveEntry = vi.mocked(api.removeEntry)
      mockRemoveEntry.mockResolvedValue({ message: 'Success' })

      const mockOnUpdate = vi.fn()
      render(<ExperienceSection experience={mockExperience} onUpdate={mockOnUpdate} />)

      const deleteButtons = screen.getAllByRole('button', { name: /delete/i })
      await user.click(deleteButtons[0])

      await user.click(screen.getByRole('button', { name: /confirm/i }))

      await waitFor(() => {
        expect(mockOnUpdate).toHaveBeenCalled()
      })
    })

    it('shows error message when delete fails', async () => {
      const user = userEvent.setup()
      const mockRemoveEntry = vi.mocked(api.removeEntry)
      mockRemoveEntry.mockRejectedValue(new Error('API Error'))

      render(<ExperienceSection experience={mockExperience} />)

      const deleteButtons = screen.getAllByRole('button', { name: /delete/i })
      await user.click(deleteButtons[0])

      await user.click(screen.getByRole('button', { name: /confirm/i }))

      await waitFor(() => {
        expect(screen.getByText(/failed to delete/i)).toBeInTheDocument()
      })
    })

    it('cancels delete when cancel clicked', async () => {
      const user = userEvent.setup()
      const mockRemoveEntry = vi.mocked(api.removeEntry)

      render(<ExperienceSection experience={mockExperience} />)

      const deleteButtons = screen.getAllByRole('button', { name: /delete/i })
      await user.click(deleteButtons[0])

      await user.click(screen.getByRole('button', { name: /cancel/i }))

      expect(screen.queryByText(/are you sure/i)).not.toBeInTheDocument()
      expect(mockRemoveEntry).not.toHaveBeenCalled()
    })
  })
})
