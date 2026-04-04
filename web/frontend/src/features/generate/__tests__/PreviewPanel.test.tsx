import { describe, it, expect, beforeEach } from 'vitest'
import { screen } from '@testing-library/react'
import { renderWithProviders } from '@/test/test-utils'
import { PreviewPanel } from '../PreviewPanel'
import { useGenerateStore } from '@/stores/useGenerateStore'

describe('PreviewPanel', () => {
  beforeEach(() => {
    useGenerateStore.setState({
      imageUrl: null,
      title: null,
      historyId: null,
      isGenerating: false,
    })
  })

  it('shows empty state when no image', () => {
    renderWithProviders(<PreviewPanel />)
    expect(screen.getByText(/your card will appear here/i)).toBeInTheDocument()
  })

  it('shows loading state when generating', () => {
    useGenerateStore.setState({ isGenerating: true })
    renderWithProviders(<PreviewPanel />)
    expect(screen.getByText(/generating/i)).toBeInTheDocument()
  })

  it('shows action bar with download and copy when image exists', () => {
    useGenerateStore.setState({
      imageUrl: '/output/test.png',
      title: 'Test Card',
      historyId: 42,
    })
    renderWithProviders(<PreviewPanel />)

    expect(screen.getByText(/download/i)).toBeInTheDocument()
  })

  it('shows HTML export button when historyId exists', () => {
    useGenerateStore.setState({
      imageUrl: '/output/test.png',
      title: 'Test Card',
      historyId: 42,
    })
    renderWithProviders(<PreviewPanel />)

    expect(screen.getByRole('button', { name: /html/i })).toBeInTheDocument()
  })

  it('does not show HTML export button when no historyId', () => {
    useGenerateStore.setState({
      imageUrl: '/output/test.png',
      title: 'Test Card',
      historyId: null,
    })
    renderWithProviders(<PreviewPanel />)

    expect(screen.queryByRole('button', { name: /html/i })).not.toBeInTheDocument()
  })
})
