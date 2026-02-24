"""
Schema Loader
=============
Loads and merges customer YAML configs with the default base schema.
"""

import copy
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

CONFIG_DIR = Path(__file__).parent.parent / "config"
CUSTOMERS_DIR = CONFIG_DIR / "customers"


def load_yaml(path: Path) -> Dict[str, Any]:
    with open(path) as f:
        return yaml.safe_load(f)


def load_default_schema() -> Dict[str, Any]:
    return load_yaml(CONFIG_DIR / "default.yaml")


def load_customer_schema(slug: str) -> Dict[str, Any]:
    """Load a customer schema, merged with defaults.

    Customer fields override defaults with the same name.
    Customer-only fields are appended.
    """
    default = load_default_schema()
    customer_path = CUSTOMERS_DIR / f"{slug}.yaml"

    if not customer_path.exists():
        raise FileNotFoundError(f"No config found for customer: {slug}")

    customer = load_yaml(customer_path)
    return _merge_schemas(default, customer)


def _merge_schemas(default: Dict, customer: Dict) -> Dict:
    """Merge customer schema on top of default."""
    merged = copy.deepcopy(customer)
    schema = merged.get("extraction_schema", {})
    default_schema = default.get("extraction_schema", {})

    # Merge fields: customer fields win, default fields fill gaps
    customer_field_names = {f["name"] for f in schema.get("fields", [])}
    for default_field in default_schema.get("fields", []):
        if default_field["name"] not in customer_field_names:
            schema.setdefault("fields", []).append(default_field)

    # Use customer chunk_levels if provided, else default
    if "chunk_levels" not in schema:
        schema["chunk_levels"] = default_schema.get("chunk_levels", [])

    # Merge call_summary
    if "call_summary" not in schema:
        schema["call_summary"] = default_schema.get("call_summary", [])

    merged["extraction_schema"] = schema
    return merged


def list_customers() -> List[Dict[str, str]]:
    """List all available customer configs."""
    customers = []
    for path in sorted(CUSTOMERS_DIR.glob("*.yaml")):
        data = load_yaml(path)
        customers.append({
            "slug": data.get("customer", path.stem),
            "display_name": data.get("display_name", path.stem),
            "industry": data.get("industry", ""),
            "config_path": str(path),
        })
    return customers


def schema_to_prompt_instructions(schema: Dict[str, Any]) -> str:
    """Convert a customer schema to Claude prompt instructions.

    This is the key function — it turns YAML config into the extraction
    prompt that tells Claude exactly what to pull from a call transcript.
    """
    extraction = schema.get("extraction_schema", {})
    lines = []

    # Field extraction instructions
    lines.append("## Fields to Extract\n")
    lines.append("For each field, extract the value from the call transcript. "
                 "If not mentioned, use null.\n")

    for field in extraction.get("fields", []):
        desc = field.get("description", "")
        field_line = f"- **{field['name']}** ({field['type']}): {desc}"
        if field.get("options"):
            field_line += f"\n  Options: {', '.join(field['options'])}"
        if field.get("examples"):
            field_line += f"\n  Examples: {', '.join(field['examples'])}"
        lines.append(field_line)

    # Chunk level instructions
    lines.append("\n## Chunking Levels\n")
    for level in extraction.get("chunk_levels", []):
        lines.append(f"### {level['level'].title()}")
        lines.append(f"{level['description']}")
        lines.append(f"Extract for each: {', '.join(level['extract'])}\n")

    # Call summary instructions
    lines.append("## Call Summary\n")
    lines.append("Provide these call-level assessments:")
    for item in extraction.get("call_summary", []):
        lines.append(f"- {item}")

    return "\n".join(lines)


def save_customer_schema(slug: str, schema_data: Dict[str, Any]) -> Path:
    """Save a customer schema to YAML file."""
    path = CUSTOMERS_DIR / f"{slug}.yaml"
    CUSTOMERS_DIR.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        yaml.dump(schema_data, f, default_flow_style=False, sort_keys=False)
    return path
