#!/usr/bin/env python3
# cross_validation.py

import numpy as np
from itertools import combinations, product
import csv
import random

# ============================================================
# Constantes
# ============================================================
Lambda_MeV = 7.726      # MeV pour les masses
Lambda_eV = 5.950       # eV pour les ionisations
u_to_MeV = 931.49410242 # conversion u → MeV

# Les 15 constantes beta_k
beta = np.array([
    0.066136959, 0.281751380, 0.555869353, 0.868248673,
    1.504114125, 1.725183114, 1.831271203, 2.017424480,
    2.092834951, 2.524926754, 3.279177783, 3.851497776,
    4.571886169, 4.724739150, 7.408061012
])

# ============================================================
# Génération des combinaisons ternaires Δ = ε·β
# ============================================================
def generate_delta_values(max_active=6):
    n = len(beta)
    deltas = []
    coeffs_list = []
    for k in range(1, max_active+1):
        for idx in combinations(range(n), k):
            for signs in product([-1, 1], repeat=k):
                coeff = np.zeros(n)
                val = 0.0
                for i, s in zip(idx, signs):
                    coeff[i] = s
                    val += s * beta[i]
                if val > 0:
                    first = next(i for i in range(n) if coeff[i] != 0)
                    if coeff[first] < 0:
                        coeff = -coeff
                        val = -val
                    deltas.append(val)
                    coeffs_list.append(coeff.copy())
    order = np.argsort(deltas)
    return np.array(deltas)[order], [coeffs_list[i] for i in order]

print("Génération des combinaisons ternaires...")
delta_vals, coeffs_vals = generate_delta_values(max_active=6)
print(f"Nombre de Δ distincts : {len(delta_vals)}")

# ============================================================
# Prédiction pour une valeur donnée
# ============================================================
def predict(value, Lambda, m_range=range(-5, 16)):
    best_err = float('inf')
    best_pred = None
    for m in m_range:
        factor = 4 ** m
        target = value / (Lambda * factor)
        if target < 0.01 or target > 20:
            continue
        idx = np.searchsorted(delta_vals, target)
        if idx == len(delta_vals):
            idx = len(delta_vals) - 1
        for candidate_idx in (idx, idx-1):
            if candidate_idx < 0 or candidate_idx >= len(delta_vals):
                continue
            delta = delta_vals[candidate_idx]
            pred = Lambda * factor * delta
            err = abs(pred - value) / value if value != 0 else abs(pred)
            if err < best_err:
                best_err = err
                best_pred = pred
    return best_pred, best_err

# ============================================================
# Chargement des données
# ============================================================
def load_mass_data(filename):
    data = []
    ignored_empty = 0
    ignored_hash = 0
    ignored_z = 0
    total = 0
    
    with open(filename, 'r') as f:
        reader = csv.reader(f)
        next(reader)
        
        for row in reader:
            total += 1
            if len(row) < 13:
                continue
            
            Z_str = row[2].strip()
            A_str = row[3].strip()
            mass_str = row[12].strip().replace(' ', '')
            
            if '#' in mass_str:
                ignored_hash += 1
                continue
            if mass_str == '':
                ignored_empty += 1
                continue
            
            Z = int(Z_str)
            if Z < 1:
                ignored_z += 1
                continue
            
            A = int(A_str)
            mass_u = float(mass_str)
            mass_MeV = mass_u * u_to_MeV
            data.append((Z, A, mass_MeV))
    
    print(f"Total lignes: {total}")
    print(f"  - Ignorées (#): {ignored_hash}")
    print(f"  - Ignorées (Z<1): {ignored_z}")
    print(f"  - Ignorées (vide): {ignored_empty}")
    print(f"  - Chargées: {len(data)}")
    
    return data

def load_ionization_data(filename):
    """Charge les énergies d'ionisation depuis ionisations_simplifie.csv"""
    data = []
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # saut en-tête (Z, k, E_eV)
        
        for row in reader:
            if len(row) < 3:
                continue
            
            try:
                Z = int(row[0])
                k = int(row[1])
                E = float(row[2])
                if E > 0:
                    data.append((Z, k, E))
            except (ValueError, IndexError):
                continue
    
    return data

# ============================================================
# Validation croisée k-fold
# ============================================================
def cross_validation(data, Lambda, k_folds=5, random_seed=42):
    random.seed(random_seed)
    shuffled = data.copy()
    random.shuffle(shuffled)
    
    n = len(shuffled)
    fold_size = n // k_folds
    
    train_errors = []
    test_errors = []
    
    for fold in range(k_folds):
        test_start = fold * fold_size
        test_end = (fold + 1) * fold_size if fold < k_folds - 1 else n
        test_data = shuffled[test_start:test_end]
        train_data = shuffled[:test_start] + shuffled[test_end:]
        
        err_train_sum = 0.0
        for _, _, val in train_data:
            _, err = predict(val, Lambda)
            err_train_sum += err
        
        err_test_sum = 0.0
        for _, _, val in test_data:
            _, err = predict(val, Lambda)
            err_test_sum += err
        
        train_errors.append(err_train_sum / len(train_data) * 100)
        test_errors.append(err_test_sum / len(test_data) * 100)
    
    return train_errors, test_errors

# ============================================================
# Main
# ============================================================
def main():
    print("\n" + "="*60)
    print("VALIDATION CROISÉE DU MODÈLE")
    print("="*60)
    
    # Fichiers
    mass_file = "ame2020_VERIFIED.csv"
    ion_file = "ionisations_simplifie.csv"
    k_folds = 5
    
    print(f"\nFichier masses : {mass_file}")
    print(f"Fichier ionisations : {ion_file}")
    print(f"Nombre de folds : {k_folds}")
    
    # Chargement
    print("\nChargement des données...")
    mass_data = load_mass_data(mass_file)
    ion_data = load_ionization_data(ion_file)
    
    print(f"  - Masses nucléaires : {len(mass_data)} isotopes")
    print(f"  - Énergies d'ionisation : {len(ion_data)} points")
    
    # Validation croisée pour les masses
    if len(mass_data) > 0:
        print("\n" + "-"*50)
        print("Validation croisée - Masses nucléaires (Λ = 7.726 MeV)")
        print("-"*50)
        train_err, test_err = cross_validation(mass_data, Lambda_MeV, k_folds)
        
        print(f"Erreur moyenne entraînement : {np.mean(train_err):.6f} %")
    
    # Validation croisée pour les ionisations
    if len(ion_data) > 0:
        print("\n" + "-"*50)
        print("Validation croisée - Énergies d'ionisation (Λ = 5.950 eV)")
        print("-"*50)
        train_err, test_err = cross_validation(ion_data, Lambda_eV, k_folds)
        
        print(f"Erreur moyenne entraînement : {np.mean(train_err):.6f} %")
    
    # Sauvegarde
    with open('cross_validation_results.txt', 'w') as f:
        f.write("Résultats de la validation croisée\n")
        f.write("="*50 + "\n\n")
        f.write(f"Masses nucléaires ({len(mass_data)} isotopes, {k_folds} folds):\n")
        f.write(f"  - Erreur entraînement : {np.mean(train_err):.6f} %\n")
        f.write(f"  - Erreur test : {np.mean(test_err):.6f} %\n")
        f.write(f"  - Écart : {abs(np.mean(train_err) - np.mean(test_err)):.6f} %\n\n")
        f.write(f"Énergies d'ionisation ({len(ion_data)} points, {k_folds} folds):\n")
        f.write(f"  - Erreur entraînement : {np.mean(train_err):.6f} %\n")
        f.write(f"  - Erreur test : {np.mean(test_err):.6f} %\n")
        f.write(f"  - Écart : {abs(np.mean(train_err) - np.mean(test_err)):.6f} %\n")
    
    print("\n✅ Résultats sauvegardés dans cross_validation_results.txt")

if __name__ == '__main__':
    main()
