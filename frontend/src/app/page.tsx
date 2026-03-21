'use client';

import { useState, useEffect, useRef } from 'react';
import { useSession } from 'next-auth/react';
import { LoginButton } from '@/components/LoginButton';
import { SessionSelector } from '@/components/SessionSelector';
import { SettingsPanel } from '@/components/SettingsPanel';
import { ChatMessage } from '@/components/ChatMessage';
import { sendChat, sendChatStream, getSessions } from '@/lib/api';
import type { SessionInfo } from '@/lib/api';
import { Send, Loader2, Settings } from 'lucide-react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  streaming?: boolean;
}

interface AgentSettings {
  model: string;
  temperature: number;
  useAgent: boolean;
  stream: boolean;
}

const DEFAULT_SETTINGS: AgentSettings = {
  model: 'gpt-oss:20b',
  temperature: 0.7,
  useAgent: true,
  stream: true,
};

export default function HomePage() {
  const { data: session } = useSession();

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string>('');
  const [sessions, setSessions] = useState<SessionInfo[]>([]);
  const [showSettings, setShowSettings] = useState(false);
  const [agentSettings, setAgentSettings] = useState<AgentSettings>(DEFAULT_SETTINGS);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  /** Scroll the message list to the bottom. */
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  /** Load session list from the backend. */
  const loadSessions = async () => {
    try {
      const data = await getSessions();
      setSessions(data.sessions);
    } catch {
      // Silently ignore if backend is unavailable
    }
  };

  useEffect(() => {
    loadSessions();
  }, []);

  /** Send the current input as a chat message. */
  const handleSend = async () => {
    const text = input.trim();
    if (!text || isLoading) return;

    setInput('');
    setIsLoading(true);

    // Optimistically add the user message
    setMessages((prev) => [...prev, { role: 'user', content: text }]);

    try {
      if (agentSettings.stream) {
        // Add a placeholder for the streaming response
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: '', streaming: true },
        ]);

        let sid = sessionId;
        await sendChatStream(
          {
            message: text,
            session_id: sid || undefined,
            model: agentSettings.model,
            temperature: agentSettings.temperature,
            use_agent: agentSettings.useAgent,
          },
          (token) => {
            setMessages((prev) => {
              const updated = [...prev];
              const last = updated[updated.length - 1];
              if (last?.role === 'assistant') {
                updated[updated.length - 1] = {
                  ...last,
                  content: last.content + token,
                };
              }
              return updated;
            });
          },
        );

        // Mark streaming as complete
        setMessages((prev) => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last?.role === 'assistant') {
            updated[updated.length - 1] = { ...last, streaming: false };
          }
          return updated;
        });
      } else {
        const res = await sendChat({
          message: text,
          session_id: sessionId || undefined,
          model: agentSettings.model,
          temperature: agentSettings.temperature,
          use_agent: agentSettings.useAgent,
        });
        if (!sessionId) setSessionId(res.session_id);
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: res.response },
        ]);
      }

      await loadSessions();
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `Error: ${err instanceof Error ? err.message : 'Unknown error'}`,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSelectSession = (sid: string) => {
    setSessionId(sid);
    setMessages([]); // Clear UI; history is kept in backend
  };

  const handleNewSession = () => {
    setSessionId('');
    setMessages([]);
  };

  return (
    <div className="flex h-screen">
      {/* ── Sidebar ──────────────────────────────────────────────────────── */}
      <aside className="w-64 bg-gray-900 border-r border-gray-800 flex flex-col">
        <div className="p-4 border-b border-gray-800">
          <h1 className="text-lg font-semibold text-white">🤖 Local AI Agent</h1>
        </div>

        {/* Google login */}
        <div className="p-4 border-b border-gray-800">
          <LoginButton />
        </div>

        {/* Session list */}
        <div className="flex-1 overflow-hidden">
          <SessionSelector
            sessions={sessions}
            activeSessionId={sessionId}
            onSelect={handleSelectSession}
            onNew={handleNewSession}
            onRefresh={loadSessions}
          />
        </div>

        {/* Settings toggle */}
        <div className="p-4 border-t border-gray-800">
          <button
            onClick={() => setShowSettings((v) => !v)}
            className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors"
          >
            <Settings size={16} />
            Settings
          </button>
        </div>
      </aside>

      {/* ── Main area ─────────────────────────────────────────────────────── */}
      <main className="flex-1 flex flex-col">
        {/* Settings panel */}
        {showSettings && (
          <SettingsPanel
            settings={agentSettings}
            onChange={setAgentSettings}
            onClose={() => setShowSettings(false)}
          />
        )}

        {/* Auth gate */}
        {!session ? (
          <div className="flex-1 flex items-center justify-center text-gray-400">
            <p className="text-center">
              Sign in with Google to enable Gmail, Calendar, and Drive tools.
              <br />
              <span className="text-sm text-gray-500">
                (You can still chat without signing in.)
              </span>
            </p>
          </div>
        ) : null}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.length === 0 && (
            <div className="flex items-center justify-center h-full">
              <p className="text-gray-500 text-center">
                Start a conversation…<br />
                <span className="text-sm">
                  The agent has access to Gmail, Calendar, and Drive.
                </span>
              </p>
            </div>
          )}
          {messages.map((msg, i) => (
            <ChatMessage key={i} role={msg.role} content={msg.content} streaming={msg.streaming} />
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Input bar */}
        <div className="border-t border-gray-800 p-4">
          <div className="flex gap-3 items-end">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Message the agent… (Enter to send, Shift+Enter for newline)"
              rows={3}
              disabled={isLoading}
              className="flex-1 bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-brand-500 disabled:opacity-50 text-gray-100 placeholder-gray-500"
            />
            <button
              onClick={handleSend}
              disabled={isLoading || !input.trim()}
              className="bg-brand-600 hover:bg-brand-700 disabled:opacity-40 text-white rounded-xl p-3 transition-colors"
              aria-label="Send message"
            >
              {isLoading ? (
                <Loader2 size={20} className="animate-spin" />
              ) : (
                <Send size={20} />
              )}
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
