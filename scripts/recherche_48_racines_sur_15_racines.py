import numpy as np
from itertools import product

# Les 15 βₖ (Tableau III)
beta = np.array([
    0.066136959,
    0.281751380,
    0.555869353,
    0.868248673,
    1.504114125,
    1.725183114,
    1.831271203,
    2.017424480,
    2.092834951,
    2.524926754,
    3.279177783,
    3.851497776,
    4.571886169,
    4.724739150,
    7.408061012
])

# Les 48 racines (à compléter avec vos valeurs)
racines = np.array([
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

def find_combination(target, beta, max_active=6):
    """
    Cherche la combinaison linéaire à coefficients {-1,0,1}
    qui approxime le mieux 'target'
    """
    n = len(beta)
    best_coeff = None
    best_error = float('inf')
    
    # On teste toutes les combinaisons de k actifs (k=1 à max_active)
    from itertools import combinations, product
    
    for k in range(1, max_active + 1):
        for indices in combinations(range(n), k):
            for signs in product([-1, 1], repeat=k):
                coeff = np.zeros(n)
                for idx, s in zip(indices, signs):
                    coeff[idx] = s
                value = np.dot(coeff, beta)
                error = abs(value - target) / target if target != 0 else abs(value)
                if error < best_error:
                    best_error = error
                    best_coeff = coeff.copy()
                    # Normalisation optionnelle
    return best_coeff, best_error

# Recherche pour chaque racine
print("Recherche des décompositions...\n")
print(f"{'i':>3} {'racine':>12} {'erreur %':>12} {'coefficients actifs'}")
print("-" * 70)

for i, r in enumerate(racines):
    coeff, err = find_combination(r, beta, max_active=6)
    if coeff is not None:
        actifs = []
        for k in range(15):
            if coeff[k] != 0:
                signe = '+' if coeff[k] > 0 else '-'
                actifs.append(f"{signe}{k}")
        eps_str = ''.join(actifs) if actifs else '0'
        print(f"{i+1:3d} {r:12.9f} {err*100:12.6f} %   {eps_str}")
    else:
        print(f"{i+1:3d} {r:12.9f} {'non trouvé':12}")

# Sauvegarde en CSV
import csv
with open('decomposition_48_racines.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['i', 'sqrt_lambda', 'eps0', 'eps1', 'eps2', 'eps3', 'eps4', 
                     'eps5', 'eps6', 'eps7', 'eps8', 'eps9', 'eps10', 'eps11', 
                     'eps12', 'eps13', 'eps14'])
    for i, r in enumerate(racines):
        coeff, err = find_combination(r, beta, max_active=6)
        if coeff is not None:
            row = [i+1, r] + [int(coeff[k]) for k in range(15)]
            writer.writerow(row)
        else:
            row = [i+1, r] + [0]*15
            writer.writerow(row)

print("\nFichier CSV généré : decomposition_48_racines.csv")
