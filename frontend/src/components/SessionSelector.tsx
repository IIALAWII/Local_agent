'use client';

import { PlusCircle, RefreshCw, Trash2 } from 'lucide-react';
import { deleteSession } from '@/lib/api';
import type { SessionInfo } from '@/lib/api';
import { clsx } from 'clsx';

interface SessionSelectorProps {
  sessions: SessionInfo[];
  activeSessionId: string;
  onSelect: (id: string) => void;
  onNew: () => void;
  onRefresh: () => void;
}

/**
 * Sidebar panel that lists active chat sessions and lets the user switch
 * between them, create new ones, or delete existing ones.
 */
export function SessionSelector({
  sessions,
  activeSessionId,
  onSelect,
  onNew,
  onRefresh,
}: SessionSelectorProps) {
  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    await deleteSession(id);
    onRefresh();
    if (id === activeSessionId) onNew();
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-gray-800">
        <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
          Sessions
        </span>
        <div className="flex gap-1">
          <button
            onClick={onRefresh}
            title="Refresh sessions"
            className="text-gray-500 hover:text-gray-300 p-1 rounded transition-colors"
          >
            <RefreshCw size={13} />
          </button>
          <button
            onClick={onNew}
            title="New session"
            className="text-gray-500 hover:text-gray-300 p-1 rounded transition-colors"
          >
            <PlusCircle size={13} />
          </button>
        </div>
      </div>

      {/* List */}
      <ul className="flex-1 overflow-y-auto py-2">
        {sessions.length === 0 && (
          <li className="px-4 py-6 text-xs text-gray-600 text-center">
            No sessions yet
          </li>
        )}
        {sessions.map((s) => (
          <li key={s.session_id}>
            <button
              onClick={() => onSelect(s.session_id)}
              className={clsx(
                'w-full flex items-center justify-between px-4 py-2 text-left text-sm transition-colors rounded',
                s.session_id === activeSessionId
                  ? 'bg-brand-600/20 text-white'
                  : 'text-gray-400 hover:bg-gray-800 hover:text-white',
              )}
            >
              <span className="truncate flex-1">
                {s.session_id.slice(0, 8)}…
              </span>
              <span className="text-xs text-gray-600 ml-2 flex-shrink-0">
                {s.message_count} msg
              </span>
              <button
                onClick={(e) => handleDelete(e, s.session_id)}
                title="Delete session"
                className="ml-2 text-gray-600 hover:text-red-400 flex-shrink-0 transition-colors"
              >
                <Trash2 size={12} />
              </button>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
