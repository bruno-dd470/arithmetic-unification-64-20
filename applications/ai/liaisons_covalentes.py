#!/usr/bin/env python3
# covalent_bonds_from_beta.py

import numpy as np
from itertools import combinations, product

# ============================================================
# Constantes universelles
# ============================================================
Lambda_e = 5.950   # eV

# Les 15 β
beta = np.array([
    0.066136959, 0.281751380, 0.555869353, 0.868248673,
    1.504114125, 1.725183114, 1.831271203, 2.017424480,
    2.092834951, 2.524926754, 3.279177783, 3.851497776,
    4.571886169, 4.724739150, 7.408061012
])

# ============================================================
# Génération des Δ ternaires
# ============================================================
def generate_delta_values(max_active=6):
    n = len(beta)
    deltas = []
    coeffs_list = []
    for k in range(1, max_active+1):
        for idx in combinations(range(n), k):
            for signs in product([-1, 1], repeat=k):
                coeff = np.zeros(n)
                for i, s in zip(idx, signs):
                    coeff[i] = s
                delta = np.dot(coeff, beta)
                if delta > 1e-12:
                    first = next(i for i in range(n) if coeff[i] != 0)
                    if coeff[first] < 0:
                        coeff = -coeff
                        delta = -delta
                    deltas.append(delta)
                    coeffs_list.append(coeff)
    order = np.argsort(deltas)
    return np.array(deltas)[order], [coeffs_list[i] for i in order]

print("Génération des combinaisons ternaires...")
delta_vals, coeffs_vals = generate_delta_values(max_active=6)
print(f"Nombre de Δ distincts : {len(delta_vals)}")

# ============================================================
# Recherche du meilleur (m, Δ) pour une énergie donnée
# ============================================================
def best_match(E, m_range=range(-5, 6)):
    best_err = float('inf')
    best_m = None
    best_delta = None
    best_coeff = None
    for m in m_range:
        factor = 4 ** m
        target = E / (Lambda_e * factor)
        if target < 0.01 or target > 20:
            continue
        idx = np.searchsorted(delta_vals, target)
        if idx == len(delta_vals):
            idx = len(delta_vals) - 1
        for candidate_idx in (idx, idx-1):
            if candidate_idx < 0 or candidate_idx >= len(delta_vals):
                continue
            delta = delta_vals[candidate_idx]
            pred = Lambda_e * factor * delta
            err = abs(pred - E) / E
            if err < best_err:
                best_err = err
                best_m = m
                best_delta = delta
                best_coeff = coeffs_vals[candidate_idx]
    return best_m, best_delta, best_coeff, best_err

def format_coeffs(coeff):
    parts = []
    for i, c in enumerate(coeff):
        if c != 0:
            parts.append(f"{'+' if c>0 else '-'}{i}")
    return ''.join(parts) if parts else '0'

# ============================================================
# Liaisons covalentes (énergie en eV)
# ============================================================
bonds = [
    ("H–H", 4.478),
    ("H–F", 5.837),
    ("H–Cl", 4.561),
    ("C–H", 4.340),
    ("C–C", 3.623),
    ("C=C", 6.351),
    ("C≡C", 8.648),
    ("N≡N", 9.917),
    ("O=O", 5.165),
    ("F–F", 1.602),
    ("Cl–Cl", 2.513),
    ("Br–Br", 1.943),
    ("I–I", 1.553),
]

print("\nRecherche des meilleurs ajustements pour les liaisons covalentes")
print(f"Λₑ = {Lambda_e:.3f} eV, m ∈ [-5,5]\n")
print(f"{'Liaison':<8} {'E_exp (eV)':>12} {'E_pred (eV)':>14} {'m':>3} {'Δ':>12} {'Err (%)':>10} {'ε actifs':>30}")
print("-" * 100)

for name, E_exp in bonds:
    m, delta, coeff, err = best_match(E_exp)
    if m is None:
        print(f"{name:<8} {E_exp:12.5f} {'--':>14} {'--':>3} {'--':>12} {'--':>10} {'--'}")
        continue
    E_pred = Lambda_e * (4**m) * delta
    err_pct = err * 100
    eps_str = format_coeffs(coeff)
    print(f"{name:<8} {E_exp:12.5f} {E_pred:14.6f} {m:3d} {delta:12.6f} {err_pct:9.5f}% {eps_str:30s}")