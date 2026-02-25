"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, CallOut, CustomerConfig } from "@/lib/api";

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

export default function CallsPage() {
  const [calls, setCalls] = useState<CallOut[]>([]);
  const [schemas, setSchemas] = useState<CustomerConfig[]>([]);
  const [selectedCustomer, setSelectedCustomer] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);

  const [showUpload, setShowUpload] = useState(false);
  const [uploadTitle, setUploadTitle] = useState("");
  const [uploadDate, setUploadDate] = useState(
    new Date().toISOString().split("T")[0]
  );
  const [uploadTranscript, setUploadTranscript] = useState("");
  const [uploadCustomer, setUploadCustomer] = useState("");
  const [uploadRepName, setUploadRepName] = useState("");
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    Promise.all([api.listCalls(), api.listSchemas()])
      .then(([c, s]) => {
        setCalls(c);
        setSchemas(s);
        if (s.length > 0) setUploadCustomer(s[0].slug);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const handleSearch = async () => {
    if (!searchQuery && !selectedCustomer) {
      const c = await api.listCalls();
      setCalls(c);
      return;
    }
    const result = await api.searchCalls({
      query: searchQuery || undefined,
      customer_slug: selectedCustomer || undefined,
    });
    setCalls(result.calls);
  };

  const handleUpload = async () => {
    if (!uploadTitle || !uploadTranscript || !uploadCustomer) return;
    setUploading(true);
    try {
      const newCall = await api.createCall({
        customer_slug: uploadCustomer,
        title: uploadTitle,
        date: new Date(uploadDate).toISOString(),
        raw_transcript: uploadTranscript,
        rep_name: uploadRepName || undefined,
      });
      setCalls((prev) => [newCall, ...prev]);
      setShowUpload(false);
      setUploadTitle("");
      setUploadTranscript("");
    } catch (err) {
      console.error(err);
      alert("Failed to upload");
    } finally {
      setUploading(false);
    }
  };

  if (loading)
    return <p className="text-mako-500 animate-pulse">Loading...</p>;

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-ff-text-bright">Calls</h1>
        <button
          onClick={() => setShowUpload(!showUpload)}
          className={showUpload ? "ff-btn" : "ff-btn-primary"}
        >
          {showUpload ? "Cancel" : "Upload Transcript"}
        </button>
      </div>

      {/* Upload Form */}
      {showUpload && (
        <div className="ff-panel-glow p-6 mb-6">
          <h2 className="text-ff-text-bright font-semibold mb-4">
            Upload Call Transcript
          </h2>
          <div className="grid grid-cols-4 gap-4 mb-4">
            <div>
              <label className="block text-xs text-ff-text/50 mb-1 uppercase tracking-wider">
                Customer
              </label>
              <select
                value={uploadCustomer}
                onChange={(e) => setUploadCustomer(e.target.value)}
                className="ff-select w-full"
              >
                {schemas.map((s) => (
                  <option key={s.slug} value={s.slug}>
                    {s.display_name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs text-ff-text/50 mb-1 uppercase tracking-wider">
                Title
              </label>
              <input
                value={uploadTitle}
                onChange={(e) => setUploadTitle(e.target.value)}
                className="ff-input"
                placeholder="Discovery call with Mario's Pizza"
              />
            </div>
            <div>
              <label className="block text-xs text-ff-text/50 mb-1 uppercase tracking-wider">
                Rep Name
              </label>
              <input
                value={uploadRepName}
                onChange={(e) => setUploadRepName(e.target.value)}
                className="ff-input"
                placeholder="e.g. John Smith"
              />
            </div>
            <div>
              <label className="block text-xs text-ff-text/50 mb-1 uppercase tracking-wider">
                Date
              </label>
              <input
                type="date"
                value={uploadDate}
                onChange={(e) => setUploadDate(e.target.value)}
                className="ff-input"
              />
            </div>
          </div>
          <div className="mb-4">
            <label className="block text-xs text-ff-text/50 mb-1 uppercase tracking-wider">
              Transcript
            </label>
            <textarea
              value={uploadTranscript}
              onChange={(e) => setUploadTranscript(e.target.value)}
              className="ff-input h-48"
              placeholder="Paste call transcript here..."
            />
          </div>
          <button
            onClick={handleUpload}
            disabled={uploading || !uploadTitle || !uploadTranscript}
            className="ff-btn-primary disabled:opacity-40"
          >
            {uploading ? "Uploading..." : "Upload"}
          </button>
        </div>
      )}

      {/* Search & Filter */}
      <div className="flex gap-4 mb-6">
        <input
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          className="ff-input flex-1"
          placeholder="Search transcripts..."
        />
        <select
          value={selectedCustomer}
          onChange={(e) => setSelectedCustomer(e.target.value)}
          className="ff-select"
        >
          <option value="">All customers</option>
          {schemas.map((s) => (
            <option key={s.slug} value={s.slug}>
              {s.display_name}
            </option>
          ))}
        </select>
        <button onClick={handleSearch} className="ff-btn">
          Search
        </button>
      </div>

      {/* Call List */}
      <div className="ff-panel">
        {calls.length === 0 ? (
          <p className="text-ff-text/50 text-sm p-6">No calls found.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-ff-text/40 border-b border-ff-border text-xs uppercase tracking-wider">
                <th className="p-4">Title</th>
                <th className="p-4">Date</th>
                <th className="p-4">Rep</th>
                <th className="p-4">Status</th>
              </tr>
            </thead>
            <tbody>
              {calls.map((call) => (
                <tr
                  key={call.id}
                  className="border-b border-ff-border/30 last:border-0 hover:bg-mako-500/5"
                >
                  <td className="p-4">
                    <Link
                      href={`/calls/${call.id}`}
                      className="text-ff-blue hover:text-mako-400"
                    >
                      {call.title}
                    </Link>
                  </td>
                  <td className="p-4 text-ff-text/50">
                    {new Date(call.date).toLocaleDateString()}
                  </td>
                  <td className="p-4 text-ff-text/50">
                    {call.rep_name || "—"}
                  </td>
                  <td className="p-4">
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
