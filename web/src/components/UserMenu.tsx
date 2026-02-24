"use client";

import { useSession, signOut } from "next-auth/react";

export default function UserMenu() {
  const { data: session } = useSession();

  if (!session?.user) return null;

  return (
    <div className="flex items-center gap-3 px-3 py-2">
      {session.user.image && (
        <img
          src={session.user.image}
          alt=""
          className="w-7 h-7 rounded-full border border-mako-500/30"
        />
      )}
      <div className="flex-1 min-w-0">
        <p className="text-xs text-ff-text truncate">{session.user.name}</p>
        <button
          onClick={() => signOut()}
          className="text-[10px] text-ff-text/40 hover:text-ff-red transition-colors"
        >
          Sign out
        </button>
      </div>
    </div>
  );
}
