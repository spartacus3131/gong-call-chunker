"""Tests for schema loader, transcript parser, and chunker prompt construction."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from src.schema_loader import (
    load_customer_schema,
    load_default_schema,
    schema_to_prompt_instructions,
    list_customers,
)
from src.transcript_parser import (
    parse_raw_text,
    parse_gong_json,
    entries_to_text,
    normalize_transcript,
)


# --- Schema Loader Tests ---


def test_load_default_schema():
    schema = load_default_schema()
    assert schema["customer"] == "default"
    assert "extraction_schema" in schema
    fields = schema["extraction_schema"]["fields"]
    assert len(fields) > 0
    field_names = [f["name"] for f in fields]
    assert "pain_points" in field_names


def test_load_touchbistro_schema():
    schema = load_customer_schema("touchbistro")
    assert schema["customer"] == "touchbistro"
    assert schema["display_name"] == "TouchBistro POS"
    fields = schema["extraction_schema"]["fields"]
    field_names = [f["name"] for f in fields]
    # Customer-specific fields
    assert "restaurant_size" in field_names
    assert "restaurant_type" in field_names
    assert "current_pos" in field_names
    # Inherited from default (not in touchbistro.yaml)
    # touchbistro defines its own call_type so it should be present
    assert "call_type" in field_names


def test_load_nonexistent_customer():
    with pytest.raises(FileNotFoundError):
        load_customer_schema("nonexistent_customer_xyz")


def test_schema_to_prompt_instructions():
    schema = load_customer_schema("touchbistro")
    instructions = schema_to_prompt_instructions(schema)
    assert "restaurant_size" in instructions
    assert "restaurant_type" in instructions
    assert "pain_points" in instructions
    assert "Topics" in instructions
    assert "Insights" in instructions
    assert "Quotes" in instructions


def test_list_customers():
    customers = list_customers()
    assert len(customers) >= 1
    slugs = [c["slug"] for c in customers]
    assert "touchbistro" in slugs


# --- Transcript Parser Tests ---


def test_parse_raw_text_speaker_labeled():
    text = """Sarah Chen: Hi, how are you today?
Mario Rossi: I'm good, thanks for calling.
Sarah Chen: Great, let me ask about your POS system."""
    entries = parse_raw_text(text)
    assert len(entries) == 3
    assert entries[0]["speaker"] == "Sarah Chen"
    assert entries[1]["speaker"] == "Mario Rossi"


def test_parse_raw_text_timestamped():
    text = """[00:00] Sarah Chen: Hi, how are you?
[00:15] Mario Rossi: Doing well.
[00:30] Sarah Chen: Tell me about your restaurant."""
    entries = parse_raw_text(text)
    assert len(entries) == 3
    assert entries[0]["timestamp"] == "00:00"
    assert entries[1]["speaker"] == "Mario Rossi"


def test_parse_raw_text_plain():
    text = """This is just a paragraph of text.

And another paragraph here."""
    entries = parse_raw_text(text)
    assert len(entries) == 2
    assert entries[0]["speaker"] == "Unknown"


def test_parse_gong_json():
    data = {
        "transcript": [
            {
                "speakerName": "Sales Rep",
                "sentences": [
                    {"text": "Hello, welcome.", "start": 0},
                    {"text": "How can I help?", "start": 5000},
                ],
            },
            {
                "speakerName": "Customer",
                "sentences": [
                    {"text": "I need a new POS.", "start": 10000},
                ],
            },
        ]
    }
    entries = parse_gong_json(data)
    assert len(entries) == 3
    assert entries[0]["speaker"] == "Sales Rep"
    assert entries[0]["timestamp"] == "00:00"
    assert entries[2]["speaker"] == "Customer"
    assert entries[2]["timestamp"] == "00:10"


def test_entries_to_text():
    entries = [
        {"speaker": "Alice", "text": "Hello", "timestamp": "00:00"},
        {"speaker": "Bob", "text": "Hi there", "timestamp": "00:05"},
    ]
    text = entries_to_text(entries)
    assert "[00:00] Alice: Hello" in text
    assert "[00:05] Bob: Hi there" in text


def test_normalize_transcript_auto_detect_text():
    text = "Sarah: Hello\nMario: Hi there\nSarah: How are you?"
    entries = normalize_transcript("paste", text)
    assert len(entries) == 3


def test_normalize_transcript_auto_detect_gong():
    import json

    data = {
        "transcript": [
            {
                "speakerName": "Rep",
                "sentences": [{"text": "Test", "start": 0}],
            }
        ]
    }
    entries = normalize_transcript("paste", json.dumps(data))
    assert len(entries) == 1
    assert entries[0]["speaker"] == "Rep"


# --- Tool Schema Generation Tests ---


def test_build_extraction_tool_has_customer_fields():
    """Tool schema should include customer-specific fields from YAML."""
    from src.call_chunker import CallChunker

    chunker = CallChunker.__new__(CallChunker)  # skip __init__ (no API key needed)
    schema = load_customer_schema("touchbistro")
    tool = chunker._build_extraction_tool(schema)

    assert tool["name"] == "extract_call_intelligence"
    input_schema = tool["input_schema"]
    assert "fields" in input_schema["properties"]
    assert "chunks" in input_schema["properties"]
    assert "summary" in input_schema["properties"]

    # Check customer-specific fields are in the tool schema
    field_props = input_schema["properties"]["fields"]["properties"]
    assert "restaurant_size" in field_props
    assert "restaurant_type" in field_props
    assert "pain_points" in field_props
    assert "current_pos" in field_props

    # Check enum field has options
    assert field_props["restaurant_size"]["enum"] is not None
    assert "fine_dining" in field_props["restaurant_type"]["enum"]

    # Check list field
    assert field_props["pain_points"]["type"] == "array"

    # Check chunks structure
    chunks = input_schema["properties"]["chunks"]["properties"]
    assert "topics" in chunks
    assert "insights" in chunks
    assert "quotes" in chunks

    # Check summary has required fields
    summary_required = input_schema["properties"]["summary"]["required"]
    assert "overall_sentiment" in summary_required
    assert "deal_likelihood" in summary_required


def test_field_to_json_schema_types():
    """Each YAML field type maps to correct JSON Schema."""
    from src.call_chunker import CallChunker

    chunker = CallChunker.__new__(CallChunker)

    # enum
    result = chunker._field_to_json_schema({"name": "x", "type": "enum", "options": ["a", "b"]})
    assert None in result["enum"]
    assert "a" in result["enum"]

    # text
    result = chunker._field_to_json_schema({"name": "x", "type": "text"})
    assert "string" in result["type"]

    # integer
    result = chunker._field_to_json_schema({"name": "x", "type": "integer"})
    assert "integer" in result["type"]

    # boolean
    result = chunker._field_to_json_schema({"name": "x", "type": "boolean"})
    assert "boolean" in result["type"]

    # list
    result = chunker._field_to_json_schema({"name": "x", "type": "list"})
    assert result["type"] == "array"
    assert result["items"]["type"] == "string"
