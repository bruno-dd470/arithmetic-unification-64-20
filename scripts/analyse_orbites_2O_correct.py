#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analyse_orbites_2O_correct.py

Analyse des 48 racines de Lambda_72 :
- Regroupement en orbites sous 2O
- Identification des 15 composantes E_k
- Calcul des discriminants quadratiques
- Comparaison avec les beta_k
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import linear_sum_assignment
from scipy.stats import spearmanr

# ================================================================
# 1. LES 48 RACINES EXACTES (EXTRAITES DE G72.NPY)
# ================================================================

racines_48 = np.array([
    0.066136959, 0.066136959, 0.104859650, 0.104859650, 0.105819547, 0.135301748,
    0.135301748, 0.171977681, 0.193287026, 0.193287026, 0.217317880, 0.251706536,
    0.251706536, 0.281742509, 0.281742509, 0.308938098, 0.342531435, 0.342531435,
    0.360145703, 0.389044244, 0.389044244, 0.426898507, 0.539423631, 0.539423631,
    0.555869872, 0.611492664, 0.628433704, 0.628433704, 0.726793942, 0.783639165,
    0.783639165, 0.868243950, 0.894793990, 0.894793990, 0.894926413, 1.181360847,
    1.388242048, 1.459592366, 1.459592366, 1.504113970, 1.582953169, 1.725259693,
    1.831267930, 1.831267930, 1.841475623, 1.891360051, 2.017422782, 2.017422782
])

print("=" * 70)
print("ANALYSE DES 48 RACINES DE LAMBDA_72")
print("=" * 70)
print(f"\nNombre de racines : {len(racines_48)}")
print(f"Racines uniques : {len(np.unique(np.round(racines_48, 9)))}")

# ================================================================
# 2. IDENTIFICATION DES VALEURS UNIQUES ET MULTIPLICITÉS
# ================================================================

print("\n" + "=" * 70)
print("2. VALEURS UNIQUES ET MULTIPLICITÉS")
print("=" * 70)

valeurs_uniques, multiplicites = np.unique(np.round(racines_48, 9), return_counts=True)

print(f"\nNombre de valeurs uniques : {len(valeurs_uniques)}")
print("\nValeurs uniques et multiplicités :")
for v, m in zip(valeurs_uniques, multiplicites):
    print(f"  {v:.9f} : {m} occurrence(s)")

# ================================================================
# 3. LES 15 BETA_K
# ================================================================

print("\n" + "=" * 70)
print("3. LES 15 BETA_K")
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
for i, b in enumerate(beta):
    print(f"  β_{i:2d} = {b:.9f}")

# ================================================================
# 4. ORBITES SOUS 2O
# ================================================================

print("\n" + "=" * 70)
print("4. ORBITES SOUS 2O")
print("=" * 70)

# Les 48 racines se regroupent en orbites sous 2O
# Chaque orbite correspond à un sous-espace E_k
# Les multiplicités des valeurs propres donnent les tailles des orbites

orbites = []
for i, v in enumerate(valeurs_uniques):
    idx = np.where(np.round(racines_48, 9) == v)[0]
    orbites.append({
        'valeur': v,
        'indices': idx.tolist(),
        'taille': len(idx),
        'valeur_carree': v**2
    })

print(f"\nNombre d'orbites : {len(orbites)}")
print("\nOrbites (par taille) :")
for o in sorted(orbites, key=lambda x: x['taille'], reverse=True):
    print(f"  valeur={o['valeur']:.9f}, taille={o['taille']}, carré={o['valeur_carree']:.6f}")

# ================================================================
# 5. IDENTIFICATION DES 15 COMPOSANTES E_k
# ================================================================

print("\n" + "=" * 70)
print("5. IDENTIFICATION DES 15 COMPOSANTES E_k")
print("=" * 70)

def discriminant_orbite(orbite):
    """Calcule le discriminant d'une orbite."""
    valeurs = orbite['valeur'] * np.ones(orbite['taille'])
    if len(valeurs) == 0:
        return 0
    prod = np.prod(np.abs(valeurs))
    return prod ** (1.0 / len(valeurs))

discriminants = []
for o in orbites:
    disq = discriminant_orbite(o)
    discriminants.append(disq)
    o['discriminant'] = disq

print("\nDiscriminants des orbites :")
for i, o in enumerate(orbites):
    print(f"  Orbite {i:2d}: valeur={o['valeur']:.9f}, taille={o['taille']}, disq={o['discriminant']:.6f}")

# ================================================================
# 6. APPARIEMENT OPTIMAL AVEC LES BETA_K
# ================================================================

print("\n" + "=" * 70)
print("6. APPARIEMENT OPTIMAL AVEC LES BETA_K")
print("=" * 70)

n_beta = len(beta)
n_orbites = len(orbites)

# Sélectionner les 15 orbites avec les plus petits discriminants
n_select = min(15, n_orbites)
orbites_triees = sorted(orbites, key=lambda x: x['discriminant'])[:n_select]

disq_values = np.array([o['discriminant'] for o in orbites_triees])
taille_orbites = np.array([o['taille'] for o in orbites_triees])

print(f"\n15 meilleures orbites :")
for i, o in enumerate(orbites_triees):
    print(f"  {i:2d}: valeur={o['valeur']:.9f}, taille={o['taille']}, disq={o['discriminant']:.6f}")

# Matrice de coût
cost = np.zeros((n_beta, n_select))
for i in range(n_beta):
    for j in range(n_select):
        if disq_values[j] != 0:
            cost[i, j] = abs(beta[i] - disq_values[j]) / max(abs(beta[i]), abs(disq_values[j]), 1e-10)
        else:
            cost[i, j] = 1e6

# Algorithme hongrois
row_ind, col_ind = linear_sum_assignment(cost)

print("\nAppariement optimal :")
ratios = []
for i, j in zip(row_ind, col_ind):
    if j < len(disq_values) and disq_values[j] != 0:
        ratio = beta[i] / disq_values[j]
        ratios.append(ratio)
        print(f"  β_{i:2d} = {beta[i]:.6f}  ↔  Orbite {j:2d} (disq={disq_values[j]:.6f}, taille={taille_orbites[j]})  ratio={ratio:.4f}")

# ================================================================
# 7. STATISTIQUES
# ================================================================

print("\n" + "=" * 70)
print("7. STATISTIQUES")
print("=" * 70)

# Vérifier que ratios existe et n'est pas vide
if len(ratios) > 0:
    ratios_arr = np.array(ratios)
    moyenne = np.mean(ratios_arr)
    ecart_type = np.std(ratios_arr)
    cv = ecart_type / moyenne * 100 if moyenne != 0 else 0
    
    print(f"Moyenne des rapports : {moyenne:.4f}")
    print(f"Écart-type : {ecart_type:.4f}")
    print(f"Coefficient de variation : {cv:.2f}%")
    
    # Corrélation
    rho, p = spearmanr(np.abs(beta[:len(disq_values[col_ind])]), np.abs(disq_values[col_ind]))
    print(f"Corrélation de Spearman : {rho:.4f} (p={p:.4f})")
    
    if cv < 5 and rho > 0.8:
        print("\n✅ La conjecture est VALIDÉE.")
        print("   Les beta_k sont les discriminants des orbites de 2O.")
    elif cv < 15 and rho > 0.6:
        print("\n⚠️ La conjecture est PARTIELLEMENT VALIDÉE.")
    else:
        print("\n❌ La conjecture n'est pas validée avec cette approche.")
else:
    print("Aucun rapport valide.")

# ================================================================
# 8. SYNTHÈSE DES 15 COMPOSANTES
# ================================================================

print("\n" + "=" * 70)
print("8. SYNTHÈSE DES 15 COMPOSANTES E_k")
print("=" * 70)

print("\nComposantes E_k (orbites sous 2O) :")
for i, o in enumerate(orbites_triees):
    # Trouver le beta correspondant (si apparié)
    beta_idx = None
    for bi, bj in zip(row_ind, col_ind):
        if bj == i:
            beta_idx = bi
            break
    
    beta_val = beta[beta_idx] if beta_idx is not None else None
    print(f"  E_{i:2d}: dim={o['taille']}, disq={o['discriminant']:.6f}, β={beta_val:.6f}")

print(f"\nSomme des dimensions : {sum(taille_orbites[:n_select])}")

# ================================================================
# 9. VISUALISATION
# ================================================================

print("\n" + "=" * 70)
print("9. VISUALISATION")
print("=" * 70)

plt.figure(figsize=(14, 10))

# 9.1 Distribution des 48 racines
plt.subplot(2, 2, 1)
plt.hist(racines_48, bins=30, edgecolor='black', alpha=0.7)
for b in beta:
    plt.axvline(x=b, color='r', linestyle='--', alpha=0.5, linewidth=1)
plt.xlabel('Valeur')
plt.ylabel('Fréquence')
plt.title('Distribution des 48 racines (barres rouges = beta_k)')
plt.grid(True, alpha=0.3)

# 9.2 Multiplicités
plt.subplot(2, 2, 2)
plt.bar(range(len(valeurs_uniques)), multiplicites, color='blue', alpha=0.7)
plt.xlabel('Index de la valeur unique')
plt.ylabel('Multiplicité')
plt.title('Multiplicités des valeurs uniques')
plt.grid(True, alpha=0.3)

# 9.3 Beta vs disq
plt.subplot(2, 2, 3)
if len(ratios) > 0:
    disq_sorted = np.array([disq_values[j] for j in col_ind])
    plt.scatter(disq_sorted, beta[:len(disq_sorted)], color='blue', s=60)
    # Ligne x=y
    max_val = max(max(disq_sorted), max(beta[:len(disq_sorted)]))
    plt.plot([0, max_val], [0, max_val], 'r--', label='β = disq')
    plt.xlabel('disq(E) (discriminant de l\'orbite)')
    plt.ylabel('β')
    plt.title('β vs disq(E)')
    plt.legend()
    plt.grid(True, alpha=0.3)

# 9.4 Matrice de coût
plt.subplot(2, 2, 4)
plt.imshow(cost, cmap='hot', aspect='auto')
plt.colorbar(label='Coût')
plt.xlabel('Orbite (E_k)')
plt.ylabel('β_i')
plt.title('Matrice de coût')
for i, j in zip(row_ind, col_ind):
    if i < cost.shape[0] and j < cost.shape[1]:
        plt.plot(j, i, 'gs', markersize=8)

plt.tight_layout()
plt.savefig('orbites_Lambda72.png', dpi=150, bbox_inches='tight')
print("Graphique sauvegardé dans 'orbites_Lambda72.png'")

# ================================================================
# 10. SYNTHÈSE FINALE
# ================================================================

print("\n" + "=" * 70)
print("10. SYNTHÈSE FINALE")
print("=" * 70)

print(f"""
Résultats clés :
--------------
1. Nombre de racines          : {len(racines_48)}
2. Valeurs uniques            : {len(valeurs_uniques)}
3. Nombre de beta_k           : {len(beta)}
4. Orbites identifiées        : {len(orbites)}
5. Coefficient de variation   : {cv:.2f}% (si disponible)
6. Corrélation de Spearman    : {rho:.4f} (si disponible)
""")

print("\n" + "=" * 70)
print("FIN DE L'ANALYSE")
print("=" * 70)