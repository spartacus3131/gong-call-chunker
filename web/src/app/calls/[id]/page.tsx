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
  const [chunkError, setChunkError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<
    "chunks" | "transcript" | "fields" | "scorecard"
  >("chunks");

  useEffect(() => {
    api
      .getCall(params.id as string)
      .then(setCall)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [params.id]);

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

  if (loading)
    return <p className="text-mako-500 animate-pulse">Loading...</p>;
  if (!call) return <p className="text-ff-red">Call not found</p>;

  const topics = call.chunks.filter((c) => c.level === "topics");
  const insights = call.chunks.filter((c) => c.level === "insights");
  const quotes = call.chunks.filter((c) => c.level === "quotes");

  return (
    <div>
      {/* Header */}
      <div className="flex justify-between items-start mb-6">
        <div>
          <h1 className="text-2xl font-bold text-ff-text-bright">
            {call.title}
          </h1>
          <p className="text-ff-text/50 text-sm mt-1">
            {new Date(call.date).toLocaleDateString()} &middot;{" "}
            {call.participants.join(", ") || "No participants listed"}
            {call.duration_seconds &&
              ` \u00B7 ${Math.round(call.duration_seconds / 60)} min`}
          </p>
        </div>
        <div className="flex gap-2 items-center">
          {call.status === "failed" && (
            <span className="ff-badge ff-badge-failed mr-2">Failed</span>
          )}
          {call.status === "processing" && (
            <span className="ff-badge ff-badge-processing mr-2">
              Processing...
            </span>
          )}
          {(call.status === "pending" || call.status === "failed") && (
            <button
              onClick={handleChunk}
              disabled={chunking}
              className="ff-btn-primary disabled:opacity-40"
            >
              {chunking
                ? "Processing..."
                : call.status === "failed"
                ? "Retry Chunking"
                : "Chunk This Call"}
            </button>
          )}
          <button onClick={handleDelete} className="ff-btn-danger">
            Delete
          </button>
        </div>
      </div>

      {/* Error Banner */}
      {(chunkError || call.error_message) && (
        <div className="ff-panel border-ff-red/30 p-4 mb-6">
          <p className="text-sm text-ff-red font-medium">Chunking failed</p>
          <p className="text-sm text-ff-red/70 mt-1">
            {chunkError || call.error_message}
          </p>
        </div>
      )}

      {/* Summary Card */}
      {call.summary && (
        <div className="ff-panel-glow p-6 mb-6">
          <h2 className="text-mako-400 font-semibold mb-3">Call Summary</h2>
          <p className="text-sm text-ff-text mb-3">
            {call.summary.summary_text}
          </p>
          <div className="grid grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-ff-text/40 text-xs uppercase tracking-wider">
                Sentiment
              </span>
              <p className="font-medium text-ff-text-bright capitalize mt-1">
                {call.summary.overall_sentiment}
              </p>
            </div>
            <div>
              <span className="text-ff-text/40 text-xs uppercase tracking-wider">
                Deal Likelihood
              </span>
              <p className="font-medium text-ff-gold mt-1">
                {call.summary.deal_likelihood}/10
              </p>
            </div>
            <div>
              <span className="text-ff-text/40 text-xs uppercase tracking-wider">
                Follow-up
              </span>
              <p className="font-medium text-ff-text-bright mt-1">
                {call.summary.follow_up_date || "Not set"}
              </p>
            </div>
            <div>
              <span className="text-ff-text/40 text-xs uppercase tracking-wider">
                Next Steps
              </span>
              <ul className="list-disc list-inside mt-1 text-ff-text">
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
        {(["chunks", "fields", "scorecard", "transcript"] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 rounded-t text-sm font-medium transition-colors ${
              activeTab === tab
                ? "bg-ff-panel text-mako-400 border border-ff-border border-b-ff-panel"
                : "text-ff-text/50 hover:text-ff-text"
            }`}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
            {tab === "chunks" && call.chunks.length > 0 && (
              <span className="ml-1 text-xs text-ff-text/30">
                ({call.chunks.length})
              </span>
            )}
            {tab === "scorecard" && call.scores?.length > 0 && (
              <span className="ml-1 text-xs text-ff-text/30">
                ({call.scores.filter(s => s.present).length}/{call.scores.length})
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="ff-panel p-6">
        {activeTab === "chunks" && (
          <>
            {call.chunks.length === 0 ? (
              <p className="text-ff-text/50 text-sm">
                Not yet chunked. Click &quot;Chunk This Call&quot; to process.
              </p>
            ) : (
              <div className="space-y-8">
                {topics.length > 0 && (
                  <Section title="Topics" color="blue">
                    {topics.map((chunk) => (
                      <div
                        key={chunk.id}
                        className="border-l-2 border-ff-blue/50 pl-4 mb-4"
                      >
                        <h4 className="font-medium text-ff-text-bright">
                          {chunk.content.title}
                        </h4>
                        {chunk.timestamp_start && (
                          <span className="text-xs text-ff-text/30">
                            {chunk.timestamp_start} - {chunk.timestamp_end}
                          </span>
                        )}
                        <p className="text-sm text-ff-text mt-1">
                          {chunk.content.summary}
                        </p>
                        {chunk.content.relevance_to_sale && (
                          <p className="text-xs text-mako-500 mt-1">
                            Sales relevance: {chunk.content.relevance_to_sale}
                          </p>
                        )}
                      </div>
                    ))}
                  </Section>
                )}

                {insights.length > 0 && (
                  <Section title="Insights" color="green">
                    {insights.map((chunk) => (
                      <div
                        key={chunk.id}
                        className="border-l-2 border-mako-500/50 pl-4 mb-4"
                      >
                        <p className="text-xs text-ff-text/30 mb-1">
                          {chunk.content.parent_topic}
                        </p>
                        <p className="text-sm text-ff-text">
                          {chunk.content.insight}
                        </p>
                        <div className="flex gap-3 mt-1 text-xs">
                          <span className="text-ff-text/40">
                            Sentiment: {chunk.content.sentiment}
                          </span>
                          {chunk.content.action_item && (
                            <span className="text-ff-gold">
                              Action: {chunk.content.action_item}
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </Section>
                )}

                {quotes.length > 0 && (
                  <Section title="Quotes" color="purple">
                    {quotes.map((chunk) => (
                      <div
                        key={chunk.id}
                        className="border-l-2 border-purple-500/50 pl-4 mb-4"
                      >
                        <blockquote className="text-sm italic text-ff-text-bright">
                          &ldquo;{chunk.content.quote}&rdquo;
                        </blockquote>
                        <p className="text-xs text-ff-text/40 mt-1">
                          &mdash; {chunk.content.speaker}
                          {chunk.content.context &&
                            ` (${chunk.content.context})`}
                        </p>
                        {chunk.content.tags && (
                          <div className="flex gap-1 mt-2">
                            {chunk.content.tags.map((tag: string) => (
                              <span
                                key={tag}
                                className="px-1.5 py-0.5 bg-purple-500/10 text-purple-400 border border-purple-500/30 rounded text-xs"
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
              <p className="text-ff-text/50 text-sm">
                No extracted fields yet.
              </p>
            ) : (
              <div className="grid grid-cols-2 gap-4">
                {call.fields.map((field) => (
                  <div
                    key={field.id}
                    className="border border-ff-border/50 rounded p-3"
                  >
                    <p className="text-xs text-mako-500/70 uppercase tracking-wide">
                      {field.field_name.replace(/_/g, " ")}
                    </p>
                    <p className="text-sm font-medium text-ff-text-bright mt-1">
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

        {activeTab === "scorecard" && (
          <>
            {(!call.scores || call.scores.length === 0) ? (
              <p className="text-ff-text/50 text-sm">
                No scorecard data yet. Chunk this call to generate scores.
              </p>
            ) : (
              <div className="space-y-6">
                {/* Overall score */}
                {(() => {
                  const avgScore = call.scores.reduce((sum, s) => sum + s.score, 0) / call.scores.length;
                  const presentCount = call.scores.filter(s => s.present).length;
                  return (
                    <div className="flex gap-6 mb-2">
                      <div>
                        <span className="text-xs text-ff-text/40 uppercase tracking-wider">Avg Score</span>
                        <p className="text-3xl font-bold text-mako-400">{avgScore.toFixed(1)}<span className="text-lg text-ff-text/30">/5</span></p>
                      </div>
                      <div>
                        <span className="text-xs text-ff-text/40 uppercase tracking-wider">Skills Present</span>
                        <p className="text-3xl font-bold text-ff-text-bright">{presentCount}<span className="text-lg text-ff-text/30">/{call.scores.length}</span></p>
                      </div>
                    </div>
                  );
                })()}

                {/* Group by category */}
                {(() => {
                  const categories = new Map<string, typeof call.scores>();
                  call.scores.forEach(s => {
                    if (!categories.has(s.skill_category)) categories.set(s.skill_category, []);
                    categories.get(s.skill_category)!.push(s);
                  });
                  const categoryLabels: Record<string, string> = {
                    discovery: "Discovery",
                    middle_of_call: "Middle of Call",
                    pricing: "Pricing",
                    end_of_call: "End of Call",
                    prospect_engagement: "Prospect Engagement",
                  };
                  const categoryColors: Record<string, string> = {
                    discovery: "border-ff-blue/50",
                    middle_of_call: "border-mako-500/50",
                    pricing: "border-ff-gold/50",
                    end_of_call: "border-purple-500/50",
                    prospect_engagement: "border-ff-blue/30",
                  };
                  return Array.from(categories.entries()).map(([cat, scores]) => (
                    <div key={cat}>
                      <h3 className="text-xs font-semibold uppercase tracking-wider text-ff-text/50 mb-3">
                        {categoryLabels[cat] || cat.replace(/_/g, " ")}
                        <span className="ml-2 text-mako-500">
                          {(scores.reduce((sum, s) => sum + s.score, 0) / scores.length).toFixed(1)} avg
                        </span>
                      </h3>
                      <div className="space-y-2">
                        {scores.map((score) => (
                          <div key={score.id} className={`border-l-2 ${categoryColors[cat] || "border-ff-border"} pl-4 py-2`}>
                            <div className="flex items-center gap-3">
                              <span className={`text-sm font-medium ${score.present ? "text-ff-text-bright" : "text-ff-text/30"}`}>
                                {score.skill_name.replace(/_/g, " ")}
                              </span>
                              <div className="flex gap-0.5">
                                {[1, 2, 3, 4, 5].map(n => (
                                  <div
                                    key={n}
                                    className={`w-5 h-2 rounded-sm ${
                                      n <= score.score
                                        ? score.score >= 4 ? "bg-mako-500" : score.score >= 3 ? "bg-ff-gold" : "bg-ff-red/70"
                                        : "bg-ff-border/30"
                                    }`}
                                  />
                                ))}
                              </div>
                              <span className="text-xs text-ff-text/30">{score.score}/5</span>
                              {!score.present && (
                                <span className="text-[10px] text-ff-red/60 uppercase tracking-wider">Not demonstrated</span>
                              )}
                            </div>
                            {score.evidence && (
                              <p className="text-xs text-ff-text/50 mt-1 italic">
                                &ldquo;{score.evidence}&rdquo;
                              </p>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  ));
                })()}
              </div>
            )}
          </>
        )}

        {activeTab === "transcript" && (
          <pre className="text-sm whitespace-pre-wrap text-ff-text max-h-[600px] overflow-y-auto">
            {call.raw_transcript}
          </pre>
        )}
      </div>
    </div>
  );
}

function Section({
  title,
  color,
  children,
}: {
  title: string;
  color: string;
  children: React.ReactNode;
}) {
  const colors: Record<string, string> = {
    blue: "text-ff-blue",
    green: "text-mako-400",
    purple: "text-purple-400",
  };
  return (
    <div>
      <h3
        className={`text-xs font-semibold uppercase tracking-wider mb-3 ${
          colors[color] || "text-ff-text/50"
        }`}
      >
        {title}
      </h3>
      {children}
    </div>
  );
}
