#!/usr/bin/env python3
# recherche_denominateur_beta.py

import numpy as np

# Les 15 β_k
beta = np.array([
    0.066136959, 0.281751380, 0.555869353, 0.868248673,
    1.504114125, 1.725183114, 1.831271203, 2.017424480,
    2.092834951, 2.524926754, 3.279177783, 3.851497776,
    4.571886169, 4.724739150, 7.408061012
])

sqrt2 = np.sqrt(2)

def trouver_a_b(beta_k, D):
    """Pour un D donné, trouve les entiers a,b tels que (a + b√2)/D ≈ beta_k"""
    # On cherche b en premier (partie en √2)
    # Approximation : b ≈ round(beta_k * D / √2)
    b = round(beta_k * D / sqrt2)
    # Puis a ≈ round(beta_k * D - b*√2)
    a = round(beta_k * D - b * sqrt2)
    erreur = abs(beta_k - (a + b*sqrt2)/D) / beta_k
    return a, b, erreur

def evaluer_D(D):
    """Évalue un dénominateur D sur les 15 β_k"""
    erreurs = []
    for bk in beta:
        a, b, err = trouver_a_b(bk, D)
        erreurs.append(err)
    return np.mean(erreurs), np.max(erreurs), erreurs

# Recherche du meilleur D entre 1 et 50000
print("Recherche du meilleur dénominateur D (1 à 50000)...")
print(f"{'D':>4} {'erreur moy (%)':>14} {'erreur max (%)':>14}")
print("-" * 40)

meilleur_D = None
meilleure_erreur_moy = float('inf')
resultats = []

for D in range(1, 50000):
    err_moy, err_max, _ = evaluer_D(D)
    resultats.append((D, err_moy, err_max))
    if err_moy < meilleure_erreur_moy:
        meilleure_erreur_moy = err_moy
        meilleur_D = D
        if D % 50 == 0 or D < 20:
            print(f"{D:4d} {err_moy*100:13.4f} % {err_max*100:13.4f} %")

print("\n" + "="*50)
print(f"✅ Meilleur D = {meilleur_D}")
print(f"   Erreur moyenne = {meilleure_erreur_moy*100:.4f} %")
print(f"   D = {meilleur_D}")

# Détail pour le meilleur D
print(f"\nDétail pour D = {meilleur_D}")
print(f"{'k':>2} {'β_k':>12} {'a':>4} {'b':>4} {'(a+b√2)/D':>14} {'erreur %':>10}")
print("-" * 60)
for i, bk in enumerate(beta):
    a, b, err = trouver_a_b(bk, meilleur_D)
    val = (a + b*sqrt2)/meilleur_D
    print(f"{i:2d} {bk:12.9f} {a:4d} {b:4d} {val:14.9f} {err*100:10.4f} %")
