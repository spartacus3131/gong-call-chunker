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
    return <p className="text-mako-500 animate-pulse">Loading analytics...</p>;

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-ff-text-bright">Analytics</h1>
        <select
          value={selectedCustomer}
          onChange={(e) => handleCustomerChange(e.target.value)}
          className="ff-select"
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
          label="Avg Deal Score"
          value={dealLikelihood?.average ?? "N/A"}
          color="gold"
        />
        <StatCard
          label="Analyzed"
          value={sentiment?.total ?? 0}
          color="purple"
          subtitle="calls with sentiment"
        />
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* Pain Points */}
        <BarChart title="Pain Points" data={painPoints} color="red" />

        {/* Competitors */}
        <BarChart title="Competitor Mentions" data={competitors} color="blue" />

        {/* Deal Likelihood Distribution */}
        {dealLikelihood?.distribution && (
          <div className="ff-panel p-6">
            <h2 className="text-ff-text-bright font-semibold mb-4">
              Deal Likelihood
            </h2>
            <div className="space-y-3">
              {Object.entries(
                dealLikelihood.distribution as Record<string, number>
              ).map(([bucket, count]) => (
                <div key={bucket} className="flex items-center gap-3">
                  <span className="text-xs w-28 text-ff-text/50">{bucket}</span>
                  <div className="flex-1 bg-ff-dark rounded h-5">
                    <div
                      className="bg-gradient-to-r from-mako-700 to-mako-500 rounded h-5 transition-all"
                      style={{
                        width: `${
                          dealLikelihood.total
                            ? ((count as number) / dealLikelihood.total) * 100
                            : 0
                        }%`,
                      }}
                    />
                  </div>
                  <span className="text-sm font-medium w-8 text-right text-mako-400">
                    {count as number}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Sentiment Distribution */}
        {sentiment?.distribution && (
          <div className="ff-panel p-6">
            <h2 className="text-ff-text-bright font-semibold mb-4">
              Call Sentiment
            </h2>
            <div className="flex gap-4">
              {Object.entries(
                sentiment.distribution as Record<string, number>
              ).map(([label, count]) => {
                const colors: Record<string, string> = {
                  positive:
                    "bg-mako-500/10 text-mako-400 border-mako-500/30",
                  neutral:
                    "bg-ff-border/20 text-ff-text border-ff-border",
                  negative: "bg-ff-red/10 text-ff-red border-ff-red/30",
                };
                return (
                  <div
                    key={label}
                    className={`flex-1 rounded-lg p-4 text-center border ${
                      colors[label] || "bg-ff-border/20 border-ff-border"
                    }`}
                  >
                    <p className="text-2xl font-bold">{count as number}</p>
                    <p className="text-xs capitalize mt-1 opacity-70">
                      {label}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* All Field Distributions */}
      {overview && overview.field_distributions.length > 0 && (
        <div className="mt-8">
          <h2 className="text-lg font-semibold text-ff-text-bright mb-4">
            All Field Distributions
          </h2>
          <div className="grid grid-cols-2 gap-6">
            {overview.field_distributions
              .filter(
                (d) =>
                  !["pain_points", "competitor_mentions"].includes(
                    d.field_name
                  )
              )
              .map((dist) => (
                <BarChart
                  key={dist.field_name}
                  title={dist.field_name.replace(/_/g, " ")}
                  data={dist.values}
                  color="green"
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
  color,
  subtitle,
}: {
  label: string;
  value: number | string;
  color: "blue" | "green" | "gold" | "purple";
  subtitle?: string;
}) {
  const colors = {
    blue: "border-ff-blue/30 text-ff-blue",
    green: "border-mako-500/30 text-mako-400",
    gold: "border-ff-gold/30 text-ff-gold",
    purple: "border-purple-500/30 text-purple-400",
  };
  return (
    <div className={`ff-panel p-4 border-l-2 ${colors[color]}`}>
      <p className="text-[10px] text-ff-text/40 uppercase tracking-wider">
        {label}
      </p>
      <p className={`text-3xl font-bold mt-1 ${colors[color].split(" ")[1]}`}>
        {value}
      </p>
      {subtitle && (
        <p className="text-[10px] text-ff-text/30 mt-1">{subtitle}</p>
      )}
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

  const gradients: Record<string, string> = {
    red: "from-ff-red/70 to-ff-red/40",
    blue: "from-ff-blue/70 to-ff-blue/40",
    green: "from-mako-600 to-mako-400",
  };
  const textColors: Record<string, string> = {
    red: "text-ff-red",
    blue: "text-ff-blue",
    green: "text-mako-400",
  };

  return (
    <div className="ff-panel p-6">
      <h2 className="text-ff-text-bright font-semibold mb-4 capitalize">
        {title}
      </h2>
      {entries.length === 0 ? (
        <p className="text-ff-text/30 text-sm">No data yet</p>
      ) : (
        <div className="space-y-2">
          {entries.slice(0, 10).map(([label, count]) => (
            <div key={label} className="flex items-center gap-3">
              <span className="text-xs w-32 text-ff-text/50 truncate capitalize">
                {label.replace(/_/g, " ")}
              </span>
              <div className="flex-1 bg-ff-dark rounded h-5">
                <div
                  className={`bg-gradient-to-r ${
                    gradients[color] || gradients.green
                  } rounded h-5 transition-all`}
                  style={{ width: `${(count / max) * 100}%` }}
                />
              </div>
              <span
                className={`text-sm font-medium w-8 text-right ${
                  textColors[color] || textColors.green
                }`}
              >
                {count}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
