"""Small JSON Schema validator fallback used by the local contract tests.

The project only needs a narrow Draft 7 subset for its bundled API contract
schemas.  This module intentionally mirrors the tiny part of the third-party
``jsonschema`` package used by ``tests/contract/test_consignment_contract.py``
so the test suite remains runnable in locked-down environments where pip cannot
download developer dependencies.
"""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import unquote, urlparse


class ValidationError(Exception):
    """Raised when an instance does not match a supported schema rule."""


class RefResolver:
    """Minimal file resolver compatible with the test suite's usage."""

    def __init__(self, base_uri: str = "", referrer: dict | None = None):
        self.base_uri = base_uri
        self.referrer = referrer
        self._cache: dict[str, dict] = {}

    def resolve(self, ref: str) -> dict:
        if ref in self._cache:
            return self._cache[ref]

        parsed_base = urlparse(self.base_uri)
        if parsed_base.scheme != "file":
            raise ValidationError(f"Unsupported $ref base URI: {self.base_uri!r}")

        base_path = Path(unquote(parsed_base.path))
        schema_path = base_path / ref
        with schema_path.open("r", encoding="utf-8") as schema_file:
            schema = json.load(schema_file)

        self._cache[ref] = schema
        return schema


def validate(instance, schema: dict, resolver: RefResolver | None = None):
    """Validate ``instance`` against the supported subset of JSON Schema."""

    _validate(instance, schema, resolver, path="$")


def _validate(instance, schema: dict, resolver: RefResolver | None, path: str):
    if "$ref" in schema:
        if resolver is None:
            raise ValidationError(f"{path}: cannot resolve {schema['$ref']!r} without resolver")
        return _validate(instance, resolver.resolve(schema["$ref"]), resolver, path)

    if "type" in schema and not _matches_type(instance, schema["type"]):
        raise ValidationError(f"{path}: expected type {schema['type']!r}, got {type(instance).__name__}")

    if isinstance(instance, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in instance:
                raise ValidationError(f"{path}: missing required property {key!r}")

        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extras = sorted(set(instance) - set(properties))
            if extras:
                raise ValidationError(f"{path}: unexpected properties {extras!r}")

        for key, value in instance.items():
            if key in properties:
                _validate(value, properties[key], resolver, f"{path}.{key}")

    if isinstance(instance, list) and "items" in schema:
        for index, item in enumerate(instance):
            _validate(item, schema["items"], resolver, f"{path}[{index}]")


def _matches_type(value, expected_type):
    if isinstance(expected_type, list):
        return any(_matches_type(value, item) for item in expected_type)

    type_checks = {
        "object": lambda item: isinstance(item, dict),
        "array": lambda item: isinstance(item, list),
        "string": lambda item: isinstance(item, str),
        "integer": lambda item: isinstance(item, int) and not isinstance(item, bool),
        "boolean": lambda item: isinstance(item, bool),
        "null": lambda item: item is None,
    }

    if expected_type not in type_checks:
        raise ValidationError(f"Unsupported schema type: {expected_type!r}")
    return type_checks[expected_type](value)
