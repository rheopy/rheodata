# rheodata 📊

**Curated, quality-checked rheology datasets — for training, simulation, and benchmarking.**

Machine learning on rheology is starving for data it can trust. Raw curves scraped from the
internet arrive with unknown geometries, missing temperatures, unlabelled units, and figures
digitised without a record of it. A dataset you cannot trust is worse than no dataset at all —
it launders its own uncertainty into your conclusions.

`rheodata` fixes the supply side: a pip-installable library of experimental rheology datasets
where every dataset carries its **provenance** (native instrument values vs digitised from a
published figure), its **measurement record** (geometry, temperature, protocol, units), and its
**citation** (source paper + DOI). Nothing enters the catalog without passing schema and data
validation — sorted shear rates, no NaNs, sample ids that match the metadata.

🔍 **Discover** — `rheodata.search(material="carbopol", experiment="flow_curve")`
📖 **Inspect** — `rheodata.info(id)` prints material, paper + clickable DOI, figure, measurement, samples
📦 **Load** — `rheodata.load(id)` gives a tidy DataFrame plus the full metadata dict
📈 **Plot** — `rheodata.plot(id)` draws the experiment-appropriate figure (twin-axis flow curves, G′/G″ sweeps, …)
🔧 **Fit** — `rheodata.to_rheofit(id, sample)` hands a flow curve to [rheofit](https://github.com/rheopy/rheofit) in exactly the shape it expects

## Quickstart

```bash
pip install rheopy-rheodata
```

```python
import rheodata

rheodata.list()                                   # every dataset, one row each
rheodata.search(material="carbopol")              # substring filters, case-insensitive
rheodata.search(experiment="flow_curve", tag="yield-stress")
rheodata.search(query="wormlike micelles")        # title / description / material

rheodata.info("caggioni_pg_carbopol_2pct")                 # readable summary + DOI link

ds = rheodata.load("caggioni_pg_carbopol_2pct")
ds.df.head()                                      # tidy data
ds.meta["measurement"]                            # type, geometry, temperature, protocol

fig = rheodata.plot("caggioni_pg_carbopol_2pct")           # one curve per sample
fig.savefig("caggioni_pg_carbopol_2pct.png")

fit_df = rheodata.to_rheofit("caggioni_pg_carbopol_2pct", sample="carbopol_2pct")
# → DataFrame with "Shear rate / 1/s" and "Stress / Pa", x sorted ascending
```

The CLI mirrors the API:

```bash
rheodata list
rheodata search --material Carbopol --experiment flow_curve
rheodata info caggioni_pg_carbopol_2pct
rheodata install-skill            # install the data-discovery agent skill
```

## How a dataset is stored

Each dataset is a directory `rheodata/datasets/<id>/` with two files:

- **`dataset.yaml`** — title, description, material, source paper + DOI, figure, provenance
  origin, measurement (type, geometry, temperature, details, protocol), the sample table,
  the `columns:` mapping (csv headers may carry units), and tags.
- **`data.csv`** — tidy data: one row per measurement point, column names from the yaml.

On import, the registry validates every dataset: required metadata keys, DOI shape
(`^10\.\S+/\S+`), csv columns matching the yaml, numeric x sorted ascending per sample, no
NaNs in x/y, and sample ids matching the metadata. A dataset that fails validation fails
loudly, naming the dataset — corrupt data never loads silently.

## Citing

Always cite the **source paper**, not just the package. Every dataset's metadata carries its
paper and DOI — `rheodata.info(id)` prints a clickable link. If you publish work built on
rheodata datasets, cite the papers and mention `rheodata` as the source of the curated files.

## Contributing

New datasets are curated through the GitHub issue workflow: open an issue on the
[rheodata repository](https://github.com/rheopy/rheodata) with the source paper or data file
and the proposed metadata. Please don't invent dataset ids or commit data yourself — curation
keeps the catalog trustworthy. See `docs` (link below) for the contributor guide.

## Documentation

Full documentation lives at the [rheodata docs site](https://github.com/rheopy/rheodata#readme)
(wired up separately) — including the dataset schema reference, the contributor guide, and the
API reference.

## License

MIT — see [LICENSE](LICENSE).
