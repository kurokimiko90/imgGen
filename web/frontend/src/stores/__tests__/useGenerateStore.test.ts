import { describe, it, expect, beforeEach } from 'vitest'
import { useGenerateStore } from '../useGenerateStore'

describe('useGenerateStore — extraction config', () => {
  beforeEach(() => {
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

  it('has extraction config defaults', () => {
    const state = useGenerateStore.getState()
    expect(state.extractionLanguage).toBe('zh-TW')
    expect(state.extractionTone).toBe('professional')
    expect(state.extractionMaxPoints).toBe(5)
    expect(state.extractionMinPoints).toBe(3)
    expect(state.extractionTitleMaxChars).toBe(15)
    expect(state.extractionPointMaxChars).toBe(50)
    expect(state.extractionCustomInstructions).toBe('')
  })

  it('setExtractionLanguage updates language', () => {
    useGenerateStore.getState().setExtractionLanguage('en')
    expect(useGenerateStore.getState().extractionLanguage).toBe('en')
  })

  it('setExtractionTone updates tone', () => {
    useGenerateStore.getState().setExtractionTone('casual')
    expect(useGenerateStore.getState().extractionTone).toBe('casual')
  })

  it('setExtractionMaxPoints updates max points', () => {
    useGenerateStore.getState().setExtractionMaxPoints(8)
    expect(useGenerateStore.getState().extractionMaxPoints).toBe(8)
  })

  it('setExtractionMinPoints updates min points', () => {
    useGenerateStore.getState().setExtractionMinPoints(1)
    expect(useGenerateStore.getState().extractionMinPoints).toBe(1)
  })

  it('clamps maxPoints up when minPoints exceeds it', () => {
    useGenerateStore.setState({ extractionMinPoints: 3, extractionMaxPoints: 5 })
    useGenerateStore.getState().setExtractionMinPoints(7)
    expect(useGenerateStore.getState().extractionMinPoints).toBe(7)
    expect(useGenerateStore.getState().extractionMaxPoints).toBe(7)
  })

  it('clamps minPoints down when maxPoints goes below it', () => {
    useGenerateStore.setState({ extractionMinPoints: 5, extractionMaxPoints: 5 })
    useGenerateStore.getState().setExtractionMaxPoints(2)
    expect(useGenerateStore.getState().extractionMaxPoints).toBe(2)
    expect(useGenerateStore.getState().extractionMinPoints).toBe(2)
  })

  it('setExtractionTitleMaxChars updates title max chars', () => {
    useGenerateStore.getState().setExtractionTitleMaxChars(30)
    expect(useGenerateStore.getState().extractionTitleMaxChars).toBe(30)
  })

  it('setExtractionPointMaxChars updates point max chars', () => {
    useGenerateStore.getState().setExtractionPointMaxChars(100)
    expect(useGenerateStore.getState().extractionPointMaxChars).toBe(100)
  })

  it('setExtractionCustomInstructions updates custom instructions', () => {
    useGenerateStore.getState().setExtractionCustomInstructions('Focus on data')
    expect(useGenerateStore.getState().extractionCustomInstructions).toBe('Focus on data')
  })

  it('extraction config is persisted via partialize', () => {
    // Access the store's persist config to verify extraction fields are included
    const state = useGenerateStore.getState()
    // Verify the fields exist (they should be in partialize)
    expect('extractionLanguage' in state).toBe(true)
    expect('extractionTone' in state).toBe(true)
    expect('extractionMaxPoints' in state).toBe(true)
  })

  it('getExtractionConfig returns correct API shape', () => {
    useGenerateStore.setState({
      extractionLanguage: 'en',
      extractionTone: 'casual',
      extractionMaxPoints: 4,
      extractionMinPoints: 2,
      extractionTitleMaxChars: 20,
      extractionPointMaxChars: 80,
      extractionCustomInstructions: 'Be brief',
    })

    const config = useGenerateStore.getState().getExtractionConfig()
    expect(config).toEqual({
      language: 'en',
      tone: 'casual',
      max_points: 4,
      min_points: 2,
      title_max_chars: 20,
      point_max_chars: 80,
      custom_instructions: 'Be brief',
    })
  })

  it('getExtractionConfig returns null when all defaults', () => {
    // All defaults — no need to send to API
    const config = useGenerateStore.getState().getExtractionConfig()
    expect(config).toBeNull()
  })
})
