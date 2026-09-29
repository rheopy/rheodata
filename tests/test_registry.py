"""Registry validation tests.

Run against the dev fixtures in tests/fixtures AND against the real
``rheodata/datasets`` directory whenever it is populated (see conftest).
"""
import re

import pandas as pd
import pytest

import rheodata
import rheodata.registry as reg
from rheodata.registry import DOI_RE, DatasetError, load_registry, validate_dataset


def _dataset_dirs(registry):
    return {ds_id: entry["path"] for ds_id, entry in registry.items()}


def test_every_dataset_dir_has_yaml_and_csv(any_registry):
    for ds_id, path in _dataset_dirs(any_registry).items():
        assert (path / "dataset.yaml").is_file(), f"{ds_id}: missing dataset.yaml"
        assert (path / "data.csv").is_file(), f"{ds_id}: missing data.csv"


def test_schema_required_keys(any_registry):
    required = {"id", "title", "description", "material", "source",
                "provenance", "measurement", "samples", "columns", "tags"}
    for ds_id, entry in any_registry.items():
        meta = entry["meta"]
        missing = required - set(meta)
        assert not missing, f"{ds_id}: missing keys {missing}"
        assert set(("name", "kind")) <= set(meta["material"]), ds_id
        paper = meta["source"]["paper"]
        assert set(("title", "authors", "journal", "year", "doi")) <= set(paper), ds_id
        assert "figure" in meta["source"], ds_id
        assert "origin" in meta["provenance"], ds_id
        assert set(("type", "geometry", "temperature_C")) <= set(meta["measurement"]), ds_id
        assert meta["measurement"]["type"] in reg.EXPERIMENT_TYPES, ds_id
        assert set(("x", "y", "sample")) <= set(meta["columns"]), ds_id
        assert isinstance(meta["samples"], list) and meta["samples"], ds_id
        for s in meta["samples"]:
            assert set(("id", "label")) <= set(s), f"{ds_id}: bad sample entry {s}"
        assert isinstance(meta["tags"], list), ds_id


def test_csv_columns_match_yaml(any_registry):
    for ds_id, entry in any_registry.items():
        cols = entry["meta"]["columns"]
        df = pd.read_csv(entry["path"] / "data.csv")
        for key in ("x", "y", "sample"):
            assert cols[key] in df.columns, \
                f"{ds_id}: yaml columns.{key}={cols[key]!r} not in data.csv"


def test_x_numeric_sorted_per_sample(any_registry):
    for ds_id, entry in any_registry.items():
        cols = entry["meta"]["columns"]
        df = pd.read_csv(entry["path"] / "data.csv")
        x = pd.to_numeric(df[cols["x"]], errors="coerce")
        assert not x.isna().any(), f"{ds_id}: non-numeric x values"
        for sid, group in df.groupby(cols["sample"], sort=False):
            assert group[cols["x"]].is_monotonic_increasing, \
                f"{ds_id}: x not sorted ascending for sample '{sid}'"


def test_no_nan_in_xy(any_registry):
    for ds_id, entry in any_registry.items():
        cols = entry["meta"]["columns"]
        df = pd.read_csv(entry["path"] / "data.csv")
        assert not df[cols["x"]].isna().any(), f"{ds_id}: NaN in x"
        assert not df[cols["y"]].isna().any(), f"{ds_id}: NaN in y"


def test_sample_ids_match(any_registry):
    for ds_id, entry in any_registry.items():
        cols = entry["meta"]["columns"]
        df = pd.read_csv(entry["path"] / "data.csv")
        yaml_ids = {s["id"] for s in entry["meta"]["samples"]}
        assert set(df[cols["sample"]].unique()) == yaml_ids, f"{ds_id}: sample id mismatch"


def test_doi_format(any_registry):
    for ds_id, entry in any_registry.items():
        meta = entry["meta"]
        doi = meta["source"]["paper"]["doi"]
        origin = meta["provenance"]["origin"]
        if doi is None:
            # null DOI only allowed off literature (community/synthetic data)
            assert origin != "literature", f"{ds_id}: null DOI on literature data"
            continue
        assert DOI_RE.match(str(doi).strip()), f"{ds_id}: bad DOI '{doi}'"


def test_ids_unique(any_registry):
    ids = list(any_registry)
    assert len(ids) == len(set(ids)), "duplicate dataset ids"


def test_id_matches_directory(any_registry):
    for ds_id, entry in any_registry.items():
        assert entry["meta"]["id"] == ds_id == entry["path"].name


def test_validation_rejects_broken_dataset(tmp_path):
    bad = tmp_path / "broken"
    bad.mkdir()
    (bad / "dataset.yaml").write_text("id: broken\n")  # missing everything else
    (bad / "data.csv").write_text("x,y,sample\n1,2,s1\n")
    with pytest.raises(DatasetError, match="broken"):
        validate_dataset(bad)
    with pytest.raises(DatasetError, match="broken"):
        load_registry(tmp_path)


# ---------------------------------------------------------------------------
# API smoke tests on every dataset
# ---------------------------------------------------------------------------

def _with_registry(registry, fn, *args, **kwargs):
    """Run an API function against an explicit registry (fixtures or real)."""
    saved = dict(rheodata.REGISTRY)
    rheodata.REGISTRY.clear()
    rheodata.REGISTRY.update(registry)
    try:
        return fn(*args, **kwargs)
    finally:
        rheodata.REGISTRY.clear()
        rheodata.REGISTRY.update(saved)


def test_list_columns(any_registry):
    frame = _with_registry(any_registry, rheodata.list)
    assert list(frame.columns) == ["id", "title", "material_name", "material_kind",
                                   "experiment_type", "n_samples", "year", "doi"]
    assert set(frame["id"]) == set(any_registry)


def test_search_filters(any_registry):
    first_id = next(iter(any_registry))
    meta = any_registry[first_id]["meta"]
    material_word = str(meta["material"]["name"]).split()[0]
    hits = _with_registry(any_registry, rheodata.search, material=material_word)
    assert first_id in set(hits["id"])
    # case-insensitivity
    hits2 = _with_registry(any_registry, rheodata.search, material=material_word.upper())
    assert set(hits["id"]) == set(hits2["id"])
    exp = meta["measurement"]["type"]
    hits3 = _with_registry(any_registry, rheodata.search, experiment=exp)
    assert first_id in set(hits3["id"])
    q = str(meta["title"]).split()[1]
    hits4 = _with_registry(any_registry, rheodata.search, query=q)
    assert first_id in set(hits4["id"])
    if meta.get("tags"):
        hits5 = _with_registry(any_registry, rheodata.search, tag=str(meta["tags"][0]))
        assert first_id in set(hits5["id"])
    none = _with_registry(any_registry, rheodata.search, query="zzz_no_such_dataset_zzz")
    assert none.empty


def test_info_runs(any_registry, capsys):
    for ds_id, entry in any_registry.items():
        _with_registry(any_registry, rheodata.info, ds_id)
        out = capsys.readouterr().out
        doi = entry["meta"]["source"]["paper"]["doi"]
        if doi is None:
            assert "unpublished (community contribution)" in out, ds_id
        else:
            assert "https://doi.org/" in out, ds_id
        assert any_registry[ds_id]["meta"]["title"] in out, ds_id


def test_load_returns_dataset(any_registry):
    for ds_id, entry in any_registry.items():
        ds = _with_registry(any_registry, rheodata.load, ds_id)
        assert ds.id == ds_id
        assert ds.meta == entry["meta"]
        assert isinstance(ds.df, pd.DataFrame) and not ds.df.empty


def test_plot_returns_figure(any_registry):
    from matplotlib.figure import Figure
    for ds_id in any_registry:
        fig = _with_registry(any_registry, rheodata.plot, ds_id)
        assert isinstance(fig, Figure), ds_id
        assert fig.axes, ds_id
        # single-sample variant, by id and by integer index
        sid = any_registry[ds_id]["meta"]["samples"][0]["id"]
        fig2 = _with_registry(any_registry, rheodata.plot, ds_id, sample=sid)
        assert isinstance(fig2, Figure), ds_id
        fig3 = _with_registry(any_registry, rheodata.plot, ds_id, sample=0)
        assert isinstance(fig3, Figure), ds_id


def test_to_rheofit_flow_curve(any_registry):
    for ds_id, entry in any_registry.items():
        if entry["meta"]["measurement"]["type"] != "flow_curve":
            continue
        sid = entry["meta"]["samples"][0]["id"]
        df = _with_registry(any_registry, rheodata.to_rheofit, ds_id, sid)
        assert list(df.columns) == ["Shear rate / 1/s", "Stress / Pa"], ds_id
        assert (df["Shear rate / 1/s"].diff().dropna() >= 0).all(), ds_id
        assert not df.isna().any().any(), ds_id


def test_to_rheofit_rejects_non_flow_curve(any_registry):
    for ds_id, entry in any_registry.items():
        if entry["meta"]["measurement"]["type"] == "flow_curve":
            continue
        sid = entry["meta"]["samples"][0]["id"]
        with pytest.raises(ValueError, match="only supports flow_curve"):
            _with_registry(any_registry, rheodata.to_rheofit, ds_id, sid)


def test_unknown_id_errors(any_registry):
    with pytest.raises(KeyError):
        _with_registry(any_registry, rheodata.load, "no_such_dataset")
    with pytest.raises(ValueError, match="unknown sample"):
        ds_id = next(iter(any_registry))
        _with_registry(any_registry, rheodata.plot, ds_id, sample="no_such_sample")
