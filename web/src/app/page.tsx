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

  if (loading) return <p className="text-gray-500">Loading...</p>;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Dashboard</h1>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <StatCard label="Total Calls" value={overview?.total_calls ?? 0} />
        <StatCard label="Chunked" value={overview?.total_chunked ?? 0} />
        <StatCard
          label="Pending"
          value={(overview?.total_calls ?? 0) - (overview?.total_chunked ?? 0)}
        />
      </div>

      {/* Recent Calls */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold">Recent Calls</h2>
          <Link
            href="/calls"
            className="text-sm text-blue-600 hover:underline"
          >
            View all
          </Link>
        </div>

        {calls.length === 0 ? (
          <p className="text-gray-500 text-sm">
            No calls yet.{" "}
            <Link href="/calls" className="text-blue-600 hover:underline">
              Upload a transcript
            </Link>{" "}
            to get started.
          </p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500 border-b">
                <th className="pb-2">Title</th>
                <th className="pb-2">Date</th>
                <th className="pb-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {calls.map((call) => (
                <tr key={call.id} className="border-b last:border-0">
                  <td className="py-2">
                    <Link
                      href={`/calls/${call.id}`}
                      className="text-blue-600 hover:underline"
                    >
                      {call.title}
                    </Link>
                  </td>
                  <td className="py-2 text-gray-500">
                    {new Date(call.date).toLocaleDateString()}
                  </td>
                  <td className="py-2">
                    {call.processed_at ? (
                      <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded text-xs">
                        Chunked
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 bg-yellow-100 text-yellow-700 rounded text-xs">
                        Pending
                      </span>
                    )}
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

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="bg-white rounded-lg shadow p-4">
      <p className="text-sm text-gray-500">{label}</p>
      <p className="text-3xl font-bold">{value}</p>
    </div>
  );
}
