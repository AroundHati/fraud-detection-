"""
Response parsing utilities for LLM outputs.

Provides helpers to extract structured data from free-text LLM
completions, with graceful degradation when parsing fails.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional, Type, TypeVar

from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class ParseError(Exception):
    """Raised when an LLM response cannot be parsed into the expected structure."""


class ResponseParser:
    """Static helpers for parsing and validating LLM responses."""

    # ------------------------------------------------------------------
    # JSON extraction
    # ------------------------------------------------------------------

    @staticmethod
    def parse_json(raw: str) -> dict[str, Any]:
        """Extract a JSON object from a raw LLM response string.

        Handles common LLM quirks such as markdown code fences and
        trailing commas.

        Args:
            raw: The raw text returned by the LLM.

        Returns:
            A dictionary parsed from the JSON content.

        Raises:
            ParseError: If no valid JSON can be extracted.
        """
        logger.debug("parse_json() — input length=%d", len(raw))

        if not raw or not raw.strip():
            raise ParseError("Cannot parse empty or whitespace-only string")

        cleaned = raw.strip()

        # Step 1: Strip markdown code fences (```json ... ``` or ``` ... ```)
        import re

        fence_pattern = r"^```(?:json)?\s*\n?(.*?)\n?\s*```$"
        fence_match = re.match(fence_pattern, cleaned, re.DOTALL)
        if fence_match:
            cleaned = fence_match.group(1).strip()

        # Step 2: Direct parse attempt
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # Step 3: Find the first '{' and last '}'
        first_brace = cleaned.find("{")
        last_brace = cleaned.rfind("}")
        if first_brace != -1 and last_brace > first_brace:
            candidate = cleaned[first_brace : last_brace + 1]
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass

        # Step 4: Fix trailing commas (common LLM mistake)
        fixed = re.sub(r",\s*([}\]])", r"\1", candidate if first_brace != -1 else cleaned)
        try:
            return json.loads(fixed)
        except json.JSONDecodeError:
            pass

        # Step 5: Nothing worked
        raise ParseError(
            f"Failed to extract valid JSON from response "
            f"(length={len(raw)}, preview={raw[:200]!r})"
        )

    # ------------------------------------------------------------------
    # Typed validation
    # ------------------------------------------------------------------

    @staticmethod
    def validate_response(
        data: dict[str, Any],
        model: Type[T],
    ) -> T:
        """Validate a dictionary against a Pydantic model.

        Args:
            data: Parsed dictionary from an LLM response.
            model: The target Pydantic model class.

        Returns:
            An instance of *model* populated with *data*.

        Raises:
            ParseError: If validation fails.
        """
        logger.debug("validate_response() — target model=%s", model.__name__)

        try:
            instance = model(**data)
        except ValidationError as exc:
            error_details = "; ".join(
                f"{'.'.join(str(loc) for loc in e['loc'])}: {e['msg']}"
                for e in exc.errors()
            )
            raise ParseError(
                f"Validation failed for {model.__name__}: {error_details}"
            ) from exc

        return instance

    # ------------------------------------------------------------------
    # Safe parse (combined)
    # ------------------------------------------------------------------

    @staticmethod
    def safe_parse(
        raw: str,
        model: Optional[Type[T]] = None,
    ) -> dict[str, Any] | T:
        """Attempt to parse an LLM response, returning partial results on failure.

        This is the recommended entry point for agent code that must
        never crash due to a malformed LLM response.

        Args:
            raw: The raw LLM response text.
            model: Optional Pydantic model to validate against.

        Returns:
            Either a validated model instance (if *model* is given) or
            a raw dictionary.  On failure, returns an empty dict so that
            downstream agents can continue with degraded data.
        """
        logger.debug("safe_parse() — model=%s", model.__name__ if model else None)

        try:
            data = ResponseParser.parse_json(raw)
        except ParseError:
            logger.warning(
                "safe_parse() — JSON extraction failed, returning empty dict"
            )
            return {}

        if model is None:
            return data

        try:
            return ResponseParser.validate_response(data, model)
        except ParseError as exc:
            logger.warning(
                "safe_parse() — validation failed for %s, returning raw dict: %s",
                model.__name__,
                exc,
            )
            return data
