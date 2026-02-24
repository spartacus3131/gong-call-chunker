"use client";

import { useEffect, useState } from "react";
import { api, CustomerConfig } from "@/lib/api";

interface FieldDef {
  name: string;
  type: string;
  description: string;
  options?: string[];
  examples?: string[];
}

export default function SchemasPage() {
  const [schemas, setSchemas] = useState<CustomerConfig[]>([]);
  const [selected, setSelected] = useState<string>("");
  const [schemaData, setSchemaData] = useState<any>(null);
  const [fields, setFields] = useState<FieldDef[]>([]);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);

  // New schema creation
  const [showCreate, setShowCreate] = useState(false);
  const [newSlug, setNewSlug] = useState("");
  const [newDisplayName, setNewDisplayName] = useState("");
  const [newIndustry, setNewIndustry] = useState("");

  useEffect(() => {
    api
      .listSchemas()
      .then((s) => {
        setSchemas(s);
        if (s.length > 0) {
          setSelected(s[0].slug);
          loadSchema(s[0].slug);
        }
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const loadSchema = async (slug: string) => {
    const data = await api.getSchema(slug);
    setSchemaData(data);
    setFields(data?.extraction_schema?.fields || []);
  };

  const handleSelect = (slug: string) => {
    setSelected(slug);
    setEditing(false);
    loadSchema(slug);
  };

  const handleSave = async () => {
    if (!schemaData) return;
    setSaving(true);
    try {
      const updated = {
        ...schemaData,
        extraction_schema: {
          ...schemaData.extraction_schema,
          fields: fields,
        },
      };
      await api.updateSchema(selected, updated);
      setSchemaData(updated);
      setEditing(false);
    } catch (err) {
      alert("Save failed");
    } finally {
      setSaving(false);
    }
  };

  const handleCreateSchema = async () => {
    if (!newSlug || !newDisplayName) return;
    try {
      await api.createSchema({
        customer: newSlug,
        display_name: newDisplayName,
        industry: newIndustry || "general",
        extraction_schema: {
          fields: [
            {
              name: "pain_points",
              type: "list",
              description: "Specific pain points mentioned during the call",
            },
            {
              name: "buying_stage",
              type: "enum",
              options: [
                "early_research",
                "evaluating",
                "decision_ready",
                "negotiating",
              ],
              description: "Where the prospect is in their buying journey",
            },
          ],
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
              description:
                "Specific customer insights within topics (2-3 per topic)",
              extract: ["parent_topic", "insight", "sentiment", "action_item"],
            },
            {
              level: "quotes",
              description: "Verbatim notable quotes (5-10 per call)",
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
      });
      const updatedSchemas = await api.listSchemas();
      setSchemas(updatedSchemas);
      setSelected(newSlug);
      loadSchema(newSlug);
      setShowCreate(false);
      setNewSlug("");
      setNewDisplayName("");
      setNewIndustry("");
    } catch (err: any) {
      alert(err?.message || "Failed to create schema");
    }
  };

  // Field editing helpers
  const addField = () => {
    setFields([
      ...fields,
      { name: "", type: "text", description: "" },
    ]);
  };

  const updateField = (index: number, updates: Partial<FieldDef>) => {
    const updated = [...fields];
    updated[index] = { ...updated[index], ...updates };
    setFields(updated);
  };

  const removeField = (index: number) => {
    setFields(fields.filter((_, i) => i !== index));
  };

  const moveField = (index: number, direction: "up" | "down") => {
    if (
      (direction === "up" && index === 0) ||
      (direction === "down" && index === fields.length - 1)
    )
      return;
    const updated = [...fields];
    const swap = direction === "up" ? index - 1 : index + 1;
    [updated[index], updated[swap]] = [updated[swap], updated[index]];
    setFields(updated);
  };

  if (loading)
    return <p className="text-mako-500 animate-pulse">Loading...</p>;

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-ff-text-bright">
          Extraction Schemas
        </h1>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className={showCreate ? "ff-btn" : "ff-btn-primary"}
        >
          {showCreate ? "Cancel" : "New Schema"}
        </button>
      </div>

      {/* Create Schema Form */}
      {showCreate && (
        <div className="ff-panel-glow p-6 mb-6">
          <h2 className="text-mako-400 font-semibold mb-4">
            Create New Customer Schema
          </h2>
          <div className="grid grid-cols-3 gap-4 mb-4">
            <div>
              <label className="block text-xs text-ff-text/50 mb-1 uppercase tracking-wider">
                Slug (ID)
              </label>
              <input
                value={newSlug}
                onChange={(e) =>
                  setNewSlug(
                    e.target.value.toLowerCase().replace(/[^a-z0-9_-]/g, "_")
                  )
                }
                className="ff-input"
                placeholder="acme_crm"
              />
            </div>
            <div>
              <label className="block text-xs text-ff-text/50 mb-1 uppercase tracking-wider">
                Display Name
              </label>
              <input
                value={newDisplayName}
                onChange={(e) => setNewDisplayName(e.target.value)}
                className="ff-input"
                placeholder="Acme CRM"
              />
            </div>
            <div>
              <label className="block text-xs text-ff-text/50 mb-1 uppercase tracking-wider">
                Industry
              </label>
              <input
                value={newIndustry}
                onChange={(e) => setNewIndustry(e.target.value)}
                className="ff-input"
                placeholder="crm_software"
              />
            </div>
          </div>
          <p className="text-xs text-ff-text/40 mb-4">
            Creates a new schema with starter fields (pain_points, buying_stage).
            You can customize fields after creation.
          </p>
          <button
            onClick={handleCreateSchema}
            disabled={!newSlug || !newDisplayName}
            className="ff-btn-primary disabled:opacity-40"
          >
            Create Schema
          </button>
        </div>
      )}

      <div className="flex gap-6">
        {/* Customer list */}
        <div className="w-48 shrink-0">
          <h2 className="text-xs text-ff-text/40 mb-2 uppercase tracking-wider">
            Customers
          </h2>
          {schemas.map((s) => (
            <button
              key={s.slug}
              onClick={() => handleSelect(s.slug)}
              className={`block w-full text-left px-3 py-2 rounded text-sm mb-1 transition-colors ${
                selected === s.slug
                  ? "bg-mako-500/10 text-mako-400 border border-mako-500/30"
                  : "text-ff-text hover:bg-mako-500/5"
              }`}
            >
              {s.display_name}
            </button>
          ))}
        </div>

        {/* Schema detail / editor */}
        <div className="flex-1">
          {schemaData && (
            <div className="ff-panel p-6">
              <div className="flex justify-between items-center mb-6">
                <div>
                  <h2 className="text-lg font-semibold text-ff-text-bright">
                    {schemaData.display_name}
                  </h2>
                  <p className="text-sm text-ff-text/40">
                    {schemaData.industry}
                  </p>
                </div>
                <div className="flex gap-2">
                  {editing ? (
                    <>
                      <button
                        onClick={() => {
                          setEditing(false);
                          setFields(
                            schemaData?.extraction_schema?.fields || []
                          );
                        }}
                        className="ff-btn"
                      >
                        Cancel
                      </button>
                      <button
                        onClick={handleSave}
                        disabled={saving}
                        className="ff-btn-primary disabled:opacity-40"
                      >
                        {saving ? "Saving..." : "Save Changes"}
                      </button>
                    </>
                  ) : (
                    <button
                      onClick={() => setEditing(true)}
                      className="ff-btn"
                    >
                      Edit Fields
                    </button>
                  )}
                </div>
              </div>

              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xs text-mako-500 uppercase tracking-wider font-semibold">
                  Extraction Fields ({fields.length})
                </h3>
                {editing && (
                  <button
                    onClick={addField}
                    className="text-xs text-mako-400 hover:text-mako-300"
                  >
                    + Add Field
                  </button>
                )}
              </div>

              {editing ? (
                /* Edit mode — form-based field editor */
                <div className="space-y-4">
                  {fields.map((field, i) => (
                    <div
                      key={i}
                      className="border border-ff-border/50 rounded-lg p-4"
                    >
                      <div className="flex gap-3 mb-3">
                        {/* Field name */}
                        <div className="flex-1">
                          <label className="block text-[10px] text-ff-text/40 mb-1 uppercase">
                            Field Name
                          </label>
                          <input
                            value={field.name}
                            onChange={(e) =>
                              updateField(i, {
                                name: e.target.value
                                  .toLowerCase()
                                  .replace(/\s+/g, "_")
                                  .replace(/[^a-z0-9_]/g, ""),
                              })
                            }
                            className="ff-input"
                            placeholder="restaurant_type"
                          />
                        </div>

                        {/* Field type */}
                        <div className="w-36">
                          <label className="block text-[10px] text-ff-text/40 mb-1 uppercase">
                            Type
                          </label>
                          <select
                            value={field.type}
                            onChange={(e) =>
                              updateField(i, { type: e.target.value })
                            }
                            className="ff-select w-full"
                          >
                            <option value="text">Text</option>
                            <option value="enum">
                              Enum (pick from list)
                            </option>
                            <option value="list">
                              List (multiple values)
                            </option>
                            <option value="integer">Number</option>
                            <option value="boolean">Yes/No</option>
                          </select>
                        </div>

                        {/* Actions */}
                        <div className="flex items-end gap-1">
                          <button
                            onClick={() => moveField(i, "up")}
                            disabled={i === 0}
                            className="p-2 text-ff-text/30 hover:text-ff-text disabled:opacity-20 text-xs"
                            title="Move up"
                          >
                            ^
                          </button>
                          <button
                            onClick={() => moveField(i, "down")}
                            disabled={i === fields.length - 1}
                            className="p-2 text-ff-text/30 hover:text-ff-text disabled:opacity-20 text-xs"
                            title="Move down"
                          >
                            v
                          </button>
                          <button
                            onClick={() => removeField(i)}
                            className="p-2 text-ff-red/50 hover:text-ff-red text-xs"
                            title="Remove"
                          >
                            x
                          </button>
                        </div>
                      </div>

                      {/* Description */}
                      <div className="mb-3">
                        <label className="block text-[10px] text-ff-text/40 mb-1 uppercase">
                          Description (tells AI what to look for)
                        </label>
                        <input
                          value={field.description}
                          onChange={(e) =>
                            updateField(i, { description: e.target.value })
                          }
                          className="ff-input"
                          placeholder="What should the AI extract for this field?"
                        />
                      </div>

                      {/* Options (for enum) */}
                      {field.type === "enum" && (
                        <div>
                          <label className="block text-[10px] text-ff-text/40 mb-1 uppercase">
                            Options (comma-separated)
                          </label>
                          <input
                            value={(field.options || []).join(", ")}
                            onChange={(e) =>
                              updateField(i, {
                                options: e.target.value
                                  .split(",")
                                  .map((s) => s.trim())
                                  .filter(Boolean),
                              })
                            }
                            className="ff-input"
                            placeholder="fast_casual, fine_dining, qsr, bar_nightclub"
                          />
                        </div>
                      )}

                      {/* Examples (for list) */}
                      {field.type === "list" && (
                        <div>
                          <label className="block text-[10px] text-ff-text/40 mb-1 uppercase">
                            Example values (comma-separated, helps the AI)
                          </label>
                          <input
                            value={(field.examples || []).join(", ")}
                            onChange={(e) =>
                              updateField(i, {
                                examples: e.target.value
                                  .split(",")
                                  .map((s) => s.trim())
                                  .filter(Boolean),
                              })
                            }
                            className="ff-input"
                            placeholder="scheduling, inventory, checkout_speed"
                          />
                        </div>
                      )}
                    </div>
                  ))}

                  <button
                    onClick={addField}
                    className="w-full border border-dashed border-ff-border/50 rounded-lg p-3 text-sm text-ff-text/40 hover:text-mako-400 hover:border-mako-500/30 transition-colors"
                  >
                    + Add another field
                  </button>
                </div>
              ) : (
                /* View mode */
                <div className="grid grid-cols-2 gap-3">
                  {fields.map((field) => (
                    <div
                      key={field.name}
                      className="border border-ff-border/30 rounded p-3 text-sm"
                    >
                      <div className="flex justify-between">
                        <span className="font-medium text-ff-text-bright">
                          {field.name.replace(/_/g, " ")}
                        </span>
                        <span className="text-[10px] px-1.5 py-0.5 bg-ff-border/30 text-ff-text/50 rounded uppercase">
                          {field.type}
                        </span>
                      </div>
                      {field.description && (
                        <p className="text-ff-text/40 text-xs mt-1">
                          {field.description}
                        </p>
                      )}
                      {field.options && (
                        <div className="flex flex-wrap gap-1 mt-2">
                          {field.options.map((opt) => (
                            <span
                              key={opt}
                              className="px-1.5 py-0.5 bg-mako-500/10 text-mako-400 border border-mako-500/20 rounded text-xs"
                            >
                              {opt}
                            </span>
                          ))}
                        </div>
                      )}
                      {field.examples && (
                        <div className="flex flex-wrap gap-1 mt-2">
                          {field.examples.map((ex) => (
                            <span
                              key={ex}
                              className="px-1.5 py-0.5 bg-ff-blue/10 text-ff-blue/70 border border-ff-blue/20 rounded text-xs"
                            >
                              {ex}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
