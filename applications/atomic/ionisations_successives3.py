#!/usr/bin/env python3
# ionisations_successives.py

import numpy as np
from itertools import combinations, product
import csv
import sys
import re

# ============================================================
# Constantes et β universels
# ============================================================
Lambda_e = 5.950   # eV

beta = np.array([
    0.066136959, 0.281751380, 0.555869353, 0.868248673,
    1.504114125, 1.725183114, 1.831271203, 2.017424480,
    2.092834951, 2.524926754, 3.279177783, 3.851497776,
    4.571886169, 4.724739150, 7.408061012
])

# Dictionnaire des symboles chimiques (Z -> symbole)
symbole_Z = {
    1: 'H', 2: 'He', 3: 'Li', 4: 'Be', 5: 'B', 6: 'C', 7: 'N', 8: 'O', 9: 'F', 10: 'Ne',
    11: 'Na', 12: 'Mg', 13: 'Al', 14: 'Si', 15: 'P', 16: 'S', 17: 'Cl', 18: 'Ar', 19: 'K', 20: 'Ca',
    21: 'Sc', 22: 'Ti', 23: 'V', 24: 'Cr', 25: 'Mn', 26: 'Fe', 27: 'Co', 28: 'Ni', 29: 'Cu', 30: 'Zn',
    31: 'Ga', 32: 'Ge', 33: 'As', 34: 'Se', 35: 'Br', 36: 'Kr', 37: 'Rb', 38: 'Sr', 39: 'Y', 40: 'Zr',
    41: 'Nb', 42: 'Mo', 43: 'Tc', 44: 'Ru', 45: 'Rh', 46: 'Pd', 47: 'Ag', 48: 'Cd', 49: 'In', 50: 'Sn',
    51: 'Sb', 52: 'Te', 53: 'I', 54: 'Xe', 55: 'Cs', 56: 'Ba', 57: 'La', 58: 'Ce', 59: 'Pr', 60: 'Nd',
    61: 'Pm', 62: 'Sm', 63: 'Eu', 64: 'Gd', 65: 'Tb', 66: 'Dy', 67: 'Ho', 68: 'Er', 69: 'Tm', 70: 'Yb',
    71: 'Lu', 72: 'Hf', 73: 'Ta', 74: 'W', 75: 'Re', 76: 'Os', 77: 'Ir', 78: 'Pt', 79: 'Au', 80: 'Hg',
    81: 'Tl', 82: 'Pb', 83: 'Bi', 84: 'Po', 85: 'At', 86: 'Rn', 87: 'Fr', 88: 'Ra', 89: 'Ac', 90: 'Th',
    91: 'Pa', 92: 'U', 93: 'Np', 94: 'Pu', 95: 'Am', 96: 'Cm', 97: 'Bk', 98: 'Cf', 99: 'Es', 100: 'Fm'
}

def clean_nist_value(val):
    """Nettoie les valeurs du format NIST comme '="1"' ou '="13.598434599702"'"""
    if not val:
        return val
    val = val.strip()
    # Enlève les guillemets et le signe égal
    if val.startswith('="') and val.endswith('"'):
        val = val[2:-1]
    elif val.startswith('"') and val.endswith('"'):
        val = val[1:-1]
    return val

# ============================================================
# Génération des combinaisons ternaires (Δ = ε·β)
# ============================================================
def generate_delta_values(max_active=6):
    n = len(beta)
    deltas = []
    coeffs_list = []
    for k in range(1, max_active+1):
        for idx in combinations(range(n), k):
            for signs in product([-1, 1], repeat=k):
                coeff = np.zeros(n)
                for i, s in zip(idx, signs):
                    coeff[i] = s
                delta = np.dot(coeff, beta)
                if delta > 1e-12:
                    # Normalisation : premier coefficient non nul positif
                    first = next(i for i in range(n) if coeff[i] != 0)
                    if coeff[first] < 0:
                        coeff = -coeff
                        delta = -delta
                    deltas.append(delta)
                    coeffs_list.append(coeff)
    order = np.argsort(deltas)
    return np.array(deltas)[order], [coeffs_list[i] for i in order]

print("Génération des combinaisons ternaires...", file=sys.stderr)
delta_vals, coeffs_vals = generate_delta_values(max_active=6)
print(f"Nombre de Δ distincts : {len(delta_vals)}", file=sys.stderr)

# ============================================================
# Recherche du meilleur (m, Δ) pour une énergie donnée
# ============================================================
def best_match(E, m_range=range(-5, 6)):
    best_err = float('inf')
    best_m = None
    best_delta = None
    best_coeff = None
    for m in m_range:
        factor = 4.0 ** m
        target = E / (Lambda_e * factor)
        if target < 0.01 or target > 20:
            continue
        idx = np.searchsorted(delta_vals, target)
        if idx == len(delta_vals):
            idx = len(delta_vals) - 1
        for candidate_idx in (idx, idx-1):
            if candidate_idx < 0 or candidate_idx >= len(delta_vals):
                continue
            delta = delta_vals[candidate_idx]
            pred = Lambda_e * factor * delta
            err = abs(pred - E) / E
            if err < best_err:
                best_err = err
                best_m = m
                best_delta = delta
                best_coeff = coeffs_vals[candidate_idx]
    return best_m, best_delta, best_coeff, best_err

# ============================================================
# Lecture du fichier d'entrée (format NIST)
# ============================================================
def read_data(filename):
    data = []
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)  # Lire l'en-tête
        
        for row in reader:
            if not row or row[0].startswith('#'):
                continue
            
            # Format NIST: 
            # 0: At. num, 1: Sp. Name, 2: Ion Charge, 3: El. Name, 
            # 4: Isoel. Seq., 5: Ground Shells, 6: Ground Level, 
            # 7: Ionized Level, 8: Prefix, 9: Ionization Energy, 
            # 10: Suffix, 11: Uncertainty, 12: References
            if len(row) >= 10:
                # Nettoyer chaque champ
                Z_str = clean_nist_value(row[0])
                sp_name = clean_nist_value(row[1])
                
                # Extraire Z
                try:
                    Z = int(float(Z_str))  # Convertir en float d'abord pour gérer '1.0'
                except (ValueError, TypeError):
                    # Essaye d'extraire le nombre du format "H I"
                    match = re.search(r'(\d+)', sp_name)  # Cherche un nombre dans "H I"
                    if match:
                        Z = int(match.group(1))
                    else:
                        print(f"Impossible de lire Z pour la ligne: {row[:3]}", file=sys.stderr)
                        continue
                
                # Extraire k (Ion Charge)
                k_str = clean_nist_value(row[2])
                try:
                    k = int(float(k_str))  # Convertir en float d'abord
                except (ValueError, TypeError):
                    # Parfois c'est vide ou '0' avec guillemets
                    if k_str == '':
                        k = 0
                    else:
                        print(f"Impossible de lire k pour la ligne: {row[:3]}", file=sys.stderr)
                        continue
                
                # Extraire l'énergie d'ionisation
                E_str = clean_nist_value(row[9])
                try:
                    E = float(E_str)
                except (ValueError, TypeError):
                    # Valeur vide ou invalide
                    print(f"Impossible de lire l'énergie pour Z={Z}, k={k}", file=sys.stderr)
                    continue
                
                # Filtrer les valeurs valides
                if E > 0:
                    data.append((Z, k, E))
                    print(f"Lecture: Z={Z}, k={k}, E={E} eV", file=sys.stderr)
    
    return data

# ============================================================
# Formatage des coefficients ε en 15 champs Eps_0 à Eps_14
# ============================================================
def format_eps_fields(coeff):
    """Convertit le vecteur coeff en 15 champs Eps_0 à Eps_14"""
    eps_fields = {}
    for i in range(15):  # 0 à 14
        if i < len(coeff):
            eps_fields[f'Eps_{i}'] = int(coeff[i]) if coeff[i] != 0 else 0
        else:
            eps_fields[f'Eps_{i}'] = 0
    return eps_fields

# ============================================================
# Calcul du facteur 4^(Z,k) = 4^(Z - k)
# ============================================================
def calculate_factor_4(Z, k):
    """Calcule 4^(Z - k)"""
    exponent = Z - k
    return 4.0 ** exponent

# ============================================================
# Main
# ============================================================
def main():
    if len(sys.argv) < 2:
        print("Usage: python ionisations_successives.py fichier_nist.csv")
        sys.exit(1)

    input_file = sys.argv[1]
    data = read_data(input_file)
    if not data:
        print("Aucune donnée lue. Vérifiez le format du fichier.", file=sys.stderr)
        sys.exit(1)

    print(f"\nAnalyse des ionisations successives (Λ_e = {Lambda_e:.3f} eV)")
    print(f"Nombre de données lues : {len(data)}\n")
    print(f"{'Sym':>3} {'Z':>3} {'k':>3} {'E_exp (eV)':>12} {'E_pred (eV)':>12} {'m':>3} {'Δ':>12} {'Err (%)':>10} {'4^(Z-k)':>12} {'λ_e':>10}")
    print("-" * 115)

    results = []
    for Z, k, E_exp in data:
        m, delta, coeff, err = best_match(E_exp)
        if m is None:
            symb = symbole_Z.get(Z, f'Z{Z}')
            print(f"{symb:3s} {Z:3d} {k:3d} {E_exp:12.5f} {'--':12} {'--':3} {'--':12} {'--':10} {'--':12} {'--':10}")
            continue
        
        # Calcul des grandeurs
        symb = symbole_Z.get(Z, f'Z{Z}')
        factor_4 = calculate_factor_4(Z, k)
        E_pred = Lambda_e * (4.0 ** m) * delta
        err_pct = err * 100
        eps_fields = format_eps_fields(coeff)
        
        # Affichage console
        print(f"{symb:3s} {Z:3d} {k:3d} {E_exp:12.5f} {E_pred:12.5f} {m:3d} {delta:12.6f} {err_pct:9.5f}% {factor_4:12.6f} {Lambda_e:10.3f}")
        
        # Construction de la ligne de résultats avec les 15 champs Eps
        result_row = {
            'Z': Z,
            'k': k,
            'Symbole': symb,
            'E_exp_eV': E_exp,
            'E_pred_eV': E_pred,
            'm': m,
            'Delta': delta,
            'Err_percent': err_pct,
            'Lambda_e': Lambda_e,
            'Factor_4_Zk': factor_4,
        }
        # Ajout des 15 champs Eps
        result_row.update(eps_fields)
        results.append(result_row)

    # Sauvegarde CSV avec tous les champs
    out_file = "resultats_ionisations.csv"
    if results:
        # Définition de l'ordre des colonnes
        fieldnames = ['Z', 'k', 'Symbole', 'E_exp_eV', 'E_pred_eV', 'm', 'Delta', 
                      'Err_percent', 'Lambda_e', 'Factor_4_Zk']
        # Ajout des Eps_0 à Eps_14
        fieldnames.extend([f'Eps_{i}' for i in range(15)])
        
        with open(out_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        
        print(f"\nRésultats sauvegardés dans {out_file}")
        print(f"Nombre de lignes : {len(results)}")
        print(f"Champs inclus : {', '.join(fieldnames[:15])}...")
    else:
        print("\nAucun résultat à sauvegarder.")

if __name__ == '__main__':
    main()