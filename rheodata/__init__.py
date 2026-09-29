"""rheodata — curated, quality-checked rheology datasets.

Find experimental datasets for training, simulation, and benchmarking:

>>> import rheodata
>>> rheodata.list()                      # every dataset, one row each
>>> rheodata.search(material="carbopol")  # substring filters
>>> rheodata.info("carbopol_flow_25C")    # human-readable summary
>>> ds = rheodata.load("carbopol_flow_25C")
>>> ds.df.head()                         # tidy DataFrame
>>> fig = rheodata.plot("carbopol_flow_25C")
>>> rdf = rheodata.to_rheofit("carbopol_flow_25C", sample="s1")
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Union

import numpy as np
import pandas as pd
from matplotlib.figure import Figure

from .registry import REGISTRY, DatasetError, load_registry

__all__ = [
    "Dataset",
    "DatasetError",
    "info",
    "list",
    "load",
    "load_registry",
    "plot",
    "search",
    "to_rheofit",
]

_LIST_COLUMNS = [
    "id", "title", "material_name", "material_kind",
    "experiment_type", "n_samples", "year", "doi",
]

_builtin_list = list  # `list()` below shadows the builtin within this module


@dataclass
class Dataset:
    """One loaded dataset: tidy data, metadata, and id."""

    df: pd.DataFrame
    """Tidy data as stored in ``data.csv``."""
    meta: dict
    """Full parsed ``dataset.yaml`` metadata."""
    id: str
    """Dataset id (directory name)."""


def _entry(ds_id: str) -> dict:
    try:
        return REGISTRY[ds_id]
    except KeyError:
        known = ", ".join(sorted(REGISTRY)) or "(registry is empty)"
        raise KeyError(f"unknown dataset id '{ds_id}'. Known ids: {known}") from None


def _row(ds_id: str, entry: dict) -> dict:
    m = entry["meta"]
    return {
        "id": ds_id,
        "title": m["title"],
        "material_name": m["material"]["name"],
        "material_kind": m["material"]["kind"],
        "experiment_type": m["measurement"]["type"],
        "n_samples": len(m["samples"]),
        "year": m["source"]["paper"]["year"],
        "doi": m["source"]["paper"]["doi"],
    }


def list() -> pd.DataFrame:
    """One row per dataset: id, title, material, experiment, samples, year, doi."""
    rows = [_row(ds_id, entry) for ds_id, entry in sorted(REGISTRY.items())]
    return pd.DataFrame(rows, columns=_LIST_COLUMNS)


def search(
    material: Optional[str] = None,
    experiment: Optional[str] = None,
    tag: Optional[str] = None,
    query: Optional[str] = None,
) -> pd.DataFrame:
    """Substring filters (case-insensitive) over the registry.

    ``query`` matches title, description, and material name.
    """
    frame = list()
    if frame.empty:
        return frame

    def _contains(series: pd.Series, text: str) -> pd.Series:
        return series.fillna("").str.contains(text, case=False, na=False)

    if material:
        frame = frame[_contains(frame["material_name"], material)]
    if experiment:
        frame = frame[_contains(frame["experiment_type"], experiment)]
    if tag:
        want = tag.casefold()
        keep = [
            ds_id
            for ds_id, entry in REGISTRY.items()
            if any(want in str(t).casefold() for t in entry["meta"].get("tags", []))
        ]
        frame = frame[frame["id"].isin(keep)]
    if query:
        desc = pd.Series(
            {ds_id: entry["meta"].get("description", "")
             for ds_id, entry in REGISTRY.items()}
        )
        hit = (
            _contains(frame["title"], query)
            | _contains(frame["material_name"], query)
            | _contains(frame["id"].map(desc), query)
        )
        frame = frame[hit]
    return frame.reset_index(drop=True)


def info(ds_id: str) -> None:
    """Print a readable summary of a dataset."""
    entry = _entry(ds_id)
    m = entry["meta"]
    paper = m["source"]["paper"]
    meas = m["measurement"]
    authors = paper["authors"]
    if isinstance(authors, (_builtin_list, tuple)):
        authors = ", ".join(str(a) for a in authors)
    source_line = f"{authors} — {paper['title']}" if authors else paper['title']
    doi = paper.get("doi")
    if doi:
        doi_s = str(doi).strip()
        doi_url = doi_s if doi_s.startswith("http") else f"https://doi.org/{doi_s}"
    else:
        doi_url = "unpublished (community contribution)"
    journal = paper.get("journal") or "—"
    year = paper.get("year") or "—"

    bar = "═" * 64
    print(bar)
    print(m["title"])
    print("─" * 64)
    print(str(m["description"]).strip())
    print()
    print(f"Material : {m['material']['name']} ({m['material']['kind']})")
    print(f"Source   : {source_line}")
    print(f"           {journal} ({year})")
    print(f"DOI      : {doi_url}")
    print(f"Figure   : {m['source']['figure']}")
    print(f"Origin   : {m['provenance']['origin']}")
    print()
    print("Measurement")
    print(f"  type        : {meas['type']}")
    print(f"  geometry    : {meas['geometry']}")
    temp = meas["temperature_C"]
    print(f"  temperature : {'—' if temp is None else f'{temp} °C'}")
    for opt in ("details", "protocol"):
        if meas.get(opt):
            print(f"  {opt:<11} : {meas[opt]}")
    print()
    print("Samples")
    width = max(len(str(s["id"])) for s in m["samples"])
    for s in m["samples"]:
        print(f"  {str(s['id']):<{width}}  {s['label']}")
    print()
    tags = m.get("tags", [])
    print("Tags     : " + (", ".join(str(t) for t in tags) if tags else "—"))
    print(bar)


def load(ds_id: str) -> Dataset:
    """Load a dataset: ``Dataset(df, meta, id)`` with the tidy ``data.csv``."""
    entry = _entry(ds_id)
    df = pd.read_csv(entry["path"] / "data.csv")
    return Dataset(df=df, meta=entry["meta"], id=ds_id)


def _sample_frames(ds: Dataset, sample: Optional[str | int]):
    """(list of (sample_id, label, frame), x_col, y_col, sample_col)."""
    m = ds.meta
    cols = m["columns"]
    x_col, y_col, sample_col = cols["x"], cols["y"], cols["sample"]
    wanted = _builtin_list(m["samples"])
    if sample is not None:
        if isinstance(sample, int):
            try:
                wanted = [wanted[sample]]
            except IndexError:
                wanted = []
        else:
            wanted = [s for s in wanted if s["id"] == sample or s["label"] == sample]
        if not wanted:
            valid = ", ".join(f"{s['id']} ({s['label']})" for s in m["samples"])
            raise ValueError(
                f"dataset '{ds.id}': unknown sample '{sample}'. Valid: {valid}"
            )
    out = []
    for s in wanted:
        frame = ds.df[ds.df[sample_col] == s["id"]].sort_values(x_col)
        out.append((s["id"], s["label"], frame))
    return out, x_col, y_col, sample_col


def _modulus_cols(ds: Dataset):
    cols = ds.meta["columns"]
    gs, gl = cols.get("g_storage"), cols.get("g_loss")
    if not gs or not gl:
        raise ValueError(
            f"dataset '{ds.id}': {ds.meta['measurement']['type']} plot needs "
            "'g_storage' and 'g_loss' entries in dataset.yaml columns"
        )
    for c in (gs, gl):
        if c not in ds.df.columns:
            raise ValueError(f"dataset '{ds.id}': data.csv missing column '{c}'")
    return gs, gl


def plot(ds_id: str, sample: Optional[Union[str, int]] = None) -> Figure:
    """Experiment-appropriate plot; returns a :class:`matplotlib.figure.Figure`.

    - flow_curve: log-log σ(x) and η(x) = y/x on twin y-axes, one curve per sample
    - amplitude_sweep / frequency_sweep: G′, G″ vs x (log-log)
    - shear_startup: stress vs strain (log-linear x)
    - creep / stress_relaxation: strain/stress vs time (log-log)
    """
    ds = load(ds_id)
    exp = ds.meta["measurement"]["type"]
    samples, x_col, y_col, _ = _sample_frames(ds, sample)

    fig = Figure(figsize=(7.5, 4.8), layout="constrained")
    title = ds.meta["title"]
    if sample is not None:
        title += f" — {sample}"

    if exp == "flow_curve":
        ax1 = fig.add_subplot(111)
        ax2 = ax1.twinx()
        for _sid, label, frame in samples:
            x = frame[x_col].to_numpy(dtype=float)
            y = frame[y_col].to_numpy(dtype=float)
            with np.errstate(divide="ignore", invalid="ignore"):
                eta = y / x
            (l1,) = ax1.loglog(x, y, "o-", ms=3, label=f"{label}  σ")
            ax2.loglog(x, eta, "s--", ms=3, color=l1.get_color(),
                       label=f"{label}  η")
        ax1.set_xlabel(x_col)
        ax1.set_ylabel(y_col, color="tab:red")
        ax2.set_ylabel(f"η = {y_col} / {x_col}", color="tab:blue")
        h1, lab1 = ax1.get_legend_handles_labels()
        h2, lab2 = ax2.get_legend_handles_labels()
        ax1.legend(h1 + h2, lab1 + lab2, loc="best", fontsize="small")
        ax1.set_title(title)
        return fig

    if exp in ("amplitude_sweep", "frequency_sweep"):
        gs, gl = _modulus_cols(ds)
        ax = fig.add_subplot(111)
        for _sid, label, frame in samples:
            x = frame[x_col].to_numpy(dtype=float)
            (l1,) = ax.loglog(x, frame[gs].to_numpy(dtype=float), "o-",
                              ms=3, label=f"{label}  G′")
            ax.loglog(x, frame[gl].to_numpy(dtype=float), "s--",
                      ms=3, color=l1.get_color(), label=f"{label}  G″")
        ax.set_xlabel(x_col)
        ax.set_ylabel("Modulus [Pa]")
        ax.legend(loc="best", fontsize="small")
        ax.set_title(title)
        return fig

    ax = fig.add_subplot(111)
    for _sid, label, frame in samples:
        x = frame[x_col].to_numpy(dtype=float)
        y = frame[y_col].to_numpy(dtype=float)
        if exp == "shear_startup":
            ax.semilogx(x, y, "o-", ms=3, label=label)
        else:  # creep, stress_relaxation
            ax.loglog(x, y, "o-", ms=3, label=label)
    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    ax.legend(loc="best", fontsize="small")
    ax.set_title(title)
    return fig


def to_rheofit(ds_id: str, sample: Union[str, int]) -> pd.DataFrame:
    """Flow-curve sample as a rheofit-compatible DataFrame.

    Columns ``"Shear rate / 1/s"`` and ``"Stress / Pa"``, x sorted ascending.
    Raises a clear error if the dataset is not a flow curve.
    """
    ds = load(ds_id)
    exp = ds.meta["measurement"]["type"]
    if exp != "flow_curve":
        raise ValueError(
            f"to_rheofit only supports flow_curve datasets; "
            f"'{ds_id}' is '{exp}'"
        )
    samples, x_col, y_col, _ = _sample_frames(ds, sample)
    _sid, _label, frame = samples[0]
    out = pd.DataFrame({
        "Shear rate / 1/s": frame[x_col].to_numpy(dtype=float),
        "Stress / Pa": frame[y_col].to_numpy(dtype=float),
    }).sort_values("Shear rate / 1/s", kind="mergesort").reset_index(drop=True)
    return out
