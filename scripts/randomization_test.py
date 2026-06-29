#!/usr/bin/env python3
"""
randomization_test.py - Version multithread/multiprocess
Test d'hypothese nulle par simulation de Monte-Carlo.
"""

import numpy as np
from itertools import combinations, product
import csv
import random
import sys
import matplotlib.pyplot as plt
from multiprocessing import Pool, cpu_count
from functools import partial

# ============================================================
# CONSTANTES
# ============================================================
Lambda_MeV = 7.726
Lambda_eV = 5.950

beta_real = np.array([
    0.066136959, 0.281751380, 0.555869353, 0.868248673,
    1.504114125, 1.725183114, 1.831271203, 2.017424480,
    2.092834951, 2.524926754, 3.279177783, 3.851497776,
    4.571886169, 4.724739150, 7.408061012
])

# ============================================================
# GENERATION DES COMBINAISONS (une fois pour toutes)
# ============================================================
def generate_delta_values(beta, max_active=6):
    n = len(beta)
    deltas = []
    for k in range(1, max_active + 1):
        for idx in combinations(range(n), k):
            for signs in product([-1, 1], repeat=k):
                val = 0.0
                for i, s in zip(idx, signs):
                    val += s * beta[i]
                if val > 1e-12:
                    deltas.append(val)
    deltas = list(set(deltas))
    deltas.sort()
    return np.array(deltas)

def predict(value, Lambda, delta_vals, m_range=range(-5, 16)):
    best_err = float('inf')
    for m in m_range:
        factor = 4 ** m
        target = value / (Lambda * factor)
        if target < 0.01 or target > 20:
            continue
        idx = np.searchsorted(delta_vals, target)
        if idx == 0:
            delta = delta_vals[0]
        elif idx == len(delta_vals):
            delta = delta_vals[-1]
        else:
            if abs(delta_vals[idx] - target) < abs(delta_vals[idx-1] - target):
                delta = delta_vals[idx]
            else:
                delta = delta_vals[idx-1]
        pred = Lambda * factor * delta
        err = abs(pred - value) / value if value != 0 else abs(pred)
        if err < best_err:
            best_err = err
    return best_err

def evaluate_single_beta(beta_data):
    """Evalue un seul jeu de beta (pour parallelisation)"""
    beta, data, Lambda = beta_data
    delta_vals = generate_delta_values(beta, 6)
    if len(delta_vals) == 0:
        return 100.0
    total_err = 0.0
    for _, _, val in data:
        err = predict(val, Lambda, delta_vals)
        total_err += err
    return total_err / len(data) * 100

# ============================================================
# CHARGEMENT DES DONNEES
# ============================================================
def load_masses(filename):
    data = []
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        try:
            next(reader)
        except StopIteration:
            return data
        for row in reader:
            if len(row) < 4:
                continue
            try:
                Z = int(float(row[0]))
                A = int(float(row[1]))
                mass_MeV = float(row[3])
                if Z >= 1 and mass_MeV > 0:
                    data.append((Z, A, mass_MeV))
            except (ValueError, IndexError):
                continue
    return data

def load_ionizations(filename):
    data = []
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        try:
            next(reader)
        except StopIteration:
            return data
        for row in reader:
            if len(row) < 3:
                continue
            try:
                Z = int(float(row[0]))
                k = int(float(row[1]))
                E = float(row[2])
                if E > 0:
                    data.append((Z, k, E))
            except (ValueError, IndexError):
                continue
    return data

# ============================================================
# SIMULATION PARALLELE
# ============================================================
def run_randomization_parallel(data, Lambda, n_iterations=1000):
    """Version parallele du test de Monte-Carlo"""
    
    # Calcul de l'erreur avec beta reels
    print("  Calcul de l'erreur avec beta reels...")
    error_real = evaluate_single_beta((beta_real, data, Lambda))
    print(f"    Erreur reelle: {error_real:.6f}%")
    
    # Generation des beta aleatoires
    print(f"  Generation de {n_iterations} jeux de beta aleatoires...")
    random.seed(42)
    np.random.seed(42)
    
    random_betas = [np.random.uniform(0, 10, 15) for _ in range(n_iterations)]
    
    # Preparation des arguments pour parallelisation
    args = [(beta, data, Lambda) for beta in random_betas]
    
    # Execution parallele
    print(f"  Execution sur {cpu_count()} coeurs...")
    with Pool(processes=cpu_count()) as pool:
        errors_random = pool.map(evaluate_single_beta, args)
    
    errors_random = np.array(errors_random)
    p_value = np.mean(errors_random <= error_real)
    
    return error_real, errors_random, p_value

# ============================================================
# VISUALISATION
# ============================================================
def plot_results(errors_real, errors_random, domain_name, output_file):
    plt.figure(figsize=(10, 6))
    
    max_err = max(30, np.max(errors_random))
    bins = np.linspace(0, max_err, 50)
    plt.hist(errors_random, bins=bins, alpha=0.7, color='gray', 
             edgecolor='black', label='Beta aleatoires (n=1000)')
    
    plt.axvline(errors_real, color='red', linewidth=2, linestyle='-',
                label=f'Beta reelles: {errors_real:.6f}%')
    
    p05 = np.percentile(errors_random, 5)
    p95 = np.percentile(errors_random, 95)
    plt.axvline(p05, color='blue', linewidth=1, linestyle='--', alpha=0.5)
    plt.axvline(p95, color='blue', linewidth=1, linestyle='--', alpha=0.5)
    
    ymin, ymax = plt.ylim()
    plt.fill_betweenx([ymin, ymax], p05, p95, alpha=0.1, color='blue',
                      label='Intervalle a 95%')
    
    plt.xlabel('Erreur moyenne (%)', fontsize=12)
    plt.ylabel('Frequence', fontsize=12)
    plt.title(f'Test de randomisation - {domain_name}', fontsize=14)
    plt.legend(loc='upper right')
    plt.grid(alpha=0.3)
    
    p_val = np.mean(errors_random <= errors_real)
    plt.text(0.7, 0.95, f'p-value = {p_val:.6f}', 
             transform=plt.gca().transAxes, fontsize=12,
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=150)
    plt.close()
    print(f"    Graphique sauvegarde: {output_file}")

# ============================================================
# MAIN
# ============================================================
def main():
    print("=" * 70)
    print("TEST DE RANDOMISATION - MONTE-CARLO (VERSION PARALLELE)")
    print("=" * 70)
    
    mass_file = "ame2020_clean+.csv"
    ion_file = "ionisations_simplifie.csv"
    n_iterations = 1000
    
    print(f"\nFichiers utilises:")
    print(f"  - Masses: {mass_file}")
    print(f"  - Ionisations: {ion_file}")
    print(f"  - Simulations: {n_iterations}")
    print(f"  - Coeurs CPU: {cpu_count()}")
    
    print("\nChargement des donnees...")
    mass_data = load_masses(mass_file)
    ion_data = load_ionizations(ion_file)
    print(f"  - Masses: {len(mass_data)} isotopes")
    print(f"  - Ionisations: {len(ion_data)} points")
    
    if len(mass_data) == 0:
        print("\nERREUR: Aucune donnee de masse chargee!")
        sys.exit(1)
    
    # ============================================================
    # TEST SUR LES MASSES
    # ============================================================
    print("\n" + "-" * 50)
    print("TEST DE RANDOMISATION - MASSES NUCLEAIRES")
    print("-" * 50)
    
    error_real_mass, errors_rand_mass, p_mass = run_randomization_parallel(
        mass_data, Lambda_MeV, n_iterations
    )
    
    print(f"\nRESULTATS DES MASSES:")
    print(f"  - Erreur avec beta reelles: {error_real_mass:.6f}%")
    print(f"  - Erreur mediane aleatoire: {np.median(errors_rand_mass):.6f}%")
    print(f"  - Erreur min aleatoire: {np.min(errors_rand_mass):.6f}%")
    print(f"  - Erreur max aleatoire: {np.max(errors_rand_mass):.6f}%")
    print(f"  - p-valeur: {p_mass:.6f}")
    
    plot_results(error_real_mass, errors_rand_mass, "Masses nucleaires", 
                 "monte_carlo_masses.pdf")
    
    # ============================================================
    # TEST SUR LES IONISATIONS
    # ============================================================
    print("\n" + "-" * 50)
    print("TEST DE RANDOMISATION - ENERGIES D'IONISATION")
    print("-" * 50)
    
    error_real_ion, errors_rand_ion, p_ion = run_randomization_parallel(
        ion_data, Lambda_eV, n_iterations
    )
    
    print(f"\nRESULTATS DES IONISATIONS:")
    print(f"  - Erreur avec beta reelles: {error_real_ion:.6f}%")
    print(f"  - Erreur mediane aleatoire: {np.median(errors_rand_ion):.6f}%")
    print(f"  - Erreur min aleatoire: {np.min(errors_rand_ion):.6f}%")
    print(f"  - Erreur max aleatoire: {np.max(errors_rand_ion):.6f}%")
    print(f"  - p-valeur: {p_ion:.6f}")
    
    plot_results(error_real_ion, errors_rand_ion, "Energies d'ionisation", 
                 "monte_carlo_ionisations.pdf")
    
    # ============================================================
    # CONCLUSION
    # ============================================================
    print("\n" + "=" * 70)
    print("CONCLUSION")
    print("=" * 70)
    
    if np.median(errors_rand_mass) < 1.0:
        print("\n[WARNING] Les erreurs aleatoires sont trop petites (<1%).")
    else:
        print("\n[OK] Les erreurs aleatoires sont de l'ordre de 10-20% (normales).")
    
    if p_mass < 0.01 and p_ion < 0.01:
        print("\n[OK] Les beta reelles sont significativement meilleures que des beta aleatoires.")
        print(f"     (p < 0.01 dans les deux domaines)")
    else:
        print("\n[WARNING] La significativite n'est pas etablie (p >= 0.01).")
    
    # Sauvegarde
    with open("monte_carlo_results.txt", "w") as f:
        f.write("MONTE-CARLO RANDOMIZATION TEST\n")
        f.write("=" * 50 + "\n\n")
        f.write("MASSES NUCLEAIRES:\n")
        f.write(f"  - Erreur avec beta reelles: {error_real_mass:.6f}%\n")
        f.write(f"  - Erreur mediane aleatoire: {np.median(errors_rand_mass):.6f}%\n")
        f.write(f"  - p-valeur: {p_mass:.6f}\n\n")
        f.write("ENERGIES D'IONISATION:\n")
        f.write(f"  - Erreur avec beta reelles: {error_real_ion:.6f}%\n")
        f.write(f"  - Erreur mediane aleatoire: {np.median(errors_rand_ion):.6f}%\n")
        f.write(f"  - p-valeur: {p_ion:.6f}\n")
    
    print("\n[OK] Resultats sauvegardes dans monte_carlo_results.txt")

if __name__ == "__main__":
    main()