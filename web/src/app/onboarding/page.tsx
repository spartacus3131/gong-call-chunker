"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, IndustryTemplate, TemplateDetail } from "@/lib/api";

interface FieldDef {
  name: string;
  type: string;
  description: string;
  options?: string[];
  examples?: string[];
}

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [templates, setTemplates] = useState<IndustryTemplate[]>([]);
  const [selectedIndustry, setSelectedIndustry] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [slug, setSlug] = useState("");
  const [fields, setFields] = useState<FieldDef[]>([]);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.listTemplates().then(setTemplates).catch(console.error);
  }, []);

  const selectIndustry = async (key: string) => {
    setSelectedIndustry(key);
    try {
      const template = await api.getTemplate(key);
      setFields(
        template.fields.map((f) => ({
          name: f.name,
          type: f.type,
          description: f.description || "",
          options: f.options,
          examples: f.examples,
        }))
      );
    } catch {
      setFields([]);
    }
    setStep(2);
  };

  const handleNameChange = (name: string) => {
    setDisplayName(name);
    setSlug(
      name
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "_")
        .replace(/^_|_$/g, "")
    );
  };

  const addField = () => {
    setFields([
      ...fields,
      { name: "", type: "text", description: "" },
    ]);
  };

  const removeField = (index: number) => {
    setFields(fields.filter((_, i) => i !== index));
  };

  const updateField = (index: number, updates: Partial<FieldDef>) => {
    setFields(
      fields.map((f, i) => (i === index ? { ...f, ...updates } : f))
    );
  };

  const finish = async () => {
    setSaving(true);
    try {
      const schemaData: any = {
        customer: slug,
        display_name: displayName,
        industry: selectedIndustry,
        extraction_schema: {
          fields: fields.map((f) => {
            const field: any = {
              name: f.name,
              type: f.type,
              description: f.description,
            };
            if (f.options?.length) field.options = f.options;
            if (f.examples?.length) field.examples = f.examples;
            return field;
          }),
          chunk_levels: [
            {
              level: "topics",
              description: "Major discussion topics (5-8 per call)",
              extract: [
                "title",
                "timestamp_start",
                "timestamp_end",
                "summary",
                "relevance_to_sale",
              ],
            },
            {
              level: "insights",
              description: "Specific insights within topics (2-3 per topic)",
              extract: ["parent_topic", "insight", "sentiment", "action_item"],
            },
            {
              level: "quotes",
              description: "Notable verbatim quotes (5-10 per call)",
              extract: ["quote", "speaker", "context", "sentiment", "tags"],
            },
          ],
          call_summary: [
            "overall_sentiment",
            "deal_likelihood",
            "next_steps",
            "follow_up_date",
          ],
        },
      };

      await api.createSchema(schemaData);
      await api.updateMe({ has_completed_onboarding: true });
      router.push("/");
    } catch (err) {
      console.error(err);
      alert("Failed to create schema. Please try again.");
    } finally {
      setSaving(false);
    }
  };

  const industryIcons: Record<string, string> = {
    restaurant: "🍽",
    saas: "☁",
    real_estate: "🏠",
    healthcare: "🏥",
    general: "📊",
  };

  return (
    <div className="max-w-2xl mx-auto">
      {/* Progress bar */}
      <div className="flex items-center gap-2 mb-8">
        {[1, 2, 3].map((s) => (
          <div key={s} className="flex items-center gap-2 flex-1">
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold border-2 transition-colors ${
                step >= s
                  ? "border-mako-500 bg-mako-500/20 text-mako-400"
                  : "border-ff-border text-ff-text/30"
              }`}
            >
              {s}
            </div>
            {s < 3 && (
              <div
                className={`flex-1 h-px ${
                  step > s ? "bg-mako-500" : "bg-ff-border"
                }`}
              />
            )}
          </div>
        ))}
      </div>

      {/* Step 1: Pick Industry */}
      {step === 1 && (
        <div>
          <h1 className="text-2xl font-bold text-ff-text-bright mb-2">
            What kind of calls do you analyze?
          </h1>
          <p className="text-ff-text/50 mb-8">
            Pick a template to start with. You can customize everything in the
            next step.
          </p>
          <div className="grid grid-cols-2 gap-4">
            {templates.map((t) => (
              <button
                key={t.key}
                onClick={() => selectIndustry(t.key)}
                className="ff-panel p-6 text-left hover:border-mako-500/50 transition-colors group"
              >
                <span className="text-2xl">
                  {industryIcons[t.key] || "📋"}
                </span>
                <h3 className="text-ff-text-bright font-semibold mt-3 group-hover:text-mako-400 transition-colors">
                  {t.display_name}
                </h3>
                <p className="text-xs text-ff-text/40 mt-1">
                  {t.field_count} pre-configured fields
                </p>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Step 2: Name Config */}
      {step === 2 && (
        <div>
          <h1 className="text-2xl font-bold text-ff-text-bright mb-2">
            Name your configuration
          </h1>
          <p className="text-ff-text/50 mb-8">
            This is the name for your extraction schema. It defines what
            intelligence gets pulled from each call.
          </p>
          <div className="space-y-4">
            <div>
              <label className="text-xs text-ff-text/50 uppercase tracking-wider">
                Display Name
              </label>
              <input
                type="text"
                value={displayName}
                onChange={(e) => handleNameChange(e.target.value)}
                placeholder="e.g. TouchBistro Sales Calls"
                className="ff-input w-full mt-1"
                autoFocus
              />
            </div>
            <div>
              <label className="text-xs text-ff-text/50 uppercase tracking-wider">
                Slug (auto-generated)
              </label>
              <input
                type="text"
                value={slug}
                onChange={(e) => setSlug(e.target.value)}
                className="ff-input w-full mt-1 text-ff-text/50"
              />
            </div>
          </div>
          <div className="flex gap-3 mt-8">
            <button
              onClick={() => setStep(1)}
              className="ff-btn"
            >
              Back
            </button>
            <button
              onClick={() => setStep(3)}
              disabled={!displayName || !slug}
              className="ff-btn-primary disabled:opacity-30"
            >
              Next
            </button>
          </div>
        </div>
      )}

      {/* Step 3: Configure Fields */}
      {step === 3 && (
        <div>
          <h1 className="text-2xl font-bold text-ff-text-bright mb-2">
            What should we extract from calls?
          </h1>
          <p className="text-ff-text/50 mb-6">
            These are the fields Claude will extract from every call transcript.
            Add, remove, or edit as needed.
          </p>

          <div className="space-y-3 max-h-[50vh] overflow-y-auto pr-2">
            {fields.map((field, i) => (
              <div
                key={i}
                className="ff-panel p-4 flex gap-3 items-start"
              >
                <div className="flex-1 grid grid-cols-3 gap-2">
                  <input
                    type="text"
                    value={field.name}
                    onChange={(e) =>
                      updateField(i, {
                        name: e.target.value.toLowerCase().replace(/\s+/g, "_"),
                      })
                    }
                    placeholder="field_name"
                    className="ff-input text-sm"
                  />
                  <select
                    value={field.type}
                    onChange={(e) => updateField(i, { type: e.target.value })}
                    className="ff-select text-sm"
                  >
                    <option value="text">Text</option>
                    <option value="enum">Enum</option>
                    <option value="list">List</option>
                    <option value="integer">Integer</option>
                    <option value="boolean">Boolean</option>
                  </select>
                  <input
                    type="text"
                    value={field.description}
                    onChange={(e) =>
                      updateField(i, { description: e.target.value })
                    }
                    placeholder="Description"
                    className="ff-input text-sm"
                  />
                  {field.type === "enum" && (
                    <input
                      type="text"
                      value={field.options?.join(", ") || ""}
                      onChange={(e) =>
                        updateField(i, {
                          options: e.target.value
                            .split(",")
                            .map((s) => s.trim())
                            .filter(Boolean),
                        })
                      }
                      placeholder="option1, option2, option3"
                      className="ff-input text-sm col-span-3"
                    />
                  )}
                  {field.type === "list" && (
                    <input
                      type="text"
                      value={field.examples?.join(", ") || ""}
                      onChange={(e) =>
                        updateField(i, {
                          examples: e.target.value
                            .split(",")
                            .map((s) => s.trim())
                            .filter(Boolean),
                        })
                      }
                      placeholder="example1, example2 (optional)"
                      className="ff-input text-sm col-span-3"
                    />
                  )}
                </div>
                <button
                  onClick={() => removeField(i)}
                  className="text-ff-text/30 hover:text-ff-red text-sm mt-1"
                >
                  ✕
                </button>
              </div>
            ))}
          </div>

          <button
            onClick={addField}
            className="ff-btn mt-3 text-sm"
          >
            + Add Field
          </button>

          <div className="flex gap-3 mt-8">
            <button onClick={() => setStep(2)} className="ff-btn">
              Back
            </button>
            <button
              onClick={finish}
              disabled={saving || fields.length === 0}
              className="ff-btn-primary disabled:opacity-30"
            >
              {saving ? "Creating..." : "Finish Setup"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
