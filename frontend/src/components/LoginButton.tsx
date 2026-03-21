'use client';

import { useSession, signIn, signOut } from 'next-auth/react';
import { LogIn, LogOut } from 'lucide-react';

/**
 * Shows a Google sign-in or sign-out button depending on session state.
 */
export function LoginButton() {
  const { data: session, status } = useSession();

  if (status === 'loading') {
    return (
      <div className="h-9 bg-gray-800 animate-pulse rounded-lg" />
    );
  }

  if (session) {
    return (
      <div className="flex flex-col gap-2">
        <div className="flex items-center gap-2">
          {session.user?.image && (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={session.user.image}
              alt={session.user.name ?? 'User'}
              className="w-7 h-7 rounded-full"
            />
          )}
          <span className="text-xs text-gray-300 truncate">{session.user?.name}</span>
        </div>
        <button
          onClick={() => signOut()}
          className="flex items-center gap-2 text-xs text-gray-400 hover:text-red-400 transition-colors"
        >
          <LogOut size={14} />
          Sign out
        </button>
      </div>
    );
  }

  return (
    <button
      onClick={() => signIn('google')}
      className="flex items-center gap-2 w-full bg-brand-600 hover:bg-brand-700 text-white text-sm font-medium px-3 py-2 rounded-lg transition-colors"
    >
      <LogIn size={16} />
      Sign in with Google
    </button>
  );
}
