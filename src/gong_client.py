"""
Gong API Client
===============
Handles authentication and data fetching from the Gong API.

Docs: https://gong.app.gong.io/settings/api/documentation
"""

import base64
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

GONG_BASE_URL = "https://us-11143.api.gong.io/v2"


class GongClient:
    """Client for the Gong REST API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
    ):
        self.api_key = api_key or os.environ.get("GONG_API_KEY", "")
        self.api_secret = api_secret or os.environ.get("GONG_API_SECRET", "")

        if not self.api_key or not self.api_secret:
            raise ValueError(
                "Gong API credentials required. Set GONG_API_KEY and GONG_API_SECRET."
            )

        # Gong uses Basic Auth with key:secret
        credentials = base64.b64encode(
            f"{self.api_key}:{self.api_secret}".encode()
        ).decode()
        self._headers = {
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/json",
        }

    async def list_calls(
        self,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        cursor: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List calls with optional date filters.

        Returns: {"calls": [...], "cursor": "next_page_token" | null}
        """
        body: Dict[str, Any] = {}
        filter_params: Dict[str, Any] = {}

        if from_date:
            filter_params["fromDateTime"] = from_date.isoformat() + "Z"
        if to_date:
            filter_params["toDateTime"] = to_date.isoformat() + "Z"
        if filter_params:
            body["filter"] = filter_params
        if cursor:
            body["cursor"] = cursor

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{GONG_BASE_URL}/calls",
                headers=self._headers,
                json=body,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()

        return {
            "calls": data.get("calls", []),
            "cursor": data.get("records", {}).get("cursor"),
        }

    async def get_call_transcript(self, call_id: str) -> Dict[str, Any]:
        """Fetch transcript for a specific call.

        Returns Gong transcript format:
        {"transcript": [{"speakerId": ..., "speakerName": ..., "sentences": [...]}]}
        """
        body = {"filter": {"callIds": [call_id]}}

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{GONG_BASE_URL}/calls/transcript",
                headers=self._headers,
                json=body,
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()

        transcripts = data.get("callTranscripts", [])
        if not transcripts:
            raise ValueError(f"No transcript found for call {call_id}")

        return transcripts[0]

    async def get_call_details(self, call_ids: List[str]) -> List[Dict[str, Any]]:
        """Fetch detailed metadata for one or more calls."""
        body = {"filter": {"callIds": call_ids}}

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{GONG_BASE_URL}/calls/extensive",
                headers=self._headers,
                json=body,
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json().get("calls", [])

    async def sync_calls(
        self,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch all calls in a date range, handling pagination.

        Returns list of call objects with metadata.
        """
        all_calls = []
        cursor = None

        while True:
            result = await self.list_calls(from_date, to_date, cursor)
            all_calls.extend(result["calls"])
            cursor = result.get("cursor")
            if not cursor:
                break

        return all_calls
