import { useState } from 'react'
import { ClipboardCheck, AlertCircle, CheckCheck, X } from 'lucide-react'
import { PageTransition } from '@/components/layout/PageTransition'
import { GlassCard } from '@/components/layout/GlassCard'
import { useReviewStore } from '@/stores/useReviewStore'
import {
  useReviewContent,
  useApproveContent,
  useRejectContent,
  useEditContent,
  useBatchAction,
  type ContentDetail,
} from '@/api/queries'
import { ReviewCard } from '@/features/review/ReviewCard'
import { ReviewFilterBar } from '@/features/review/ReviewFilterBar'
import { EditDrawer } from '@/features/review/EditDrawer'
import { PreflightDialog } from '@/features/review/PreflightDialog'
import { BatchBar } from '@/features/review/BatchBar'
import { ReviewDetailModal } from '@/features/review/ReviewDetailModal'

export function ReviewPage() {
  const {
    filterAccount,
    filterStatus,
    batchMode,
    selectedIds,
    editingId,
    preflightWarnings,
    pendingApproveId,
    setEditingId,
    clearPreflightWarnings,
    toggleBatchMode,
    clearSelection,
  } = useReviewStore()

  const statusParam = filterStatus.join(',')
  const review = useReviewContent({
    status: statusParam,
    account: filterAccount,
    limit: 50,
  })

  const approveMutation = useApproveContent()
  const rejectMutation = useRejectContent()
  const editMutation = useEditContent()
  const batchMutation = useBatchAction()

  const [rejectingId, setRejectingId] = useState<string | null>(null)
  const [rejectReason, setRejectReason] = useState('')
  const [detailId, setDetailId] = useState<string | null>(null)

  const items: ContentDetail[] = review.data?.items ?? []
  const detailIndex = items.findIndex((i) => i.id === detailId)
  const detailItem = detailIndex >= 0 ? items[detailIndex] : null
  const pendingCount = items.filter((i) => i.status === 'PENDING_REVIEW').length
  const draftCount = items.filter((i) => i.status === 'DRAFT').length

  async function handleApprove(id: string, publishTime?: string) {
    const result = await approveMutation.mutateAsync({ id, publish_time: publishTime })
    if (result.status === 'ERROR') {
      useReviewStore.getState().showPreflightWarnings(id, result.warnings)
    }
  }

  async function handleReject(id: string) {
    await rejectMutation.mutateAsync({ id, reason: rejectReason || undefined })
    setRejectingId(null)
    setRejectReason('')
  }

  async function handleBatchApprove() {
    await batchMutation.mutateAsync({ ids: [...selectedIds], action: 'approve' })
    clearSelection()
    toggleBatchMode()
  }

  async function handleBatchReject() {
    await batchMutation.mutateAsync({ ids: [...selectedIds], action: 'reject' })
    clearSelection()
    toggleBatchMode()
  }

  function handleDetailNavigate(direction: 'prev' | 'next') {
    if (direction === 'prev' && detailIndex > 0) {
      setDetailId(items[detailIndex - 1].id)
    } else if (direction === 'next' && detailIndex < items.length - 1) {
      setDetailId(items[detailIndex + 1].id)
    }
  }

  function handleOpenDetail(id: string) {
    setDetailId(id)
  }

  return (
    <PageTransition>
      <div className="p-6 space-y-5 max-w-5xl">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <ClipboardCheck size={22} className="text-accent" />
            <div>
              <h1 className="text-xl font-semibold text-text-primary">Review</h1>
              <p className="text-sm text-text-muted">
                {draftCount} draft · {pendingCount} pending review
              </p>
            </div>
          </div>
        </div>

        {/* Filter bar */}
        <ReviewFilterBar />

        {/* Batch bar */}
        {batchMode && (
          <BatchBar
            selectedCount={selectedIds.size}
            onApprove={handleBatchApprove}
            onReject={handleBatchReject}
            onCancel={() => { clearSelection(); toggleBatchMode() }}
            isLoading={batchMutation.isPending}
          />
        )}

        {/* Content list */}
        {review.isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-32 animate-pulse rounded-xl bg-white/5" />
            ))}
          </div>
        ) : review.isError ? (
          <GlassCard>
            <div className="flex items-center gap-2 text-red-600">
              <AlertCircle size={16} />
              <span className="text-sm">Failed to load review content</span>
            </div>
          </GlassCard>
        ) : items.length === 0 ? (
          <GlassCard>
            <div className="flex flex-col items-center gap-2 py-8 text-text-muted">
              <CheckCheck size={32} className="text-accent opacity-70" />
              <p className="text-sm">No content pending review</p>
            </div>
          </GlassCard>
        ) : (
          <div className="space-y-3">
            {items.map((item) => (
              <div
                key={item.id}
                onClick={() => !batchMode && handleOpenDetail(item.id)}
                className={!batchMode ? 'cursor-pointer' : ''}
              >
                <ReviewCard
                  item={item}
                  selectable={batchMode}
                  selected={selectedIds.has(item.id)}
                  onApprove={handleApprove}
                  onReject={(id) => { setRejectingId(id); setRejectReason('') }}
                  onEdit={(id) => setEditingId(id)}
                  isApproving={approveMutation.isPending}
                  isRejecting={rejectMutation.isPending && rejectingId === item.id}
                />
              </div>
            ))}
          </div>
        )}

        {/* Edit drawer */}
        {editingId && (
          <EditDrawer
            id={editingId}
            onClose={() => setEditingId(null)}
            onSave={async (title, body) => {
              await editMutation.mutateAsync({ id: editingId, title, body })
              setEditingId(null)
            }}
            isLoading={editMutation.isPending}
          />
        )}

        {/* Preflight warning dialog */}
        {preflightWarnings.length > 0 && pendingApproveId && (
          <PreflightDialog
            warnings={preflightWarnings}
            onClose={() => clearPreflightWarnings()}
          />
        )}

        {/* Detail modal */}
        {detailItem && detailIndex >= 0 && (
          <ReviewDetailModal
            item={detailItem}
            currentIndex={detailIndex}
            totalItems={items.length}
            onClose={() => setDetailId(null)}
            onNavigate={handleDetailNavigate}
            onApprove={handleApprove}
            onReject={(id) => { setRejectingId(id); setRejectReason('') }}
            isApproving={approveMutation.isPending}
            isRejecting={rejectMutation.isPending && rejectingId === detailItem.id}
          />
        )}

        {/* Reject confirmation dialog */}
        {rejectingId && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
            <div className="bg-bg-surface border border-border-subtle rounded-xl p-5 w-80 shadow-2xl space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-text-primary">Reject Content</h3>
                <button onClick={() => setRejectingId(null)} className="text-text-muted hover:text-text-primary">
                  <X size={16} />
                </button>
              </div>
              <textarea
                className="w-full bg-bg-base border border-border-subtle rounded-lg p-2 text-sm text-text-primary resize-none h-20 focus:outline-none focus:border-accent"
                placeholder="Reason (optional)"
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
              />
              <div className="flex gap-2 justify-end">
                <button
                  onClick={() => setRejectingId(null)}
                  className="px-3 py-1.5 text-sm text-text-muted hover:text-text-primary rounded-lg hover:bg-hover"
                >
                  Cancel
                </button>
                <button
                  onClick={() => handleReject(rejectingId)}
                  disabled={rejectMutation.isPending}
                  className="px-3 py-1.5 text-sm bg-red-600/20 text-red-600 hover:bg-red-600/30 rounded-lg disabled:opacity-50"
                >
                  {rejectMutation.isPending ? 'Rejecting...' : 'Confirm Reject'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </PageTransition>
  )
}
