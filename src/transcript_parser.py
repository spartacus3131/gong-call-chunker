"""
Transcript Parser
=================
Normalizes call transcripts from various sources into a common format.

Common format:
    [{"speaker": "John Smith", "text": "Hello...", "timestamp": "00:01:23"}, ...]
"""

import json
import re
from typing import Any, Dict, List, Optional


def parse_gong_json(data: Dict[str, Any]) -> List[Dict[str, str]]:
    """Parse Gong API transcript response.

    Gong returns transcripts as a list of monologues, each with a speaker
    and a list of sentences with timestamps.
    """
    entries = []
    for monologue in data.get("transcript", []):
        speaker = monologue.get("speakerName", monologue.get("speakerId", "Unknown"))
        sentences = monologue.get("sentences", [])
        for sentence in sentences:
            entries.append({
                "speaker": speaker,
                "text": sentence.get("text", ""),
                "timestamp": _ms_to_timestamp(sentence.get("start", 0)),
            })
    return entries


def parse_raw_text(text: str) -> List[Dict[str, str]]:
    """Parse raw text transcript.

    Supports formats:
    - "Speaker Name: text here"
    - "[00:01:23] Speaker Name: text here"
    - Plain text (no speaker labels) — treated as single speaker
    """
    entries = []

    # Try timestamped format: [00:01:23] Speaker: text
    timestamped = re.findall(
        r'\[(\d{1,2}:\d{2}(?::\d{2})?)\]\s*([^:]+):\s*(.+)',
        text
    )
    if timestamped:
        for ts, speaker, content in timestamped:
            entries.append({
                "speaker": speaker.strip(),
                "text": content.strip(),
                "timestamp": ts,
            })
        return entries

    # Try speaker-labeled format: Speaker Name: text
    labeled = re.findall(r'^([A-Z][a-zA-Z\s]+?):\s*(.+)', text, re.MULTILINE)
    if labeled and len(labeled) > 2:
        for speaker, content in labeled:
            entries.append({
                "speaker": speaker.strip(),
                "text": content.strip(),
                "timestamp": "",
            })
        return entries

    # Fallback: plain text, split by paragraphs
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    for p in paragraphs:
        entries.append({
            "speaker": "Unknown",
            "text": p,
            "timestamp": "",
        })
    return entries


def parse_csv_text(text: str) -> List[Dict[str, str]]:
    """Parse CSV transcript (speaker,timestamp,text)."""
    import csv
    from io import StringIO

    entries = []
    reader = csv.DictReader(StringIO(text))
    for row in reader:
        entries.append({
            "speaker": row.get("speaker", row.get("Speaker", "Unknown")),
            "text": row.get("text", row.get("Text", row.get("content", ""))),
            "timestamp": row.get("timestamp", row.get("Timestamp", "")),
        })
    return entries


def normalize_transcript(
    source: str,
    data: Any,
    format_hint: Optional[str] = None,
) -> List[Dict[str, str]]:
    """Auto-detect format and normalize.

    Args:
        source: "gong_api", "file_upload", or "paste"
        data: Raw data (dict for Gong JSON, str for text/CSV)
        format_hint: Optional hint ("json", "csv", "text")
    """
    if source == "gong_api" or (isinstance(data, dict) and "transcript" in data):
        return parse_gong_json(data)

    if isinstance(data, str):
        if format_hint == "csv" or (data.strip().startswith("speaker,") or data.strip().startswith("Speaker,")):
            return parse_csv_text(data)
        # Try JSON string
        try:
            parsed = json.loads(data)
            if isinstance(parsed, dict) and "transcript" in parsed:
                return parse_gong_json(parsed)
        except (json.JSONDecodeError, TypeError):
            pass
        return parse_raw_text(data)

    raise ValueError(f"Cannot parse transcript: unsupported source={source}")


def entries_to_text(entries: List[Dict[str, str]]) -> str:
    """Convert normalized entries back to readable text for Claude."""
    lines = []
    for e in entries:
        ts = f"[{e['timestamp']}] " if e.get("timestamp") else ""
        lines.append(f"{ts}{e['speaker']}: {e['text']}")
    return "\n".join(lines)


def _ms_to_timestamp(ms: int) -> str:
    """Convert milliseconds to MM:SS or HH:MM:SS."""
    total_seconds = ms // 1000
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"
