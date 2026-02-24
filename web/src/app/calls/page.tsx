"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, CallOut, CustomerConfig } from "@/lib/api";

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    pending: "bg-yellow-100 text-yellow-700",
    processing: "bg-blue-100 text-blue-700",
    chunked: "bg-green-100 text-green-700",
    failed: "bg-red-100 text-red-700",
  };
  return (
    <span className={`px-2 py-0.5 rounded text-xs capitalize ${styles[status] || "bg-gray-100 text-gray-600"}`}>
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

  // Upload state
  const [showUpload, setShowUpload] = useState(false);
  const [uploadTitle, setUploadTitle] = useState("");
  const [uploadDate, setUploadDate] = useState(
    new Date().toISOString().split("T")[0]
  );
  const [uploadTranscript, setUploadTranscript] = useState("");
  const [uploadCustomer, setUploadCustomer] = useState("");
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

  if (loading) return <p className="text-gray-500">Loading...</p>;

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Calls</h1>
        <button
          onClick={() => setShowUpload(!showUpload)}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm"
        >
          {showUpload ? "Cancel" : "Upload Transcript"}
        </button>
      </div>

      {/* Upload Form */}
      {showUpload && (
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="font-semibold mb-4">Upload Call Transcript</h2>
          <div className="grid grid-cols-3 gap-4 mb-4">
            <div>
              <label className="block text-sm text-gray-600 mb-1">
                Customer
              </label>
              <select
                value={uploadCustomer}
                onChange={(e) => setUploadCustomer(e.target.value)}
                className="w-full border rounded px-3 py-2 text-sm"
              >
                {schemas.map((s) => (
                  <option key={s.slug} value={s.slug}>
                    {s.display_name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">Title</label>
              <input
                value={uploadTitle}
                onChange={(e) => setUploadTitle(e.target.value)}
                className="w-full border rounded px-3 py-2 text-sm"
                placeholder="Discovery call with Mario's Pizza"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">Date</label>
              <input
                type="date"
                value={uploadDate}
                onChange={(e) => setUploadDate(e.target.value)}
                className="w-full border rounded px-3 py-2 text-sm"
              />
            </div>
          </div>
          <div className="mb-4">
            <label className="block text-sm text-gray-600 mb-1">
              Transcript
            </label>
            <textarea
              value={uploadTranscript}
              onChange={(e) => setUploadTranscript(e.target.value)}
              className="w-full border rounded px-3 py-2 text-sm h-48 font-mono"
              placeholder="Paste call transcript here... (supports Speaker: text, [timestamp] Speaker: text, or plain text)"
            />
          </div>
          <button
            onClick={handleUpload}
            disabled={uploading || !uploadTitle || !uploadTranscript}
            className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 text-sm disabled:opacity-50"
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
          className="flex-1 border rounded px-3 py-2 text-sm"
          placeholder="Search transcripts..."
        />
        <select
          value={selectedCustomer}
          onChange={(e) => {
            setSelectedCustomer(e.target.value);
          }}
          className="border rounded px-3 py-2 text-sm"
        >
          <option value="">All customers</option>
          {schemas.map((s) => (
            <option key={s.slug} value={s.slug}>
              {s.display_name}
            </option>
          ))}
        </select>
        <button
          onClick={handleSearch}
          className="px-4 py-2 bg-gray-800 text-white rounded text-sm"
        >
          Search
        </button>
      </div>

      {/* Call List */}
      <div className="bg-white rounded-lg shadow">
        {calls.length === 0 ? (
          <p className="text-gray-500 text-sm p-6">No calls found.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500 border-b">
                <th className="p-4">Title</th>
                <th className="p-4">Date</th>
                <th className="p-4">Participants</th>
                <th className="p-4">Status</th>
              </tr>
            </thead>
            <tbody>
              {calls.map((call) => (
                <tr
                  key={call.id}
                  className="border-b last:border-0 hover:bg-gray-50"
                >
                  <td className="p-4">
                    <Link
                      href={`/calls/${call.id}`}
                      className="text-blue-600 hover:underline"
                    >
                      {call.title}
                    </Link>
                  </td>
                  <td className="p-4 text-gray-500">
                    {new Date(call.date).toLocaleDateString()}
                  </td>
                  <td className="p-4 text-gray-500">
                    {call.participants.slice(0, 3).join(", ")}
                    {call.participants.length > 3 && "..."}
                  </td>
                  <td className="p-4">
                    <StatusBadge status={(call as any).status || (call.processed_at ? "chunked" : "pending")} />
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
