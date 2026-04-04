import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiFetch, apiPost } from './client'

// ---------------------------------------------------------------------------
// Shared types
// ---------------------------------------------------------------------------

export interface ExtractedData {
  title: string
  key_points: { text: string }[]
  source: string
  theme_suggestion?: string
}

// ---------------------------------------------------------------------------
// Generate
// ---------------------------------------------------------------------------

interface ExtractionConfigParams {
  language: string
  tone: string
  max_points: number
  min_points: number
  title_max_chars: number
  point_max_chars: number
  custom_instructions: string
}

interface GenerateParams {
  text?: string
  url?: string
  theme: string
  format: string
  formats?: string[]
  provider: string
  mode?: string
  color_mood?: string | null
  social?: boolean
  scale?: number
  webp?: boolean
  brand_name?: string
  watermark_position?: string
  watermark_opacity?: number
  thread?: boolean
  extraction_config?: ExtractionConfigParams | null
}

interface GenerateResult {
  ok: boolean
  image_url: string
  title: string
  points_count: number
  file_size: number | null
  extracted_data: ExtractedData
  history_id: number
}

export function useGenerate() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (params: GenerateParams) =>
      apiPost<GenerateResult>('/api/generate', params),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['history'] })
      qc.invalidateQueries({ queryKey: ['stats'] })
    },
  })
}

interface GenerateMultiResult {
  ok: boolean
  images: { url: string; format: string; size: number | null; history_id?: number }[]
  title: string
  extracted_data: ExtractedData
}

export function useGenerateMulti() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (params: GenerateParams) =>
      apiPost<GenerateMultiResult>('/api/generate/multi', params),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['history'] })
    },
  })
}

// ---------------------------------------------------------------------------
// Re-render
// ---------------------------------------------------------------------------

interface ReRenderParams {
  history_id?: number | null
  extracted_data: ExtractedData
  theme: string
  format: string
  scale?: number
  webp?: boolean
  brand_name?: string
  watermark_position?: string
  watermark_opacity?: number
}

interface ReRenderResult {
  ok: boolean
  image_url: string
  title: string
  file_size: number | null
  extracted_data: ExtractedData
  history_id: number
}

export function useReRender() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (params: ReRenderParams) =>
      apiPost<ReRenderResult>('/api/re-render', params),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['history'] })
      qc.invalidateQueries({ queryKey: ['stats'] })
    },
  })
}

// ---------------------------------------------------------------------------
// History
// ---------------------------------------------------------------------------

export interface HistoryRow {
  id: number
  url: string | null
  title: string
  theme: string
  format: string
  provider: string
  created_at: string
  output_path: string
  file_size: number | null
  key_points_count: number
  source: string | null
  mode: string
  extracted_data: ExtractedData | null
}

export function useHistory(days?: number, q?: string, limit = 20) {
  const params = new URLSearchParams()
  if (days != null) params.set('days', String(days))
  if (q) params.set('q', q)
  params.set('limit', String(limit))
  return useQuery({
    queryKey: ['history', days, q, limit],
    queryFn: () => apiFetch<{ ok: boolean; rows: HistoryRow[] }>(`/api/history?${params}`),
  })
}

export function useHistoryDetail(id: number | null) {
  return useQuery({
    queryKey: ['history-detail', id],
    queryFn: () => apiFetch<{ ok: boolean; row: HistoryRow & { image_url: string | null } }>(`/api/history/${id}`),
    enabled: id != null,
  })
}

// ---------------------------------------------------------------------------
// Stats
// ---------------------------------------------------------------------------

export function useStats(days?: number) {
  const params = days != null ? `?days=${days}` : ''
  return useQuery({
    queryKey: ['stats', days],
    queryFn: () => apiFetch<{
      ok: boolean
      total: number
      by_theme: { name: string; count: number }[]
      by_provider: { name: string; count: number }[]
      by_format: { name: string; count: number }[]
      avg_points: number
      date_range: { earliest: string; latest: string }
      recent_titles: string[]
    }>(`/api/stats${params}`),
  })
}

// ---------------------------------------------------------------------------
// Meta
// ---------------------------------------------------------------------------

export function useMeta() {
  return useQuery({
    queryKey: ['meta'],
    queryFn: () => apiFetch<{
      ok: boolean
      themes: string[]
      formats: string[]
      providers: string[]
    }>('/api/meta'),
    staleTime: Infinity,
  })
}

// ---------------------------------------------------------------------------
// Caption
// ---------------------------------------------------------------------------

interface CaptionParams {
  platforms: string[]
  provider: string
  data: Record<string, unknown>
}

export function useCaption() {
  return useMutation({
    mutationFn: (params: CaptionParams) =>
      apiPost<{ ok: boolean; captions: Record<string, string> }>('/api/caption', params),
  })
}

// ---------------------------------------------------------------------------
// Presets
// ---------------------------------------------------------------------------

export function usePresets() {
  return useQuery({
    queryKey: ['presets'],
    queryFn: () => apiFetch<{ ok: boolean; presets: Record<string, Record<string, unknown>> }>('/api/presets'),
  })
}

export function useSavePreset() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (params: { name: string; values: Record<string, unknown> }) =>
      apiPost('/api/presets', params),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['presets'] }),
  })
}

export function useDeletePreset() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (name: string) =>
      apiFetch(`/api/presets/${encodeURIComponent(name)}`, { method: 'DELETE' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['presets'] }),
  })
}

// ---------------------------------------------------------------------------
// Dashboard / LevelUp
// ---------------------------------------------------------------------------

export interface ContentItem {
  id: string
  account_type: string
  title: string
  status: string
  content_type: string | null
  image_url: string | null
  created_at: string
}

export interface AccountStats {
  name: string
  counts: Record<string, number>
  weekly_output: number
  approval_rate: number
}

export interface AccountInfo {
  name: string
  platforms: string[]
  publish_time: string
  color_mood: string
  tone: string
}

export interface ScheduleItem extends ContentItem {
  scheduled_time: string
}

export function useContentStats() {
  return useQuery({
    queryKey: ['content-stats'],
    queryFn: () => apiFetch<{ ok: boolean; accounts: Record<string, AccountStats> }>('/api/content/stats'),
    refetchInterval: 30_000,
  })
}

export function useRecentContent(limit = 10) {
  return useQuery({
    queryKey: ['content-recent', limit],
    queryFn: () => apiFetch<{ ok: boolean; items: ContentItem[] }>(`/api/content/recent?limit=${limit}`),
    refetchInterval: 30_000,
  })
}

export function useScheduledContent(date?: string) {
  const params = date ? `?date=${date}` : ''
  return useQuery({
    queryKey: ['content-schedule', date],
    queryFn: () => apiFetch<{ ok: boolean; items: ScheduleItem[] }>(`/api/content/schedule${params}`),
    refetchInterval: 60_000,
  })
}

export function useAccounts() {
  return useQuery({
    queryKey: ['accounts'],
    queryFn: () => apiFetch<{ ok: boolean; accounts: Record<string, AccountInfo> }>('/api/accounts'),
    staleTime: 60_000,
  })
}

// ---------------------------------------------------------------------------
// Digest
// ---------------------------------------------------------------------------

export function useDigest() {
  return useMutation({
    mutationFn: (params: { days: number; theme: string; provider: string }) =>
      apiPost<{ ok: boolean; image_url: string; title: string }>('/api/digest', params),
  })
}

// ---------------------------------------------------------------------------
// LevelUp Review API  (Phase A)
// ---------------------------------------------------------------------------

export interface ContentDetail {
  id: string
  account_type: string
  status: string
  content_type: string | null
  title: string
  body: string
  reasoning: string
  image_url: string | null
  source_url: string | null
  source: string | null
  scheduled_time: string | null
  created_at: string
  updated_at: string
  preflight_warnings: string[]
  account_name: string
  platforms: string[]
}

interface ReviewListResult {
  ok: boolean
  items: ContentDetail[]
  total: number
}

export function useReviewContent(params: {
  status?: string
  account?: string | null
  limit?: number
}) {
  const searchParams = new URLSearchParams()
  if (params.status) searchParams.set('status', params.status)
  if (params.account) searchParams.set('account', params.account)
  if (params.limit) searchParams.set('limit', String(params.limit))

  return useQuery({
    queryKey: ['review', params],
    queryFn: () =>
      apiFetch<ReviewListResult>(`/api/content/review?${searchParams}`),
    refetchInterval: 30_000,
  })
}

export function useContentDetail(id: string | null) {
  return useQuery({
    queryKey: ['content-detail', id],
    queryFn: () => apiFetch<{ ok: boolean; item: ContentDetail }>(`/api/content/${id}/detail`),
    enabled: id != null,
  })
}

interface ApproveResult {
  ok: boolean
  status: 'OK' | 'WARNING' | 'ERROR'
  warnings: string[]
  message?: string
  item?: ContentDetail
}

export function useApproveContent() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, publish_time }: { id: string; publish_time?: string }) =>
      apiPost<ApproveResult>(`/api/content/${id}/approve`, { publish_time }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['review'] })
      qc.invalidateQueries({ queryKey: ['content-stats'] })
      qc.invalidateQueries({ queryKey: ['content-scheduled'] })
    },
  })
}

export function useRejectContent() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, reason }: { id: string; reason?: string }) =>
      apiPost<{ ok: boolean; item: ContentDetail }>(`/api/content/${id}/reject`, { reason }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['review'] })
      qc.invalidateQueries({ queryKey: ['content-stats'] })
    },
  })
}

export function useEditContent() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, title, body }: { id: string; title?: string; body?: string }) =>
      apiFetch<{ ok: boolean; item: ContentDetail }>(`/api/content/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, body }),
      }),
    onSuccess: (_, { id }) => {
      qc.invalidateQueries({ queryKey: ['review'] })
      qc.invalidateQueries({ queryKey: ['content-detail', id] })
    },
  })
}

export function useBatchAction() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ ids, action, reason }: { ids: string[]; action: 'approve' | 'reject'; reason?: string }) =>
      apiPost<{ ok: boolean; results: { id: string; status: string; item?: ContentDetail }[] }>(
        '/api/content/batch',
        { ids, action, reason }
      ),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['review'] })
      qc.invalidateQueries({ queryKey: ['content-stats'] })
    },
  })
}

// ---------------------------------------------------------------------------
// LevelUp Curation API  (Phase B)
// ---------------------------------------------------------------------------

export interface CurationProgress {
  type: string
  account: string
  title?: string
  source?: string
  reason?: string
  error?: string
  drafted?: number
}

export function useCurationStatus() {
  return useQuery({
    queryKey: ['curation-status'],
    queryFn: () => apiFetch<{ ok: boolean; running: boolean; started_at: string | null; progress: CurationProgress[] }>('/api/curation/status'),
  })
}

export function useCurationStats() {
  return useQuery({
    queryKey: ['curation-stats'],
    queryFn: () => apiFetch<{ ok: boolean; stats: Record<string, { today: Record<string, number>; week: Record<string, number>; approval_rate: number }> }>('/api/curation/stats'),
    refetchInterval: 60_000,
  })
}

// ---------------------------------------------------------------------------
// LevelUp Scheduling API  (Phase C)
// ---------------------------------------------------------------------------

export function useScheduledRange(start?: string, end?: string, account?: string | null) {
  const params = new URLSearchParams()
  if (start) params.set('start', start)
  if (end) params.set('end', end)
  if (account) params.set('account', account)

  return useQuery({
    queryKey: ['content-scheduled', start, end, account],
    queryFn: () =>
      apiFetch<{ ok: boolean; items: ContentDetail[]; total: number }>(`/api/content/scheduled?${params}`),
    refetchInterval: 30_000,
  })
}

export function useReschedule() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, scheduled_time }: { id: string; scheduled_time: string }) =>
      apiFetch<{ ok: boolean; item: ContentDetail }>(`/api/content/${id}/reschedule`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scheduled_time }),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['content-scheduled'] })
    },
  })
}

// ---------------------------------------------------------------------------
// LevelUp Drafts API  (Phase D)
// ---------------------------------------------------------------------------

export function useDrafts(params: {
  account?: string | null
  source?: string | null
  days?: number | null
}) {
  const searchParams = new URLSearchParams()
  if (params.account) searchParams.set('account', params.account)
  if (params.source) searchParams.set('source', params.source)
  if (params.days != null) searchParams.set('days', String(params.days))

  return useQuery({
    queryKey: ['content-drafts', params],
    queryFn: () =>
      apiFetch<{ ok: boolean; items: ContentDetail[]; total: number }>(`/api/content/drafts?${searchParams}`),
    refetchInterval: 30_000,
  })
}

export function useUpdateContentStatus() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      apiFetch<{ ok: boolean; item: ContentDetail }>(`/api/content/${id}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status }),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['content-drafts'] })
      qc.invalidateQueries({ queryKey: ['review'] })
      qc.invalidateQueries({ queryKey: ['content-stats'] })
    },
  })
}

// ---------------------------------------------------------------------------
// LevelUp Settings API  (Phase E)
// ---------------------------------------------------------------------------

export interface AccountConfig {
  id: string
  name: string
  platforms: string[]
  publish_time: string
  color_mood: string
  tone: string
  prompt_file: string
}

export function useAccountPrompt(accountId: string | null) {
  return useQuery({
    queryKey: ['account-prompt', accountId],
    queryFn: () =>
      apiFetch<{ ok: boolean; account_id: string; prompt: string; path: string }>(
        `/api/accounts/${accountId}/prompt`
      ),
    enabled: accountId != null,
  })
}

export function useUpdateAccount() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({
      id,
      ...updates
    }: {
      id: string
      name?: string
      platforms?: string[]
      publish_time?: string
      color_mood?: string
      tone?: string
      prompt_content?: string
    }) =>
      apiFetch<{ ok: boolean; account: AccountConfig }>(`/api/accounts/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['accounts'] })
    },
  })
}

export function useAccountPreview() {
  return useMutation({
    mutationFn: ({ id, color_mood }: { id: string; color_mood: string }) =>
      apiPost<{ ok: boolean; account_id: string; color_mood: string; preview_url: string }>(
        `/api/accounts/${id}/preview`,
        { color_mood }
      ),
  })
}
