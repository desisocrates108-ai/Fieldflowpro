import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { AlertTriangle, Trash2, Loader2 } from 'lucide-react';

/**
 * ForceDeleteModal - Admin override delete confirmation modal
 * Requires typing "DELETE" to confirm force deletion
 */
export default function ForceDeleteModal({
  open,
  onClose,
  onConfirm,
  title,
  itemName,
  dependencies = {},
  loading = false
}) {
  const [confirmText, setConfirmText] = useState('');
  const [mode, setMode] = useState('deactivate'); // 'deactivate' or 'force'

  const handleConfirm = () => {
    if (mode === 'force' && confirmText !== 'DELETE') {
      return;
    }
    onConfirm(mode === 'force');
    setConfirmText('');
    setMode('deactivate');
  };

  const handleClose = () => {
    setConfirmText('');
    setMode('deactivate');
    onClose();
  };

  const hasDependencies = Object.values(dependencies).some(v => typeof v === 'number' && v > 0);

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-red-600">
            <AlertTriangle className="h-5 w-5" />
            {title || 'Delete Confirmation'}
          </DialogTitle>
          <DialogDescription>
            You are about to delete: <strong>{itemName}</strong>
          </DialogDescription>
        </DialogHeader>

        {hasDependencies && (
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 space-y-2">
            <p className="font-medium text-amber-800">This item has dependencies:</p>
            <ul className="text-sm text-amber-700 space-y-1">
              {Object.entries(dependencies).map(([key, value]) => (
                value > 0 && (
                  <li key={key} className="flex justify-between">
                    <span>{key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:</span>
                    <span className="font-medium">{value}</span>
                  </li>
                )
              ))}
            </ul>
          </div>
        )}

        <div className="space-y-4 pt-2">
          <p className="text-sm text-zinc-600">Choose an action:</p>
          
          <div className="space-y-2">
            {hasDependencies && (
              <label className="flex items-center gap-3 p-3 border rounded-lg cursor-pointer hover:bg-zinc-50">
                <input
                  type="radio"
                  name="deleteMode"
                  checked={mode === 'deactivate'}
                  onChange={() => setMode('deactivate')}
                  className="w-4 h-4"
                />
                <div>
                  <p className="font-medium">Deactivate</p>
                  <p className="text-sm text-zinc-500">Mark as inactive, keep data for records</p>
                </div>
              </label>
            )}
            
            <label className="flex items-center gap-3 p-3 border border-red-200 rounded-lg cursor-pointer hover:bg-red-50">
              <input
                type="radio"
                name="deleteMode"
                checked={mode === 'force'}
                onChange={() => setMode('force')}
                className="w-4 h-4 accent-red-600"
              />
              <div>
                <p className="font-medium text-red-600">Force Delete (Admin Only)</p>
                <p className="text-sm text-zinc-500">Permanently delete with ALL dependencies</p>
              </div>
            </label>
          </div>

          {mode === 'force' && (
            <div className="space-y-2 pt-2 border-t">
              <p className="text-sm font-medium text-red-600">
                Type <span className="font-mono bg-red-100 px-1">DELETE</span> to confirm:
              </p>
              <Input
                value={confirmText}
                onChange={(e) => setConfirmText(e.target.value.toUpperCase())}
                placeholder="Type DELETE"
                className="font-mono"
                data-testid="force-delete-confirm-input"
              />
            </div>
          )}
        </div>

        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={handleClose} disabled={loading}>
            Cancel
          </Button>
          <Button
            variant={mode === 'force' ? 'destructive' : 'default'}
            onClick={handleConfirm}
            disabled={loading || (mode === 'force' && confirmText !== 'DELETE')}
            data-testid="confirm-delete-btn"
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
            ) : (
              <Trash2 className="h-4 w-4 mr-2" />
            )}
            {mode === 'force' ? 'Force Delete' : hasDependencies ? 'Deactivate' : 'Delete'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
