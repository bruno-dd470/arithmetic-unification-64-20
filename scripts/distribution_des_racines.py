import numpy as np
from collections import Counter

# Les 48 racines (à copier depuis sqrt_distinct dans ton script principal)
sqrt_lambda = [
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
]

# Charger les deltas depuis le fichier
deltas = []
with open("isotope_fits_original.txt", "r") as f:
    for line in f:
        if line.startswith('#'):
            continue
        parts = line.split()
        if len(parts) < 7:
            continue
        delta = float(parts[4])
        deltas.append(delta)

# Pour chaque delta, trouver les deux racines (i,j) dont la somme ou la différence donne delta
root_usage = Counter()

for delta in deltas:
    best_i, best_j = -1, -1
    best_sum = float('inf')
    for i, ri in enumerate(sqrt_lambda):
        for j, rj in enumerate(sqrt_lambda):
            # essayer i + j
            if abs((ri + rj) - delta) < 1e-5:
                root_usage[i] += 1
                root_usage[j] += 1
                break
            # essayer |i - j|
            if abs(abs(ri - rj) - delta) < 1e-5:
                root_usage[i] += 1
                root_usage[j] += 1
                break
        else:
            continue
        break

# Afficher les résultats
print("Racines les plus utilisées (indice, √λ, occurrences) :")
for idx, count in root_usage.most_common(15):
    print(f"  {idx:2d} : √λ = {sqrt_lambda[idx]:.6f} → {count:3d} occurrences")
