"use client";

import { useEffect, useState } from "react";
import { api, CustomerConfig } from "@/lib/api";

export default function SchemasPage() {
  const [schemas, setSchemas] = useState<CustomerConfig[]>([]);
  const [selected, setSelected] = useState<string>("");
  const [schemaData, setSchemaData] = useState<any>(null);
  const [editing, setEditing] = useState(false);
  const [editJson, setEditJson] = useState("");
  const [loading, setLoading] = useState(true);

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
    setEditJson(JSON.stringify(data, null, 2));
  };

  const handleSelect = (slug: string) => {
    setSelected(slug);
    setEditing(false);
    loadSchema(slug);
  };

  const handleSave = async () => {
    try {
      const parsed = JSON.parse(editJson);
      await api.updateSchema(selected, parsed);
      setSchemaData(parsed);
      setEditing(false);
    } catch (err) {
      alert("Invalid JSON or save failed");
    }
  };

  if (loading) return <p className="text-gray-500">Loading...</p>;

  const fields = schemaData?.extraction_schema?.fields || [];

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Extraction Schemas</h1>

      <div className="flex gap-6">
        {/* Customer list */}
        <div className="w-48 shrink-0">
          <h2 className="text-sm font-semibold text-gray-500 mb-2">
            Customers
          </h2>
          {schemas.map((s) => (
            <button
              key={s.slug}
              onClick={() => handleSelect(s.slug)}
              className={`block w-full text-left px-3 py-2 rounded text-sm mb-1 ${
                selected === s.slug
                  ? "bg-blue-100 text-blue-700"
                  : "hover:bg-gray-100"
              }`}
            >
              {s.display_name}
            </button>
          ))}
        </div>

        {/* Schema detail */}
        <div className="flex-1">
          {schemaData && !editing && (
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex justify-between items-center mb-4">
                <div>
                  <h2 className="text-lg font-semibold">
                    {schemaData.display_name}
                  </h2>
                  <p className="text-sm text-gray-500">
                    {schemaData.industry}
                  </p>
                </div>
                <button
                  onClick={() => setEditing(true)}
                  className="px-3 py-1.5 bg-gray-100 text-gray-700 rounded text-sm hover:bg-gray-200"
                >
                  Edit JSON
                </button>
              </div>

              <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
                Extraction Fields ({fields.length})
              </h3>
              <div className="grid grid-cols-2 gap-3">
                {fields.map((field: any) => (
                  <div
                    key={field.name}
                    className="border rounded p-3 text-sm"
                  >
                    <div className="flex justify-between">
                      <span className="font-medium">
                        {field.name.replace(/_/g, " ")}
                      </span>
                      <span className="text-xs px-1.5 py-0.5 bg-gray-100 rounded">
                        {field.type}
                      </span>
                    </div>
                    {field.description && (
                      <p className="text-gray-500 text-xs mt-1">
                        {field.description}
                      </p>
                    )}
                    {field.options && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {field.options.map((opt: string) => (
                          <span
                            key={opt}
                            className="px-1.5 py-0.5 bg-blue-50 text-blue-600 rounded text-xs"
                          >
                            {opt}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {editing && (
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-semibold">
                  Edit: {schemaData?.display_name}
                </h2>
                <div className="flex gap-2">
                  <button
                    onClick={() => setEditing(false)}
                    className="px-3 py-1.5 text-gray-600 text-sm"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSave}
                    className="px-3 py-1.5 bg-green-600 text-white rounded text-sm"
                  >
                    Save
                  </button>
                </div>
              </div>
              <textarea
                value={editJson}
                onChange={(e) => setEditJson(e.target.value)}
                className="w-full h-[600px] font-mono text-sm border rounded p-3"
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
