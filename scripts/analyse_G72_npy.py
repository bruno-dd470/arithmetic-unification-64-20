#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analyse_G72_npy_corrige.py

Analyse de la matrice G72.npy (diagonalisée)
Les valeurs propres sont les carrés des racines.
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.linalg import eigh
from scipy.optimize import linear_sum_assignment
from scipy.stats import spearmanr

# ================================================================
# 1. CHARGEMENT
# ================================================================

print("=" * 70)
print("ANALYSE DE LA MATRICE DE GRAM DE LAMBDA_72 (DIAGONALISÉE)")
print("=" * 70)

G = np.load('G72.npy')
print(f"\nMatrice chargée : {G.shape}")
print(f"Type : {G.dtype}")

# ================================================================
# 2. PROPRIÉTÉS DE BASE
# ================================================================

print("\n" + "=" * 70)
print("2. PROPRIÉTÉS DE BASE")
print("=" * 70)

print(f"Symétrique : {np.allclose(G, G.T)}")

# Diagonalisation
vals = eigh(G, eigvals_only=True)
vals = np.sort(vals)

print(f"Valeurs propres :")
print(f"  Min : {vals.min():.6f}")
print(f"  Max : {vals.max():.6f}")
print(f"  Moyenne : {vals.mean():.6f}")
print(f"  Nombre de négatives : {np.sum(vals < 0)}")

# ================================================================
# 3. LES 48 RACINES (RACINES CARRÉES DES VALEURS PROPRES)
# ================================================================

print("\n" + "=" * 70)
print("3. LES 48 RACINES")
print("=" * 70)

# Les 48 plus petites valeurs propres
valeurs_propres_48 = vals[:48]
racines_48 = np.sqrt(valeurs_propres_48)

print(f"48 racines :")
for i, r in enumerate(racines_48):
    print(f"  {i+1:2d}: {r:.9f}")

# ================================================================
# 4. LES 15 BETA_K
# ================================================================

print("\n" + "=" * 70)
print("4. LES 15 BETA_K")
print("=" * 70)

beta = np.array([
    0.06613695904451328,
    0.28174250870863576,
    0.5558698717637468,
    0.8682439499340019,
    1.5041139699699269,
    1.7252596926363315,
    1.831267929898219,
    2.0174227816393127,
    2.092837042770219,
    2.524927313875301,
    3.279177783,
    3.851477234958053,
    4.571556651552703,
    4.724739892029763,
    7.407963149728111
])

print(f"\nNombre de beta_k : {len(beta)}")
print(f"beta_k : {beta}")

# ================================================================
# 5. IDENTIFICATION DES BETA_K PARMI LES RACINES
# ================================================================

print("\n" + "=" * 70)
print("5. IDENTIFICATION DES BETA_K PARMI LES RACINES")
print("=" * 70)

# Pour chaque beta, trouver la racine la plus proche
tolerance = 1e-3
correspondances = []
for i, b in enumerate(beta):
    differences = np.abs(racines_48 - b)
    idx = np.argmin(differences)
    min_diff = differences[idx]
    if min_diff < tolerance:
        correspondances.append((i, b, idx, racines_48[idx], min_diff))
    else:
        correspondances.append((i, b, -1, 0, min_diff))

print("\nCorrespondances beta ↔ racines :")
for i, b, idx, r, diff in correspondances:
    if idx >= 0:
        print(f"  β_{i:2d} = {b:.6f}  ↔  racine_{idx+1:2d} = {r:.6f}  (diff={diff:.6f})")
    else:
        print(f"  β_{i:2d} = {b:.6f}  ↔  AUCUNE  (proche={racines_48[np.argmin(np.abs(racines_48 - b))]:.6f})")

# ================================================================
# 6. STATISTIQUES
# ================================================================

print("\n" + "=" * 70)
print("6. STATISTIQUES")
print("=" * 70)

# Corrélation entre beta et les racines correspondantes
if len(correspondances) > 0:
    beta_correspondants = [c[1] for c in correspondances if c[2] >= 0]
    racines_correspondantes = [c[3] for c in correspondances if c[2] >= 0]
    
    if len(beta_correspondants) > 0:
        rho, p = spearmanr(beta_correspondants, racines_correspondantes)
        print(f"Corrélation de Spearman : {rho:.4f} (p={p:.4f})")
        
        # Rapport beta/racine
        ratios = np.array(beta_correspondants) / np.array(racines_correspondantes)
        print(f"Moyenne des rapports : {np.mean(ratios):.4f}")
        print(f"Écart-type des rapports : {np.std(ratios):.4f}")
        print(f"Coefficient de variation : {np.std(ratios)/np.mean(ratios)*100:.2f}%")
        
        if rho > 0.9 and np.std(ratios)/np.mean(ratios) < 0.1:
            print("\n✅ Les beta_k sont très proches des racines de Lambda_72.")
        else:
            print("\n⚠️ Les beta_k ne correspondent pas exactement aux racines.")

# ================================================================
# 7. VISUALISATION
# ================================================================

print("\n" + "=" * 70)
print("7. VISUALISATION")
print("=" * 70)

plt.figure(figsize=(14, 6))

# 7.1 Distribution des 48 racines
plt.subplot(1, 2, 1)
plt.hist(racines_48, bins=20, edgecolor='black', alpha=0.7)
for b in beta:
    plt.axvline(x=b, color='r', linestyle='--', alpha=0.5, linewidth=1)
plt.xlabel('Valeur')
plt.ylabel('Fréquence')
plt.title('Distribution des 48 racines (barres rouges = beta_k)')
plt.grid(True, alpha=0.3)

# 7.2 Beta vs racines
plt.subplot(1, 2, 2)
if len(beta_correspondants) > 0:
    plt.scatter(racines_correspondantes, beta_correspondants, color='blue', s=60)
    # Ligne x=y
    max_val = max(max(racines_correspondantes), max(beta_correspondants))
    plt.plot([0, max_val], [0, max_val], 'r--', label='β = racine')
    plt.xlabel('Racine de Lambda_72')
    plt.ylabel('β_k')
    plt.title('β_k vs racines de Lambda_72')
    plt.legend()
    plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('racines_beta_comparaison.png', dpi=150, bbox_inches='tight')
print("Graphique sauvegardé dans 'racines_beta_comparaison.png'")

# ================================================================
# 8. SYNTHÈSE FINALE
# ================================================================

print("\n" + "=" * 70)
print("8. SYNTHÈSE FINALE")
print("=" * 70)

print(f"""
Résultats clés :
--------------
1. Matrice : {G.shape}
2. Valeurs propres : min={vals.min():.4f}, max={vals.max():.4f}
3. 48 racines extraites : {len(racines_48)}
4. Nombre de beta_k : {len(beta)}
5. Correspondances exactes : {len([c for c in correspondances if c[2] >= 0])}/{len(beta)}
6. Corrélation de Spearman : {rho:.4f} (si disponible)
""")

print("\n" + "=" * 70)
print("FIN DE L'ANALYSE")
print("=" * 70)