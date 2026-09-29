# 🤝 Contributing a dataset

`rheodata` grows the way good science grows: from the literature and from the
community. If you know a paper whose curves deserve a second life — or you have
your own measurements to share — here's how to get them into the registry.

## 1️⃣ Open a submission issue

Every dataset starts as a **GitHub issue** using the
[data submission template](https://github.com/rheopy/rheodata/issues/new?template=data-submission.md),
which carries the `data-submission` label.

At minimum the issue must give us:

- 📄 **Paper name** (title, authors, journal, year)
- 🔗 **DOI** — every dataset cites its source with a clickable DOI link, no exceptions
- 📊 Which **figure(s)** the data comes from

Anything else you know is welcome: the samples, the instrument, the geometry,
the temperature, the protocol. The more you tell us, the better the metadata
entry, and the more useful the dataset becomes.

A maintainer will then extract the data from the figures (digitized curves are
marked as such in the provenance record), tidy it up, and open a pull request
adding the dataset.

## 2️⃣ What good metadata looks like 🗂️

A dataset nobody can contextualize is a dataset nobody trusts. Every entry in
the registry documents:

- **Material** — name and kind (e.g. *Carbopol 940*, *yield-stress fluid*;
  *aqueous PEO*, *linear polymer solution*)
- **Source** — full citation of the paper plus a clickable DOI, and the figure
  the data was taken from
- **Measurement** — the experiment *type* (flow curve, frequency sweep, …),
  the **geometry** (cone–plate, parallel plate, Couette, capillary, …) with
  details when they matter (cone angle and diameter, gap, bob radius),
  the **temperature** in °C, and the **protocol** (pre-shear, equilibration
  time, sweep direction, points per decade…)
- **Samples** — one row per curve: sample id and a human-readable label
- **Provenance** — *literature* (digitized from a published figure) or
  *community* (contributed directly), and whether the numbers are digitized

If a field is genuinely unknown, it stays empty rather than guessed — an
honest gap beats a fabricated detail.

## 3️⃣ Tidy-CSV rules 📋

Every dataset ships its numbers as tidy CSV files — one row per observation —
and must follow these rules before it is accepted:

1. **SI units, always.** Shear rate in s⁻¹, shear stress in Pa, viscosity in
   Pa·s, temperature in °C, moduli in Pa, frequency in rad·s⁻¹. No mPa, no
   cP, no hidden factors.
2. **x sorted.** Within each sample, rows are sorted by the independent
   variable (shear rate, frequency, …) in ascending order.
3. **No NaNs.** Missing values are not allowed; a row with a NaN is a row
   that shouldn't exist.
4. **One header row** with snake_case column names (`shear_rate`,
   `shear_stress`, `viscosity`, …).
5. **UTF-8, comma-separated**, Unix line endings.

## 4️⃣ The `dataset.yaml` schema 📐

Each dataset directory (`rheodata/datasets/<id>/`) carries a `dataset.yaml`
that describes the dataset. Every field:

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `id` | string | ✅ | Short slug identifying the dataset, e.g. `carbopol_caggioni_2020`. Used in `load(id)` / `plot(id)` and as the page filename. |
| `title` | string | ✅ | Human-readable title shown on the dataset page. |
| `description` | string | ✅ | One or two sentences: what the data shows and why it's interesting. |
| `material.name` | string | ✅ | Material name, e.g. `Carbopol 940`. |
| `material.kind` | string | ✅ | Material class, e.g. `yield-stress fluid`, `linear polymer solution`, `wormlike micelles`. |
| `source.paper.title` | string | ✅ | Paper title. |
| `source.paper.authors` | list of strings | ✅ | Authors in order. |
| `source.paper.journal` | string | ✅ | Journal name. |
| `source.paper.year` | integer | ✅ | Publication year. |
| `source.paper.doi` | string | ✅ | DOI (bare, e.g. `10.1122/1.5120633`) — rendered as a clickable link on the dataset page. |
| `source.figure` | string | ✅ | Figure the data was taken from, e.g. `Figure 3`. |
| `provenance.origin` | string | ✅ | `literature` or `community`. |
| `provenance.digitized` | boolean | ✅ | `true` if the numbers were digitized from a figure; `false` for directly contributed data. |
| `measurement.type` | string | ✅ | Experiment type: `flow curve`, `frequency sweep`, `amplitude sweep`, … |
| `measurement.geometry` | string | ✅ | Geometry, e.g. `cone–plate`, `parallel plate`, `Couette`, `capillary`. |
| `measurement.geometry_details` | string | | Details that matter: cone angle/diameter, gap, bob radius, … |
| `measurement.temperature_C` | number | ✅ | Measurement temperature in °C. |
| `measurement.protocol` | string | | Protocol notes: pre-shear, equilibration, sweep direction, points per decade, … |
| `samples` | list of `{id, label}` | ✅ | One entry per curve: a short `id` and a human-readable `label` (e.g. concentration, temperature). |
| `columns` | list of `{name, description}` | | Documents every CSV column and its units — this is what users see in the *Data columns* table. |
| `tags` | list of strings | | Search tags, e.g. `yield stress`, `temperature series`, `thixotropy`. |

## 5️⃣ What happens next 🔄

A maintainer turns the issue into a pull request: tidy CSVs, the
`dataset.yaml`, and the registry entry. The docs build then generates the
dataset's page (metadata table, samples, preview plot) automatically. Once
merged, the dataset is live in the catalog and loadable with
`rheodata.load("<id>")`.
