#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
distances_merkabah.py

Calcul des distances spectrales entre les 20 attracteurs de la Merkabah.
Extraction des 15 valeurs singulières et comparaison avec les beta_k.
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.linalg import svd, eigh
from scipy.spatial.distance import pdist, squareform
from scipy.optimize import linear_sum_assignment
from scipy.stats import spearmanr

print("=" * 70)
print("DISTANCES SPECTRALES DE LA MERKABAH")
print("=" * 70)

# ================================================================
# 1. LES 20 ATTRACTEURS ET LEURS TRIPLETS DE PENTADES
# ================================================================

print("\n1. Construction de la matrice d'incidence des 20 attracteurs...")

# Les 20 attracteurs avec leurs triplets de pentades (d'après l'Annexe D)
attracteurs = [
    # 3P (3 classes)
    {'nom': 'A', 'triplet': ['P1', 'P2', 'P4'], 'polarite': '3P'},
    {'nom': 'B', 'triplet': ['P1', 'P3', 'P5'], 'polarite': '3P'},
    {'nom': 'C', 'triplet': ['P2', 'P3', 'P6'], 'polarite': '3P'},
    # 2P+1N (5 classes)
    {'nom': 'D', 'triplet': ['P4', 'P5', 'N2'], 'polarite': '2P+1N'},
    {'nom': 'E', 'triplet': ['P5', 'P6', 'N3'], 'polarite': '2P+1N'},
    {'nom': 'F', 'triplet': ['P1', 'P6', 'N4'], 'polarite': '2P+1N'},
    {'nom': 'G', 'triplet': ['P2', 'P5', 'N6'], 'polarite': '2P+1N'},
    {'nom': 'H', 'triplet': ['P3', 'P4', 'N6'], 'polarite': '2P+1N'},
    # 1P+2N (11 classes)
    {'nom': 'I', 'triplet': ['P1', 'N2', 'N6'], 'polarite': '1P+2N'},
    {'nom': 'J', 'triplet': ['P1', 'N3', 'N5'], 'polarite': '1P+2N'},
    {'nom': 'K', 'triplet': ['P2', 'N3', 'N5'], 'polarite': '1P+2N'},
    {'nom': 'L', 'triplet': ['P3', 'N2', 'N4'], 'polarite': '1P+2N'},
    {'nom': 'M', 'triplet': ['P4', 'N1', 'N3'], 'polarite': '1P+2N'},
    {'nom': 'N', 'triplet': ['P4', 'N5', 'N6'], 'polarite': '1P+2N'},
    {'nom': 'O', 'triplet': ['P5', 'N1', 'N4'], 'polarite': '1P+2N'},
    {'nom': 'P', 'triplet': ['P6', 'N1', 'N2'], 'polarite': '1P+2N'},
    {'nom': 'Q', 'triplet': ['P2', 'N1', 'N4'], 'polarite': '1P+2N'},
    {'nom': 'R', 'triplet': ['P3', 'N1', 'N5'], 'polarite': '1P+2N'},
    {'nom': 'S', 'triplet': ['P6', 'N5', 'N6'], 'polarite': '1P+2N'},
    # 3N (1 classe)
    {'nom': 'T', 'triplet': ['N2', 'N3', 'N4'], 'polarite': '3N'},
]

n_attracteurs = len(attracteurs)
print(f"Nombre d'attracteurs : {n_attracteurs}")

# Liste des pentades
pentades = ['P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'N1', 'N2', 'N3', 'N4', 'N5', 'N6']
n_pentades = len(pentades)
pentade_to_idx = {p: i for i, p in enumerate(pentades)}

# ================================================================
# 2. MATRICE D'INCIDENCE ATTRACTEURS ↔ PENTADES
# ================================================================

print("\n2. Construction de la matrice d'incidence...")

# Matrice d'incidence : attracteurs (lignes) × pentades (colonnes)
M = np.zeros((n_attracteurs, n_pentades))
for i, attr in enumerate(attracteurs):
    for p in attr['triplet']:
        M[i, pentade_to_idx[p]] = 1

print(f"Matrice d'incidence : {M.shape}")

# ================================================================
# 3. MATRICE DE SIMILARITÉ ENTRE ATTRACTEURS
# ================================================================

print("\n3. Calcul de la matrice de similarité...")

# Similarité : nombre de pentades communes
S = np.dot(M, M.T)
print(f"Matrice de similarité : {S.shape}")

# ================================================================
# 4. MATRICE DE DISTANCE
# ================================================================

print("\n4. Calcul de la matrice de distance...")

# Distance : dissimilarité entre attracteurs
# d(i,j) = 3 - S[i,j] (car chaque attracteur a 3 pentades)
D = 3 - S
np.fill_diagonal(D, 0)

print(f"Matrice de distance : {D.shape}")

# ================================================================
# 5. VALEURS SINGULIÈRES DE LA MATRICE DE DISTANCE
# ================================================================

print("\n5. Calcul des valeurs singulières...")

# Centrer la matrice de distance (pour l'analyse spectrale)
# (double centrage)
n = D.shape[0]
H = np.eye(n) - np.ones((n, n)) / n
B = -0.5 * H @ (D**2) @ H

# Valeurs propres de la matrice de Gram centrée
vals = eigh(B, eigvals_only=True)
vals = np.sort(vals)[::-1]  # Tri décroissant
vals = vals[vals > 1e-10]    # Enlever les valeurs négatives (erreurs numériques)

print(f"Nombre de valeurs propres positives : {len(vals)}")
print(f"Premières 15 valeurs propres :")
for i, v in enumerate(vals[:15]):
    print(f"  {i+1:2d}: {v:.6f}")

# ================================================================
# 6. LES 15 BETA_K
# ================================================================

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

# ================================================================
# 7. APPARIEMENT OPTIMAL
# ================================================================

print("\n7. Appariement optimal avec les beta_k...")

# Prendre les 15 plus grandes valeurs propres
vals_15 = vals[:15]

# Normaliser les valeurs propres pour les comparer avec beta
# On cherche un facteur d'échelle lambda
lambda_opt = np.sum(vals_15 * beta[:len(vals_15)]) / np.sum(vals_15**2)
print(f"λ optimal : {lambda_opt:.4f}")

# Comparaison
ratios = beta[:len(vals_15)] / vals_15
print("\nComparaison beta / eigenvals :")
for i in range(min(15, len(beta), len(vals_15))):
    print(f"  β_{i:2d} = {beta[i]:.6f}  ↔  λ_{i:2d} = {vals_15[i]:.6f}  ratio={ratios[i]:.4f}")

# Statistiques
ratios_arr = np.array(ratios)
moyenne = np.mean(ratios_arr)
ecart_type = np.std(ratios_arr)
cv = ecart_type / moyenne * 100 if moyenne != 0 else 0

print(f"\nMoyenne des rapports : {moyenne:.4f}")
print(f"Écart-type : {ecart_type:.4f}")
print(f"Coefficient de variation : {cv:.2f}%")

# Corrélation (convertir en scalaires)
rho, p = spearmanr(beta[:len(vals_15)], vals_15)
rho_val = float(rho) if hasattr(rho, 'item') else rho
p_val = float(p) if hasattr(p, 'item') else p
print(f"Corrélation de Spearman : {rho_val:.4f} (p={p_val:.4f})")

if cv < 20 and rho_val > 0.7:
    print("\n✅ La conjecture est PLAUSIBLE.")
elif cv < 50 and rho_val > 0.5:
    print("\n⚠️ La conjecture est PARTIELLEMENT PLAUSIBLE.")
else:
    print("\n❌ La conjecture n'est pas validée.")

# ================================================================
# 8. COORDONNÉES DES ATTRACTEURS (MDS)
# ================================================================

print("\n8. Projection MDS des attracteurs...")

# Calcul des coordonnées par MDS (MultiDimensional Scaling)
# On prend les 3 premières composantes principales
eigvals, eigvecs = eigh(B)
idx = np.argsort(eigvals)[::-1]
eigvals = eigvals[idx]
eigvecs = eigvecs[:, idx]

# Coordonnées 3D
coords_3d = eigvecs[:, :3] * np.sqrt(eigvals[:3])

print(f"Coordonnées 3D : {coords_3d.shape}")

# ================================================================
# 9. VISUALISATION
# ================================================================

print("\n9. Visualisation...")

plt.figure(figsize=(14, 12))

# 9.1 Matrice de distance
plt.subplot(2, 2, 1)
plt.imshow(D, cmap='hot', aspect='auto')
plt.colorbar(label='Distance')
plt.xlabel('Attracteur')
plt.ylabel('Attracteur')
plt.title('Matrice de distance entre les 20 attracteurs')

# 9.2 Spectre des valeurs propres
plt.subplot(2, 2, 2)
plt.bar(range(1, len(vals)+1), vals, color='blue', alpha=0.7)
for b in beta:
    plt.axhline(y=b, color='r', linestyle='--', alpha=0.5, linewidth=1, label='β' if b == beta[0] else '')
plt.xlabel('Indice')
plt.ylabel('Valeur propre')
plt.title('Spectre de la matrice de distance\n(barres rouges = beta_k)')
plt.grid(True, alpha=0.3)

# 9.3 Beta vs valeurs propres
plt.subplot(2, 2, 3)
plt.scatter(vals_15, beta[:len(vals_15)], color='blue', s=60)
# Ligne de régression
p = np.polyfit(vals_15, beta[:len(vals_15)], 1)
x_line = np.linspace(min(vals_15), max(vals_15), 100)
plt.plot(x_line, p[0]*x_line + p[1], 'r--', label=f'β = {p[0]:.3f}×λ + {p[1]:.3f}')
plt.xlabel('Valeurs propres')
plt.ylabel('β')
plt.title('β vs valeurs propres de la matrice de distance')
plt.legend()
plt.grid(True, alpha=0.3)

# 9.4 Projection 3D des attracteurs
from mpl_toolkits.mplot3d import Axes3D
ax = plt.subplot(2, 2, 4, projection='3d')
# Colorer selon la polarité
colors = {'3P': 'red', '2P+1N': 'orange', '1P+2N': 'blue', '3N': 'green'}
color_map = [colors[a['polarite']] for a in attracteurs]
ax.scatter(coords_3d[:, 0], coords_3d[:, 1], coords_3d[:, 2], 
           c=color_map, s=80, alpha=0.7)
for i, attr in enumerate(attracteurs):
    ax.text(coords_3d[i, 0], coords_3d[i, 1], coords_3d[i, 2], 
            attr['nom'], fontsize=8)
ax.set_xlabel('Composante 1')
ax.set_ylabel('Composante 2')
ax.set_zlabel('Composante 3')
ax.set_title('Projection MDS 3D des 20 attracteurs\n(rouge=3P, orange=2P+1N, bleu=1P+2N, vert=3N)')

plt.tight_layout()
plt.savefig('distances_merkabah.png', dpi=150, bbox_inches='tight')
print("Graphique sauvegardé dans 'distances_merkabah.png'")

# ================================================================
# 10. SYNTHÈSE
# ================================================================

print("\n" + "=" * 70)
print("10. SYNTHÈSE")
print("=" * 70)

print(f"""
Résultats clés :
--------------
1. Nombre d'attracteurs          : {n_attracteurs}
2. Nombre de pentades            : {n_pentades}
3. Valeurs propres positives     : {len(vals)}
4. Nombre de beta_k              : {len(beta)}
5. Coefficient de variation      : {cv:.2f}%
6. Corrélation de Spearman       : {rho_val:.4f} (p={p_val:.4f})
""")

if cv < 20 and rho_val > 0.7:
    print("\n✅ La conjecture est PLAUSIBLE.")
    print("   Les beta_k sont proches des valeurs propres de la matrice de distance.")
elif cv < 50 and rho_val > 0.5:
    print("\n⚠️ La conjecture est PARTIELLEMENT PLAUSIBLE.")
    print("   Une relation existe, mais elle n'est pas exacte.")
else:
    print("\n❌ La conjecture n'est pas validée.")
    print("   Les beta_k ne correspondent pas aux valeurs propres de la matrice de distance.")

print("=" * 70)
print("FIN")
print("=" * 70)