[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc/4.0/)
[![DOI](https://zenodo.org/badge/1284323833.svg)](https://doi.org/10.5281/zenodo.21044905)
[![Clones](https://img.shields.io/badge/Clones-View%20on%20GitHub-blue?logo=github)](https://github.com/bruno-dd470/arithmetic-unification-64-20/graphs/traffic)


# A Unique Arithmetic for Three Ontologies: Matter, Life, and Information

**一种适用于三种本体（物质、生命与信息）的统一算术**

---

## 📖 Overview

This repository provides the complete data, code, and results accompanying the paper:

> **A Unique Arithmetic for Three Ontologies: Matter, Life, and Information**  
> *Validation of a Universal Law Across Seven Domains, from Nuclear Physics to Artificial Intelligence — Hydrodynamic, Algebraic, and Arithmetic Foundations via Exceptional Networks*  
> Bruno De Dominicis (June 2026)

**中文摘要**：本文提出一种统一物理、生物与信息科学的普遍算术定律。该定律以三元组合的形式表达任何质量或能量，从原子核到ATP水解，包括半导体带隙，均由15个普适常数 βₖ 调制。

We present a universal arithmetic law that unifies physics, biology, and information sciences:

$$E = \Lambda \cdot 4^{m} \cdot \sum_{k=0}^{14} \varepsilon_k \beta_k, \qquad \varepsilon_k \in \{-1, 0, 1\}$$

It expresses any mass or energy — from the atomic nucleus to ATP hydrolysis, including semiconductor band gaps — as a ternary combination of 15 universal constants $\beta_k$, modulated by a scale factor $\Lambda \cdot 4^m$.

---

## 📄 Paper

| Language | Markdown | PDF |
|:---|:---|:---|
| **English** | [article_A_H_R_N_v3_EN.md](article/article_A_H_R_N_v3_EN.md) | [article_A_H_R_N_v3_EN.pdf](article/article_A_H_R_N_v3_EN.pdf) |
| **French** | [article_A_H_R_N_v3_FR.md](article/article_A_H_R_N_v3_FR.md) | [article_A_H_R_N_v3_FR.pdf](article/article_A_H_R_N_v3_FR.pdf) |

---

## 🔬 Key Results

| Domain | Data points | Precision | Key Result |
|--------|-------------|-----------|------------|
| Nuclear masses (AME2020) | 295 isotopes | 0.0287% | 100% of isotopes < 0.2% error |
| Ionization energies (NIST) | 5,811 values | 0.00065% | 80% < 0.001% error |
| Covalent bonds | 6 bonds | < 0.001% | Same βₖ as nuclear masses |
| DNA base pairs (A-T, G-C) | 2 | < 0.001% | G-C/A-T ratio = 1.485 |
| Protein interactions | 4 types | < 0.003% | Energy hierarchy reproduced |
| Semiconductor band gaps | 5 materials | < 0.0015% | Ge/ATP spectral isomorphism |
| Neural network initialization | 10 runs | +2.1% accuracy | Variance reduced by 42% |

---

## 📁 Repository Structure

```
arithmetic-unification-64-20/
├── article/                    # Papers and publication files
│   ├── article_A_H_R_N_v3_EN.md     # English version
│   ├── article_A_H_R_N_v3_FR.md     # French version
│   ├── article_A_H_R_N_v3_EN.pdf
│   ├── article_A_H_R_N_v3_FR.pdf
│   ├── references.bib
│   ├── template_FR.tex
│   └── ieee.csl
│
├── code/                       # Code for reproducing the paper
│   ├── scripts/                # Core scripts
│   │   ├── extract_ame2020.py
│   │   ├── randomization_test.py
│   │   ├── cross_validation_final.py
│   │   ├── graphe_dual_pentades.py
│   │   ├── DSM-861_v3.py
│   │   ├── dirac_pentades_approfondi.py
│   │   ├── distances_merkabah.py
│   │   ├── frequences_DSM861_affine.py
│   │   ├── test_paires_beta_k_disq.py
│   │   └── analyse_orbites_2O_correct.py
│   ├── applications/           # Domain-specific applications
│   │   ├── nuclear/            # Nuclear masses (AME2020)
│   │   ├── atomic/             # Ionization energies (NIST)
│   │   └── ai/                 # Neural network experiments
│   └── figures/                # Figures from the paper
│       ├── Penta_graph.png
│       ├── tore_DSM.png
│       ├── IA_accuracy_loss.png
│       └── isotope_errors.png
│
├── exploration/                # Exploratory work (archives)
│   ├── nuclear/
│   ├── atomic/
│   ├── ai/
│   ├── quadratic_fields/
│   ├── docs/
│   └── scripts_old/
│
├── data/                       # Data
│   ├── raw/                    # Raw experimental data
│   └── processed/              # Processed data and results
│
├── README.md
├── LICENSE
├── CITATION.cff
├── requirements.txt
└── .gitignore
```

---

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/bruno-dd470/arithmetic-unification-64-20.git
cd arithmetic-unification-64-20

# Install dependencies
pip install -r requirements.txt

# Run nuclear mass fits
python code/applications/nuclear/isotopes4.py

# Run ionization energy fits
python code/applications/atomic/ionisations_successives3.py

# Run neural network experiments
python code/applications/ai/cross_validation_final.py

# Generate visualizations
python code/scripts/graphe_dual_pentades.py
python code/scripts/DSM-861_v3.py
```

---

## 📦 Dependencies

```bash
pip install numpy pandas matplotlib scikit-learn networkx
```

- **SageMath** (optional, for quadratic field calculations in `exploration/quadratic_fields/`)

---

## 📊 Validation Results

| Test | Result | Significance |
|------|--------|--------------|
| 5-fold cross-validation | Train/test deviation < 10⁻⁶% | No overfitting |
| Monte Carlo (10,000 random sets) | 0/10,000 beats nuclear masses | p < 3 × 10⁻¹⁰ |
| Clifford centroid multiplicativity | 87.6% success rate | p < 10⁻¹⁵ |
| Exponential Dirac spectral relation | R² = 0.9563 | Strong structural link |

---

## 🔮 Predictions

The repository includes predictions for:

- **Superheavy isotopes** (Ds-279, Ds-280, Rg-282)
- **First ionization energies** for elements Z = 105 to 110
- **Semiconductor band gaps** for SiC (3C), AlN, ZnO

See `data/processed/` for complete tables.

---

## 📝 Citation

```bibtex
@article{DeDominicis_2026,
  title = {A Unique Arithmetic for Three Ontologies: Matter, Life, and Information},
  author = {De Dominicis, Bruno},
  year = {2026},
  doi = {10.5281/zenodo.21044906}
}
```

---

## 📄 License

[![License: CC BY-NC 4.0](https://licensebuttons.net/l/by-nc/4.0/88x31.png)](https://creativecommons.org/licenses/by-nc/4.0/)

This work is licensed under a **Creative Commons Attribution-NonCommercial 4.0 International License**.

---

## 🙏 Acknowledgments

- **Peter Rowlands** and **Vanessa Hill** — nilpotent Clifford algebras and the genetic code
- **David Hestenes** — Spacetime Algebra (STA) and the zitterbewegung model
- **Mikhail I. Aksman** — vortons, DSM-861 network, hydrodynamic compactification
- **Gabriele Nebe** — exceptional lattice Λ₇₂
- **Tobias Braun** — Clifford centroids

---

## 📧 Contact

For questions, please open an issue on GitHub.
