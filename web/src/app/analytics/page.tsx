"use client";

import { useEffect, useState } from "react";
import { api, AnalyticsOverview, CustomerConfig } from "@/lib/api";

export default function AnalyticsPage() {
  const [schemas, setSchemas] = useState<CustomerConfig[]>([]);
  const [selectedCustomer, setSelectedCustomer] = useState<string>("");
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [painPoints, setPainPoints] = useState<Record<string, number>>({});
  const [competitors, setCompetitors] = useState<Record<string, number>>({});
  const [dealLikelihood, setDealLikelihood] = useState<any>(null);
  const [sentiment, setSentiment] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const loadData = async (slug?: string) => {
    setLoading(true);
    try {
      const [o, pp, comp, dl, sent] = await Promise.all([
        api.getOverview(slug),
        api.getPainPoints(slug),
        api.getCompetitors(slug),
        api.getDealLikelihood(slug),
        api.getSentiment(slug),
      ]);
      setOverview(o);
      setPainPoints(pp.counts || {});
      setCompetitors(comp.counts || {});
      setDealLikelihood(dl);
      setSentiment(sent);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    api.listSchemas().then(setSchemas).catch(console.error);
    loadData();
  }, []);

  const handleCustomerChange = (slug: string) => {
    setSelectedCustomer(slug);
    loadData(slug || undefined);
  };

  if (loading && !overview)
    return <p className="text-gray-500">Loading analytics...</p>;

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Analytics</h1>
        <select
          value={selectedCustomer}
          onChange={(e) => handleCustomerChange(e.target.value)}
          className="border rounded px-3 py-2 text-sm"
        >
          <option value="">All customers</option>
          {schemas.map((s) => (
            <option key={s.slug} value={s.slug}>
              {s.display_name}
            </option>
          ))}
        </select>
      </div>

      {/* Summary Row */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        <StatCard label="Total Calls" value={overview?.total_calls ?? 0} />
        <StatCard label="Chunked" value={overview?.total_chunked ?? 0} />
        <StatCard
          label="Avg Deal Likelihood"
          value={dealLikelihood?.average ?? "N/A"}
        />
        <StatCard
          label="Total Sentiment"
          value={sentiment?.total ?? 0}
          subtitle="calls analyzed"
        />
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* Pain Points */}
        <BarChart title="Pain Points" data={painPoints} color="red" />

        {/* Competitors */}
        <BarChart title="Competitor Mentions" data={competitors} color="blue" />

        {/* Deal Likelihood Distribution */}
        {dealLikelihood?.distribution && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="font-semibold mb-4">Deal Likelihood Distribution</h2>
            <div className="space-y-2">
              {Object.entries(dealLikelihood.distribution as Record<string, number>).map(
                ([bucket, count]) => (
                  <div key={bucket} className="flex items-center gap-3">
                    <span className="text-sm w-32 text-gray-600">{bucket}</span>
                    <div className="flex-1 bg-gray-100 rounded h-6">
                      <div
                        className="bg-green-500 rounded h-6"
                        style={{
                          width: `${
                            dealLikelihood.total
                              ? ((count as number) / dealLikelihood.total) * 100
                              : 0
                          }%`,
                        }}
                      />
                    </div>
                    <span className="text-sm font-medium w-8 text-right">
                      {count as number}
                    </span>
                  </div>
                )
              )}
            </div>
          </div>
        )}

        {/* Sentiment Distribution */}
        {sentiment?.distribution && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="font-semibold mb-4">Sentiment Distribution</h2>
            <div className="flex gap-4">
              {Object.entries(sentiment.distribution as Record<string, number>).map(
                ([label, count]) => {
                  const colors: Record<string, string> = {
                    positive: "bg-green-100 text-green-700",
                    neutral: "bg-gray-100 text-gray-700",
                    negative: "bg-red-100 text-red-700",
                  };
                  return (
                    <div
                      key={label}
                      className={`flex-1 rounded-lg p-4 text-center ${
                        colors[label] || "bg-gray-100"
                      }`}
                    >
                      <p className="text-2xl font-bold">{count as number}</p>
                      <p className="text-sm capitalize">{label}</p>
                    </div>
                  );
                }
              )}
            </div>
          </div>
        )}
      </div>

      {/* Field Distributions */}
      {overview && overview.field_distributions.length > 0 && (
        <div className="mt-8">
          <h2 className="text-lg font-semibold mb-4">All Field Distributions</h2>
          <div className="grid grid-cols-2 gap-6">
            {overview.field_distributions
              .filter(
                (d) =>
                  !["pain_points", "competitor_mentions"].includes(d.field_name)
              )
              .map((dist) => (
                <BarChart
                  key={dist.field_name}
                  title={dist.field_name.replace(/_/g, " ")}
                  data={dist.values}
                  color="indigo"
                />
              ))}
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({
  label,
  value,
  subtitle,
}: {
  label: string;
  value: number | string;
  subtitle?: string;
}) {
  return (
    <div className="bg-white rounded-lg shadow p-4">
      <p className="text-sm text-gray-500">{label}</p>
      <p className="text-3xl font-bold">{value}</p>
      {subtitle && <p className="text-xs text-gray-400">{subtitle}</p>}
    </div>
  );
}

function BarChart({
  title,
  data,
  color,
}: {
  title: string;
  data: Record<string, number>;
  color: string;
}) {
  const entries = Object.entries(data).sort((a, b) => b[1] - a[1]);
  const max = entries.length > 0 ? entries[0][1] : 1;

  const colorMap: Record<string, string> = {
    red: "bg-red-400",
    blue: "bg-blue-400",
    green: "bg-green-400",
    indigo: "bg-indigo-400",
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="font-semibold mb-4 capitalize">{title}</h2>
      {entries.length === 0 ? (
        <p className="text-gray-400 text-sm">No data yet</p>
      ) : (
        <div className="space-y-2">
          {entries.slice(0, 10).map(([label, count]) => (
            <div key={label} className="flex items-center gap-3">
              <span className="text-sm w-36 text-gray-600 truncate capitalize">
                {label.replace(/_/g, " ")}
              </span>
              <div className="flex-1 bg-gray-100 rounded h-5">
                <div
                  className={`${colorMap[color] || "bg-gray-400"} rounded h-5`}
                  style={{ width: `${(count / max) * 100}%` }}
                />
              </div>
              <span className="text-sm font-medium w-8 text-right">
                {count}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
