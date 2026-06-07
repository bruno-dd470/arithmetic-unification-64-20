import numpy as np
from itertools import product

# Les 15 β
beta = [
    0.066136959, 0.281751380, 0.555869353, 0.868248673,
    1.504114125, 1.725183114, 1.831271203, 2.017424480,
    2.092834951, 2.524926754, 3.279177783, 3.851497776,
    4.571886169, 4.724739150, 7.408061012
]

# Les 48 racines
roots = [
    0.066136959, 0.104861556, 0.105819546, 0.135301931,
    0.171977681, 0.193286510, 0.217318285, 0.251706536,
    0.281751380, 0.308944245, 0.342536900, 0.360145691,
    0.389044757, 0.426899914, 0.539423867, 0.555869353,
    0.611492405, 0.628435246, 0.726794491, 0.783638283,
    0.868248673, 0.894790972, 0.895000741, 1.181361718,
    1.388242400, 1.459652785, 1.504114125, 1.582953046,
    1.725183114, 1.831271203, 1.841477693, 1.891359664,
    2.017424480, 2.092834951, 2.304598960, 2.524926754,
    2.911315620, 3.157658906, 3.158280845, 3.279177783,
    3.289042432, 3.851497776, 4.571886169, 4.724739150,
    4.755055358, 5.943089000, 7.408061012, 8.102307717
]

def find_combination(target, basis, tol=1e-5):
    n = len(basis)
    for coeffs in product([-1,0,1], repeat=n):
        s = sum(c*b for c,b in zip(coeffs, basis))
        if abs(s - target) < tol:
            return coeffs
    return None

print("Décomposition des 48 racines dans la base β :")
for i, root in enumerate(roots):
    comb = find_combination(root, beta)
    if comb:
        # Afficher les β non nuls
        terms = [f"{c}·β_{j}" for j,c in enumerate(comb) if c != 0]
        print(f"{i+1:2d} : √λ = {' + '.join(terms)}")
    else:
        print(f"{i+1:2d} : √λ = {root} → pas de combinaison trouvée")