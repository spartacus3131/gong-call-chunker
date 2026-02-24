"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api, CallDetail } from "@/lib/api";

export default function CallDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [call, setCall] = useState<CallDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [chunking, setChunking] = useState(false);
  const [activeTab, setActiveTab] = useState<"chunks" | "transcript" | "fields">("chunks");

  useEffect(() => {
    api
      .getCall(params.id as string)
      .then(setCall)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [params.id]);

  const [chunkError, setChunkError] = useState<string | null>(null);

  const handleChunk = async () => {
    if (!call) return;
    setChunking(true);
    setChunkError(null);
    try {
      const updated = await api.chunkCall(call.id);
      setCall(updated);
    } catch (err: any) {
      const msg = err?.message || "Unknown error";
      setChunkError(msg);
      // Refresh call to get the failed status from server
      try {
        const refreshed = await api.getCall(call.id);
        setCall(refreshed);
      } catch {}
    } finally {
      setChunking(false);
    }
  };

  const handleDelete = async () => {
    if (!call || !confirm("Delete this call?")) return;
    await api.deleteCall(call.id);
    router.push("/calls");
  };

  if (loading) return <p className="text-gray-500">Loading...</p>;
  if (!call) return <p className="text-red-500">Call not found</p>;

  const topics = call.chunks.filter((c) => c.level === "topics");
  const insights = call.chunks.filter((c) => c.level === "insights");
  const quotes = call.chunks.filter((c) => c.level === "quotes");

  return (
    <div>
      {/* Header */}
      <div className="flex justify-between items-start mb-6">
        <div>
          <h1 className="text-2xl font-bold">{call.title}</h1>
          <p className="text-gray-500 text-sm mt-1">
            {new Date(call.date).toLocaleDateString()} &middot;{" "}
            {call.participants.join(", ") || "No participants listed"}
            {call.duration_seconds &&
              ` \u00B7 ${Math.round(call.duration_seconds / 60)} min`}
          </p>
        </div>
        <div className="flex gap-2 items-center">
          {call.status === "failed" && (
            <span className="px-2 py-0.5 bg-red-100 text-red-700 rounded text-xs mr-2">
              Failed
            </span>
          )}
          {call.status === "processing" && (
            <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs mr-2">
              Processing...
            </span>
          )}
          {(call.status === "pending" || call.status === "failed") && (
            <button
              onClick={handleChunk}
              disabled={chunking}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm disabled:opacity-50"
            >
              {chunking ? "Processing..." : call.status === "failed" ? "Retry Chunking" : "Chunk This Call"}
            </button>
          )}
          <button
            onClick={handleDelete}
            className="px-4 py-2 bg-red-100 text-red-700 rounded hover:bg-red-200 text-sm"
          >
            Delete
          </button>
        </div>
      </div>

      {/* Error Banner */}
      {(chunkError || call.error_message) && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <p className="text-sm text-red-700 font-medium">Chunking failed</p>
          <p className="text-sm text-red-600 mt-1">
            {chunkError || call.error_message}
          </p>
        </div>
      )}

      {/* Summary Card */}
      {call.summary && (
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="font-semibold mb-3">Call Summary</h2>
          <p className="text-sm text-gray-700 mb-3">{call.summary.summary_text}</p>
          <div className="grid grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-gray-500">Sentiment</span>
              <p className="font-medium capitalize">
                {call.summary.overall_sentiment}
              </p>
            </div>
            <div>
              <span className="text-gray-500">Deal Likelihood</span>
              <p className="font-medium">{call.summary.deal_likelihood}/10</p>
            </div>
            <div>
              <span className="text-gray-500">Follow-up</span>
              <p className="font-medium">
                {call.summary.follow_up_date || "Not set"}
              </p>
            </div>
            <div>
              <span className="text-gray-500">Next Steps</span>
              <ul className="list-disc list-inside">
                {call.summary.next_steps.map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 mb-4">
        {(["chunks", "fields", "transcript"] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 rounded-t text-sm font-medium ${
              activeTab === tab
                ? "bg-white text-gray-900 shadow"
                : "bg-gray-200 text-gray-600 hover:bg-gray-300"
            }`}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
            {tab === "chunks" && call.chunks.length > 0 && (
              <span className="ml-1 text-xs text-gray-400">
                ({call.chunks.length})
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="bg-white rounded-lg shadow p-6">
        {activeTab === "chunks" && (
          <>
            {call.chunks.length === 0 ? (
              <p className="text-gray-500 text-sm">
                Not yet chunked. Click &quot;Chunk This Call&quot; to process.
              </p>
            ) : (
              <div className="space-y-6">
                {/* Topics */}
                {topics.length > 0 && (
                  <Section title="Topics">
                    {topics.map((chunk) => (
                      <div key={chunk.id} className="border-l-4 border-blue-400 pl-4 mb-4">
                        <h4 className="font-medium">{chunk.content.title}</h4>
                        {chunk.timestamp_start && (
                          <span className="text-xs text-gray-400">
                            {chunk.timestamp_start} - {chunk.timestamp_end}
                          </span>
                        )}
                        <p className="text-sm text-gray-600 mt-1">
                          {chunk.content.summary}
                        </p>
                        {chunk.content.relevance_to_sale && (
                          <p className="text-xs text-blue-600 mt-1">
                            Sales relevance: {chunk.content.relevance_to_sale}
                          </p>
                        )}
                      </div>
                    ))}
                  </Section>
                )}

                {/* Insights */}
                {insights.length > 0 && (
                  <Section title="Insights">
                    {insights.map((chunk) => (
                      <div key={chunk.id} className="border-l-4 border-green-400 pl-4 mb-4">
                        <p className="text-xs text-gray-400 mb-1">
                          {chunk.content.parent_topic}
                        </p>
                        <p className="text-sm">{chunk.content.insight}</p>
                        <div className="flex gap-3 mt-1 text-xs">
                          <span className="text-gray-500">
                            Sentiment: {chunk.content.sentiment}
                          </span>
                          {chunk.content.action_item && (
                            <span className="text-orange-600">
                              Action: {chunk.content.action_item}
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </Section>
                )}

                {/* Quotes */}
                {quotes.length > 0 && (
                  <Section title="Quotes">
                    {quotes.map((chunk) => (
                      <div key={chunk.id} className="border-l-4 border-purple-400 pl-4 mb-4">
                        <blockquote className="text-sm italic">
                          &ldquo;{chunk.content.quote}&rdquo;
                        </blockquote>
                        <p className="text-xs text-gray-500 mt-1">
                          &mdash; {chunk.content.speaker}
                          {chunk.content.context &&
                            ` (${chunk.content.context})`}
                        </p>
                        {chunk.content.tags && (
                          <div className="flex gap-1 mt-1">
                            {chunk.content.tags.map((tag: string) => (
                              <span
                                key={tag}
                                className="px-1.5 py-0.5 bg-purple-50 text-purple-600 rounded text-xs"
                              >
                                {tag}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </Section>
                )}
              </div>
            )}
          </>
        )}

        {activeTab === "fields" && (
          <>
            {call.fields.length === 0 ? (
              <p className="text-gray-500 text-sm">No extracted fields yet.</p>
            ) : (
              <div className="grid grid-cols-2 gap-4">
                {call.fields.map((field) => (
                  <div key={field.id} className="border rounded p-3">
                    <p className="text-xs text-gray-500 uppercase tracking-wide">
                      {field.field_name.replace(/_/g, " ")}
                    </p>
                    <p className="text-sm font-medium mt-1">
                      {Array.isArray(field.field_value)
                        ? field.field_value.join(", ")
                        : typeof field.field_value === "boolean"
                        ? field.field_value
                          ? "Yes"
                          : "No"
                        : String(field.field_value)}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </>
        )}

        {activeTab === "transcript" && (
          <pre className="text-sm whitespace-pre-wrap font-mono text-gray-700 max-h-[600px] overflow-y-auto">
            {call.raw_transcript}
          </pre>
        )}
      </div>
    </div>
  );
}

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
        {title}
      </h3>
      {children}
    </div>
  );
}
