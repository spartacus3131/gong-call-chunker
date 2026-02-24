"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, CallOut, AnalyticsOverview } from "@/lib/api";

export default function Dashboard() {
  const [calls, setCalls] = useState<CallOut[]>([]);
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.listCalls(), api.getOverview()])
      .then(([c, o]) => {
        setCalls(c.slice(0, 10));
        setOverview(o);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading)
    return <p className="text-mako-500 animate-pulse">Loading...</p>;

  return (
    <div>
      <h1 className="text-2xl font-bold text-ff-text-bright mb-6">
        Dashboard
      </h1>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <StatCard
          label="Total Calls"
          value={overview?.total_calls ?? 0}
          color="blue"
        />
        <StatCard
          label="Chunked"
          value={overview?.total_chunked ?? 0}
          color="green"
        />
        <StatCard
          label="Pending"
          value={(overview?.total_calls ?? 0) - (overview?.total_chunked ?? 0)}
          color="gold"
        />
      </div>

      {/* Recent Calls */}
      <div className="ff-panel p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-ff-text-bright font-semibold">Recent Calls</h2>
          <Link href="/calls" className="text-sm text-mako-400 hover:text-mako-300">
            View all &rarr;
          </Link>
        </div>

        {calls.length === 0 ? (
          <p className="text-ff-text/50 text-sm">
            No calls yet.{" "}
            <Link href="/calls" className="text-mako-400 hover:underline">
              Upload a transcript
            </Link>{" "}
            to get started.
          </p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-ff-text/50 border-b border-ff-border">
                <th className="pb-2">Title</th>
                <th className="pb-2">Date</th>
                <th className="pb-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {calls.map((call) => (
                <tr
                  key={call.id}
                  className="border-b border-ff-border/30 last:border-0 hover:bg-mako-500/5"
                >
                  <td className="py-2">
                    <Link
                      href={`/calls/${call.id}`}
                      className="text-ff-blue hover:text-mako-400"
                    >
                      {call.title}
                    </Link>
                  </td>
                  <td className="py-2 text-ff-text/50">
                    {new Date(call.date).toLocaleDateString()}
                  </td>
                  <td className="py-2">
                    <StatusBadge
                      status={
                        (call as any).status ||
                        (call.processed_at ? "chunked" : "pending")
                      }
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

function StatCard({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: "blue" | "green" | "gold";
}) {
  const colors = {
    blue: "border-ff-blue/30 text-ff-blue",
    green: "border-mako-500/30 text-mako-400",
    gold: "border-ff-gold/30 text-ff-gold",
  };
  return (
    <div className={`ff-panel p-4 border-l-2 ${colors[color]}`}>
      <p className="text-xs text-ff-text/50 uppercase tracking-wider">
        {label}
      </p>
      <p className={`text-3xl font-bold mt-1 ${colors[color].split(" ")[1]}`}>
        {value}
      </p>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const cls: Record<string, string> = {
    pending: "ff-badge-pending",
    processing: "ff-badge-processing",
    chunked: "ff-badge-chunked",
    failed: "ff-badge-failed",
  };
  return (
    <span className={`ff-badge ${cls[status] || "ff-badge-pending"} capitalize`}>
      {status}
    </span>
  );
}
