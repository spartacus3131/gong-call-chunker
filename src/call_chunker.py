"""
Call Chunker
============
Core chunking engine. Takes a normalized transcript + customer schema
and uses Claude to extract structured intelligence.

Uses Claude's tool use (structured output) for guaranteed valid JSON responses.
The tool schema is built dynamically from customer YAML configs.

Pattern adapted from podcast_chunker.py in the LinkedIn Posting Engine.
"""

import json
import os
from typing import Any, Dict, List, Optional

from anthropic import Anthropic

from .schema_loader import load_customer_schema, schema_to_prompt_instructions
from .transcript_parser import entries_to_text, normalize_transcript

CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-20250514")

# Import scorecard skills for tool schema generation
try:
    from api.templates import DEFAULT_SCORECARD_SKILLS, SCORECARD_CATEGORIES
except ImportError:
    # Fallback if running outside the API context
    DEFAULT_SCORECARD_SKILLS = []
    SCORECARD_CATEGORIES = []


class CallChunker:
    """Chunks call transcripts into structured, queryable data."""

    def __init__(self):
        self.anthropic = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    def chunk_call(
        self,
        transcript_entries: List[Dict[str, str]],
        customer_slug: str,
        title: str = "",
        participants: Optional[List[str]] = None,
        scorecard_skills: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """Chunk a call transcript using a customer's extraction schema.

        Uses Claude tool use to get guaranteed structured JSON output.
        The tool schema is built dynamically from the customer's YAML config.

        If scorecard_skills is provided, the tool schema will include a scorecard
        section that scores each skill on a 1-5 scale with evidence quotes.
        """
        schema = load_customer_schema(customer_slug)
        transcript_text = entries_to_text(transcript_entries)

        system_prompt = self._build_system_prompt(schema, scorecard_skills)
        user_prompt = self._build_user_prompt(
            schema=schema,
            transcript=transcript_text,
            title=title,
            participants=participants or [],
        )
        tool = self._build_extraction_tool(schema, scorecard_skills)

        response = self.anthropic.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=8192,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            tools=[tool],
            tool_choice={"type": "tool", "name": "extract_call_intelligence"},
        )

        # With tool_choice forced, the response is guaranteed to be a tool_use block
        for block in response.content:
            if block.type == "tool_use":
                return block.input

        raise ValueError("No tool_use block in response — unexpected model behavior")

    def process_call(
        self,
        raw_transcript: str,
        customer_slug: str,
        title: str = "",
        participants: Optional[List[str]] = None,
        source: str = "paste",
        format_hint: Optional[str] = None,
    ) -> Dict[str, Any]:
        """End-to-end: parse transcript -> chunk -> return structured result."""
        entries = normalize_transcript(source, raw_transcript, format_hint)
        return self.chunk_call(entries, customer_slug, title, participants)

    def _build_extraction_tool(
        self, schema: Dict[str, Any], scorecard_skills: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """Build a Claude tool definition from customer schema.

        This is the key innovation — the tool's input_schema is generated
        dynamically from the YAML config, so Claude is forced to return
        exactly the fields the customer defined.

        If scorecard_skills is provided, adds a `scorecard` property that
        scores each skill 1-5 with evidence.
        """
        extraction = schema.get("extraction_schema", {})

        # Build field properties from customer config
        field_properties = {}
        for field in extraction.get("fields", []):
            field_schema = self._field_to_json_schema(field)
            field_properties[field["name"]] = field_schema

        properties = {
            "fields": {
                "type": "object",
                "description": "Extracted field values from the call",
                "properties": field_properties,
            },
            "chunks": {
                "type": "object",
                "properties": {
                    "topics": {
                        "type": "array",
                        "description": "Major discussion topics (5-8 per call)",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "timestamp_start": {"type": "string"},
                                "timestamp_end": {"type": "string"},
                                "summary": {"type": "string"},
                                "relevance_to_sale": {"type": "string"},
                            },
                            "required": ["title", "summary"],
                        },
                    },
                    "insights": {
                        "type": "array",
                        "description": "Specific customer insights (2-3 per topic)",
                        "items": {
                            "type": "object",
                            "properties": {
                                "parent_topic": {"type": "string"},
                                "insight": {"type": "string"},
                                "sentiment": {
                                    "type": "string",
                                    "enum": ["positive", "neutral", "negative"],
                                },
                                "action_item": {"type": ["string", "null"]},
                            },
                            "required": ["parent_topic", "insight", "sentiment"],
                        },
                    },
                    "quotes": {
                        "type": "array",
                        "description": "Verbatim notable quotes (5-10 per call)",
                        "items": {
                            "type": "object",
                            "properties": {
                                "quote": {"type": "string"},
                                "speaker": {"type": "string"},
                                "context": {"type": "string"},
                                "sentiment": {
                                    "type": "string",
                                    "enum": ["positive", "neutral", "negative"],
                                },
                                "tags": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                            },
                            "required": ["quote", "speaker"],
                        },
                    },
                },
                "required": ["topics", "insights", "quotes"],
            },
            "summary": {
                "type": "object",
                "properties": {
                    "overall_sentiment": {
                        "type": "string",
                        "enum": ["positive", "neutral", "negative"],
                    },
                    "deal_likelihood": {
                        "type": "number",
                        "minimum": 1,
                        "maximum": 10,
                        "description": "1 = very unlikely, 10 = certain to close",
                    },
                    "next_steps": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "follow_up_date": {"type": ["string", "null"]},
                    "summary_text": {
                        "type": "string",
                        "description": "2-3 sentence overview of the call",
                    },
                },
                "required": [
                    "overall_sentiment",
                    "deal_likelihood",
                    "next_steps",
                    "summary_text",
                ],
            },
        }
        required = ["fields", "chunks", "summary"]

        # Add scorecard if skills are provided
        if scorecard_skills:
            skill_items = []
            for skill in scorecard_skills:
                skill_items.append({
                    "type": "object",
                    "properties": {
                        "skill_name": {
                            "type": "string",
                            "const": skill["skill_name"],
                        },
                        "skill_category": {
                            "type": "string",
                            "const": skill["skill_category"],
                        },
                        "present": {
                            "type": "boolean",
                            "description": f"Was this skill demonstrated? {skill['description']}",
                        },
                        "score": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 5,
                            "description": "1=poor, 2=below avg, 3=average, 4=good, 5=excellent. Score 1 if not present.",
                        },
                        "evidence": {
                            "type": ["string", "null"],
                            "description": "Brief quote or explanation from the call supporting this score. Null if skill was not present.",
                        },
                    },
                    "required": ["skill_name", "skill_category", "present", "score", "evidence"],
                })

            properties["scorecard"] = {
                "type": "array",
                "description": (
                    "Score each sales skill based on the call. "
                    "Rate 1-5 (1=poor/absent, 5=excellent). "
                    "Include a brief evidence quote for skills that were present."
                ),
                "items": {
                    "type": "object",
                    "properties": {
                        "skill_name": {"type": "string"},
                        "skill_category": {"type": "string"},
                        "present": {"type": "boolean"},
                        "score": {"type": "integer", "minimum": 1, "maximum": 5},
                        "evidence": {"type": ["string", "null"]},
                    },
                    "required": ["skill_name", "skill_category", "present", "score", "evidence"],
                },
                "minItems": len(scorecard_skills),
                "maxItems": len(scorecard_skills),
            }
            required.append("scorecard")

        return {
            "name": "extract_call_intelligence",
            "description": (
                "Extract structured intelligence from a sales call transcript. "
                "Call this tool with the complete extraction results."
            ),
            "input_schema": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        }

    def _field_to_json_schema(self, field: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a YAML field definition to a JSON Schema property."""
        field_type = field.get("type", "text")
        desc = field.get("description", "")

        if field_type == "enum":
            options = field.get("options", [])
            return {
                "type": ["string", "null"],
                "enum": options + [None],
                "description": desc,
            }
        elif field_type == "text":
            return {
                "type": ["string", "null"],
                "description": desc,
            }
        elif field_type == "integer":
            return {
                "type": ["integer", "null"],
                "description": desc,
            }
        elif field_type == "boolean":
            return {
                "type": ["boolean", "null"],
                "description": desc,
            }
        elif field_type == "list":
            item_schema: Dict[str, Any] = {"type": "string"}
            examples = field.get("examples")
            if examples:
                desc += f" (common values: {', '.join(examples)})"
            return {
                "type": "array",
                "items": item_schema,
                "description": desc,
            }
        else:
            return {"type": ["string", "null"], "description": desc}

    def _build_system_prompt(
        self, schema: Dict[str, Any], scorecard_skills: Optional[List[Dict[str, str]]] = None
    ) -> str:
        customer_name = schema.get("display_name", schema.get("customer", ""))
        industry = schema.get("industry", "")

        prompt = (
            f"You are a sales call analyst for {customer_name} ({industry}). "
            f"Your job is to extract structured intelligence from sales call transcripts.\n\n"
            f"Be precise:\n"
            f"- Extract exact quotes when asked for quotes (don't paraphrase)\n"
            f"- Use null for fields not mentioned in the call\n"
            f"- For list fields, return empty arrays [] if nothing applies\n"
            f"- For enum fields, pick the closest match from the allowed options\n"
            f"- Sentiment should be: positive, neutral, or negative\n"
            f"- Deal likelihood is 1-10 (1 = very unlikely, 10 = certain)\n"
            f"- Timestamps should match the format in the transcript"
        )

        if scorecard_skills:
            prompt += (
                f"\n\n## Sales Skills Scorecard\n"
                f"Score each of the following sales skills on a 1-5 scale:\n"
                f"1 = Not demonstrated / Poor\n"
                f"2 = Below average attempt\n"
                f"3 = Average / Acceptable\n"
                f"4 = Good / Above average\n"
                f"5 = Excellent / Best practice\n\n"
                f"For each skill, indicate whether it was present (true/false), "
                f"assign a score (1 if not present), and provide a brief evidence "
                f"quote or explanation from the call.\n"
            )

        return prompt

    def _build_user_prompt(
        self,
        schema: Dict[str, Any],
        transcript: str,
        title: str,
        participants: List[str],
    ) -> str:
        participants_str = ", ".join(participants) if participants else "Unknown"
        instructions = schema_to_prompt_instructions(schema)

        return (
            f"Analyze this sales call and extract all requested information "
            f"using the extract_call_intelligence tool.\n\n"
            f"**Call:** {title}\n"
            f"**Participants:** {participants_str}\n\n"
            f"{instructions}\n\n"
            f"## Transcript\n\n"
            f"{transcript}"
        )
