#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
frequences_DSM861_affine.py

Modèle réaliste du réseau DSM-861 avec :
- tenseur de rigidité (interactions entre pentades)
- conditions aux limites périodiques
- modes localisés sur les seuils polaires P4/N4
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.stats import spearmanr

print("=" * 70)
print("RÉSEAU DSM-861 - MODÈLE RÉALISTE")
print("=" * 70)

# ================================================================
# 1. PARAMÈTRES
# ================================================================

N = 861          # Nombre de nœuds
secteurs = 72    # Symétrie

print(f"N = {N} nœuds, symétrie à {secteurs} secteurs")

# ================================================================
# 2. MODÈLE AVEC TENSEUR DE RIGIDITÉ
# ================================================================

print("\n1. Construction du tenseur de rigidité...")

def dispersion_amelioree(kx, ky, alpha=0.1, beta=0.05):
    """
    Relation de dispersion améliorée.
    alpha : rigidité des pentades
    beta : couplage aux seuils polaires
    """
    # Terme de base (modèle simplifié)
    omega2_base = 4 - 2*np.cos(kx) - 2*np.cos(ky)
    
    # Terme de rigidité des pentades (couplage entre modes)
    omega2_rigidite = alpha * (np.sin(2*kx) + np.sin(2*ky))
    
    # Terme de couplage aux seuils polaires P4/N4
    omega2_seuils = beta * (np.cos(3*kx) + np.cos(3*ky))
    
    return omega2_base + omega2_rigidite + omega2_seuils

# Générer tous les modes avec les paramètres par défaut
print("Génération des modes avec α=0.1, β=0.05...")
modes = []
for m in range(-secteurs//2, secteurs//2):
    for n in range(-secteurs//2, secteurs//2):
        kx = 2 * np.pi * m / secteurs
        ky = 2 * np.pi * n / secteurs
        omega2 = dispersion_amelioree(kx, ky, 0.1, 0.05)
        if omega2 > 0:
            omega = np.sqrt(omega2)
            modes.append((omega, m, n))

modes = sorted(modes, key=lambda x: x[0])

print(f"Nombre de modes : {len(modes)}")

# Extraire les 15 premières fréquences (sans dégénérescences)
freqs = []
seen = set()
for omega, m, n in modes:
    omega_rounded = round(omega, 6)
    if omega_rounded not in seen:
        freqs.append(omega)
        seen.add(omega_rounded)
        if len(freqs) >= 15:
            break

freqs = np.array(freqs[:15])
print(f"\n15 premières fréquences (sans dégénérescences) :")
for i, f in enumerate(freqs):
    print(f"  {i+1:2d}: {f:.6f}")

# ================================================================
# 3. LES BETA_K
# ================================================================

beta = np.array([
    0.06613695904451328, 0.28174250870863576, 0.5558698717637468,
    0.8682439499340019, 1.5041139699699269, 1.7252596926363315,
    1.831267929898219, 2.0174227816393127, 2.092837042770219,
    2.524927313875301, 3.279177783, 3.851477234958053,
    4.571556651552703, 4.724739892029763, 7.407963149728111
])

print(f"\nNombre de beta_k : {len(beta)}")

# ================================================================
# 4. RECHERCHE DU FACTEUR D'ÉCHELLE OPTIMAL
# ================================================================

print("\n2. Recherche du facteur d'échelle optimal...")

# Moindres carrés
lambda_opt = np.sum(freqs * beta[:len(freqs)]) / np.sum(freqs**2)
print(f"λ optimal : {lambda_opt:.4f}")

# Comparaison
ratios = beta[:len(freqs)] / freqs
print("\nComparaison beta / freq :")
for i in range(len(freqs)):
    print(f"  β_{i:2d} = {beta[i]:.6f}  ↔  ω_{i:2d} = {freqs[i]:.6f}  ratio={ratios[i]:.4f}")

# Statistiques
moyenne = np.mean(ratios)
ecart_type = np.std(ratios)
cv = ecart_type / moyenne * 100 if moyenne != 0 else 0

print(f"\nMoyenne des rapports : {moyenne:.4f}")
print(f"Écart-type : {ecart_type:.4f}")
print(f"Coefficient de variation : {cv:.2f}%")

# Corrélation
rho, p = spearmanr(beta[:len(freqs)], freqs)
print(f"Corrélation de Spearman : {rho:.4f} (p={p:.4f})")

if cv < 20 and rho > 0.7:
    print("\n✅ La conjecture est PLAUSIBLE avec le modèle amélioré.")
elif cv < 50 and rho > 0.5:
    print("\n⚠️ La conjecture est PARTIELLEMENT PLAUSIBLE.")
else:
    print("\n❌ La conjecture n'est pas validée.")

# ================================================================
# 5. RECHERCHE DES PARAMÈTRES OPTIMAUX (α, β)
# ================================================================

print("\n3. Recherche des paramètres optimaux (α, β)...")

def erreur_modele(params):
    """Calcule l'erreur entre beta et les fréquences pour des paramètres donnés."""
    alpha, beta_param = params
    modes_local = []
    for m in range(-secteurs//2, secteurs//2):
        for n in range(-secteurs//2, secteurs//2):
            kx = 2 * np.pi * m / secteurs
            ky = 2 * np.pi * n / secteurs
            omega2 = dispersion_amelioree(kx, ky, alpha, beta_param)
            if omega2 > 0:
                modes_local.append(np.sqrt(omega2))
    
    # Trier et prendre les 15 premières fréquences uniques
    modes_local = sorted(modes_local)
    freqs_local = []
    seen_local = set()
    for f in modes_local:
        f_rounded = round(f, 6)
        if f_rounded not in seen_local:
            freqs_local.append(f)
            seen_local.add(f_rounded)
            if len(freqs_local) >= len(beta):
                break
    
    # Convertir en array NumPy
    freqs_local = np.array(freqs_local[:len(beta)])
    
    if len(freqs_local) >= len(beta):
        # Normaliser les fréquences
        lambda_local = np.sum(freqs_local * beta) / np.sum(freqs_local**2)
        beta_pred = lambda_local * freqs_local
        return np.mean((beta - beta_pred)**2)
    return 1e6

# Recherche simple des paramètres
alphas = np.linspace(0, 0.5, 11)
betas_param = np.linspace(0, 0.3, 11)

best_alpha = 0.1
best_beta_param = 0.05
best_err = 1e6

print("Recherche des paramètres optimaux...")
for alpha in alphas:
    for beta_p in betas_param:
        err = erreur_modele([alpha, beta_p])
        if err < best_err:
            best_err = err
            best_alpha = alpha
            best_beta_param = beta_p
            print(f"  α={alpha:.3f}, β={beta_p:.3f} → err={err:.6f}")

print(f"\nMeilleurs paramètres : α = {best_alpha:.3f}, β = {best_beta_param:.3f}")
print(f"Erreur minimale : {best_err:.6f}")

# ================================================================
# 6. MODÈLE AVEC LES MEILLEURS PARAMÈTRES
# ================================================================

print("\n4. Modèle avec les meilleurs paramètres...")

# Recalculer les fréquences avec les meilleurs paramètres
modes_opt = []
for m in range(-secteurs//2, secteurs//2):
    for n in range(-secteurs//2, secteurs//2):
        kx = 2 * np.pi * m / secteurs
        ky = 2 * np.pi * n / secteurs
        omega2 = dispersion_amelioree(kx, ky, best_alpha, best_beta_param)
        if omega2 > 0:
            omega = np.sqrt(omega2)
            modes_opt.append((omega, m, n))

modes_opt = sorted(modes_opt, key=lambda x: x[0])

freqs_opt = []
seen_opt = set()
for omega, m, n in modes_opt:
    omega_rounded = round(omega, 6)
    if omega_rounded not in seen_opt:
        freqs_opt.append(omega)
        seen_opt.add(omega_rounded)
        if len(freqs_opt) >= 15:
            break

freqs_opt = np.array(freqs_opt[:15])
print(f"\nFréquences avec α={best_alpha:.3f}, β={best_beta_param:.3f} :")
for i, f in enumerate(freqs_opt):
    print(f"  {i+1:2d}: {f:.6f}")

# Comparaison
ratios_opt = beta[:len(freqs_opt)] / freqs_opt
moyenne_opt = np.mean(ratios_opt)
ecart_type_opt = np.std(ratios_opt)
cv_opt = ecart_type_opt / moyenne_opt * 100 if moyenne_opt != 0 else 0

print(f"\nMoyenne des rapports : {moyenne_opt:.4f}")
print(f"Écart-type : {ecart_type_opt:.4f}")
print(f"Coefficient de variation : {cv_opt:.2f}%")

rho_opt, p_opt = spearmanr(beta[:len(freqs_opt)], freqs_opt)
print(f"Corrélation de Spearman : {rho_opt:.4f} (p={p_opt:.4f})")

if cv_opt < 20 and rho_opt > 0.7:
    print("\n✅ La conjecture est PLAUSIBLE avec les paramètres optimaux.")
elif cv_opt < 50 and rho_opt > 0.5:
    print("\n⚠️ La conjecture est PARTIELLEMENT PLAUSIBLE.")
else:
    print("\n❌ La conjecture n'est pas validée.")

# ================================================================
# 7. VISUALISATION
# ================================================================

print("\n5. Visualisation...")

plt.figure(figsize=(14, 10))

# 7.1 Distribution des fréquences (modèle optimal)
plt.subplot(2, 2, 1)
all_freqs_opt = sorted([m[0] for m in modes_opt])
plt.hist(all_freqs_opt, bins=50, edgecolor='black', alpha=0.7)
for b in beta:
    plt.axvline(x=b, color='r', linestyle='--', alpha=0.5, linewidth=1)
plt.xlabel('Fréquence')
plt.ylabel('Nombre de modes')
plt.title('Distribution des fréquences (modèle optimal)')
plt.grid(True, alpha=0.3)

# 7.2 β vs fréquences (modèle optimal)
plt.subplot(2, 2, 2)
plt.scatter(freqs_opt, beta[:len(freqs_opt)], color='blue', s=60)
# Ligne de régression
p = np.polyfit(freqs_opt, beta[:len(freqs_opt)], 1)
x_line = np.linspace(min(freqs_opt), max(freqs_opt), 100)
plt.plot(x_line, p[0]*x_line + p[1], 'r--', label=f'β = {p[0]:.3f}×ω + {p[1]:.3f}')
plt.xlabel('Fréquence propre')
plt.ylabel('β')
plt.title('β vs fréquences (modèle optimal)')
plt.legend()
plt.grid(True, alpha=0.3)

# 7.3 Rapport β/ω (modèle optimal)
plt.subplot(2, 2, 3)
plt.bar(range(len(ratios_opt)), ratios_opt, color='purple', alpha=0.7)
plt.axhline(y=moyenne_opt, color='r', linestyle='--', label=f'Moyenne = {moyenne_opt:.3f}')
plt.xlabel('Indice')
plt.ylabel('β / ω')
plt.title('Rapports β / fréquence (modèle optimal)')
plt.legend()
plt.grid(True, alpha=0.3)

# 7.4 Comparaison des modèles
plt.subplot(2, 2, 4)
# Modèle simple (premier run)
freqs_simple = [0.087239, 0.087239, 0.087239, 0.087239, 0.123374, 0.123374, 0.123374, 0.123374, 0.174311, 0.174311, 0.174311, 0.174311, 0.194923, 0.194923, 0.194923]
plt.scatter(beta[:15], freqs_simple[:15], color='red', s=40, label='Modèle simple')
plt.scatter(beta[:len(freqs_opt)], freqs_opt, color='blue', s=40, label='Modèle optimal')
plt.plot([0, 8], [0, 8], 'k--', alpha=0.3, label='β = ω')
plt.xlabel('β')
plt.ylabel('ω')
plt.title('Comparaison des modèles')
plt.legend()
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('frequences_DSM861_affine.png', dpi=150, bbox_inches='tight')
print("Graphique sauvegardé dans 'frequences_DSM861_affine.png'")

print("\n" + "=" * 70)
print("FIN")
print("=" * 70)