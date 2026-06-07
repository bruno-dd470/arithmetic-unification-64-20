import numpy as np
from itertools import product
from tqdm import tqdm
import json
import csv

# ============================================================================
# CONSTANTES
# ============================================================================

# Base réduite des 15 racines (dans l'ordre Table III)
beta = [
    0.066136959000,   # β0 - 1s1/2
    0.281751380000,   # β1 - 2p1/2
    0.555869353000,   # β2 - 3s1/2
    0.868248673000,   # β3 - 3p1/2
    1.504114125000,   # β4 - 2g9/2
    1.725183114000,   # β5 - 3d5/2
    1.831271203000,   # β6 - 4p1/2
    2.017424480000,   # β7 - 1j15/2
    2.092834951000,   # β8 - 2h9/2
    2.524926754000,   # β9 - 3f5/2
    3.279177783000,   # β10 - 5p1/2
    3.851497776000,   # β11 - 6s1/2
    4.571886169000,   # β12 - 1k17/2
    4.724739150000,   # β13 - 2i11/2
    7.408061012000    # β14 - 3g9/2
]

# Noms des éléments chimiques
ELEMENTS = {
    0: "n", 1: "H", 2: "He", 3: "Li", 4: "Be", 5: "B", 6: "C", 7: "N", 8: "O", 9: "F", 10: "Ne",
    11: "Na", 12: "Mg", 13: "Al", 14: "Si", 15: "P", 16: "S", 17: "Cl", 18: "Ar", 19: "K", 20: "Ca",
    21: "Sc", 22: "Ti", 23: "V", 24: "Cr", 25: "Mn", 26: "Fe", 27: "Co", 28: "Ni", 29: "Cu", 30: "Zn",
    31: "Ga", 32: "Ge", 33: "As", 34: "Se", 35: "Br", 36: "Kr", 37: "Rb", 38: "Sr", 39: "Y", 40: "Zr",
    41: "Nb", 42: "Mo", 43: "Tc", 44: "Ru", 45: "Rh", 46: "Pd", 47: "Ag", 48: "Cd", 49: "In", 50: "Sn",
    51: "Sb", 52: "Te", 53: "I", 54: "Xe", 55: "Cs", 56: "Ba", 57: "La", 58: "Ce", 59: "Pr", 60: "Nd",
    61: "Pm", 62: "Sm", 63: "Eu", 64: "Gd", 65: "Tb", 66: "Dy", 67: "Ho", 68: "Er", 69: "Tm", 70: "Yb",
    71: "Lu", 72: "Hf", 73: "Ta", 74: "W", 75: "Re", 76: "Os", 77: "Ir", 78: "Pt", 79: "Au", 80: "Hg",
    81: "Tl", 82: "Pb", 83: "Bi", 84: "Po", 85: "At", 86: "Rn", 87: "Fr", 88: "Ra", 89: "Ac", 90: "Th",
    91: "Pa", 92: "U", 93: "Np", 94: "Pu", 95: "Am", 96: "Cm", 97: "Bk", 98: "Cf", 99: "Es", 100: "Fm",
    101: "Md", 102: "No", 103: "Lr", 104: "Rf", 105: "Db", 106: "Sg", 107: "Bh", 108: "Hs", 109: "Mt", 110: "Ds",
    111: "Rg", 112: "Cn", 113: "Nh", 114: "Fl", 115: "Mc", 116: "Lv", 117: "Ts", 118: "Og"
}

# Constante nucléaire (MeV)
LAMBDA_NUC = 7.726

# ============================================================================
# PRÉ-CALCUL DES COMBINAISONS POUR ACCÉLÉRER LA RECHERCHE
# ============================================================================

def precalculer_combinaisons(tol=1e-8):
    """
    Pré-calcule toutes les combinaisons ternaires possibles avec leurs valeurs.
    Retourne un dictionnaire {valeur_arrondie: (epsilon, valeur_exacte)}
    """
    print("🔄 Pré-calcul des combinaisons ternaires...")
    combos = {}
    
    # 3^15 = 14M combinaisons - on utilise une approche plus intelligente
    # On se limite aux combinaisons avec max 6 termes actifs (les plus probables)
    from itertools import combinations
    
    n = len(beta)
    total_combos = 0
    
    for n_actifs in tqdm(range(1, 7), desc="  Termes actifs"):
        for indices in combinations(range(n), n_actifs):
            for signes in product([-1, 1], repeat=n_actifs):
                eps = [0] * n
                val = 0.0
                for idx, sgn in zip(indices, signes):
                    eps[idx] = sgn
                    val += sgn * beta[idx]
                
                if 0.01 < val < 12.0:  # Plage réaliste pour Δ
                    # Arrondir pour éviter les problèmes de flottants
                    val_key = round(val, 10)
                    if val_key not in combos:
                        combos[val_key] = (eps, val)
                    total_combos += 1
    
    # Ajouter la combinaison nulle
    combos[0.0] = ([0] * n, 0.0)
    
    print(f"  ✅ {len(combos)} combinaisons uniques pré-calculées")
    return combos

# Pré-calculer les combinaisons (global pour éviter de recalculer)
COMBOS = precalculer_combinaisons()

def epsilon_from_delta_fast(delta, tol=1e-6):
    """
    Version rapide utilisant le pré-calcul.
    Trouve les coefficients ε_k ∈ {-1,0,1} tels que Σ ε_k β_k ≈ delta
    """
    # Chercher la valeur la plus proche dans le dictionnaire pré-calculé
    meilleure_erreur = float('inf')
    meilleur_coeffs = None
    meilleure_valeur = 0
    
    # Parcourir les combinaisons pré-calculées
    for val_key, (eps, val) in COMBOS.items():
        erreur = abs(val - delta)
        if erreur < meilleure_erreur:
            meilleure_erreur = erreur
            meilleur_coeffs = eps
            meilleure_valeur = val
            if erreur < tol:
                break
    
    erreur_rel = (meilleure_erreur / delta * 100) if delta != 0 else 0
    return meilleur_coeffs, meilleure_valeur, erreur_rel

def signature_to_str(eps):
    """
    Convertit les coefficients ε en chaîne lisible (format: +0 -3 +5)
    """
    actifs = []
    for k, val in enumerate(eps):
        if val == 1:
            actifs.append(f"+{k}")
        elif val == -1:
            actifs.append(f"-{k}")
    return ' '.join(actifs) if actifs else "0"

def reconstruire_masse(m, delta):
    """
    Reconstruit la masse à partir de m et delta
    M = Λ × 4^m × Δ
    """
    return LAMBDA_NUC * (4 ** m) * delta

def get_isotope_symbol(Z, A):
    """Retourne le symbole de l'isotope (ex: H-1, Fe-56)"""
    nom = ELEMENTS.get(Z, f"X{Z}")
    return f"{nom}-{A}"

# ============================================================================
# LECTURE DES DONNÉES
# ============================================================================

def lire_isotopes(filename):
    """Lit le fichier des isotopes et retourne une liste"""
    isotopes = []
    with open(filename, "r") as f:
        # Sauter l'en-tête
        header = f.readline()
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split()
            if len(parts) < 7:
                continue
            isotopes.append({
                'Z': int(parts[0]),
                'A': int(parts[1]),
                'M_exp': float(parts[2]),
                'm_oct': int(parts[3]),
                'delta': float(parts[4]),
                'M_pred': float(parts[5]),
                'err_original': float(parts[6])
            })
    return isotopes

# ============================================================================
# TRAITEMENT PRINCIPAL
# ============================================================================

def main():
    print("=" * 100)
    print("PROJECTION DES ISOTOPES SUR LA BASE DES 15 RACINES Λ₇₂")
    print("=" * 100)
    
    # Fichiers d'entrée et de sortie
    input_file = "isotope_fits_original.txt"
    output_file = "isotopes_projetes_15_racines.csv"
    json_file = "isotopes_projetes_15_racines.json"
    
    # Lecture des données
    print("\n📖 Lecture du fichier des isotopes...")
    isotopes = lire_isotopes(input_file)
    print(f"   {len(isotopes)} isotopes chargés")
    
    # Traitement avec barre de progression
    print("\n🔍 Projection sur les 15 racines...")
    resultats = []
    erreurs = []
    non_trouves = []
    
    # Barre de progression tqdm
    with tqdm(total=len(isotopes), desc="  Projection", unit="isotope", ncols=100) as pbar:
        for iso in isotopes:
            Z = iso['Z']
            A = iso['A']
            M_exp = iso['M_exp']
            m_oct = iso['m_oct']
            delta = iso['delta']
            M_pred = iso['M_pred']
            err_original = iso['err_original']
            
            # Recherche des coefficients ε (version rapide)
            eps, delta_calc, erreur_eps = epsilon_from_delta_fast(delta)
            
            if eps is None:
                non_trouves.append((Z, A, delta))
                pbar.set_postfix({"non_trouves": len(non_trouves)})
                pbar.update(1)
                continue
            
            # Symbole de l'isotope
            symbole = get_isotope_symbol(Z, A)
            
            # Générer la signature lisible
            sig_str = signature_to_str(eps)
            
            # Stocker
            resultats.append({
                'Z': Z, 'A': A, 'symbole': symbole,
                'M_exp': M_exp, 'm': m_oct, 'delta': delta,
                'M_pred': M_pred, 'err_original': err_original,
                'epsilon': eps, 'signature': sig_str,
                'delta_calc': delta_calc, 'erreur_epsilon': erreur_eps
            })
            erreurs.append(erreur_eps)
            
            # Mise à jour de la barre
            pbar.update(1)
            if len(resultats) % 50 == 0:
                pbar.set_postfix({"ok": len(resultats), "err_moy": f"{np.mean(erreurs):.2e}"})
    
    # ========================================================================
    # ÉCRITURE DU FICHIER DE SORTIE
    # ========================================================================
    print("\n💾 Écriture du fichier de sortie...")
    
    with open(output_file, 'w', newline='') as f_out:
        writer = csv.writer(f_out)
        
        # En-tête CSV
        writer.writerow(['Z', 'A', 'symbole', 'M_exp_MeV', 'm_oct', 'Delta', 'M_pred_MeV', 'err_pct', 'signature_epsilon', 'epsilon_0', 'epsilon_1', 'epsilon_2', 'epsilon_3', 'epsilon_4', 'epsilon_5', 'epsilon_6', 'epsilon_7', 'epsilon_8', 'epsilon_9', 'epsilon_10', 'epsilon_11', 'epsilon_12', 'epsilon_13', 'epsilon_14'])
        
        for r in tqdm(resultats, desc="  Écriture", unit="ligne"):
            # Écrire une ligne CSV avec les 15 coefficients epsilon en colonnes séparées
            row = [
                r['Z'], r['A'], r['symbole'], 
                f"{r['M_exp']:.3f}", r['m'], f"{r['delta']:.6f}", 
                f"{r['M_pred']:.3f}", f"{r['err_original']:.4f}", 
                r['signature']
            ]
            # Ajouter les 15 coefficients epsilon
            row.extend(r['epsilon'])
            writer.writerow(row)
    
    # ========================================================================
    # SAUVEGARDE JSON
    # ========================================================================
    with open(json_file, 'w') as f_json:
        json_data = {
            'meta': {
                'description': 'Projection des isotopes sur les 15 racines de Λ72',
                'lambda_nuc_MeV': LAMBDA_NUC,
                'nb_isotopes': len(resultats),
                'erreur_epsilon_moyenne_pct': float(np.mean(erreurs)) if erreurs else 0,
                'erreur_epsilon_max_pct': float(np.max(erreurs)) if erreurs else 0
            },
            'beta_racines': beta,
            'isotopes': [
                {
                    'Z': r['Z'],
                    'A': r['A'],
                    'symbole': r['symbole'],
                    'M_exp_MeV': r['M_exp'],
                    'm_oct': r['m'],
                    'Delta': r['delta'],
                    'M_pred_MeV': r['M_pred'],
                    'err_pct': r['err_original'],
                    'epsilon': r['epsilon'],
                    'signature': r['signature']
                }
                for r in resultats
            ]
        }
        json.dump(json_data, f_json, indent=2)
    
    # ========================================================================
    # STATISTIQUES
    # ========================================================================
    print("\n" + "=" * 100)
    print("📊 STATISTIQUES DE LA PROJECTION")
    print("=" * 100)
    print(f"  Isotopes traités avec succès : {len(resultats)}")
    print(f"  Isotopes non trouvés         : {len(non_trouves)}")
    
    if erreurs:
        print(f"  Erreur epsilon moyenne       : {np.mean(erreurs):.4e} %")
        print(f"  Erreur epsilon médiane       : {np.median(erreurs):.4e} %")
        print(f"  Erreur epsilon max           : {np.max(erreurs):.4e} %")
        print(f"  Erreur epsilon min           : {np.min(erreurs):.4e} %")
        print(f"  Écart-type des erreurs       : {np.std(erreurs):.4e} %")
    
    if non_trouves:
        print(f"\n⚠️ Isotopes sans combinaison ε trouvée:")
        for Z, A, delta in non_trouves[:10]:
            print(f"     {get_isotope_symbol(Z, A)} (delta={delta:.6f})")
    
    print(f"\n💾 Fichiers sauvegardés :")
    print(f"     - {output_file}")
    print(f"     - {json_file}")
    
    # ========================================================================
    # APERÇU DES PREMIERS RÉSULTATS
    # ========================================================================
    print("\n" + "=" * 100)
    print("APERÇU DES PREMIERS ISOTOPES")
    print("=" * 100)
    print(f"{'Symbole':>8s} {'M_exp(MeV)':>12s} {'m':>3s} {'Delta':>10s} {'Signature ε':<40s}")
    print("-" * 80)
    
    for r in resultats[:20]:
        print(f"{r['symbole']:>8s} {r['M_exp']:12.3f} {r['m']:3d} {r['delta']:10.6f} {r['signature']:<40s}")
    
    # ========================================================================
    # VÉRIFICATION DES 15 β
    # ========================================================================
    print("\n" + "=" * 100)
    print("VÉRIFICATION : LES 15 RACINES β_k DANS LES ISOTOPES")
    print("=" * 100)
    
    for k, b in enumerate(beta):
        trouve = False
        for r in resultats:
            if abs(r['delta'] - b) < 1e-6:
                print(f"  β_{k:2d} = {b:.9f} → trouvé dans {r['symbole']}")
                trouve = True
                break
        if not trouve:
            for r in resultats:
                if len(r['epsilon']) > k and abs(r['epsilon'][k]) == 1:
                    print(f"  β_{k:2d} = {b:.9f} → présent dans {r['symbole']} (ε={r['epsilon'][k]})")
                    trouve = True
                    break
        if not trouve:
            print(f"  β_{k:2d} = {b:.9f} → ⚠️ non trouvé")

if __name__ == "__main__":
    main()
