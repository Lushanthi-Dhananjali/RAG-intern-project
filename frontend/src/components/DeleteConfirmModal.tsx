'use client';

import React from 'react';

interface DeleteConfirmModalProps {
  isOpen: boolean;
  filename: string;
  planTitle: string;
  isDeleting: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export default function DeleteConfirmModal({
  isOpen,
  filename,
  planTitle,
  isDeleting,
  onConfirm,
  onCancel,
}: DeleteConfirmModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in duration-150">
      <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200 space-y-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-red-100 flex items-center justify-center text-red-600 text-xl font-bold">
            🗑️
          </div>
          <div>
            <h3 className="text-lg font-bold text-slate-900">Delete Lesson Plan</h3>
            <p className="text-xs text-slate-500">This action cannot be undone.</p>
          </div>
        </div>

        <div className="p-3 bg-red-50/70 border border-red-200/80 rounded-xl text-xs text-red-800 space-y-1">
          <p className="font-semibold">Are you sure you want to permanently delete this plan?</p>
          <p className="text-slate-700 font-mono text-[11px] break-all bg-white/70 px-2 py-1 rounded border border-red-100">
            {filename}
          </p>
          {planTitle && (
            <p className="text-slate-600 italic mt-1 line-clamp-2">
              &ldquo;{planTitle}&rdquo;
            </p>
          )}
        </div>

        <div className="flex items-center justify-end gap-3 pt-2">
          <button
            type="button"
            disabled={isDeleting}
            onClick={onCancel}
            className="px-4 py-2 text-xs font-bold text-slate-600 hover:text-slate-800 hover:bg-slate-100 rounded-xl transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="button"
            disabled={isDeleting}
            onClick={onConfirm}
            className="px-4 py-2 text-xs font-bold text-white bg-red-600 hover:bg-red-700 rounded-xl transition-all shadow-md shadow-red-500/20 disabled:opacity-50 inline-flex items-center gap-2"
          >
            {isDeleting ? (
              <>
                <span className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Deleting...
              </>
            ) : (
              'Confirm Delete'
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
