# 🌊 rheodata

**Quality rheology data, curated for the age of simulation and AI.**

`rheodata` is a growing collection of rheological datasets — flow curves, linear
viscoelastic spectra, and more — gathered from the **literature** and from the
**community**, cleaned and standardized so you can load a dataset with one
function call and get on with the science.

Good models are trained on good data, and good models are *tested* on good data
too. Machine-learning surrogates need large, tidy training sets; constitutive
models need independent curves to benchmark against; researchers need
reproducible numbers they can cite. `rheodata` exists to be that shared,
trusted ground: every dataset ships with its full provenance — the paper, the
figure it was digitized from, the geometry, the temperature, the protocol —
so you always know exactly what you're looking at. 🔬

## 📦 Installation

```bash
pip install rheodata
```

## 🚀 Quickstart

```python
import rheodata

rheodata.list()        # what's in the registry?
df = rheodata.load("carbopol_2020")   # tidy pandas DataFrame (SI units)
rheodata.plot("carbopol_2020")        # take a look
```

The catalog below has one page per dataset — metadata, samples, column schema,
and a preview plot.

## 🤝 Contribute

Found a paper whose data should live here? Have data of your own to share?
Read **[Contributing a dataset](contributing)** — submissions arrive as a GitHub
issue with a DOI, and the bar is simple: tidy CSVs in SI units with complete
metadata.

```{toctree}
:maxdepth: 2
:caption: Datasets

datasets/index
```

```{toctree}
:maxdepth: 2
:caption: Contribute

contributing
```

```{toctree}
:maxdepth: 2
:caption: Reference

api
```
