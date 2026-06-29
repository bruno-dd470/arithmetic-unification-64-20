#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Visualisation 3D du réseau DSM-861 (réseau triangulaire de 861 nœuds sur un tore)
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.collections import LineCollection
from mpl_toolkits.mplot3d.art3d import Line3DCollection

# Paramètres du tore
R = 3.0          # grand rayon
r = 1.0          # petit rayon

# Génération des indices (i,j) pour le réseau triangulaire
# N = 861 = 41*42/2, donc i et j tels que i+j < 41
nodes = []
for i in range(41):
    for j in range(41 - i):
        nodes.append((i, j))

# Nombre total de nœuds
N = len(nodes)
print(f"Nombre de nœuds : {N}")

# Périodes (41 pour chaque direction)
period = 41

# Fonction pour mapper (i,j) sur un tore
def to_torus(i, j, R=3.0, r=1.0, period=41):
    # Angles : u = 2π * i / period, v = 2π * j / period
    u = 2 * np.pi * i / period
    v = 2 * np.pi * j / period
    x = (R + r * np.cos(v)) * np.cos(u)
    y = (R + r * np.cos(v)) * np.sin(u)
    z = r * np.sin(v)
    return x, y, z

# Générer les coordonnées 3D
coords = np.array([to_torus(i, j, R, r, period) for (i, j) in nodes])

# Tracer les points
fig = plt.figure(figsize=(12, 10))
ax = fig.add_subplot(111, projection='3d')

# Points
ax.scatter(coords[:,0], coords[:,1], coords[:,2], c='blue', s=5, alpha=0.8)

# Optionnel : tracer les arêtes du réseau triangulaire
# On connecte les voisins (i+1,j) et (i,j+1) en tenant compte des conditions périodiques
edges = []
for (i, j) in nodes:
    # Voisin (i+1, j) : si i+1 + j < period
    if i + 1 + j < period:
        edges.append(((i,j), (i+1, j)))
    # Voisin (i, j+1) : si i + j+1 < period
    if i + j + 1 < period:
        edges.append(((i,j), (i, j+1)))
    # Voisin (i-1, j+1) ou (i+1, j-1) pour former les triangles
    # On peut ajouter des arêtes pour le troisième côté des triangles
    if i > 0 and j + 1 < period and i-1 + j+1 < period:
        edges.append(((i,j), (i-1, j+1)))
    # Conditions périodiques : on peut ajouter des arêtes qui traversent les bords
    # (à faire si on veut un tore parfait)

# Tracer les arêtes en 3D
if edges:
    edge_coords = []
    for (i1,j1), (i2,j2) in edges:
        p1 = to_torus(i1, j1, R, r, period)
        p2 = to_torus(i2, j2, R, r, period)
        edge_coords.append([p1, p2])
    lc = Line3DCollection(edge_coords, colors='lightgray', linewidths=0.5, alpha=0.3)
    ax.add_collection(lc)

# Mise en forme
ax.set_title("Réseau DSM-861 : 861 nœuds sur un tore")
ax.set_xlabel("X")
ax.set_ylabel("Y")
ax.set_zlabel("Z")
ax.set_box_aspect([1,1,0.6])
plt.tight_layout()
plt.show()