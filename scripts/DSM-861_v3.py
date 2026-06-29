#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Visualisation 3D du réseau DSM-861 sur un tore
- Non fermé (représente fidèlement le défaut de commensurabilité)
- Triangles en transparence avec couleurs par secteur
- Symétrie à 72 secteurs
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

# Paramètres du tore
R = 3.0
r = 1.2
N = 41

# Génération des nœuds
nodes = [(i, j) for i in range(N) for j in range(N - i)]

def to_torus(i, j):
    u = 2 * np.pi * i / (N - 1)
    v = 2 * np.pi * j / (N - 1)
    x = (R + r * np.cos(v)) * np.cos(u)
    y = (R + r * np.cos(v)) * np.sin(u)
    z = r * np.sin(v)
    return x, y, z

coords = np.array([to_torus(i, j) for (i, j) in nodes])
idx_map = {(i, j): idx for idx, (i, j) in enumerate(nodes)}

# Construction des triangles
triangles = []
for (i, j) in nodes:
    if i + 1 + j < N and i + j + 1 < N:
        p0 = idx_map[(i, j)]
        p1 = idx_map[(i + 1, j)]
        p2 = idx_map[(i, j + 1)]
        triangles.append((p0, p1, p2))
    if i + j + 1 < N and i + 1 + j < N and i + 1 + (j - 1) < N and j - 1 >= 0:
        p0 = idx_map[(i, j + 1)]
        p1 = idx_map[(i + 1, j)]
        p2 = idx_map[(i + 1, j - 1)]
        triangles.append((p0, p1, p2))

triangles = list(set(triangles))
print(f"Triangles : {len(triangles)}")

# Couleurs par azimut
azimuth = np.arctan2(coords[:, 1], coords[:, 0])
norm_azimuth = (azimuth + np.pi) % (2 * np.pi) / (2 * np.pi)
tri_azimuth = [np.mean([norm_azimuth[p] for p in tri]) for tri in triangles]
colors = plt.cm.hsv(tri_azimuth)

# Affichage
fig = plt.figure(figsize=(14, 10))
ax = fig.add_subplot(111, projection='3d')

poly3d = [coords[list(tri)] for tri in triangles]
mesh = Poly3DCollection(poly3d, facecolors=colors, alpha=0.5, edgecolor='k', linewidth=0.2)
ax.add_collection3d(mesh)

ax.scatter(coords[:, 0], coords[:, 1], coords[:, 2], c='black', s=3, alpha=0.5)

# Symétrie 72
for k in range(72):
    theta = 2 * np.pi * k / 72
    v_vals = np.linspace(0, 2 * np.pi, 30)
    x_arc = (R + r * np.cos(v_vals)) * np.cos(theta)
    y_arc = (R + r * np.cos(v_vals)) * np.sin(theta)
    z_arc = r * np.sin(v_vals)
    ax.plot(x_arc, y_arc, z_arc, color='gray', linewidth=0.5, alpha=0.3)

ax.set_title("DSM-861 : réseau triangulaire sur tore (non fermé, symétrie 72)")
ax.set_xlabel("X")
ax.set_ylabel("Y")
ax.set_zlabel("Z")
ax.view_init(elev=20, azim=-40)
plt.tight_layout()
plt.show()