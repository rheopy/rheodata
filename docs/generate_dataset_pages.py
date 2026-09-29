#!/usr/bin/env python3
"""Generate one documentation page per dataset in the rheodata registry.

Run BEFORE sphinx-build. It is invoked automatically from the top of
``docs/conf.py`` so Read the Docs builds need no extra steps; it can also be
run by hand::

    python docs/generate_dataset_pages.py

API contract (written against the rheodata public API as specified):

* ``rheodata.list()``  -> iterable of dataset ids (str), or of dicts with an
  ``"id"`` key
* ``rheodata.info(id)`` -> the ``dataset.yaml`` metadata as a (possibly
  nested) dict
* ``rheodata.load(id)`` -> pandas DataFrame of the tidy data
* ``rheodata.plot(id)`` -> a ``matplotlib.figure.Figure`` of the dataset

Outputs (idempotent — every file is rewritten from scratch on each run):

* ``docs/datasets/<id>.md``  — one page per dataset
* ``docs/datasets/index.md``  — catalog table linking every dataset page
* ``docs/datasets/_plots/<id>.png`` — PNG rendered by ``rheodata.plot(id)``

Stale pages (ids no longer in the registry) are removed.
"""
from __future__ import annotations

import os
import sys

DATASET_YAML_FIELDS = (
    "id",
    "title",
    "description",
    "material",
    "source",
    "provenance",
    "measurement",
    "samples",
    "columns",
    "tags",
)


def _get(obj, key, default=None):
    """Attribute-or-key lookup so metadata works as dicts or objects."""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _get_id(entry):
    if isinstance(entry, str):
        return entry
    return str(_get(entry, "id"))


def _doi_link(doi):
    doi = (doi or "").strip()
    if not doi:
        return "—"
    if doi.startswith(("http://", "https://")):
        return f"[{doi}]({doi})"
    return f"[{doi}](https://doi.org/{doi})"


def _cell(value):
    """Make a value safe for a Markdown table cell."""
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, (list, tuple)):
        return ", ".join(str(v) for v in value) or "—"
    text = str(value).strip()
    return text.replace("|", "\\|").replace("\n", " ") if text else "—"


def _metadata_rows(meta):
    """Ordered (label, value) rows for the dataset metadata table."""
    material = _get(meta, "material") or {}
    source = _get(meta, "source") or {}
    paper = _get(source, "paper") or {}
    provenance = _get(meta, "provenance") or {}
    measurement = _get(meta, "measurement") or {}

    authors = _get(paper, "authors")
    if isinstance(authors, (list, tuple)):
        authors = "; ".join(authors)
    citation = "; ".join(
        part
        for part in (
            _cell(authors),
            _cell(_get(paper, "title")),
            _cell(_get(paper, "journal")),
            str(_get(paper, "year") or "").strip(),
        )
        if part and part != "—"
    )

    geometry = _cell(_get(measurement, "geometry"))
    geometry_details = _get(measurement, "geometry_details")
    if geometry_details and str(geometry_details).strip().lower() not in ("", "not reported"):
        geometry = f"{geometry} ({_cell(geometry_details)})"

    temperature = _get(measurement, "temperature_C")
    if temperature is None:
        temperature = "—"
    elif isinstance(temperature, (int, float)):
        temperature = f"{temperature:g} °C"

    provenance_text = ", ".join(
        part
        for part in (
            _cell(_get(provenance, "origin")),
            f"digitized: {_cell(_get(provenance, 'digitized'))}",
        )
        if part and part != "—"
    )

    return [
        ("Material", _cell(_get(material, "name"))),
        ("Material kind", _cell(_get(material, "kind"))),
        ("Source", citation or "—"),
        ("DOI", _doi_link(_get(paper, "doi"))),
        ("Figure", _cell(_get(source, "figure"))),
        ("Measurement type", _cell(_get(measurement, "type"))),
        ("Geometry", geometry),
        ("Temperature", temperature),
        ("Protocol", _cell(_get(measurement, "protocol"))),
        ("Provenance", provenance_text or "—"),
    ]


def _page_markdown(ds_id, meta):
    title = _cell(_get(meta, "title")) or ds_id
    description = (_get(meta, "description") or "").strip()

    lines = [
        f"# 🧪 {title}",
        "",
        f"`dataset id: {ds_id}`",
        "",
    ]
    if description:
        lines += [description, ""]

    # Plot (rendered by rheodata.plot and saved next to this file).
    lines += [
        "## 📈 Data",
        "",
        f"![Data for {ds_id}](_plots/{ds_id}.png)",
        "",
    ]

    # Metadata table.
    lines += ["## 🗂️ Metadata", "", "| Field | Value |", "| --- | --- |"]
    for label, value in _metadata_rows(meta):
        lines.append(f"| {label} | {value} |")
    lines.append("")

    # Samples table.
    samples = _get(meta, "samples") or []
    lines += ["## 🧫 Samples", "", "| Sample id | Label |", "| --- | --- |"]
    if samples:
        for sample in samples:
            lines.append(f"| {_cell(_get(sample, 'id'))} | {_cell(_get(sample, 'label'))} |")
    else:
        lines.append("| — | — |")
    lines.append("")

    # Columns table (tidy-CSV schema, if the registry documents it).
    columns = _get(meta, "columns") or []
    lines += ["## 📋 Data columns", "", "| Role | Column | Units |", "| --- | --- | --- |"]
    units = _get(meta, "units") or {}
    if columns:
        for role in ("x", "y", "sample"):
            col = _get(columns, role)
            if col:
                lines.append(
                    f"| `{role}` | `{_cell(col)}` | {_cell(_get(units, role))} |"
                )
    else:
        lines.append("| — | — | — |")
    lines.append("")

    # Tags.
    tags = _get(meta, "tags") or []
    lines += ["## 🏷️ Tags", ""]
    lines.append(" ".join(f"`{t}`" for t in tags) if tags else "—")
    lines.append("")

    return "\n".join(lines)


def _index_markdown(ids_and_meta):
    lines = [
        "# 📚 Dataset catalog",
        "",
        "Every curated dataset in the registry, each with its own page: "
        "metadata, sample table, column schema, and a preview plot.",
        "",
        "| Dataset | Material | Source | Temperature |",
        "| --- | --- | --- | --- |",
    ]
    for ds_id, meta in ids_and_meta:
        title = _cell(_get(meta, "title")) or ds_id
        material = _get(meta, "material") or {}
        measurement = _get(meta, "measurement") or {}
        paper = _get(_get(meta, "source") or {}, "paper") or {}
        year = str(_get(paper, "year") or "").strip()
        journal = _cell(_get(paper, "journal"))
        source_cell = f"{journal} ({year})" if year and journal != "—" else journal
        temperature = _get(measurement, "temperature_C")
        if isinstance(temperature, (int, float)):
            temperature = f"{temperature:g} °C"
        lines.append(
            f"| [{title}]({ds_id}) | {_cell(_get(material, 'name'))} | "
            f"{_cell(source_cell)} | {_cell(temperature)} |"
        )
    if not ids_and_meta:
        lines += ["", "_The registry is empty — no datasets have been curated yet._"]
    lines += [
        "",
        "```{toctree}",
        ":hidden:",
        "",
    ]
    for ds_id, _meta in ids_and_meta:
        lines.append(ds_id)
    lines += ["```", ""]
    return "\n".join(lines)


def main(repo_root=None, docs_dir=None):
    """Generate the dataset pages. Returns the number of datasets written."""
    docs_dir = docs_dir or os.path.join(os.getcwd(), "docs")
    repo_root = repo_root or os.path.dirname(docs_dir)

    # The package must be importable: the repo root (sibling of docs/).
    if os.path.isdir(repo_root) and repo_root not in sys.path:
        sys.path.insert(0, repo_root)

    try:
        import rheodata  # noqa: E402
    except ImportError as exc:
        raise RuntimeError(
            f"could not import the rheodata package from {repo_root!r}: {exc}"
        ) from exc

    out_dir = os.path.join(docs_dir, "datasets")
    plots_dir = os.path.join(out_dir, "_plots")
    os.makedirs(plots_dir, exist_ok=True)

    catalog = rheodata.list()
    ids = catalog["id"].tolist()

    written = []
    for ds_id in ids:
        meta = rheodata.load(ds_id).meta

        # Plot first; a missing plot must not kill the page.
        try:
            fig = rheodata.plot(ds_id)
            if fig is not None:
                fig.savefig(os.path.join(plots_dir, f"{ds_id}.png"), dpi=150, bbox_inches="tight")
                try:
                    import matplotlib.pyplot as plt

                    plt.close(fig)
                except Exception:
                    pass
        except Exception as exc:
            print(f"[generate_dataset_pages] plot for {ds_id!r} failed: {exc}")

        with open(os.path.join(out_dir, f"{ds_id}.md"), "w", encoding="utf-8") as fh:
            fh.write(_page_markdown(ds_id, meta))
        written.append((ds_id, meta))

    # Remove stale pages for datasets no longer in the registry.
    current = {f"{ds_id}.md" for ds_id in ids}
    for fname in os.listdir(out_dir):
        if fname.endswith(".md") and fname != "index.md" and fname not in current:
            os.remove(os.path.join(out_dir, fname))
            print(f"[generate_dataset_pages] removed stale page {fname}")

    with open(os.path.join(out_dir, "index.md"), "w", encoding="utf-8") as fh:
        fh.write(_index_markdown(written))

    return len(written)


if __name__ == "__main__":
    here = os.path.abspath(os.path.dirname(__file__))  # docs/
    count = main(repo_root=os.path.dirname(here), docs_dir=here)
    print(f"generated {count} dataset page(s)")
