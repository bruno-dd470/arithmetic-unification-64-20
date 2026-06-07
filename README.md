[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

# Arithmetic unification of masses and energies via the exceptional lattice Λ₇₂

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20042320.svg)](https://doi.org/10.5281/zenodo.20042320)

## Overview

This repository provides the complete data, code, and results accompanying the paper:

> **Arithmetic unification of masses and energies in physics, chemistry, biology and artificial intelligence via the exceptional lattice Λ₇₂**  
> Bruno De Dominicis (May 2026)

Experimental data for atomic masses (AME2020), ionization energies (NIST), covalent bond energies, semiconductor band gaps, DNA base pairs, protein interactions, and even neural network training admit a compact arithmetic representation:

$$E = \Lambda \cdot 4^{m} \cdot \sum_{k=0}^{14} \epsilon_k \beta_k$$

where $\Lambda$ is a scale constant, $m$ an integer, $\epsilon_k \in \{-1,0,1\}$, and $\beta_k$ are 15 universal constants that numerically coincide with 15 of the 48 non-degenerate roots of the exceptional lattice $\Lambda_{72}$ (Nebe, 2010).

## Key results

| Domain | Data points | Precision |
|--------|-------------|-----------|
| Nuclear masses (AME2020) | 295 isotopes | 0.0287% |
| Ionization energies (NIST) | 5,811 values | 0.00065% |
| Covalent bonds | 6 bonds | < 0.001% |
| DNA base pairs | A-T, G-C | < 0.001% |
| Protein interactions | 4 types | < 0.001% |
| Semiconductor band gaps | 5 materials | < 0.0015% |
| Neural network initialization | 10 runs | +2.1% accuracy |

## Repository structure

```
mass_unification_L72_git/
├── article/               # Paper (EN/FR) and references
├── data/
│   ├── raw/              # Raw experimental data (AME2020, NIST)
│   └── processed/        # Cleaned data and β_k constants
├── scripts/               # Core Python scripts
├── applications/          # Domain-specific analyses
│   ├── ai/               # Neural network experiments
│   ├── atomic/           # Ionization energies
│   ├── nuclear/          # Nuclear masses
│   ├── chemistry/        # Covalent bonds (to be populated)
│   ├── biology/          # DNA, proteins (to be populated)
│   └── electronics/      # Band gaps (to be populated)
├── docs/                  # Markdown documentation
├── quadratic_fields/      # SageMath Q(√2) calculations
├── results/               # Output tables and predictions
└── lattice72/             # Λ72 lattice root data
```

## Quick start

```bash
# Clone the repository
git clone https://github.com/your-username/mass-unification-L72.git
cd mass-unification-L72

# Install dependencies
pip install -r requirements.txt

# Run nuclear mass fits
python scripts/isotopes4.py

# Run ionization energy fits
python applications/atomic/ionisations_successives3.py

# Run neural network initialization comparison
python applications/ai/cross_validation_final.py
```

## Dependencies

- Python 3.8+
- numpy, pandas, matplotlib, scikit-learn
- SageMath (for quadratic field calculations)

## Predictions

The repository includes predictions for:
- Superheavy isotopes (Ds-279, Ds-280, Rg-282)
- First ionization energies for elements Z = 105 to 110 (Db, Sg, Bh, Hs, Mt, Ds)

See `results/predictions/` for complete tables.

## Citation

If you use this work, please cite:

```bibtex
@article{DeDominicis2026,
  title = {Arithmetic unification of masses and energies in physics, chemistry, biology and artificial intelligence via the exceptional lattice $\Lambda_{72}$},
  author = {De Dominicis, Bruno},
  year = {2026},
  doi = {10.5281/zenodo.20042320}
}
```

## License

[Specify your license here, e.g., MIT, CC-BY-NC, etc.]

## References

- Huang et al., Chinese Physics C 45, 030002 (2021) - AME2020
- NIST Atomic Spectra Database
- Nebe, G. (2010) - Exceptional lattices
- Rowlands, P. (2007) - Zero to Infinity

## Related work

- **Nebe, G. (2010)** - *An even unimodular 72-dimensional lattice of minimum 8*  
  arXiv:1008.2862 | [DOI: 10.48550/arXiv.1008.2862](https://doi.org/10.48550/arXiv.1008.2862)
  
  This paper constructs the exceptional lattice Λ72, whose 48 non-degenerate roots numerically coincide with our 15 β_k constants.

## Contact

For questions or collaboration, please open an issue on GitHub.

