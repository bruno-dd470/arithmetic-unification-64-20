#!/usr/bin/env python3
# particle_masses_from_beta.py

import numpy as np
from itertools import combinations, product

# ============================================================
# 1. Constantes universelles
# ============================================================
Lambda_MeV = 7.726   # MeV (échelle nucléaire/particulaire)

# Les 15 β (issus du réseau Λ72)
beta = np.array([
    0.066136959, 0.281751380, 0.555869353, 0.868248673,
    1.504114125, 1.725183114, 1.831271203, 2.017424480,
    2.092834951, 2.524926754, 3.279177783, 3.851497776,
    4.571886169, 4.724739150, 7.408061012
])

# ============================================================
# 2. Génération de toutes les combinaisons ternaires Δ = ε·β
#    avec ε ∈ {-1,0,1} et jusqu'à max_active coefficients non nuls.
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
                    # Normalisation : premier coefficient non nul >0
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
# 3. Recherche du meilleur (m, Δ) pour une masse donnée
# ============================================================
def best_match(mass, m_range=range(-5, 11)):
    best_err = float('inf')
    best_m = None
    best_delta = None
    best_coeff = None
    for m in m_range:
        factor = 4 ** m
        target = mass / (Lambda_MeV * factor)
        if target < 0.01 or target > 20:
            continue
        idx = np.searchsorted(delta_vals, target)
        if idx == len(delta_vals):
            idx = len(delta_vals) - 1
        for candidate_idx in (idx, idx-1):
            if candidate_idx < 0 or candidate_idx >= len(delta_vals):
                continue
            delta = delta_vals[candidate_idx]
            pred = Lambda_MeV * factor * delta
            err = abs(pred - mass) / mass
            if err < best_err:
                best_err = err
                best_m = m
                best_delta = delta
                best_coeff = coeffs_vals[candidate_idx]
    return best_m, best_delta, best_coeff, best_err

# ============================================================
# 4. Formatage des coefficients ε
# ============================================================
def format_coeffs(coeff):
    parts = []
    for i, c in enumerate(coeff):
        if c != 0:
            parts.append(f"{'+' if c>0 else '-'}{i}")
    return ''.join(parts) if parts else '0'

# ============================================================
# 5. Liste des particules (nom, masse en MeV)
#    Valeurs moyennes PDG 2024
# ============================================================
particles = [
    ("e⁻ (electron)",      0.5109989461),
    ("μ⁻ (muon)",        105.6583745),
    ("τ⁻ (tau)",        1776.86),
    ("ν_e (electron neutrino)", 0.0),      # quasi nul, on ignore
    ("ν_μ (muon neutrino)",    0.0),
    ("ν_τ (tau neutrino)",      0.0),
    ("π⁰ (pion neutral)",     134.9768),
    ("π⁺ (pion charged)",     139.57039),
    ("K⁰ (kaon short)",       497.611),
    ("K⁺ (kaon)",             493.677),
    ("η (eta)",               547.862),
    ("ρ (rho)",               775.26),
    ("ω (omega)",             782.65),
    ("φ (phi)",              1019.461),
    ("J/ψ",                  3096.9),
    ("Υ (upsilon)",          9460.30),
    ("p (proton)",           938.272088),
    ("n (neutron)",          939.565420),
    ("Λ (lambda)",          1115.683),
    ("Σ⁺ (sigma)",          1189.37),
    ("Ξ⁻ (cascade)",        1321.71),
    ("Ω⁻ (omega)",          1672.45),
    ("W⁺ (W boson)",       80379.0),
    ("Z⁰ (Z boson)",       91237.6),
    ("H (Higgs)",         125250.0),
]

# ============================================================
# 6. Exécution et affichage
# ============================================================
print("\nRecherche des meilleurs ajustements pour les particules élémentaires")
print(f"Λ = {Lambda_MeV:.3f} MeV, m ∈ [-5,10]\n")
print(f"{'Particule':<20} {'Masse (MeV)':>12} {'M_pred (MeV)':>14} {'m':>3} {'Δ':>12} {'Err (%)':>10} {'ε actifs':>30}")
print("-" * 110)

for name, mass in particles:
    if mass <= 0:
        print(f"{name:<20} {mass:12.3f} {'--':>14} {'--':>3} {'--':>12} {'--':>10} {'--'}")
        continue
    m, delta, coeff, err = best_match(mass)
    pred = Lambda_MeV * (4**m) * delta
    err_pct = err * 100
    eps_str = format_coeffs(coeff)
    print(f"{name:<20} {mass:12.6f} {pred:14.6f} {m:3d} {delta:12.6f} {err_pct:9.5f}% {eps_str:30s}")