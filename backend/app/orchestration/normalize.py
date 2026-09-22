"""Coerce common AI JSON shape mismatches before Pydantic validation."""

from __future__ import annotations

from typing import Any, Union, get_args, get_origin

from pydantic import BaseModel


def coerce_to_str(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        return ", ".join(coerce_to_str(item) for item in value)
    if isinstance(value, dict):
        return "; ".join(f"{key}: {coerce_to_str(val)}" for key, val in value.items())
    return str(value)


def _unwrap_optional(annotation: Any) -> Any:
    origin = get_origin(annotation)
    if origin is Union:
        args = [arg for arg in get_args(annotation) if arg is not type(None)]
        if len(args) == 1:
            return args[0]
    return annotation


def normalize_for_model(data: Any, model: type[BaseModel]) -> Any:
    if not isinstance(data, dict):
        return data

    normalized: dict[str, Any] = {}
    for name, field in model.model_fields.items():
        if name not in data:
            continue
        value = normalize_value(data[name], _unwrap_optional(field.annotation))
        if isinstance(value, list):
            for constraint in field.metadata:
                max_length = getattr(constraint, "max_length", None)
                if isinstance(max_length, int):
                    value = value[:max_length]
                    break
        normalized[name] = value
    return normalized


def normalize_value(value: Any, annotation: Any) -> Any:
    annotation = _unwrap_optional(annotation)
    origin = get_origin(annotation)

    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        if isinstance(value, dict):
            return normalize_for_model(value, annotation)
        return value

    if origin is list:
        inner = get_args(annotation)[0] if get_args(annotation) else Any
        inner = _unwrap_optional(inner)
        if not isinstance(value, list):
            value = [value] if value is not None else []

        if inner is str:
            return [coerce_to_str(item) for item in value]

        if isinstance(inner, type) and issubclass(inner, BaseModel):
            return [
                normalize_for_model(item, inner) if isinstance(item, dict) else item
                for item in value
            ]

        inner_origin = get_origin(inner)
        if inner_origin is dict:
            dict_args = get_args(inner)
            value_type = dict_args[1] if len(dict_args) > 1 else Any
            if value_type is str:
                return [
                    {str(key): coerce_to_str(val) for key, val in item.items()}
                    if isinstance(item, dict)
                    else item
                    for item in value
                ]

        return [normalize_value(item, inner) for item in value]

    if origin is dict:
        dict_args = get_args(annotation)
        value_type = dict_args[1] if len(dict_args) > 1 else Any
        if not isinstance(value, dict):
            return value
        if value_type is str:
            return {str(key): coerce_to_str(val) for key, val in value.items()}
        return value

    if annotation is str and not isinstance(value, str):
        return coerce_to_str(value)

    return value


def normalize_json_payload(raw: dict[str, Any], model: type[BaseModel]) -> dict[str, Any]:
    normalized = normalize_for_model(raw, model)
    if not isinstance(normalized, dict):
        raise TypeError("Normalized AI payload must be a JSON object")
    return normalized
