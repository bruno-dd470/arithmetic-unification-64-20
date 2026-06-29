#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dirac_pentades_approfondi.py

Analyse approfondie de la relation entre β_k et les valeurs propres
de l'opérateur de Dirac discret sur le graphe des pentades.
Recherche de fonctions simples : β = a/λ + b, β = a/λ^2, β = a*exp(-bλ), etc.
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.stats import spearmanr, pearsonr
import networkx as nx

print("=" * 70)
print("OPÉRATEUR DE DIRAC DISCRET - ANALYSE APPROFONDIE")
print("=" * 70)

# ================================================================
# 1. CONSTRUCTION DU GRAPHE DES 12 PENTADES
# ================================================================

print("\n1. Construction du graphe des 12 pentades...")

pentades = ['P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'N1', 'N2', 'N3', 'N4', 'N5', 'N6']

# Ceintures tropicales
C_P = ['P1', 'P3', 'P5', 'P6', 'P2']
C_N = ['N1', 'N2', 'N6', 'N5', 'N3']

# Triple de l'Annexe D
triplets = [
    ['P1', 'P2', 'P4'], ['P1', 'P3', 'P5'], ['P2', 'P3', 'P6'],
    ['P4', 'P5', 'N2'], ['P5', 'P6', 'N3'], ['P1', 'P6', 'N4'],
    ['P2', 'P5', 'N6'], ['P3', 'P4', 'N6'], ['P1', 'N2', 'N6'],
    ['P1', 'N3', 'N5'], ['P2', 'N3', 'N5'], ['P3', 'N2', 'N4'],
    ['P4', 'N1', 'N3'], ['P4', 'N5', 'N6'], ['P5', 'N1', 'N4'],
    ['P6', 'N1', 'N2'], ['P2', 'N1', 'N4'], ['P3', 'N1', 'N5'],
    ['P6', 'N5', 'N6'], ['N2', 'N3', 'N4']
]

# Créer le graphe
G = nx.Graph()
G.add_nodes_from(pentades)

edges = set()
for triplet in triplets:
    for i in range(len(triplet)):
        for j in range(i+1, len(triplet)):
            edges.add((triplet[i], triplet[j]))

G.add_edges_from(list(edges))

print(f"Nœuds : {G.number_of_nodes()}, Arêtes : {G.number_of_edges()}")

# ================================================================
# 2. MATRICE D'ADJACENCE PONDÉRÉE
# ================================================================

n = G.number_of_nodes()
nodes = list(G.nodes())
node_to_idx = {node: i for i, node in enumerate(nodes)}

# Poids dépendant des ceintures
A = np.zeros((n, n))
for i, node_i in enumerate(nodes):
    for j, node_j in enumerate(nodes):
        if G.has_edge(node_i, node_j):
            in_CP_i = node_i in C_P
            in_CP_j = node_j in C_P
            in_CN_i = node_i in C_N
            in_CN_j = node_j in C_N
            
            if (in_CP_i and in_CP_j) or (in_CN_i and in_CN_j):
                weight = 1.0  # même ceinture
            elif node_i in ['P4', 'N4'] or node_j in ['P4', 'N4']:
                weight = 0.3  # seuils polaires
            else:
                weight = 0.5  # inter-ceinture
            
            A[i, j] = weight
            A[j, i] = weight

# ================================================================
# 3. VALEURS PROPRES DE L'OPÉRATEUR DE DIRAC
# ================================================================

print("\n2. Valeurs propres de D...")

from scipy.linalg import eigh
eigenvals = np.sort(eigh(A, eigvals_only=True))

# Compter le nombre de valeurs propres disponibles
n_eigenvals = len(eigenvals)
print(f"Nombre de valeurs propres disponibles : {n_eigenvals}")

# Les 15 plus grandes valeurs propres (en valeur absolue)
# On prend autant que possible (max 15)
n_take = min(15, n_eigenvals)
eigenvals_abs = np.abs(eigenvals)
idx_large = np.argsort(eigenvals_abs)[-n_take:]
eigenvals_15_large = eigenvals[idx_large]
eigenvals_15_large_abs = eigenvals_abs[idx_large]

print(f"{n_take} plus grandes valeurs propres (en valeur absolue) :")
for i, (v, va) in enumerate(zip(eigenvals_15_large, eigenvals_15_large_abs)):
    print(f"  {i+1:2d}: {v:.6f} (abs={va:.6f})")

# ================================================================
# 4. LES 15 BETA_K
# ================================================================

beta = np.array([
    0.06613695904451328, 0.28174250870863576, 0.5558698717637468,
    0.8682439499340019, 1.5041139699699269, 1.7252596926363315,
    1.831267929898219, 2.0174227816393127, 2.092837042770219,
    2.524927313875301, 3.279177783, 3.851477234958053,
    4.571556651552703, 4.724739892029763, 7.407963149728111
])

# Trier beta par ordre croissant
beta_sorted = np.sort(beta)

# On prend les n_take premiers beta (les plus petits)
beta_take = beta_sorted[:n_take]
print(f"\nbeta utilisés ({n_take} premiers) : {beta_take}")

# ================================================================
# 5. RECHERCHE DE LA MEILLEURE FONCTION f(1/λ)
# ================================================================

print("\n3. Recherche de la meilleure fonction f(1/λ)...")

# Variables
x = 1.0 / eigenvals_15_large_abs  # 1/|λ|
y = beta_take  # beta correspondants

print(f"x (1/|λ|) : {x}")
print(f"y (β) : {y}")

# 5.1 Régression linéaire : β = a/|λ| + b
def func_linear(x, a, b):
    return a * x + b

try:
    popt_lin, pcov_lin = curve_fit(func_linear, x, y)
    a_lin, b_lin = popt_lin
    y_pred_lin = func_linear(x, a_lin, b_lin)
    r2_lin = 1 - np.sum((y - y_pred_lin)**2) / np.sum((y - np.mean(y))**2)
    print(f"\n1. β = a/|λ| + b")
    print(f"   a = {a_lin:.4f}, b = {b_lin:.4f}")
    print(f"   R² = {r2_lin:.4f}")
except Exception as e:
    print(f"\n1. β = a/|λ| + b : échec ({e})")

# 5.2 Régression quadratique : β = a/λ² + b/λ + c
def func_quad(x, a, b, c):
    return a * x**2 + b * x + c

try:
    popt_quad, pcov_quad = curve_fit(func_quad, x, y)
    a_quad, b_quad, c_quad = popt_quad
    y_pred_quad = func_quad(x, a_quad, b_quad, c_quad)
    r2_quad = 1 - np.sum((y - y_pred_quad)**2) / np.sum((y - np.mean(y))**2)
    print(f"\n2. β = a/λ² + b/λ + c")
    print(f"   a = {a_quad:.4f}, b = {b_quad:.4f}, c = {c_quad:.4f}")
    print(f"   R² = {r2_quad:.4f}")
except Exception as e:
    print(f"\n2. β = a/λ² + b/λ + c : échec ({e})")

# 5.3 Exponentielle : β = a * exp(-b/|λ|) + c
def func_exp(x, a, b, c):
    return a * np.exp(-b * x) + c

try:
    popt_exp, pcov_exp = curve_fit(func_exp, x, y, maxfev=5000)
    a_exp, b_exp, c_exp = popt_exp
    y_pred_exp = func_exp(x, a_exp, b_exp, c_exp)
    r2_exp = 1 - np.sum((y - y_pred_exp)**2) / np.sum((y - np.mean(y))**2)
    print(f"\n3. β = a*exp(-b/|λ|) + c")
    print(f"   a = {a_exp:.4f}, b = {b_exp:.4f}, c = {c_exp:.4f}")
    print(f"   R² = {r2_exp:.4f}")
except Exception as e:
    print(f"\n3. β = a*exp(-b/|λ|) + c : échec ({e})")

# 5.4 Puissance : β = a * (1/|λ|)^b
def func_power(x, a, b):
    return a * x**b

try:
    popt_pow, pcov_pow = curve_fit(func_power, x, y)
    a_pow, b_pow = popt_pow
    y_pred_pow = func_power(x, a_pow, b_pow)
    r2_pow = 1 - np.sum((y - y_pred_pow)**2) / np.sum((y - np.mean(y))**2)
    print(f"\n4. β = a*(1/|λ|)^b")
    print(f"   a = {a_pow:.4f}, b = {b_pow:.4f}")
    print(f"   R² = {r2_pow:.4f}")
except Exception as e:
    print(f"\n4. β = a*(1/|λ|)^b : échec ({e})")

# 5.5 Logistique : β = a / (1 + exp(-b*(x - c)))
def func_logistic(x, a, b, c):
    return a / (1 + np.exp(-b * (x - c)))

try:
    popt_log, pcov_log = curve_fit(func_logistic, x, y, maxfev=5000)
    a_log, b_log, c_log = popt_log
    y_pred_log = func_logistic(x, a_log, b_log, c_log)
    r2_log = 1 - np.sum((y - y_pred_log)**2) / np.sum((y - np.mean(y))**2)
    print(f"\n5. β = a/(1+exp(-b*(x-c)))")
    print(f"   a = {a_log:.4f}, b = {b_log:.4f}, c = {c_log:.4f}")
    print(f"   R² = {r2_log:.4f}")
except Exception as e:
    print(f"\n5. β = a/(1+exp(-b*(x-c))) : échec ({e})")

# ================================================================
# 6. MEILLEURE FONCTION
# ================================================================

print("\n4. Meilleure fonction...")

results = []
if 'r2_lin' in locals():
    results.append(("Linéaire", r2_lin))
if 'r2_quad' in locals():
    results.append(("Quadratique", r2_quad))
if 'r2_exp' in locals():
    results.append(("Exponentielle", r2_exp))
if 'r2_pow' in locals():
    results.append(("Puissance", r2_pow))
if 'r2_log' in locals():
    results.append(("Logistique", r2_log))

if results:
    best_func, best_r2 = max(results, key=lambda x: x[1])
    print(f"Meilleure fonction : {best_func} (R² = {best_r2:.4f})")
    
    if best_r2 > 0.9:
        print("\n✅ Relation très forte ! β_k est bien une fonction simple de 1/|λ|.")
    elif best_r2 > 0.7:
        print("\n⚠️ Relation modérée.")
    else:
        print("\n❌ Aucune fonction simple ne décrit la relation.")
else:
    print("Aucune régression n'a convergé.")

# ================================================================
# 7. VISUALISATION
# ================================================================

print("\n5. Visualisation...")

plt.figure(figsize=(14, 10))

# 7.1 β vs 1/|λ|
plt.subplot(2, 2, 1)
plt.scatter(x, y, color='blue', s=60, label='Données')
# Tracer la meilleure fonction
if results:
    x_plot = np.linspace(min(x), max(x), 100)
    try:
        if best_func == "Linéaire":
            y_plot = func_linear(x_plot, a_lin, b_lin)
        elif best_func == "Quadratique":
            y_plot = func_quad(x_plot, a_quad, b_quad, c_quad)
        elif best_func == "Puissance":
            y_plot = func_power(x_plot, a_pow, b_pow)
        elif best_func == "Exponentielle":
            y_plot = func_exp(x_plot, a_exp, b_exp, c_exp)
        elif best_func == "Logistique":
            y_plot = func_logistic(x_plot, a_log, b_log, c_log)
        plt.plot(x_plot, y_plot, 'r--', label=f'{best_func} (R²={best_r2:.4f})')
    except:
        pass
plt.xlabel('1/|λ|')
plt.ylabel('β')
plt.title('β vs 1/|λ|')
plt.legend()
plt.grid(True, alpha=0.3)

# 7.2 β vs |λ|
plt.subplot(2, 2, 2)
plt.scatter(eigenvals_15_large_abs, y, color='green', s=60)
plt.xlabel('|λ|')
plt.ylabel('β')
plt.title('β vs |λ|')
plt.grid(True, alpha=0.3)

# 7.3 Log-Log
plt.subplot(2, 2, 3)
plt.loglog(x, y, 'o', color='blue', markersize=6)
plt.xlabel('log(1/|λ|)')
plt.ylabel('log(β)')
plt.title('β vs 1/|λ| (échelle log-log)')
plt.grid(True, alpha=0.3)

# 7.4 Matrice d'adjacence
plt.subplot(2, 2, 4)
plt.imshow(A, cmap='hot', aspect='auto')
plt.colorbar(label='Poids')
plt.xlabel('Nœud')
plt.ylabel('Nœud')
plt.title('Matrice d\'adjacence pondérée')

plt.tight_layout()
plt.savefig('dirac_pentades_approfondi.png', dpi=150, bbox_inches='tight')
print("Graphique sauvegardé dans 'dirac_pentades_approfondi.png'")

print("\n" + "=" * 70)
print("FIN")
print("=" * 70)