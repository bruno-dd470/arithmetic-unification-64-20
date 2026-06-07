#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script avec les 15 βₖ à haute précision (extraites de √λᵢ de Λ₇₂)
Objectif : Utiliser les valeurs exactes pour PSLQ, recherche de dénominateur, etc.
"""

import numpy as np
from math import gcd

# =============================================================================
# LES 15 βₖ À HAUTE PRÉCISION (extraites des √λᵢ de Λ₇₂)
# Format : (k, beta_precise, lambda_value, error_rel_vs_9dec)
# =============================================================================
beta_precise = np.array([
    0.06613695904451328,   # k=0, λ=0.004374097351655627
    0.28174250870863576,   # k=1, λ=0.0793788412134357
    0.5558698717637468,    # k=2, λ=0.30899131433464433
    0.8682439499340019,    # k=3, λ=0.7538475565969975
    1.5041139699699269,    # k=4, λ=2.262358834658694
    1.7252596926363315,    # k=5, λ=2.976521007035609
    1.831267929898219,     # k=6, λ=3.3535422310737086
    2.0174227816393127,    # k=7, λ=4.0699946798773015
    2.092837042770219,     # k=8, λ=4.379966887591197
    2.524927313875301,     # k=9, λ=6.375257940353542
    3.279177783,           # k=10 (inchangé, pas de match direct dans CSV)
    3.851477234958053,     # k=11, λ=14.83387689140013
    4.571556651552703,     # k=12, λ=20.899130218355758
    4.724739892029763,     # k=13, λ=22.32316704733742
    7.407963149728111,     # k=14, λ=54.87791802772964
])

# =============================================================================
# FONCTION : Recherche du meilleur dénominateur dans ℚ(√2)
# =============================================================================
def find_best_denominator(beta, max_D=5000, max_coeff=5000):
    """
    Cherche le plus petit D tel que beta ≈ (a + b√2)/D avec a,b entiers.
    Retourne (a, b, D, erreur_relative) ou None si non trouvé.
    """
    sqrt2 = np.sqrt(2.0)
    best = None
    best_err = float('inf')
    
    for D in range(1, max_D+1):
        target = beta * D
        for b in range(-max_coeff, max_coeff+1):
            a_approx = target - b * sqrt2
            a_candidate = int(round(a_approx))
            if abs(a_candidate) > max_coeff:
                continue
            approx = (a_candidate + b * sqrt2) / D
            err = abs(approx - beta) / beta if beta != 0 else abs(approx)
            if err < best_err:
                best_err = err
                best = (a_candidate, b, D, err)
        # Critère d'arrêt précoce si erreur très faible
        if best_err < 1e-12:
            break
    
    return best if best_err < 1e-10 else None

# =============================================================================
# CALCUL DU PPCM DES DÉNOMINATEURS OPTIMAUX
# =============================================================================
def compute_ppcm_denominators(beta_list):
    """Calcule le PPCM des dénominateurs optimaux pour chaque βₖ."""
    def lcm(a, b):
        return a * b // gcd(a, b) if a and b else (a or b)
    
    ppm = 1
    results = []
    
    for k, beta in enumerate(beta_list):
        res = find_best_denominator(beta, max_D=2000, max_coeff=2000)
        if res:
            a, b, D, err = res
            results.append((k, beta, a, b, D, err))
            ppm = lcm(ppm, D)
            print(f"[β_{k:2d}] ≈ ({a:6d} + {b:6d}√2)/{D:4d}, err={err:.2e}")
        else:
            print(f"[β_{k:2d}] Aucune relation simple trouvée (err > 1e-10)")
    
    return ppm, results

# =============================================================================
# TEST PSLQ DIRECT DANS ℚ(√2) (version Python avec mpmath)
# =============================================================================
def pslq_test_python(beta, max_coeff=10**7):
    """
    Version Python pure avec mpmath pour PSLQ.
    Cherche une relation : a + b√2 + c·beta = 0.
    """
    try:
        from mpmath import mp, pslq, sqrt as mp_sqrt
        
        mp.dps = 50  # 50 chiffres décimaux
        sqrt2 = mp_sqrt(2)
        
        # Vecteur pour PSLQ : [1, √2, beta]
        vec = [mp.mpf(1), sqrt2, mp.mpf(str(beta))]
        
        # Application de PSLQ
        rel = pslq(vec, maxsteps=200)
        
        if rel and any(c != 0 for c in rel) and rel[2] != 0:
            a, b, c = rel
            # beta ≈ -(a + b√2)/c
            approx = -(a + b * sqrt2) / c
            err = abs(approx - beta) / beta if beta != 0 else abs(approx)
            return (int(a), int(b), int(c), float(err))
    except ImportError:
        print("[WARN] mpmath non installé ; installez avec : pip install mpmath")
    except Exception as e:
        print(f"[WARN] Erreur PSLQ : {e}")
    return None

# =============================================================================
# EXÉCUTION PRINCIPALE
# =============================================================================
def main():
    print("\n" + "="*70)
    print("RECHERCHE DU PPCM AVEC βₖ À HAUTE PRÉCISION (Λ₇₂)")
    print("="*70)
    
    # 1. Recherche par dénominateur borné
    print("\n[1] Recherche de dénominateurs optimaux dans ℚ(√2)...")
    ppm, results = compute_ppcm_denominators(beta_precise)
    
    print(f"\n[RESULTAT] PPCM des dénominateurs : {ppm}")
    
    if ppm < 10**6:
        print("✓ PPCM modéré → structure arithmétique simple probable")
    elif ppm < 10**12:
        print("⚠ PPCM élevé mais gérable → structure possible avec normalisation")
    else:
        print("✗ PPCM très élevé → soit structure complexe, soit besoin de plus de précision")
    
    # 2. Test PSLQ direct (si mpmath disponible)
    print("\n[2] Test PSLQ direct dans ℚ(√2)...")
    try:
        from mpmath import mp
        mp.dps = 50
        pslq_success = 0
        for k, beta in enumerate(beta_precise):
            rel = pslq_test_python(beta, max_coeff=10**8)
            if rel:
                a, b, c, err = rel
                print(f"[β_{k:2d}] PSLQ : ({a} + {b}√2)/{-c}, err={err:.2e}")
                pslq_success += 1
            else:
                print(f"[β_{k:2d}] PSLQ : aucune relation trouvée")
        print(f"\n[STAT] {pslq_success}/15 βₖ avec relation PSLQ détectée")
    except ImportError:
    
    # 3. Export des résultats pour analyse ultérieure
    print("\n[3] Export des résultats...")
    with open('beta_precise_results.csv', 'w') as f:
        f.write("k,beta_precise,a,b,D,error_rel\n")
        for k, beta, a, b, D, err in results:
            f.write(f"{k},{beta},{a},{b},{D},{err}\n")
    print("[OK] Résultats exportés dans 'beta_precise_results.csv'")
    
    # 4. Comparaison avec les valeurs à 9 décimales
    print("\n" + "="*70)
    print("COMPARAISON : 9 décimales vs haute précision")
    print("="*70)
    beta_9dec = np.array([
        0.066136959, 0.28175138, 0.555869353, 0.868248673, 1.504114125,
        1.725183114, 1.831271203, 2.01742448, 2.092834951, 2.524926754,
        3.279177783, 3.851497776, 4.571886169, 4.72473915, 7.408061012
    ])
    
    max_diff = np.max(np.abs(beta_precise - beta_9dec))
    mean_diff = np.mean(np.abs(beta_precise - beta_9dec))
    print(f"Écart maximal (9 déc vs haute préc.) : {max_diff:.2e}")
    print(f"Écart moyen : {mean_diff:.2e}")
    
    if max_diff < 1e-8:
        print("✓ Les 9 décimales suffisent pour la plupart des applications.")
    else:
        print("⚠ Certaines βₖ nécessitent plus de décimales pour une identification exacte.")

if __name__ == "__main__":
    main()
