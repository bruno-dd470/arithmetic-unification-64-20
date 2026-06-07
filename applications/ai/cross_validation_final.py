#!/usr/bin/env python3
# cross_validation_final.py

import numpy as np
from itertools import combinations, product
import csv
import random

# ============================================================
# Constantes
# ============================================================
Lambda_MeV = 7.726      # MeV pour les masses
Lambda_eV = 5.950       # eV pour les ionisations

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
    for k in range(1, max_active+1):
        for idx in combinations(range(n), k):
            for signs in product([-1, 1], repeat=k):
                val = 0.0
                for i, s in zip(idx, signs):
                    val += s * beta[i]
                if val > 0:
                    deltas.append(val)
    deltas = list(set(deltas))  # Supprimer les doublons
    deltas.sort()
    return np.array(deltas)

print("Génération des combinaisons ternaires...")
delta_vals = generate_delta_values(max_active=6)
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
            best_pred = pred
    return best_pred, best_err

# ============================================================
# Chargement des données
# ============================================================
def load_masses(filename):
    """Charge les masses depuis ame2020_clean+.csv"""
    data = []
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            return data
        
        for row in reader:
            if len(row) < 2:
                continue
            try:
                # Format: Z,A,El,mass_MeV,estimated
                Z = int(float(row[0]))
                A = int(float(row[1]))
                mass_MeV = float(row[3])
                if Z > 0 and mass_MeV > 0:
                    data.append((Z, A, mass_MeV))
            except (ValueError, IndexError):
                continue
    return data

def load_ionizations(filename):
    """Charge les énergies d'ionisation depuis ionisations_simplifie.csv"""
    data = []
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
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
    mass_file = "ame2020_clean+.csv"
    ion_file = "ionisations_simplifie.csv"
    k_folds = 5
    
    print(f"\nFichier masses : {mass_file}")
    print(f"Fichier ionisations : {ion_file}")
    print(f"Nombre de folds : {k_folds}")
    
    # Chargement
    print("\nChargement des données...")
    mass_data = load_masses(mass_file)
    ion_data = load_ionizations(ion_file)
    
    print(f"  - Masses nucléaires : {len(mass_data)} isotopes")
    print(f"  - Énergies d'ionisation : {len(ion_data)} points")
    
    if len(mass_data) == 0:
        print("\n⚠️ Aucune donnée de masse chargée!")
        print("   Vérifiez le format du fichier ame2020_clean+.csv")
        print("   Format attendu: Z,A,El,mass_MeV,estimated")
        return
    
    if len(ion_data) == 0:
        print("\n⚠️ Aucune donnée d'ionisation chargée!")
        print("   Vérifiez le format du fichier ionisations_simplifie.csv")
        print("   Format attendu: Z,k,E_eV")
        return
    
    # Validation croisée pour les masses
    print("\n" + "-"*50)
    print("Validation croisée - Masses nucléaires (Λ = 7.726 MeV)")
    print("-"*50)
    train_err, test_err = cross_validation(mass_data, Lambda_MeV, k_folds)
    
    print(f"Erreur moyenne entraînement : {np.mean(train_err):.6f} %")
    
    # Validation croisée pour les ionisations
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
        f.write(f"  - Écart : {abs(np.mean(train_err) - np.mean(test_err)):.6f} %\n")
        f.write(f"  - Erreur max test : {np.max(test_err):.6f} %\n\n")
        f.write(f"Énergies d'ionisation ({len(ion_data)} points, {k_folds} folds):\n")
        f.write(f"  - Erreur entraînement : {np.mean(train_err):.6f} %\n")
        f.write(f"  - Erreur test : {np.mean(test_err):.6f} %\n")
        f.write(f"  - Écart : {abs(np.mean(train_err) - np.mean(test_err)):.6f} %\n")
        f.write(f"  - Erreur max test : {np.max(test_err):.6f} %\n")
    
    print("\n✅ Résultats sauvegardés dans cross_validation_results.txt")

if __name__ == '__main__':
    main()