import numpy as np
from itertools import product

# Base réduite des 15 racines (dans l'ordre donné ci-dessus)
beta = [
    0.066136959000, 0.281751380000, 0.555869353000, 0.868248673000,
    1.504114125000, 1.725183114000, 1.831271203000, 2.017424480000,
    2.092834951000, 2.524926754000, 3.279177783000, 3.851497776000,
    4.571886169000, 4.724739150000, 7.408061012000
]

# Fonction pour trouver les coefficients d'un delta donné
def epsilon_from_delta(delta, tol=1e-5):
    for coeffs in product([-1,0,1], repeat=len(beta)):
        s = sum(c*b for c,b in zip(coeffs, beta))
        if abs(s - delta) < tol:
            return list(coeffs)
    return None

# Lire le fichier des isotopes
with open("isotope_fits_original.txt", "r") as f:
    next(f)  # skip header
    for line in f:
        parts = line.split()
        if len(parts) < 7:
            continue
        Z = int(parts[0])
        A = int(parts[1])
        n_oct = int(parts[3])
        delta = float(parts[4])
        eps = epsilon_from_delta(delta)
        if eps is None:
            print(f"⚠️ Aucune combinaison trouvée pour {Z}-{A}, delta={delta}")
        else:
            print(f"{Z} {A} {n_oct} " + " ".join(str(e) for e in eps))