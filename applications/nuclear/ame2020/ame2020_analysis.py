#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AME2020 - Analyse complète des masses isotopiques
Auteur : Généré par analyse automatique
Date : 2025

Ce script :
1. Parse le fichier mass.mas20.txt original
2. Extrait tous les isotopes (Z, A, masse en MeV)
3. Calcule les prédictions via le modèle des 48 racines
4. Optimise les paramètres de la formule fermée
5. Génère graphiques et statistiques
"""

import numpy as np
import matplotlib.pyplot as plt
import csv
from scipy.optimize import differential_evolution, minimize
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# CONSTANTES PHYSIQUES
# ============================================================
Lambda_fund = 7.726          # MeV (constante fondamentale)
u_to_MeV = 931.49410242      # 1 u → MeV
m_p = 938.272088             # MeV (masse proton)
m_n = 939.565420             # MeV (masse neutron)

# ============================================================
# 1. LES 48 RACINES DISTINCTES (BASE CANONIQUE)
# ============================================================
sqrt_distinct = np.array([
    0.066136959000, 0.104861556000, 0.105819546000, 0.135301931000,
    0.171977681000, 0.193286510000, 0.217318285000, 0.251706536000,
    0.281751380000, 0.308944245000, 0.342536900000, 0.360145691000,
    0.389044757000, 0.426899914000, 0.539423867000, 0.555869353000,
    0.611492405000, 0.628435246000, 0.726794491000, 0.783638283000,
    0.868248673000, 0.894790972000, 0.895000741000, 1.181361718000,
    1.388242400000, 1.459652785000, 1.504114125000, 1.582953046000,
    1.725183114000, 1.831271203000, 1.841477693000, 1.891359664000,
    2.017424480000, 2.092834951000, 2.304598960000, 2.524926754000,
    2.911315620000, 3.157658906000, 3.158280845000, 3.279177783000,
    3.289042432000, 3.851497776000, 4.571886169000, 4.724739150000,
    4.755055358000, 5.943089000000, 7.408061012000, 8.102307717000
])

# Génération des combinaisons Δ = √λ_i ± √λ_j
def generate_combos(roots):
    """Génère toutes les combinaisons Δ à partir d'un ensemble de racines"""
    combos = set()
    n = len(roots)
    for i in range(n):
        for j in range(i+1, n):
            combos.add(roots[i] + roots[j])
            combos.add(abs(roots[i] - roots[j]))
    for r in roots:
        combos.add(r)
    return np.array(sorted(combos))

combos_original = generate_combos(sqrt_distinct)
print(f"Combinaisons Δ générées : {len(combos_original)}")

# ============================================================
# 2. PARSING DU FICHIER mass.mas20.txt
# ============================================================
def parse_mass_file(filename):
    """Parse le fichier mass.mas20.txt et retourne la liste des isotopes"""
    isotopes = []  # (Z, A, mass_MeV)
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"ERREUR: Fichier {filename} introuvable.")
        print("Veuillez placer le fichier mass.mas20.txt dans le même répertoire.")
        return []
    
    # Localiser la première ligne de données
    start_idx = 0
    for i, line in enumerate(lines):
        if '0  1    1    0    1  n' in line:
            start_idx = i + 1
            break
    
    line_count = 0
    for line in lines[start_idx:]:
        if len(line) < 120 or line[0] not in '0123456789-':
            continue
        
        # Extraction par positions fixes (0-indexé) d'après format Fortran
        try:
            nz = line[1:4].strip()           # non utilisé
            n = line[4:9].strip()            # neutrons (non utilisé)
            z = line[9:14].strip()           # protons
            a = line[14:19].strip()          # nombre de masse
            el = line[20:23].strip()         # symbole (non utilisé)
            
            # Masse atomique (micro-u) positions 107-119
            mass_str = line[106:119].strip().replace(' ', '')
            if not mass_str:
                continue
            # Gérer le '#' (valeur estimée)
            mass_str = mass_str.replace('#', '')
            
            Z = int(z)
            A = int(a)
            mass_u = float(mass_str) / 1e6   # µu → u
            mass_MeV = mass_u * u_to_MeV
            
            if 1 <= A <= 295 and mass_MeV > 0:
                isotopes.append((Z, A, mass_MeV))
                line_count += 1
                
        except (ValueError, IndexError) as e:
            continue
    
    print(f"Fichier parsé : {line_count} isotopes extraits")
    return isotopes

# ============================================================
# 3. PRÉDICTION DES MASSES
# ============================================================
def best_delta(target, combos):
    """Trouve la combinaison Δ la plus proche de target"""
    idx = np.argmin(np.abs(combos - target))
    return combos[idx]

def predict_mass(M_true, combos, Lambda_fund=7.726):
    """Trouve la meilleure prédiction pour une masse donnée"""
    best_err = float('inf')
    best_n_oct = None
    best_delta_val = None
    best_pred = None
    
    for n_oct in range(-5, 16):
        factor = 4 ** n_oct
        needed = M_true / (Lambda_fund * factor)
        if needed < 0.01 or needed > 20:
            continue
        delta = best_delta(needed, combos)
        pred = Lambda_fund * factor * delta
        err = abs(pred - M_true) / M_true
        if err < best_err:
            best_err = err
            best_n_oct = n_oct
            best_delta_val = delta
            best_pred = pred
    
    return best_n_oct, best_delta_val, best_pred, best_err

# ============================================================
# 4. FORMULE FERMÉE POUR LES RACINES
# ============================================================
def compute_root(params, n, l, j):
    """√λ = (Λ₀/n²) × [n² + α·l(l+1) + β·n·j(j+1)]"""
    Lambda0, alpha, beta = params
    l_term = alpha * l * (l + 1)
    j_term = beta * n * j * (j + 1)
    inner = n**2 + l_term + j_term
    return (Lambda0 / n**2) * inner

def generate_roots_from_params(params):
    """Génère les 48 racines à partir des paramètres (Λ₀, α, β)"""
    orbitals = [
        # n=1
        (1, 0, 0.5),
        # n=2
        (2, 1, 0.5), (2, 1, 1.5),
        # n=3
        (3, 2, 1.5), (3, 2, 2.5), (3, 0, 0.5),
        # n=4
        (4, 3, 2.5), (4, 3, 3.5), (4, 1, 0.5), (4, 1, 1.5), (4, 0, 0.5),
        # n=5
        (5, 4, 3.5), (5, 4, 4.5), (5, 2, 1.5), (5, 2, 2.5),
        # n=6
        (6, 5, 4.5), (6, 5, 5.5), (6, 3, 2.5), (6, 3, 3.5), (6, 1, 0.5), (6, 1, 1.5),
        # n=7
        (7, 6, 5.5), (7, 6, 6.5), (7, 4, 3.5), (7, 4, 4.5), (7, 2, 1.5), (7, 2, 2.5), (7, 0, 0.5),
    ]
    roots = []
    for n, l, j in orbitals:
        roots.append(compute_root(params, n, l, j))
    return np.array(roots)

def predict_mass_with_formula(M_true, params):
    """Prédiction avec la formule fermée (3 paramètres)"""
    roots = generate_roots_from_params(params)
    combos = generate_combos(roots)
    return predict_mass(M_true, combos)

# ============================================================
# 5. FONCTION OBJECTIF POUR L'OPTIMISATION
# ============================================================
def objective(params, masses):
    """Fonction objectif à minimiser (erreur moyenne)"""
    Lambda0, alpha, beta = params
    
    # Bornes implicites
    if Lambda0 < 0.02 or Lambda0 > 0.15:
        return 1e10
    if alpha < 0.3 or alpha > 1.5:
        return 1e10
    if beta < 0.01 or beta > 0.10:
        return 1e10
    
    try:
        roots = generate_roots_from_params(params)
        combos = generate_combos(roots)
        errors = []
        for M in masses:
            _, _, _, err = predict_mass(M, combos)
            if err < float('inf'):
                errors.append(err)
        return np.mean(errors) if errors else 1e10
    except:
        return 1e10

# ============================================================
# 6. FONCTION PRINCIPALE
# ============================================================
def main():
    print("=" * 70)
    print("AME2020 - ANALYSE COMPLÈTE DES MASSES ISOTOPIQUES")
    print("=" * 70)
    
    # ------------------------------------------------------------------
    # Étape 1 : Parser le fichier mass.mas20.txt
    # ------------------------------------------------------------------
    print("\n[1] Parsing du fichier mass.mas20.txt...")
    isotopes = parse_mass_file('mass.mas20.txt')
    
    if not isotopes:
        print("ERREUR: Aucun isotope chargé. Vérifiez le fichier mass.mas20.txt")
        return
    
    masses = np.array([iso[2] for iso in isotopes])
    print(f"  → {len(isotopes)} isotopes chargés (Z=0 à {max(iso[0] for iso in isotopes)}, A=1 à {max(iso[1] for iso in isotopes)})")
    
    # ------------------------------------------------------------------
    # Étape 2 : Prédiction avec le modèle original (48 racines)
    # ------------------------------------------------------------------
    print("\n[2] Prédiction avec le modèle original (48 racines)...")
    
    results_original = []
    for Z, A, M in isotopes:
        n_oct, delta, pred, err = predict_mass(M, combos_original)
        if n_oct is not None:
            results_original.append((Z, A, M, n_oct, delta, pred, err))
    
    errors_original = np.array([r[6]*100 for r in results_original])
    
    print(f"  → {len(results_original)} isotopes prédits")
    print(f"  → Erreur moyenne : {np.mean(errors_original):.5f} %")
    print(f"  → Écart-type : {np.std(errors_original):.5f} %")
    print(f"  → Erreur max : {np.max(errors_original):.5f} %")
    print(f"  → % < 0.2% : {100 * np.sum(errors_original < 0.2) / len(errors_original):.1f} %")
    
    # Sauvegarde des résultats
    with open('isotope_fits_original.txt', 'w') as f:
        f.write("# Z A M_true(MeV) n_oct Delta M_pred(MeV) err(%)\n")
        for Z, A, M, n, d, Mp, e in results_original:
            f.write(f"{Z} {A} {M:.6f} {n} {d:.6f} {Mp:.6f} {e*100:.6f}\n")
    print("  → Sauvegardé dans 'isotope_fits_original.txt'")
    
    # ------------------------------------------------------------------
    # Étape 3 : Optimisation des paramètres de la formule fermée
    # ------------------------------------------------------------------
    print("\n[3] Optimisation des paramètres de la formule fermée...")
    print("  (Recherche globale en cours, environ 1-2 minutes)")
    
    # Bornes : (Λ₀, α, β)
    bounds = [(0.02, 0.15), (0.3, 1.5), (0.01, 0.10)]
    
    # Optimisation globale
    result_global = differential_evolution(
        objective, bounds,
        args=(masses,),
        maxiter=30, popsize=10, seed=42,
        disp=False
    )
    
    print(f"  → Optimisation globale : Λ₀={result_global.x[0]:.6f}, α={result_global.x[1]:.6f}, β={result_global.x[2]:.6f}")
    print(f"    Erreur moyenne = {result_global.fun*100:.5f}%")
    
    # Affinage local
    result_local = minimize(
        objective, result_global.x,
        args=(masses,),
        method='L-BFGS-B', bounds=bounds
    )
    
    optimal_params = result_local.x
    print(f"\n  → Paramètres optimaux finaux :")
    print(f"    Λ₀ = {optimal_params[0]:.8f}")
    print(f"    α  = {optimal_params[1]:.8f}")
    print(f"    β  = {optimal_params[2]:.8f}")
    print(f"    Erreur moyenne = {result_local.fun*100:.5f}%")
    
    # Sauvegarde des paramètres
    with open('optimized_parameters.txt', 'w') as f:
        f.write("# Paramètres optimisés pour la formule des masses AME2020\n")
        f.write(f"Lambda0 = {optimal_params[0]:.10f}\n")
        f.write(f"alpha = {optimal_params[1]:.10f}\n")
        f.write(f"beta = {optimal_params[2]:.10f}\n")
        f.write(f"Lambda_fund = {Lambda_fund}\n")
        f.write(f"u_to_MeV = {u_to_MeV}\n")
        f.write(f"\n# Statistiques sur l'ensemble des isotopes\n")
        f.write(f"mean_error_percent = {np.mean(errors_original):.6f}\n")
        f.write(f"std_error_percent = {np.std(errors_original):.6f}\n")
        f.write(f"percent_below_0.2 = {100 * np.sum(errors_original < 0.2) / len(errors_original):.2f}\n")
    
    # ------------------------------------------------------------------
    # Étape 4 : Prédiction avec la formule optimisée
    # ------------------------------------------------------------------
    print("\n[4] Validation de la formule optimisée...")
    
    results_formula = []
    for Z, A, M in isotopes:
        n_oct, delta, pred, err = predict_mass_with_formula(M, optimal_params)
        if n_oct is not None:
            results_formula.append((Z, A, M, n_oct, delta, pred, err))
    
    errors_formula = np.array([r[6]*100 for r in results_formula])
    
    print(f"  → Erreur moyenne : {np.mean(errors_formula):.5f} %")
    print(f"  → Écart-type : {np.std(errors_formula):.5f} %")
    print(f"  → % < 0.2% : {100 * np.sum(errors_formula < 0.2) / len(errors_formula):.1f} %")
    
    # Sauvegarde
    with open('isotope_fits_formula.txt', 'w') as f:
        f.write("# Z A M_true(MeV) n_oct Delta M_pred(MeV) err(%)\n")
        for Z, A, M, n, d, Mp, e in results_formula:
            f.write(f"{Z} {A} {M:.6f} {n} {d:.6f} {Mp:.6f} {e*100:.6f}\n")
    print("  → Sauvegardé dans 'isotope_fits_formula.txt'")
    
    # ------------------------------------------------------------------
    # Étape 5 : Graphiques
    # ------------------------------------------------------------------
    print("\n[5] Génération des graphiques...")
    
    masses_plot = np.array([r[2] for r in results_original])
    
    plt.figure(figsize=(15, 10))
    
    # Graphique 1 : Erreur vs masse (modèle original)
    plt.subplot(2, 2, 1)
    plt.scatter(masses_plot, errors_original, s=2, alpha=0.5, c='blue')
    plt.axhline(y=0.2, color='red', linestyle='--', label='Seuil 0.2%')
    plt.xscale('log')
    plt.xlabel('Masse (MeV)')
    plt.ylabel('Erreur (%)')
    plt.title(f'Modèle original (48 racines)\nErreur moyenne = {np.mean(errors_original):.4f}%')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Graphique 2 : Distribution des erreurs
    plt.subplot(2, 2, 2)
    plt.hist(errors_original, bins=50, edgecolor='black', alpha=0.7, color='green')
    plt.xlabel('Erreur (%)')
    plt.ylabel('Fréquence')
    plt.title(f'Distribution des erreurs\n{len(errors_original)} isotopes')
    plt.grid(True, alpha=0.3)
    
    # Graphique 3 : Comparaison original vs formule
    plt.subplot(2, 2, 3)
    plt.scatter(errors_original, errors_formula, s=2, alpha=0.5, c='purple')
    plt.plot([0, max(errors_original)], [0, max(errors_original)], 'r--', label='Égalité')
    plt.xlabel('Erreur originale (%)')
    plt.ylabel('Erreur formule (%)')
    plt.title('Comparaison des deux modèles')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Graphique 4 : Évolution n_oct vs A
    plt.subplot(2, 2, 4)
    A_vals = [r[1] for r in results_original]
    n_vals = [r[3] for r in results_original]
    plt.scatter(A_vals, n_vals, s=2, alpha=0.5, c='orange')
    plt.xlabel('Nombre de masse A')
    plt.ylabel('Exposant n_oct')
    plt.title('n_oct en fonction de A')
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('isotope_analysis.png', dpi=150)
    print("  → Sauvegardé dans 'isotope_analysis.png'")
    
    # Graphique supplémentaire : racines originales vs optimisées
    roots_opt = generate_roots_from_params(optimal_params)
    
    plt.figure(figsize=(10, 6))
    plt.plot(range(1, len(sqrt_distinct)+1), sqrt_distinct, 'o-', label='Originales (48 racines)', markersize=4)
    plt.plot(range(1, len(roots_opt)+1), roots_opt, 's-', label=f'Optimisées ({len(roots_opt)} racines)', markersize=4)
    plt.xlabel('Indice de la racine')
    plt.ylabel('√λ')
    plt.title('Comparaison des racines originales vs optimisées')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig('roots_comparison.png', dpi=150)
    print("  → Sauvegardé dans 'roots_comparison.png'")
    
    # ------------------------------------------------------------------
    # Étape 6 : Résumé final
    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("RÉSUMÉ FINAL")
    print("=" * 70)
    print(f"""
┌─────────────────────────────────────────────────────────────────────┐
│                    STATISTIQUES DES MODÈLES                          │
├─────────────────────────────────────────────────────────────────────┤
│  Modèle original (48 racines) :                                      │
│    - Isotopes prédits : {len(results_original)}                                           │
│    - Erreur moyenne : {np.mean(errors_original):.5f} %                                  │
│    - Écart-type : {np.std(errors_original):.5f} %                                    │
│    - % avec erreur < 0.2% : {100 * np.sum(errors_original < 0.2) / len(errors_original):.1f} %                   │
├─────────────────────────────────────────────────────────────────────┤
│  Formule fermée (3 paramètres) :                                     │
│    - Λ₀ = {optimal_params[0]:.8f}                                                 │
│    - α  = {optimal_params[1]:.8f}                                                 │
│    - β  = {optimal_params[2]:.8f}                                                 │
│    - Erreur moyenne : {np.mean(errors_formula):.5f} %                                  │
│    - % avec erreur < 0.2% : {100 * np.sum(errors_formula < 0.2) / len(errors_formula):.1f} %                   │
├─────────────────────────────────────────────────────────────────────┤
│  Formule complète :                                                  │
│    √λ(n,l,j) = (Λ₀/n²) × [n² + α·l(l+1) + β·n·j(j+1)]               │
│    M ≈ Λ_fund × 4^{n_oct} × (√λ_i ± √λ_j)                           │
│    avec Λ_fund = {Lambda_fund} MeV                                           │
└─────────────────────────────────────────────────────────────────────┘
""")
    
    print("\n✅ Analyse terminée ! Fichiers générés :")
    print("   - isotope_fits_original.txt   (prédictions modèle original)")
    print("   - isotope_fits_formula.txt    (prédictions formule fermée)")
    print("   - optimized_parameters.txt    (paramètres optimaux)")
    print("   - isotope_analysis.png        (graphiques d'analyse)")
    print("   - roots_comparison.png        (comparaison des racines)")

# ============================================================
# EXÉCUTION
# ============================================================
if __name__ == "__main__":
    main()