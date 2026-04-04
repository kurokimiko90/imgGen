import { describe, it, expect, beforeEach } from 'vitest'
import { screen } from '@testing-library/react'
import { renderWithProviders, userEvent } from '@/test/test-utils'
import { ExtractionSettings } from '../ExtractionSettings'
import { useGenerateStore } from '@/stores/useGenerateStore'

describe('ExtractionSettings', () => {
  beforeEach(() => {
    // Reset store to defaults
    useGenerateStore.setState({
      extractionLanguage: 'zh-TW',
      extractionTone: 'professional',
      extractionMaxPoints: 5,
      extractionMinPoints: 3,
      extractionTitleMaxChars: 15,
      extractionPointMaxChars: 50,
      extractionCustomInstructions: '',
    })
  })

  it('renders all extraction setting fields', () => {
    renderWithProviders(<ExtractionSettings />)

    expect(screen.getByLabelText(/language/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/tone/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/min points/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/max points/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/title max/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/custom instructions/i)).toBeInTheDocument()
  })

  it('shows default values from store', () => {
    renderWithProviders(<ExtractionSettings />)

    expect(screen.getByLabelText(/language/i)).toHaveValue('zh-TW')
    expect(screen.getByLabelText(/tone/i)).toHaveValue('professional')
    expect(screen.getByLabelText(/min points/i)).toHaveValue(3)
    expect(screen.getByLabelText(/max points/i)).toHaveValue(5)
    expect(screen.getByLabelText(/title max/i)).toHaveValue(15)
  })

  it('updates store when language changes', async () => {
    const user = userEvent.setup()
    renderWithProviders(<ExtractionSettings />)

    await user.selectOptions(screen.getByLabelText(/language/i), 'en')

    expect(useGenerateStore.getState().extractionLanguage).toBe('en')
  })

  it('updates store when tone changes', async () => {
    const user = userEvent.setup()
    renderWithProviders(<ExtractionSettings />)

    await user.selectOptions(screen.getByLabelText(/tone/i), 'casual')

    expect(useGenerateStore.getState().extractionTone).toBe('casual')
  })

  it('updates store when min points changes', async () => {
    const user = userEvent.setup()
    renderWithProviders(<ExtractionSettings />)

    const input = screen.getByLabelText(/min points/i)
    await user.clear(input)
    await user.type(input, '2')

    expect(useGenerateStore.getState().extractionMinPoints).toBe(2)
  })

  it('updates store when custom instructions changes', async () => {
    const user = userEvent.setup()
    renderWithProviders(<ExtractionSettings />)

    const textarea = screen.getByLabelText(/custom instructions/i)
    await user.type(textarea, 'Focus on technical details')

    expect(useGenerateStore.getState().extractionCustomInstructions).toBe('Focus on technical details')
  })
})
