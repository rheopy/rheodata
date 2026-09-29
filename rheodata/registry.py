"""Discovery and validation of the rheodata dataset registry.

Datasets live in ``rheodata/datasets/<dataset-id>/`` with two files:

- ``dataset.yaml`` — metadata (schema documented in :func:`validate_dataset`)
- ``data.csv``     — tidy data; the physical column names are given by the
  ``columns:`` mapping in the yaml (csv headers may carry units, e.g.
  ``"Shear rate / 1/s"``).

Discovery uses :mod:`importlib.resources`, so the registry works from an
installed wheel with no repo-relative paths and no network access.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

try:  # Python >= 3.9
    from importlib.resources import files as _res_files
except ImportError:  # pragma: no cover
    _res_files = None  # type: ignore[assignment]

DOI_RE = re.compile(r"^10\.\S+/\S+$")

#: Allowed values for ``measurement.type`` in dataset.yaml.
EXPERIMENT_TYPES = frozenset({
    "flow_curve",
    "amplitude_sweep",
    "frequency_sweep",
    "shear_startup",
    "creep",
    "stress_relaxation",
})

_REQUIRED_TOP = (
    "id", "title", "description", "material", "source", "provenance",
    "measurement", "samples", "columns", "tags",
)


class DatasetError(Exception):
    """Raised when a dataset fails registry validation."""


def _default_root() -> Path | None:
    """Locate the packaged ``rheodata/datasets`` directory, or None."""
    if _res_files is None:
        return None
    try:
        root = _res_files("rheodata.datasets")
    except (ImportError, ModuleNotFoundError, TypeError):
        return None
    return Path(str(root)) if root.is_dir() else None


def _require(mapping: dict, key: str, where: str, ds: str) -> Any:
    if not isinstance(mapping, dict) or key not in mapping:
        raise DatasetError(f"dataset '{ds}': {where} missing required key '{key}'")
    return mapping[key]


def validate_dataset(d: Path | str) -> dict:
    """Validate one dataset directory; return its parsed ``dataset.yaml``.

    Raises :class:`DatasetError` naming the dataset on any failure.
    """
    d = Path(d)
    ds = d.name
    yaml_path = d / "dataset.yaml"
    csv_path = d / "data.csv"
    if not yaml_path.is_file():
        raise DatasetError(f"dataset '{ds}': missing dataset.yaml in {d}")
    if not csv_path.is_file():
        raise DatasetError(f"dataset '{ds}': missing data.csv in {d}")

    meta = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    if not isinstance(meta, dict):
        raise DatasetError(f"dataset '{ds}': dataset.yaml must contain a mapping")

    for key in _REQUIRED_TOP:
        _require(meta, key, "dataset.yaml", ds)
    if meta["id"] != ds:
        raise DatasetError(
            f"dataset '{ds}': dataset.yaml id '{meta['id']}' does not match directory name"
        )

    material = meta["material"]
    _require(material, "name", "material", ds)
    _require(material, "kind", "material", ds)

    source = meta["source"]
    paper = _require(source, "paper", "source", ds)
    for key in ("title", "authors", "journal", "year", "doi"):
        _require(paper, key, "source.paper", ds)
    _require(source, "figure", "source", ds)

    provenance = meta["provenance"]
    origin = _require(provenance, "origin", "provenance", ds)
    doi = paper["doi"]
    if origin == "literature" or doi is not None:
        # Literature data must carry a valid DOI. Unpublished community (or
        # synthetic test) data may carry doi: null — but a DOI that is
        # present must be valid, never fabricated.
        if not DOI_RE.match(str(doi).strip()):
            raise DatasetError(
                f"dataset '{ds}': source.paper.doi '{doi}' is not a valid DOI"
            )

    measurement = meta["measurement"]
    exp_type = _require(measurement, "type", "measurement", ds)
    if exp_type not in EXPERIMENT_TYPES:
        raise DatasetError(
            f"dataset '{ds}': measurement.type '{exp_type}' not in "
            f"{sorted(EXPERIMENT_TYPES)}"
        )
    _require(measurement, "geometry", "measurement", ds)
    _require(measurement, "temperature_C", "measurement", ds)

    samples = meta["samples"]
    if not isinstance(samples, list) or not samples:
        raise DatasetError(f"dataset '{ds}': 'samples' must be a non-empty list")
    for s in samples:
        _require(s, "id", "samples entry", ds)
        _require(s, "label", "samples entry", ds)
    sample_ids = [s["id"] for s in samples]
    if len(set(sample_ids)) != len(sample_ids):
        raise DatasetError(f"dataset '{ds}': duplicate sample ids in 'samples'")

    columns = meta["columns"]
    x_col = _require(columns, "x", "columns", ds)
    y_col = _require(columns, "y", "columns", ds)
    sample_col = _require(columns, "sample", "columns", ds)

    # ---- data.csv checks ----
    try:
        df = pd.read_csv(csv_path)
    except Exception as exc:
        raise DatasetError(f"dataset '{ds}': cannot read data.csv ({exc})") from exc
    for col in (x_col, y_col, sample_col):
        if col not in df.columns:
            raise DatasetError(
                f"dataset '{ds}': data.csv missing column '{col}' "
                f"(yaml columns: x={x_col!r}, y={y_col!r}, sample={sample_col!r})"
            )
    if df[x_col].isna().any():
        raise DatasetError(f"dataset '{ds}': NaN found in x column '{x_col}'")
    if df[y_col].isna().any():
        raise DatasetError(f"dataset '{ds}': NaN found in y column '{y_col}'")
    x_num = pd.to_numeric(df[x_col], errors="coerce")
    if x_num.isna().any():
        raise DatasetError(f"dataset '{ds}': x column '{x_col}' must be numeric")
    if pd.to_numeric(df[y_col], errors="coerce").isna().any():
        raise DatasetError(f"dataset '{ds}': y column '{y_col}' must be numeric")

    for sid, group in df.groupby(sample_col, sort=False):
        if not group[x_col].is_monotonic_increasing:
            raise DatasetError(
                f"dataset '{ds}': x column '{x_col}' not sorted ascending "
                f"for sample '{sid}'"
            )
    csv_ids = set(df[sample_col].unique())
    if csv_ids != set(sample_ids):
        raise DatasetError(
            f"dataset '{ds}': data.csv sample ids {sorted(map(str, csv_ids))} "
            f"do not match dataset.yaml samples {sample_ids}"
        )

    return meta


def load_registry(root: Path | str | None = None) -> dict:
    """Load and validate every dataset under *root*.

    Defaults to the packaged ``rheodata/datasets`` directory discovered via
    :mod:`importlib.resources`. Returns ``{dataset_id: {"meta": ..., "path": ...}}``.
    Raises :class:`DatasetError` naming the offending dataset on failure.
    """
    if root is None:
        root = _default_root()
    registry: dict = {}
    if root is None:
        return registry
    root = Path(root)
    if not root.is_dir():
        return registry
    for d in sorted(root.iterdir()):
        if not d.is_dir() or d.name.startswith((".", "_")):
            continue
        meta = validate_dataset(d)
        ds_id = meta["id"]
        if ds_id in registry:
            raise DatasetError(f"duplicate dataset id '{ds_id}'")
        registry[ds_id] = {"meta": meta, "path": d}
    return registry


#: The import-time registry of packaged datasets (validated on import).
REGISTRY = load_registry()
