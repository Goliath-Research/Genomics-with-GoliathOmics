"""Teaching helpers for Module 8: the configuration overlay, with provenance.

``deep_merge`` is a teaching copy of GoliathOmics ``methyl_utils.action_config_resolver.deep_merge``:
nested dicts merge, lists and scalars replace, and an overlay value of ``None`` (JSON null) deletes
the key. ``resolve`` applies the documented layer order and records which layer set each leaf:

    site -> pipeline profile -> procedure/program -> instance/step   (later wins)
    then analyte fill-missing (never overrides a value that is already set)

A worker ``stepOverride`` still wins over the baked slice at run time. tests/test_module_08.py
compares this copy with the official resolver from the pinned checkout.
"""

from __future__ import annotations

import copy
from typing import Any, Mapping

LAYERS = ("site", "profile", "procedure", "instance")


def deep_merge(base: dict[str, Any], overlay: Mapping[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(base)
    for key, val in overlay.items():
        if val is None:
            out.pop(key, None)
        elif isinstance(val, dict) and isinstance(out.get(key), dict):
            out[key] = deep_merge(dict(out[key]), val)
        else:
            out[key] = copy.deepcopy(val)
    return out


def deep_setdefault(target: dict[str, Any], patch: Mapping[str, Any]) -> None:
    for key, val in patch.items():
        if key not in target:
            target[key] = copy.deepcopy(val)
        elif isinstance(val, dict) and isinstance(target[key], dict):
            deep_setdefault(target[key], val)


def _leaves(d: Mapping[str, Any], prefix: str = "") -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in d.items():
        path = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict) and v:
            out.update(_leaves(v, path))
        else:
            out[path] = v
    return out


def resolve(layers: Mapping[str, Mapping[str, Any] | None], analyte_patch: Mapping[str, Any] | None = None):
    """Return (merged, provenance) where provenance maps each leaf path to the layer that set it."""
    merged: dict[str, Any] = {}
    provenance: dict[str, str] = {}
    for name in LAYERS:
        overlay = layers.get(name) or {}
        before = _leaves(merged)
        merged = deep_merge(merged, overlay)
        after = _leaves(merged)
        for path, value in after.items():
            if path not in before or before[path] != value or path in _leaves(overlay):
                provenance[path] = name
        for path in set(before) - set(after):
            provenance.pop(path, None)
    if analyte_patch:
        before = _leaves(merged)
        deep_setdefault(merged, analyte_patch)
        for path in set(_leaves(merged)) - set(before):
            provenance[path] = "analyte (fill-missing)"
    return merged, provenance
