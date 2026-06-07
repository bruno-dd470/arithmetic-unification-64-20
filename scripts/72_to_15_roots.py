#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de comparaison : βₖ vs √λᵢ (racines des valeurs propres de Λ₇₂)
Les 72 valeurs du tableau sont les λᵢ (valeurs propres), pas leurs racines.
"""

import numpy as np
import pandas as pd

# =============================================================================
# 1. DONNÉES : 72 valeurs propres λᵢ du tableau (18 lignes × 4 colonnes)
# =============================================================================
lambda_values = np.array([
    [0.0043740973516556257583, 0.12970492710948967363, 1.9272159835255295502, 9.9708989763601574938],
    [0.0043740973516556258844, 0.15135542346526064350, 2.1304098745750085324, 9.9708989763601574952],
    [0.010995546215077851813, 0.15135542346526064357, 2.1304098745750085327, 9.9747326396419946309],
    [0.010995546215077851848, 0.18224233526029199232, 2.2623588346586941297, 10.750743903593353286],
    [0.011197776487850081092, 0.29097785324761605221, 2.5057407355677230608, 10.816291213992858611],
    [0.018306563103388413523, 0.29097785324761605252, 2.9765210070356088852, 10.816291213992858612],
    [0.018306563103388413687, 0.30899131433464432369, 3.3535422310737084466, 14.833876891400130416],
    [0.029576322793137380691, 0.37392327826684409393, 3.3535422310737084469, 14.833876891400130420],
    [0.037359874463993147761, 0.39492892060870845764, 3.3910324700320243714, 20.899130218355758941],
    [0.037359874463993147996, 0.39492892060870845765, 3.5772428437732089992, 22.323167047337420512],
    [0.047227060779061605995, 0.52822943431040091584, 4.0699946798773017446, 22.610473853320698014],
    [0.063356180109664584017, 0.61409034101999347408, 4.0699946798773017447, 22.610473853320698025],
    [0.063356180109664584215, 0.61409034101999347415, 4.3799668875911968964, 35.319193889558946140],
    [0.079378841213435711453, 0.75384755659699768997, 5.3111753784848464945, 35.319193889558946146],
    [0.079378841213435712007, 0.80065628469062346170, 5.3111753784848464965, 54.877918027729634123],
    [0.095442748560291922283, 0.80065628469062346178, 6.3752579403535408666, 54.877918027729634137],
    [0.11732778393430706981, 0.80089328381005198496, 8.4757579813397957892, 65.647359292863189710],
    [0.11732778393430706997, 1.3956134502248842121, 8.4757579813397957895, 65.647359292863189714]
])

# Aplatissement et calcul des racines carrées √λᵢ
lambda_flat = lambda_values.flatten()
sqrt_lambda = np.sqrt(lambda_flat)  # ← ÉTAPE CRUCIALE : racine carrée des λᵢ

print(f"[INFO] 72 valeurs propres λᵢ → {len(sqrt_lambda)} racines √λᵢ calculées")
print(f"[INFO] Plage des √λᵢ : [{sqrt_lambda.min():.6f}, {sqrt_lambda.max():.6f}]")

# =============================================================================
# 2. FILTRAGE DES RACINES NON DÉGÉNÉRÉES (regroupement à tolérance près)
# =============================================================================
# Les vecteurs minimaux de Λ₇₂ apparaissent par paires opposées → mêmes √λᵢ
# On regroupe les valeurs très proches pour isoler les ~48 racines distinctes
sorted_sqrt = np.sort(sqrt_lambda)
non_degenerate = []
tol_group = 1e-10  # tolérance de regroupement

for val in sorted_sqrt:
    if not non_degenerate or abs(val - non_degenerate[-1]) > tol_group:
        non_degenerate.append(val)

print(f"[INFO] {len(sqrt_lambda)} racines brutes → {len(non_degenerate)} racines non dégénérées")

# =============================================================================
# 3. COMPARAISON AVEC LES 15 βₖ DE RÉFÉRENCE (Tableau III)
# =============================================================================
beta_ref = np.array([
    0.066136959, 0.281751380, 0.555869353, 0.868248673, 1.504114125,
    1.725183114, 1.831271203, 2.017424480, 2.092834951, 2.524926754,
    3.279177783, 3.851497776, 4.571886169, 4.724739150, 7.408061012
])

# Tolérance de correspondance (ajustable)
TOLERANCE = 1e-4

matches = []
for k, b_target in enumerate(beta_ref):
    diffs = np.abs(np.array(non_degenerate) - b_target)
    idx_min = np.argmin(diffs)
    err_rel = diffs[idx_min] / b_target if b_target != 0 else diffs[idx_min]
    
    if err_rel < TOLERANCE:
        matches.append({
            'k': k,
            'beta_ref': b_target,
            'sqrt_lambda_value': non_degenerate[idx_min],
            'lambda_value': non_degenerate[idx_min]**2,
            'error_rel': err_rel,
            'error_abs': diffs[idx_min]
        })

# =============================================================================
# 4. RÉSULTATS & EXPORT
# =============================================================================
print("\n" + "="*70)
print("CORRESPONDANCES βₖ ↔ √λᵢ (racines des valeurs propres de Λ₇₂)")
print("="*70)

if matches:
    df = pd.DataFrame(matches)
    print(df.to_string(index=False, float_format='%.9f'))
    df.to_csv("beta_k_vs_sqrt_lambda_matches.csv", index=False)
    print(f"\n[OK] {len(matches)}/15 βₖ retrouvés avec erreur relative < {TOLERANCE:.0e}")
    print("[EXPORT] Résultats exportés dans 'beta_k_vs_sqrt_lambda_matches.csv'")
else:
    print(f"[WARN] Aucune correspondance trouvée avec tolérance = {TOLERANCE:.0e}")
    print("       → Essayez d'augmenter la tolérance ou de vérifier l'échelle des λᵢ.")

# =============================================================================
# 5. OPTION : Afficher les meilleures correspondances sans seuil
# =============================================================================
print("\n" + "-"*70)
print("TOP 3 DES MEILLEURES CORRESPONDANCES POUR CHAQUE βₖ (sans seuil)")
print("-"*70)

for k, b_target in enumerate(beta_ref):
    diffs = np.abs(np.array(non_degenerate) - b_target)
    idx_sorted = np.argsort(diffs)[:3]
    
    print(f"\nβ_{k:2d} = {b_target:.9f} :")
    for rank, idx in enumerate(idx_sorted, 1):
        err_abs = diffs[idx]
        err_rel = err_abs / b_target if b_target != 0 else err_abs
        print(f"  {rank}. √λ[{idx:2d}] = {non_degenerate[idx]:.9f} "
              f"→ err_rel = {err_rel:.2e} ({err_rel*100:.4f}%)")

# =============================================================================
# 6. STATISTIQUES GLOBALES
# =============================================================================
print("\n" + "="*70)
print("STATISTIQUES GLOBALES")
print("="*70)

all_errors = []
for b_target in beta_ref:
    diffs = np.abs(np.array(non_degenerate) - b_target)
    min_err = np.min(diffs) / b_target if b_target != 0 else np.min(diffs)
    all_errors.append(min_err)

print(f"Erreur relative moyenne (meilleure correspondance) : {np.mean(all_errors):.2e}")
print(f"Erreur relative médiane : {np.median(all_errors):.2e}")
print(f"Erreur relative maximale : {np.max(all_errors):.2e}")
print(f"Nombre de βₖ avec err < 1e-4 : {sum(e < 1e-4 for e in all_errors)}/15")
print(f"Nombre de βₖ avec err < 1e-3 : {sum(e < 1e-3 for e in all_errors)}/15")
