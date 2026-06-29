#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Visualisation 3D du réseau DSM-861 sur un tore
- 861 nœuds (réseau triangulaire)
- Triangles du pavage colorés selon leur secteur azimutal
- Lignes marquant les 72 secteurs de symétrie
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

# ========== Paramètres du tore ==========
R = 3.0          # grand rayon
r = 1.2          # petit rayon
N = 41           # base du nombre triangulaire (41 -> 861 nœuds)

# ========== Génération des nœuds ==========
nodes = [(i, j) for i in range(N) for j in range(N - i)]
print(f"Nombre de nœuds : {len(nodes)}")  # 861

# Fonction de projection sur le tore
def to_torus(i, j):
    u = 2 * np.pi * i / (N - 1)
    v = 2 * np.pi * j / (N - 1)
    x = (R + r * np.cos(v)) * np.cos(u)
    y = (R + r * np.cos(v)) * np.sin(u)
    z = r * np.sin(v)
    return x, y, z

coords = np.array([to_torus(i, j) for (i, j) in nodes])

# Dictionnaire pour retrouver l'indice d'un nœud à partir de ses coordonnées (i,j)
idx_map = {(i, j): idx for idx, (i, j) in enumerate(nodes)}

# ========== Construction des triangles ==========
triangles = []

# Parcours des nœuds pour créer les deux triangles de chaque maille
for (i, j) in nodes:
    # Triangle "haut" : (i,j), (i+1,j), (i,j+1)
    if i + 1 + j < N and i + j + 1 < N:
        p0 = idx_map[(i, j)]
        p1 = idx_map[(i + 1, j)]
        p2 = idx_map[(i, j + 1)]
        triangles.append((p0, p1, p2))   # utiliser un tuple
    # Triangle "bas" : (i, j+1), (i+1, j), (i+1, j-1)
    if i + j + 1 < N and i + 1 + j < N and i + 1 + (j - 1) < N and j - 1 >= 0:
        p0 = idx_map[(i, j + 1)]
        p1 = idx_map[(i + 1, j)]
        p2 = idx_map[(i + 1, j - 1)]
        triangles.append((p0, p1, p2))

# Élimination des doublons éventuels
triangles = list(set(triangles))
print(f"Nombre de triangles : {len(triangles)}")

# ========== Préparation des couleurs ==========
# Calcul de l'angle azimutal (autour de l'axe Z) pour chaque nœud
azimuth = np.arctan2(coords[:, 1], coords[:, 0])
# Normalisation entre 0 et 1
norm_azimuth = (azimuth + np.pi) % (2 * np.pi) / (2 * np.pi)

# Pour chaque triangle, on prend la moyenne des azimuths de ses sommets
tri_azimuth = []
for tri in triangles:
    # tri est un tuple de 3 entiers
    tri_azimuth.append(np.mean([norm_azimuth[p] for p in tri]))

# Couleurs selon un dégradé cyclique (HSV)
colors = plt.cm.hsv(tri_azimuth)

# ========== Affichage 3D ==========
fig = plt.figure(figsize=(14, 10))
ax = fig.add_subplot(111, projection='3d')

# Dessin des triangles : on convertit chaque tuple en liste pour l'indexation
poly3d = [coords[list(tri)] for tri in triangles]
mesh = Poly3DCollection(poly3d, facecolors=colors, alpha=0.7, edgecolor='k', linewidth=0.2)
ax.add_collection3d(mesh)

# Dessin des nœuds
ax.scatter(coords[:, 0], coords[:, 1], coords[:, 2], c='black', s=5, alpha=0.6)

# ========== Marquage des 72 secteurs de symétrie ==========
# On trace des arcs (à v variable, u constant) pour chaque secteur
for k in range(72):
    theta = 2 * np.pi * k / 72
    v_vals = np.linspace(0, 2 * np.pi, 30)
    x_arc = (R + r * np.cos(v_vals)) * np.cos(theta)
    y_arc = (R + r * np.cos(v_vals)) * np.sin(theta)
    z_arc = r * np.sin(v_vals)
    ax.plot(x_arc, y_arc, z_arc, color='gray', linewidth=0.5, alpha=0.4)

# ========== Mise en forme ==========
ax.set_xlim([-R - r - 0.5, R + r + 0.5])
ax.set_ylim([-R - r - 0.5, R + r + 0.5])
ax.set_zlim([-r - 0.5, r + 0.5])
ax.set_title("Réseau DSM-861 : 861 nœuds, triangles colorés par secteur (symétrie 72)")
ax.set_xlabel("X")
ax.set_ylabel("Y")
ax.set_zlabel("Z")
ax.view_init(elev=25, azim=-60)

plt.tight_layout()
plt.show()