#!/usr/bin/env python3
"""
randomization_test.py - Version avec plus de simulations
"""

import numpy as np
from itertools import combinations, product
import csv
import random
import sys
import matplotlib.pyplot as plt
from multiprocessing import Pool, cpu_count
from functools import partial

Lambda_MeV = 7.726
Lambda_eV = 5.950

beta_real = np.array([
    0.066136959, 0.281751380, 0.555869353, 0.868248673,
    1.504114125, 1.725183114, 1.831271203, 2.017424480,
    2.092834951, 2.524926754, 3.279177783, 3.851497776,
    4.571886169, 4.724739150, 7.408061012
])

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

def predict(value, Lambda, delta_vals):
    best_err = float('inf')
    for m in range(-5, 16):
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
    beta, data, Lambda = beta_data
    delta_vals = generate_delta_values(beta, 6)
    if len(delta_vals) == 0:
        return 100.0
    total_err = 0.0
    for _, _, val in data:
        err = predict(val, Lambda, delta_vals)
        total_err += err
    return total_err / len(data) * 100

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

def run_randomization_parallel(data, Lambda, n_iterations=10000):
    print("  Calcul de l'erreur avec beta reels...")
    error_real = evaluate_single_beta((beta_real, data, Lambda))
    print(f"    Erreur reelle: {error_real:.8f}%")
    
    print(f"  Generation de {n_iterations} jeux de beta aleatoires...")
    random.seed(42)
    np.random.seed(42)
    
    # Differentes strategies pour generer des beta aleatoires
    # Strategy 1: uniforme [0, 10]
    random_betas = [np.random.uniform(0, 10, 15) for _ in range(n_iterations)]
    
    print(f"  Execution sur {cpu_count()} coeurs...")
    args = [(beta, data, Lambda) for beta in random_betas]
    
    with Pool(processes=cpu_count()) as pool:
        errors_random = pool.map(evaluate_single_beta, args)
    
    errors_random = np.array(errors_random)
    p_value = np.mean(errors_random <= error_real)
    
    return error_real, errors_random, p_value

def plot_results(errors_real, errors_random, domain_name, output_file):
    plt.figure(figsize=(12, 8))
    
    # Deux histogrammes: zoom sur les petites erreurs et vue d'ensemble
    plt.subplot(1, 2, 1)
    bins1 = np.linspace(0, min(0.001, np.max(errors_random)), 50)
    plt.hist(errors_random, bins=bins1, alpha=0.7, color='gray', edgecolor='black')
    plt.axvline(errors_real, color='red', linewidth=2, linestyle='-')
    plt.xlabel('Erreur moyenne (%)')
    plt.ylabel('Frequence')
    plt.title('Zoom sur les petites erreurs')
    plt.grid(alpha=0.3)
    
    plt.subplot(1, 2, 2)
    bins2 = np.linspace(0, max(0.01, np.max(errors_random)), 50)
    plt.hist(errors_random, bins=bins2, alpha=0.7, color='gray', edgecolor='black')
    plt.axvline(errors_real, color='red', linewidth=2, linestyle='-',
                label=f'Beta reelles: {errors_real:.6f}%')
    plt.xlabel('Erreur moyenne (%)')
    plt.ylabel('Frequence')
    plt.title('Vue d\'ensemble')
    plt.legend()
    plt.grid(alpha=0.3)
    
    p_val = np.mean(errors_random <= errors_real)
    plt.suptitle(f'Test de randomisation - {domain_name} (p = {p_val:.6f})', fontsize=14)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=150)
    plt.close()
    print(f"    Graphique sauvegarde: {output_file}")

def main():
    print("=" * 70)
    print("TEST DE RANDOMISATION - MONTE-CARLO (VERSION PARALLELE)")
    print("=" * 70)
    
    mass_file = "ame2020_clean+.csv"
    ion_file = "ionisations_simplifie.csv"
    n_iterations = 10000  # Augmente a 10000
    
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
    
    # TEST SUR LES MASSES
    print("\n" + "-" * 50)
    print("TEST DE RANDOMISATION - MASSES NUCLEAIRES")
    print("-" * 50)
    
    error_real_mass, errors_rand_mass, p_mass = run_randomization_parallel(
        mass_data, Lambda_MeV, n_iterations
    )
    
    print(f"\nRESULTATS DES MASSES:")
    print(f"  - Erreur avec beta reelles: {error_real_mass:.8f}%")
    print(f"  - Erreur mediane aleatoire: {np.median(errors_rand_mass):.8f}%")
    print(f"  - Erreur min aleatoire: {np.min(errors_rand_mass):.8f}%")
    print(f"  - Erreur max aleatoire: {np.max(errors_rand_mass):.8f}%")
    print(f"  - Ecart-type aleatoire: {np.std(errors_rand_mass):.8f}%")
    print(f"  - p-valeur: {p_mass:.6f}")
    print(f"  - Beta reelles meilleures que {p_mass*100:.2f}% des aleatoires")
    
    plot_results(error_real_mass, errors_rand_mass, "Masses nucleaires", 
                 "monte_carlo_masses.pdf")
    
    # TEST SUR LES IONISATIONS
    print("\n" + "-" * 50)
    print("TEST DE RANDOMISATION - ENERGIES D'IONISATION")
    print("-" * 50)
    
    error_real_ion, errors_rand_ion, p_ion = run_randomization_parallel(
        ion_data, Lambda_eV, n_iterations
    )
    
    print(f"\nRESULTATS DES IONISATIONS:")
    print(f"  - Erreur avec beta reelles: {error_real_ion:.8f}%")
    print(f"  - Erreur mediane aleatoire: {np.median(errors_rand_ion):.8f}%")
    print(f"  - Erreur min aleatoire: {np.min(errors_rand_ion):.8f}%")
    print(f"  - Erreur max aleatoire: {np.max(errors_rand_ion):.8f}%")
    print(f"  - Ecart-type aleatoire: {np.std(errors_rand_ion):.8f}%")
    print(f"  - p-valeur: {p_ion:.6f}")
    print(f"  - Beta reelles meilleures que {p_ion*100:.2f}% des aleatoires")
    
    plot_results(error_real_ion, errors_rand_ion, "Energies d'ionisation", 
                 "monte_carlo_ionisations.pdf")
    
    # CONCLUSION
    print("\n" + "=" * 70)
    print("CONCLUSION")
    print("=" * 70)
    
    if p_mass < 0.01 and p_ion < 0.01:
        print("\n[OK] Les beta reelles sont significativement meilleures que des beta aleatoires.")
    else:
        print("\n[WARNING] La significativite n'est pas etablie (p >= 0.01).")
    
    with open("monte_carlo_results.txt", "w") as f:
        f.write("MONTE-CARLO RANDOMIZATION TEST\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Simulations: {n_iterations}\n\n")
        f.write("MASSES NUCLEAIRES:\n")
        f.write(f"  - Erreur avec beta reelles: {error_real_mass:.8f}%\n")
        f.write(f"  - Erreur mediane aleatoire: {np.median(errors_rand_mass):.8f}%\n")
        f.write(f"  - p-valeur: {p_mass:.6f}\n\n")
        f.write("ENERGIES D'IONISATION:\n")
        f.write(f"  - Erreur avec beta reelles: {error_real_ion:.8f}%\n")
        f.write(f"  - Erreur mediane aleatoire: {np.median(errors_rand_ion):.8f}%\n")
        f.write(f"  - p-valeur: {p_ion:.6f}\n")
    
    print("\n[OK] Resultats sauvegardes dans monte_carlo_results.txt")

if __name__ == "__main__":
    main()