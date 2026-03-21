'use client';

import { clsx } from 'clsx';
import { Bot, User } from 'lucide-react';

interface ChatMessageProps {
  role: 'user' | 'assistant';
  content: string;
  streaming?: boolean;
}

/**
 * Renders a single chat message bubble with role-specific styling.
 * Shows an animated cursor while `streaming` is true.
 */
export function ChatMessage({ role, content, streaming }: ChatMessageProps) {
  const isUser = role === 'user';

  return (
    <div
      className={clsx(
        'flex gap-3',
        isUser ? 'flex-row-reverse' : 'flex-row',
      )}
    >
      {/* Avatar */}
      <div
        className={clsx(
          'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0',
          isUser ? 'bg-brand-600' : 'bg-gray-700',
        )}
      >
        {isUser ? <User size={16} /> : <Bot size={16} />}
      </div>

      {/* Bubble */}
      <div
        className={clsx(
          'max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap break-words',
          isUser
            ? 'bg-brand-600 text-white rounded-tr-none'
            : 'bg-gray-800 text-gray-100 rounded-tl-none',
        )}
      >
        {content}
        {streaming && (
          <span className="inline-block w-2 h-4 bg-gray-400 ml-0.5 animate-pulse rounded-sm" />
        )}
        {!content && !streaming && (
          <span className="text-gray-500 italic">Thinking…</span>
        )}
      </div>
    </div>
  );
}
