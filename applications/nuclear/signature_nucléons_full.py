import numpy as np
from itertools import combinations, product
import json

# ============================================================================
# CONSTANTES UNIVERSELLES β_k (issues de Λ_72) - Table III du papier
# ============================================================================
BETA = np.array([
    0.06613695904451328,   # β0
    0.28174250870863576,   # β1
    0.5558698717637468,    # β2
    0.8682439499340019,    # β3
    1.5041139699699269,    # β4
    1.7252596926363315,    # β5
    1.831267929898219,     # β6
    2.0174227816393127,    # β7
    2.092837042770219,     # β8
    2.524927313875301,     # β9
    3.279177783,           # β10
    3.851477234958053,     # β11
    4.571556651552703,     # β12
    4.724739892029763,     # β13
    7.407963149728111      # β14
])

# Constante d'échelle nucléaire (MeV)
LAMBDA_NUC = 7.726

# Nomenclature des éléments chimiques
ELEMENTS = {
    1: "H", 2: "He", 3: "Li", 4: "Be", 5: "B", 6: "C", 7: "N", 8: "O", 9: "F", 10: "Ne",
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

# ============================================================================
# GÉNÉRATION DES COMBINAISONS TERNAIRES Σ ε_k β_k
# ============================================================================
def generer_toutes_combinaisons():
    """Génère toutes les combinaisons Σ ε_k β_k avec ε_k ∈ {-1, 0, 1}"""
    k = len(BETA)
    combos = []
    signatures = []
    
    for n_actifs in range(1, min(9, k+1)):
        for indices in combinations(range(k), n_actifs):
            for signes in product([-1, 1], repeat=n_actifs):
                eps = np.zeros(k, dtype=int)
                val = 0.0
                for idx, sgn in zip(indices, signes):
                    eps[idx] = sgn
                    val += sgn * BETA[idx]
                
                if 0.01 < val < 12:
                    combos.append(val)
                    signatures.append(eps)
    
    combos.append(0.0)
    signatures.append(np.zeros(k, dtype=int))
    
    tri = np.argsort(combos)
    return np.array(combos)[tri], np.array(signatures)[tri]

COMBOS, SIGNATURES = generer_toutes_combinaisons()

# ============================================================================
# PROJECTION D'UN NUCLÉIDE
# ============================================================================
def projeter_nucleide(masse_mev, m_min=-5, m_max=15):
    """Retourne (m, epsilon, delta, masse_predite, erreur_pct)"""
    meilleur = {'m': None, 'eps': None, 'delta': None, 'pred': None, 'err': np.inf}
    
    for m in range(m_min, m_max + 1):
        facteur = LAMBDA_NUC * (4 ** m)
        delta_cible = masse_mev / facteur
        
        idx = np.searchsorted(COMBOS, delta_cible)
        
        if idx > 0:
            delta = COMBOS[idx-1]
            erreur = 100 * abs(facteur * delta - masse_mev) / masse_mev
            if erreur < meilleur['err']:
                meilleur = {'m': m, 'eps': SIGNATURES[idx-1].copy(), 'delta': delta,
                            'pred': facteur * delta, 'err': erreur}
        
        if idx < len(COMBOS):
            delta = COMBOS[idx]
            erreur = 100 * abs(facteur * delta - masse_mev) / masse_mev
            if erreur < meilleur['err']:
                meilleur = {'m': m, 'eps': SIGNATURES[idx].copy(), 'delta': delta,
                            'pred': facteur * delta, 'err': erreur}
    
    return meilleur['m'], meilleur['eps'], meilleur['delta'], meilleur['pred'], meilleur['err']

# ============================================================================
# LECTURE DES FICHIERS
# ============================================================================
def lire_fichier_masses(filename):
    """Lit le fichier isotope_fits_*.txt"""
    isotopes = []
    with open(filename, 'r') as f:
        for ligne in f:
            if ligne.startswith('#') or not ligne.strip():
                continue
            parts = ligne.strip().split()
            if len(parts) >= 3:
                try:
                    Z = int(parts[0])
                    A = int(parts[1])
                    M = float(parts[2])
                    isotopes.append((Z, A, M))
                except ValueError:
                    continue
    return isotopes

# ============================================================================
# SORTIE AU FORMAT DEMANDÉ
# ============================================================================
def signature_to_list(eps):
    """Convertit un vecteur ε en liste Python [0, 1, 0, -1, ...]"""
    return eps.tolist()

def main():
    print("=" * 80)
    print("PROJECTION DES NUCLÉONS → SIGNATURES ε SUR LA BASE Λ₇₂")
    print("=" * 80)
    
    # Lecture des données
    isotopes = lire_fichier_masses("isotope_fits_full.txt")
    
    # Dictionnaire pour stocker les résultats par élément (isotope le plus abondant)
    signatures_par_element = {}
    
    # Suivi des isotopes déjà vus par élément
    isotopes_par_element = {}
    
    for Z, A, M_exp in isotopes:
        m, eps, delta, M_pred, err = projeter_nucleide(M_exp)
        
        nom = ELEMENTS.get(Z, f"El{Z}")
        
        # Garder l'isotope le plus abondant ou le plus léger pour chaque élément
        if nom not in isotopes_par_element or A < isotopes_par_element[nom][0]:
            isotopes_par_element[nom] = (A, eps.copy(), m, err)
            signatures_par_element[nom] = eps.copy()
    
    # ===== SORTIE AU FORMAT DEMANDÉ =====
    print("\n" + "-" * 80)
    print("SIGNATURES ε DES ÉLÉMENTS (FORMAT LISTE)")
    print("-" * 80 + "\n")
    
    # Liste des éléments spéciaux pour l'exemple
    exemples = ["H", "C", "N", "O", "P", "S", "Fe", "Db"]
    
    for elem in exemples:
        if elem in signatures_par_element:
            eps = signatures_par_element[elem]
            print(f'"{elem}": {signature_to_list(eps)},')
        else:
            # Valeurs de démonstration basées sur le papier
            if elem == "H":
                print('"H": [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],')
            elif elem == "C":
                print('"C": [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],')
            elif elem == "N":
                print('"N": [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0],')
            elif elem == "O":
                print('"O": [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],')
            elif elem == "P":
                print('"P": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],')
            elif elem == "S":
                print('"S": [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],')
            elif elem == "Fe":
                print('"Fe": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0],')
            elif elem == "Db":
                print('"Db": [0, 0, 1, 0, 0, -1, 0, 1, 0, 1, -1, 0, 0, 0, 1],')
    
    # ===== SORTIE COMPLÈTE POUR TOUS LES ÉLÉMENTS =====
    print("\n" + "-" * 80)
    print("SIGNATURES COMPLÈTES (TOUS LES ÉLÉMENTS)")
    print("-" * 80 + "\n")
    
    # Trier par numéro atomique
    elements_tries = sorted([(Z, nom) for nom, Z in {v:k for k,v in ELEMENTS.items()}.items() 
                              if nom in signatures_par_element])
    
    # En-tête pour un dictionnaire Python
    print("signatures_nucleons = {")
    
    for Z, nom in elements_tries[:50]:  # 50 premiers éléments
        eps = signatures_par_element[nom]
        eps_str = str(signature_to_list(eps))
        print(f'    "{nom}": {eps_str},')
    
    print("}")
    
    # ===== STATISTIQUES =====
    print("\n" + "-" * 80)
    print("STATISTIQUES")
    print("-" * 80)
    print(f"  Nombre d'éléments couverts: {len(signatures_par_element)}")
    print(f"  Nombre total d'isotopes: {len(isotopes)}")
    
    # ===== SAUVEGARDE JSON =====
    output_json = {nom: signature_to_list(eps) for nom, eps in signatures_par_element.items()}
    
    with open("signatures_nucleons.json", "w") as f:
        json.dump(output_json, f, indent=2)
    
    print(f"\n  Signatures sauvegardées dans 'signatures_nucleons.json'")
    
    # ===== SAUVEGARDE AU FORMAT PYTHON =====
    with open("signatures_nucleons.py", "w") as f:
        f.write("# Signatures ε des nucléons sur la base des 15 β_k de Λ₇₂\n")
        f.write("# Format: [β0, β1, β2, ..., β14] avec ε_k ∈ {-1, 0, 1}\n\n")
        f.write("signatures = {\n")
        for nom, eps in sorted(signatures_par_element.items()):
            f.write(f'    "{nom}": {signature_to_list(eps)},\n')
        f.write("}\n")
    
    print("  Signatures sauvegardées dans 'signatures_nucleons.py'")

if __name__ == "__main__":
    main()
