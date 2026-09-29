---
name: data-discovery
description: "Find, inspect, load, and plot quality rheological datasets from the rheodata library — literature and community flow curves, frequency sweeps, and other benchmark-quality measurements. Use for: find rheology dataset, rheodata, benchmark data, training data rheology, load flow curve data, literature rheology data, rheology test datasets, search rheometry measurements, citation for rheology data."
---

# Data Discovery 🔍

**`rheodata`** is a pip-installable library of quality rheological datasets — literature and
community — for training, simulation, and benchmarking. Every dataset is curated, documented, and
versioned, so a fit, a benchmark, or a simulation built on it is reproducible and citable.

## Why curated data matters

Raw data scraped from the internet is a minefield: unknown geometries, missing temperatures,
unlabelled units, plots digitised without a record of it, materials described as "gel-like".
A dataset you cannot trust is worse than no dataset at all, because it launders its own
uncertainty into your conclusions.

`rheodata` exists to remove that uncertainty:

- **Provenance is explicit** — every dataset records whether it is natively measured
  (values as recorded by the instrument) or digitised (reconstructed from a published figure),
  and says so in its metadata.
- **Measurements are described** — geometry, temperature, protocol, and units are part of the
  record, not buried in a paper's methods section.
- **Citations travel with the data** — every dataset carries its source paper and DOI, so the
  credit (and the reproducibility chain) is never lost.

---

## Skill and Library Are One Thing

All behaviour described here is implemented by the **`rheodata`** library (`rheodata/`).
This file is simultaneously the agent workflow *and* the user-facing documentation of that library.

The user can drive the exact same code in three interchangeable ways:

| Route          | Command / call                                            | Best for                          |
| -------------- | --------------------------------------------------------- | --------------------------------- |
| Python API     | `import rheodata` → `rheodata.search(...)`                | notebooks, scripts, custom plots  |
| CLI            | `uv run rheodata <args>`                                  | one-shot runs from a terminal     |
| Skill (agent)  | this file — the agent runs the code on the user's behalf  | guided dataset discovery          |

Because the skill only calls the library, the two can never drift. If you change the library's
API, CLI flags or dataset schema, **update this file in the same edit**.

Install once, then use anywhere:

```bash
pip install rheodata
```

If the library is not installed and you are inside the repo, `python -m rheodata <args>` or the
wrapper in `scripts/` (see **How to Run**) works instead.

### Library quick reference

```python
import rheodata

rheodata.list()                                   # DataFrame: id, title, material_name, material_kind,
                                                  #            experiment_type, n_samples, year, doi
rheodata.search(material="Carbopol",              # filtered DataFrame (any filter may be omitted)
                experiment="flow_curve",
                tag="yield_stress",
                query="temperature series")
rheodata.info("caggioni_pg_carbopol_2pct")                # prints description, material, paper + DOI link,
                                                  # measurement details, samples, tags

ds = rheodata.load("caggioni_pg_carbopol_2pct")           # Dataset
ds.df                                             # tidy DataFrame (one row per point)
ds.meta                                           # dict: description, material, provenance, geometry,
                                                  # protocol, temperature, units, paper, doi, tags ...

fig = rheodata.plot("caggioni_pg_carbopol_2pct")          # experiment-appropriate matplotlib Figure
fig = rheodata.plot("caggioni_pg_carbopol_2pct", sample=0)

fit_df = rheodata.to_rheofit("caggioni_pg_carbopol_2pct", sample=0)   # DataFrame ready for rheofit.fit
```

The CLI mirrors the API:

```bash
rheodata list                              # full catalog
rheodata search --material Carbopol --experiment flow_curve
rheodata info caggioni_pg_carbopol_2pct
rheodata install-skill                     # install this skill into the user's agent
```

---

## Golden Rule — Clarify Before Searching

A rheology question is only as precise as its conditions. Before running `search`, ask what the
user actually needs — a five-second clarification beats a blind sweep of the catalog:

- **Material** — what material (or class of material)?
- **Experiment** — flow curve, frequency sweep, amplitude sweep, temperature series, …?
- **Conditions** — which temperature(s), concentration(s), geometry? Any deal-breakers?
- **Purpose** — training a model, benchmarking a fit, validating a simulation, teaching?

Then propose a search plan and run it — searching is read-only, so no approval gate is needed
for the search itself. Approval gates apply later: before **mixing** datasets or **contributing**
new ones (see **Guardrails**).

---

## The Discovery Workflow

### Step 1 — Clarify the need

Ask the material / experiment / conditions / purpose questions above, or recover them from the
conversation. Turn the answers into a search:

```python
df = rheodata.search(material="carbopol", experiment="flow_curve", tag="yield_stress")
```

Start broad (`list()` or a single filter), then narrow. An empty result is a finding, not a
failure — report it and offer to widen the search (different material class, digitised datasets
included, etc.).

### Step 2 — Search and browse

Use `search()` / `list()` and report the hits with their **id, title, material, experiment type,
n_samples, and year**. This is the moment to show the user what exists, not to load anything yet.

```python
rheodata.list()                                    # the whole catalog
rheodata.search(experiment="frequency_sweep")      # every frequency sweep
rheodata.search(query="wormlike micelles")         # free-text across titles/descriptions
```

### Step 3 — Check measurement details and provenance with `info()`

Before recommending a dataset, read its `info()` output carefully — this is where you check that
the data actually measures what the user needs. Say this part out loud in your report (see
**How to read dataset metadata** below).

```bash
rheodata info caggioni_pg_carbopol_2pct
```

```python
rheodata.info("caggioni_pg_carbopol_2pct")
```

If two candidate datasets disagree in geometry, temperature, or protocol, **flag it** — don't
silently treat them as comparable (see **Guardrails**).

### Step 4 — Load and look at the data

```python
ds = rheodata.load("caggioni_pg_carbopol_2pct")
ds.df.head()     # tidy DataFrame: one row per measurement point
ds.meta          # the full metadata dict — cite from here, never from memory

fig = rheodata.plot("caggioni_pg_carbopol_2pct", sample=0)
fig.savefig("caggioni_pg_carbopol_2pct_sample0.png")
```

Always plot before handing data downstream. A one-glance look catches problems no metadata can:
instrument noise at low torque, truncated shear-rate windows, obvious digitisation artefacts.
Report anything you see.

### Step 5 — Hand off

Discovery ends where modelling begins. Route by purpose:

- **Fitting** → hand the loaded data to rheofit's **flow-curve-analysis** skill:
  `rheodata.to_rheofit(id, sample)` returns a DataFrame in exactly the shape `rheofit.fit`
  expects (standardised columns `Shear rate / 1/s`, `Viscosity / Pa.s`, `Stress / Pa`, test type
  in `df.attrs`). Quote the dataset id and the source paper DOI in the handoff so the fit
  report inherits the provenance.
- **Simulation / ML training** → export a plain CSV the user's pipeline can read:
  `ds.df.to_csv("caggioni_pg_carbopol_2pct.csv", index=False)`, and ship `ds.meta` alongside as
  `caggioni_pg_carbopol_2pct_meta.json` so the metadata survives the export.
- **Teaching / exploratory plotting** → `rheodata.plot(id)` figures are publication-ready
  as-is (log-log axes where decades are spanned).

---

## How to Read Dataset Metadata 📋

`info()` and `ds.meta` describe each dataset along the same axes. Here's how to interpret them:

| Field            | What it tells you                                        | Why it matters                                  |
| ---------------- | -------------------------------------------------------- | ----------------------------------------------- |
| `material_name` / `material_kind` | what the sample is (e.g. Carbopol 940, 1 wt%) | is it the material you need, or a cousin? |
| `experiment_type` | `flow_curve`, `frequency_sweep`, `amplitude_sweep`, …   | what the data can be used for                    |
| `geometry`       | cone-plate, parallel plate, Couette, … + dimensions      | edge effects, slip risk, gap errors differ per geometry |
| `protocol`       | sweep direction, equilibration, pre-shear, ramp time     | hysteresis and thixotropy hide here              |
| `temperature`    | measurement temperature(s)                               | rheology is temperature-sensitive — never compare across T silently |
| `provenance`     | `native` (instrument values) vs `digitized` (reconstructed from a published figure) | digitised data inherits figure-resolution error; see below |
| `n_samples`      | how many samples/conditions the dataset holds            | one curve vs a full series                       |
| `paper` / `doi`  | source publication                                       | cite it — always (see **Citing**)                |
| `tags`           | e.g. `yield_stress`, `shear_thinning`, `temperature_series` | quick filtering, not a substitute for reading `info()` |

### Native vs digitised — what provenance implies for trust

- **Native** datasets are the values as recorded by the instrument (or as supplied by the
  authors). Treat them as primary data; the usual experimental caveats (torque limits, slip,
  evaporation) apply and are usually noted in the protocol.
- **Digitised** datasets were reconstructed from a published figure with digitisation software.
  They carry **figure-resolution error**: roughly ±1% of the axis span per point, plus whatever
  the original figure's rendering lost. They are perfectly fine for training, benchmarking model
  *selection*, and qualitative comparison — but do not use them to claim a parameter to three
  significant figures, and **never present digitised data as measured data**. The `info()` output
  says which is which; relay that label verbatim to the user.

---

## Citing 📚

**Always cite the source paper.** Every dataset's metadata carries its `paper` and `doi` — use
them, don't paraphrase from memory. When you hand data downstream (a fit report, a CSV export, a
benchmark table), the citation goes with it:

> Flow curve for Carbopol 940 (1 wt%), 25 °C, cone-plate — rheodata `caggioni_pg_carbopol_2pct`,
> from Caggioni, Trappe & Spicer (2020), https://doi.org/10.1122/1.5120633.

(Example DOI shown for format only — use the DOI from the dataset's own metadata.)

If the user publishes or presents work built on rheodata datasets, remind them: cite the paper,
and mention `rheodata` as the source of the curated files.

---

## Guardrails 🛡️

1. **Never invent data.** If a dataset doesn't exist in the catalog, say so. Do not fabricate
   dataset ids, parameter values, or "typical" curves.
2. **Never relabel digitised data as measured.** The provenance label from `info()` is part of
   the data — relay it exactly. A digitised curve is a faithful copy, not an instrument record.
3. **Flag temperature and geometry mismatches when comparing datasets.** Two flow curves at
   different temperatures, or one cone-plate vs one parallel-plate, are not interchangeable
   observations of "the same material". State the mismatch before any comparison, and prefer
   normalising (e.g. temperature-shift) or restricting to matched conditions.
4. **Ask before mixing community and literature data in one benchmark.** Community-contributed
   datasets are welcome and versioned, but they have not necessarily passed the same scrutiny as
   literature data. Mixing them in one benchmark table or training set needs the user's explicit
   go-ahead — propose it, don't assume it.
5. **Don't over-claim precision.** Metadata fields are curated, not measured by you. Quote them;
   don't round them into false precision, and don't fill gaps the metadata leaves ("the gap was
   probably 1 mm" is not a fact).
6. **Contributions go through the issue workflow.** If the user wants to contribute a dataset
   (or points at one worth curating), open/file a GitHub issue on the rheodata repo with the
   source paper or data file — do not invent a dataset id or commit data yourself. See
   `USAGE.md` for the copy-paste template.
7. **Keep the handoff honest.** When passing data to the fitting skill, include the dataset id,
   sample index, provenance label, and source DOI — the fit report should never lose track of
   where its data came from.

---

## How to Run

**Preferred — installed package:**

```bash
pip install rheodata
rheodata search --material Carbopol --experiment flow_curve
```

**From the repo (editable / source checkout):**

```bash
python -m rheodata <args>
```

**If `rheodata` is not installed at all** — the skill ships a wrapper that adds the repo's
package directory to `sys.path` and forwards to the same CLI, so the flags are identical:

```bash
python scripts/rheodata_cli.py <args>
```

Every `rheodata …` command below can be replaced by either fallback without changing the result.

---

## When to Use

- User asks to find a rheology dataset for a material, or browses what's available
- User needs benchmark data to test a model, a fit, or a simulation against
- User needs training data for ML on rheological measurements
- User wants literature rheology data with citable provenance
- User wants to load a flow curve (or sweep) from the catalog and plot it
- User wants to prepare catalog data for fitting with rheofit (`to_rheofit`)
- User wants to contribute a dataset or points at data worth curating

---

## When NOT to Use

- The user has their **own** measurement file to analyse → that's rheofit's
  **flow-curve-analysis** skill (TRIOS JSON in, fitted model out).
- The user asks for data the catalog doesn't hold → say so plainly and offer the contribution
  workflow (GitHub issue) instead of improvising.
- The user wants a **new** measurement designed or an instrument protocol → out of scope;
  suggest consulting the source papers' methods sections via the DOIs in the catalog.

---

## Changelog

- 2026-09-29 — initial version of the skill, written against the rheodata Python API contract
  (`list`, `search`, `info`, `load`, `plot`, `to_rheofit`) and CLI
  (`list | search | info <id> | install-skill`).
