#!/usr/bin/env python3
# test_beta_electronic_shell.py
# Recherche d'un facteur d'échelle universel Λ_e tel que
# E_ion ≈ Λ_e * (ε·β) avec ε_k ∈ {-1,0,1} et β_k les 15 racines fondamentales.

import numpy as np
from itertools import combinations, product
import sys

# ============================================================================
# 1. Les 15 β_k (échelle nucléaire, sans dimension)
# ============================================================================
beta = np.array([
    0.066136959, 0.281751380, 0.555869353, 0.868248673,
    1.504114125, 1.725183114, 1.831271203, 2.017424480,
    2.092834951, 2.524926754, 3.279177783, 3.851497776,
    4.571886169, 4.724739150, 7.408061012
])

# ============================================================================
# 2. Énergies d'ionisation expérimentales (eV) pour les premiers éléments
# Source : NIST (valeurs standard)
# ============================================================================
ionization = {
    1: 13.59844,   # H
    2: 24.58741,   # He
    3: 5.39172,    # Li
    4: 9.32270,    # Be
    5: 8.29803,    # B
    6: 11.26030,   # C
    7: 14.53414,   # N
    8: 13.61806,   # O
    9: 17.42282,   # F
    10: 21.56454,  # Ne
    11: 5.13908,   # Na
    12: 7.64624,   # Mg
    # On peut ajouter Al, Si, ... mais on se limite aux 12 premiers pour l'exemple
}

# ============================================================================
# 3. Génération de toutes les combinaisons ternaires (ε·β) avec ε ∈ {-1,0,1}
# On limite le nombre de coefficients non nuls à max_active (ici 6).
# On ne conserve que les valeurs Δ positives (en prenant la valeur absolue
# et en normalisant le signe du premier coefficient non nul).
# ============================================================================
def generate_delta_values(max_active=6):
    n = len(beta)
    deltas = []            # liste des valeurs Δ = ε·β (>0)
    coeffs_list = []       # vecteur ε correspondant (avec signe normalisé)
    
    # Parcourir toutes les combinaisons d'indices actifs (k de 1 à max_active)
    for k in range(1, max_active+1):
        for idx in combinations(range(n), k):
            # Pour un ensemble d'indices fixé, parcourir tous les signes
            for signs in product([-1, 1], repeat=k):
                coeff = np.zeros(n)
                for i, s in zip(idx, signs):
                    coeff[i] = s
                delta = np.dot(coeff, beta)
                # On ne garde que les valeurs strictement positives
                if delta > 0:
                    # Normalisation : s'assurer que le premier coefficient non nul est positif
                    # (pour éviter les doublons ε et -ε)
                    first_idx = next(i for i in range(n) if coeff[i] != 0)
                    if coeff[first_idx] < 0:
                        coeff = -coeff
                        delta = -delta   # delta reste positif
                    deltas.append(delta)
                    coeffs_list.append(coeff)
    # Trier par ordre croissant pour faciliter la recherche dichotomique
    order = np.argsort(deltas)
    deltas_sorted = np.array(deltas)[order]
    coeffs_sorted = [coeffs_list[i] for i in order]
    return deltas_sorted, coeffs_sorted

print("Génération des combinaisons ternaires (cela peut prendre quelques secondes)...")
delta_vals, coeffs_vals = generate_delta_values(max_active=6)
print(f"Nombre de Δ distincts retenus : {len(delta_vals)}")

# ============================================================================
# 4. Recherche du meilleur Λ_e universel
# On balaye Λ_e de 5 à 30 eV par pas de 0.05 eV.
# Pour chaque Λ_e, on associe à chaque élément le Δ le plus proche de E/Λ_e
# (recherche dichotomique). On calcule l'erreur quadratique moyenne.
# ============================================================================
def best_match(target, deltas):
    """Retourne l'indice du Δ le plus proche de target."""
    idx = np.searchsorted(deltas, target)
    if idx == 0:
        return 0
    if idx == len(deltas):
        return len(deltas)-1
    if abs(deltas[idx] - target) < abs(deltas[idx-1] - target):
        return idx
    else:
        return idx-1

def evaluate_Lambda(Lambda_e, deltas, E_dict):
    total_sq_err = 0.0
    for Z, E in E_dict.items():
        target = E / Lambda_e
        idx = best_match(target, deltas)
        delta_best = deltas[idx]
        E_pred = Lambda_e * delta_best
        total_sq_err += (E_pred - E)**2
    return total_sq_err

Lambda_candidates = np.arange(5.0, 30.05, 0.05)
best_Lambda = None
best_err = float('inf')

print("\nRecherche de Λ_e optimal...")
for Lam in Lambda_candidates:
    err = evaluate_Lambda(Lam, delta_vals, ionization)
    if err < best_err:
        best_err = err
        best_Lambda = Lam

print(f"\n✅ Meilleur Λ_e trouvé : {best_Lambda:.3f} eV")
print(f"   Erreur quadratique totale : {best_err:.6f} eV²")
print(f"   Écart quadratique moyen : {np.sqrt(best_err/len(ionization)):.5f} eV")

# ============================================================================
# 5. Affichage des résultats par élément
# ============================================================================
print("\nRésultats détaillés :")
print(" Z | Élément | E_exp (eV) | E_pred (eV) | Δ utilisé | ε actifs")
print("---|---------|------------|-------------|-----------|----------")
for Z in sorted(ionization.keys()):
    E_exp = ionization[Z]
    target = E_exp / best_Lambda
    idx = best_match(target, delta_vals)
    delta_best = delta_vals[idx]
    E_pred = best_Lambda * delta_best
    err_rel = 100 * abs(E_pred - E_exp) / E_exp
    coeffs = coeffs_vals[idx]
    active_str = " ".join(f"{int(c):+d}" for c in coeffs if c != 0)
    print(f"{Z:2d} | {ionization[Z]:>5.2f} | {E_pred:>10.4f} | {E_exp:>10.4f} | {err_rel:6.2f}% | {active_str}")