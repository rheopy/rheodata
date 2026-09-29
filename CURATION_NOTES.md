# rheodata seed datasets — curation notes (2026-09-29)

Curated into `rheodata/datasets/` from two sources: 8 literature flow-curve CSVs
fetched from `rheopy/rheodata` (master, `raw_data/experiments/flow_curves/`) via the
GitHub API, and 4 community datasets extracted from TRIOS JSONs in the local
rheofit checkout (`~/workspace/repo-study/rheofit`, read-only reference).
No PR opened; nothing in `~/workspace/repo-study/rheofit` was modified.

All literature CSVs share one layout: the header row lists volume fractions with a
blank column between groups; below it each group is a shear-rate/stress column pair,
NaN-padded to a rectangle. Conversion to the tidy `data.csv` (`sample_id`,
`shear_rate_1/s`, `stress_Pa`) was done by a single script
(`/tmp/rheodata_curate.py`), which sorts x ascending per sample.

## Judgment calls, per dataset

### Literature

**dinkgreve2015_fig2** — `dinkgreve2015universal_2.csv`, 7 samples (φ 0.65–0.80), 146 points.
No cleanup needed; values already in SI units. Material verified from the paper's
open PDF (TU/e repository): Fig. 2 = castor-oil-in-water emulsions with *rigid*
droplet interfaces (0.4 wt% BSA + 0.4 wt% PGA) — **not** the mobile (SDS) system of
Fig. 1. Geometry: cone-plate on an Anton Paar MCR 301 (controlled shear stress),
per the paper's §II.A. Protocol: preshear 100 s⁻¹ / 30 s, 30 s rest, up-and-down
shear-rate sweeps. Temperature not stated in the methods → `temperature_C: null`.

**ghosh2019_fig3** — `ghosh2019linear_3.csv`, 7 samples (φ 0.46–0.881), 133 points.
No cleanup needed. Kept both near-duplicate φ = 0.88 and φ = 0.881 curves as
separate samples (`phi_0.88`, `phi_0.881`), flagged in the description.
Geometry/temperature/protocol not verifiable from a quick search → "not reported".

**mason1996_fig5** — `mason1996yielding_5.csv`, 6 samples (φ 0.55–0.65), 77 points.
**Unit conversion applied**: the old `figures.yml` records `unit_y: dynes/cm2`, so
all stresses multiplied by **0.1** (dynes/cm² → Pa). Post-conversion ranges are
plausible for a jammed emulsion (φ = 0.65 max 53.6 Pa vs. 536 Pa pre-conversion).
Geometry/temperature/protocol "not reported".

**pamvouxoglou2021_fig6** — `pamvouxoglou2021stress_6.csv`, 3 samples, 32 points.
No unit conversion. One out-of-order digitization point (φ = 0.624, 0.0976 → 0.0503)
fixed by sorting x ascending. Geometry/temperature/protocol "not reported".

**paredes2013_fig1** — `paredes2013rheology_1.csv`, 10 samples (φ 0.65–0.80), 342 points.
No cleanup needed. Note: the φ = 0.65 curve is truncated at low shear rate (starts
at 6.4e-2 s⁻¹ while the others start at ~1.3e-4) — this is how the source digitized
file is; not an error. Geometry/temperature/protocol "not reported".

**petekidis2004_fig5** — `petekidis2004yielding_5.csv`, 5 samples, 230 points.
**Scale factors applied from the old metadata**: the original figure had normalized
axes, so shear rate × **0.158** → s⁻¹ and stress × **0.0825** → Pa. Sanity check:
post-conversion ranges are x ≈ 1.7e-5–2.5 s⁻¹, y ≈ 1–145 Pa (yield stresses of
order 10–100 Pa at φ = 0.63) — plausible for PMMA hard-sphere colloidal glasses;
the audit's ranges (≈ x: 1.7e-5–2.5, y: 0.9–145) are confirmed. One out-of-order
point (φ = 0.596, 0.243 → 0.175) fixed by sorting. Geometry/temperature/protocol
"not reported".

**seth2011_S4a** — `seth2011micromecanical_S4a.csv` (**source filename typo preserved**:
"micromecanical"), 6 samples, 177 points. **One trailing artifact point dropped**:
the φ = 0.92 column ends with a low point (x = 0.049, y = 79.65) that is an
out-of-order duplicate of an earlier measurement; per the curation instructions it
was dropped rather than sorted. Geometry verified from the paper's methods (PDF at
sites.utexas.edu/bonnecazegroup): Anton-Paar MCR 501, cone-and-Peltier-plate,
50 mm, 2°, 48 µm truncation, solvent trap, 20 °C, sandpaper-roughened shearing
surfaces to suppress slip. `figure: "S4a"` (supplementary).

**seth2011_S4b** — `seth2011micromechanical_S4b.csv`, 3 samples, 101 points. One
small digitization glitch (φ = 0.72, 120.8 → 117.6) fixed by sorting. Same geometry/
temperature/protocol as S4a (same paper, same apparatus).

### Community (provenance: `origin: community`, `digitized: false`)

These come from the rheofit walkthrough TRIOS JSONs (never published as papers),
so `source.paper` is honest about that (title "Unpublished (community
contribution)", null journal/year/doi). Geometry/protocol taken only from what the
walkthrough docs state; anything else is "not reported".

**caggioni_pg_carbopol_2pct** — from `rheofit/data/pgpol_2pc_ultrez21.json`
("Flow sweep - 1"), 1 sample, 61 points, 10⁻³–10³ s⁻¹, 20 °C. Geometry:
concentric-cylinder (stated in walkthrough.md §"case study").

**caggioni_linear_polymer_flow** — from `docs/walkthrough/a_remake_dhr2.json`
("Flow sweep - 2", 51 points, 0.01–1000 s⁻¹, 25 °C). Geometry "not reported".

**caggioni_linear_polymer_amplitude_sweep** — from `docs/walkthrough/a_remake_dhr2.json`
("Amplitude sweep - 1"), 41 points, strain 1000→0.1 % at fixed ω = 1 rad/s, 25 °C.
G′/G″ strain-independent to γ₀ ≈ 10–25 % (LVE locator); feeds the Delaware–Rutgers
rule. Tidy columns: `strain_pct`, `Gp_Pa`, `Gpp_Pa`.

**caggioni_linear_polymer_frequency_sweep** — from `docs/walkthrough/a_remake_dhr2.json`
("Frequency sweep - 3"), 31 points, ω 100→0.1 rad/s at γ₀ = 0.5 %, 25 °C.
Feeds the Cox–Merz superposition. Tidy columns: `omega_rad/s`, `Gp_Pa`, `Gpp_Pa`.

**caggioni_wlm_polymer_temp_series** — from `docs/walkthrough/aos_2_1.json`, all
seven flow sweeps ("Flow sweep - 1..7"), 41 points each, 0.01–100 s⁻¹. Step → sample
mapping taken from the `Temperature_°C` column (rounded): sweeps 1–6 → T = 18, 20,
22, 24, 26, 28; sweep 7 → T = 18 (repeat) → sample id `T_18_repeat`. Samples are
ordered 18, 20, 22, 24, 26, 28, 18-repeat. `measurement.temperature_C` is null;
each sample carries its own `temperature_C`. Geometry "not reported".

**caggioni_carbopol_glycerin_temp** — from `docs/walkthrough/cp05_gly_newsample.json`.
"Flow sweep - 1" = 50 °C (first step) is **dropped** per the walkthrough's own
treatment; sweeps 2/3/4 → 40/30/20 °C kept, 51 points each, 0.001–100 s⁻¹.
Samples ordered T_20, T_30, T_40. Protocol from the walkthrough doc: equilibrium
flow sweeps on a Peltier plate with 200 s thermal soaks between temperature steps.
Geometry "not reported" (a Peltier plate is the temperature stage, not a verified
geometry).

## DOIs (all verified via web search, 2026-09-29)

| dataset | DOI |
|---|---|
| dinkgreve2015_fig2 | 10.1103/PhysRevE.92.012305 |
| ghosh2019_fig3 | 10.1039/c8sm02014k |
| mason1996_fig5 | 10.1006/jcis.1996.0235 |
| pamvouxoglou2021_fig6 | 10.1122/8.0000212 |
| paredes2013_fig1 | 10.1103/PhysRevLett.111.015701 |
| petekidis2004_fig5 | 10.1088/0953-8984/16/38/013 |
| seth2011_S4a / seth2011_S4b | 10.1038/nmat3119 |

## Validation

`/tmp/rheodata_selfcheck.py` passed: all 12 dataset dirs contain `data.csv` +
`dataset.yaml`; every yaml parses and carries the contract's required keys;
csv headers match the yaml `columns` mapping; x is sorted ascending within each
sample; no NaN/Inf/non-positive x or y values; sample ids are consistent between
csv and yaml.
