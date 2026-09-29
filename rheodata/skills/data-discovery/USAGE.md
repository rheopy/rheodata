# rheodata — Data Discovery: Usage Examples

Three copy-paste recipes for the `data-discovery` skill. All assume
`pip install rheodata` (or the skill's `scripts/rheodata_cli.py` fallback —
replace `rheodata` with `python scripts/rheodata_cli.py` in the CLI examples).

---

## 1. Find + load + plot a dataset 🔍

Pick a literature flow curve for a yield-stress fluid, inspect its provenance,
and plot it.

```python
import rheodata

# 1. Search the catalog
hits = rheodata.search(material="carbopol", experiment="flow_curve", tag="yield_stress")
print(hits[["id", "title", "material_name", "n_samples", "year", "doi"]])

# 2. Check measurement details and provenance before loading
rheodata.info("caggioni_pg_carbopol_2pct")

# 3. Load and plot
ds = rheodata.load("caggioni_pg_carbopol_2pct")
print(ds.meta["provenance"], "|", ds.meta["geometry"], "|", ds.meta["temperature"])
fig = rheodata.plot("caggioni_pg_carbopol_2pct", sample=0)
fig.savefig("caggioni_pg_carbopol_2pct_sample0.png", dpi=150)
```

CLI equivalent:

```bash
rheodata search --material carbopol --experiment flow_curve --tag yield_stress
rheodata info caggioni_pg_carbopol_2pct
```

> Always read `info()` before `load()`: it tells you the geometry, protocol,
> temperature, and whether the data is `native` or `digitized` — the label you
> must carry into anything you build on the data.

---

## 2. Benchmark prep: catalog data → rheofit-ready 📊

Assemble several literature datasets into one benchmark set for fitting with
rheofit's `flow-curve-analysis` skill. Export each curve as a CSV with its
metadata sidecar so provenance survives the handoff.

```python
import json
import rheodata

dataset_ids = [
    "caggioni_pg_carbopol_2pct",   # yield-stress fluid
    "xanthan_1pct",        # shear-thinning polymer
    "glycerol_pure",       # Newtonian reference
]

for ds_id in dataset_ids:
    ds = rheodata.load(ds_id)
    print(ds_id, "->", ds.meta["provenance"], "|", ds.meta["doi"])

    # DataFrame ready for rheofit.fit (standardised columns, test type in df.attrs)
    fit_df = rheodata.to_rheofit(ds_id, sample=0)
    fit_df.to_csv(f"{ds_id}.csv", index=False)

    # Metadata sidecar — ship it with the CSV, always
    with open(f"{ds_id}_meta.json", "w") as f:
        json.dump(ds.meta, f, indent=2, default=str)

print("Done. Hand the CSVs + DOIs to the flow-curve-analysis skill for fitting.")
```

> **Benchmark hygiene:** only compare datasets measured under matched conditions.
> If temperatures or geometries differ across your set, say so in the benchmark
> table — and ask before mixing community-contributed data with literature data
> (see the skill's guardrails).

---

## 3. Contribute a dataset pointer (GitHub issue workflow) 🤝

`rheodata` grows by curation, not by commit-from-chat. If you spot a paper (or a
community file) worth adding, file an issue on the rheodata repo — don't invent
a dataset id or commit data yourself. Copy-paste template:

```markdown
**Dataset suggestion**

- Paper / source: <authors, year, title>
- DOI: https://doi.org/<doi>
- Material: <e.g. Carbopol 940, 1 wt% in water>
- Experiment type: <flow_curve / frequency_sweep / amplitude_sweep / ...>
- Conditions: <temperature, geometry, concentration — whatever the paper states>
- Data form: [ ] values tabulated in the paper / SI
             [ ] figure only (would need digitising)
             [ ] author-provided file (attach or link)
- Why it's worth curating: <one or two sentences — e.g. clean temperature
  series, rare geometry, classic benchmark material>
```

Then:

```bash
# open the issue in your browser
rheodata info <existing-similar-id>   # optional: check for duplicates first
```

The maintainers will curate, version, and assign the dataset id — it appears in
`rheodata.list()` from the next release on.

---

*See `SKILL.md` for the full workflow, the metadata field guide, citation rules,
and guardrails.*
