import numpy as np

# ============================================================
# Les 15 racines fondamentales (β_k)
# ============================================================
beta = np.array([
    0.066136959000, 0.281751380000, 0.555869353000, 0.868248673000,
    1.504114125000, 1.725183114000, 1.831271203000, 2.017424480000,
    2.092834951000, 2.524926754000, 3.279177783000, 3.851497776000,
    4.571886169000, 4.724739150000, 7.408061012000
])

# Constantes physiques
Lambda_fund = 7.726
u_to_MeV = 931.49410242

# ============================================================
# Charger la table des coefficients
# ============================================================
data = []
with open("table_isotopes_en_15_racines.txt", "r") as f:
    for line in f:
        parts = list(map(int, line.strip().split()))
        if len(parts) < 18:
            continue
        Z = parts[0]
        A = parts[1]
        n_oct = parts[2]
        eps = np.array(parts[3:18])
        data.append((Z, A, n_oct, eps))

print(f"Chargé {len(data)} isotopes")
print("-" * 80)
print("Vérification des 10 premiers isotopes :")
print("Z A | M_pred (MeV) | M_true (MeV) | Δ (%)")
print("-" * 80)

# Vérification sur les 10 premiers isotopes
for Z, A, n_oct, eps in data[:10]:
    delta = np.dot(eps, beta)
    M_pred = Lambda_fund * (4 ** n_oct) * delta
    
    # Trouver la masse réelle dans isotope_fits_original.txt
    M_true = None
    with open("isotope_fits_original.txt", "r") as f:
        for line in f:
            if line.startswith('#'):
                continue
            parts = line.split()
            if len(parts) >= 7 and int(parts[0]) == Z and int(parts[1]) == A:
                M_true = float(parts[2])
                break
    
    if M_true:
        err = abs(M_pred - M_true) / M_true * 100
        print(f"{Z:2d} {A:2d} | {M_pred:12.6f} | {M_true:12.6f} | {err:8.5f}")
    else:
        print(f"{Z:2d} {A:2d} | {M_pred:12.6f} | (non trouvé)    | -")

# ============================================================
# Analyse des coefficients
# ============================================================
print("\n" + "=" * 80)
print("ANALYSE DES COEFFICIENTS ε_k")
print("=" * 80)

counts = np.zeros((15, 3), dtype=int)
for _, _, _, eps in data:
    for k in range(15):
        if eps[k] == -1:
            counts[k, 0] += 1
        elif eps[k] == 0:
            counts[k, 1] += 1
        else:
            counts[k, 2] += 1

print("\nFréquence d'utilisation des 15 racines fondamentales :")
print(" k |     β_k     |   -1   |    0   |   +1   |  utilisé")
print("-" * 55)
for k in range(15):
    used = counts[k, 0] + counts[k, 2]
    print(f"{k:2d} | {beta[k]:10.6f} | {counts[k,0]:5d} | {counts[k,1]:5d} | {counts[k,2]:5d} | {used:5d}")

# ============================================================
# Tentative d'identification des β_k avec des orbitales
# ============================================================
print("\n" + "=" * 80)
print("IDENTIFICATION AVEC LES ORBITALES (n,l,j)")
print("=" * 80)

Lambda0 = 0.1069892866
alpha = 1.2795330564
beta_param = 0.0795943175

def compute_root_from_orbitale(n, l, j):
    term = n**2 + alpha * l*(l+1) + beta_param * n * j*(j+1)
    return (Lambda0 / n**2) * term

# Orbitales candidates
orbitals = [
    (1, 0, 0.5), (2, 0, 0.5), (2, 1, 0.5), (2, 1, 1.5),
    (3, 0, 0.5), (3, 1, 0.5), (3, 1, 1.5), (3, 2, 1.5),
    (3, 2, 2.5), (4, 0, 0.5), (4, 1, 0.5), (4, 1, 1.5),
    (4, 2, 1.5), (4, 2, 2.5), (4, 3, 2.5), (4, 3, 3.5),
    (5, 0, 0.5), (5, 1, 0.5), (5, 1, 1.5), (5, 2, 1.5),
    (5, 2, 2.5), (5, 3, 2.5), (5, 3, 3.5), (5, 4, 3.5),
    (5, 4, 4.5)
]

print("\nRecherche de la meilleure correspondance β_k ↔ orbitale :")
print(" k |     β_k     | orbitale | √λ_orbitale | écart")
print("-" * 60)

for k, bk in enumerate(beta):
    best_match = None
    best_diff = float('inf')
    best_nlj = None
    for n, l, j in orbitals:
        r = compute_root_from_orbitale(n, l, j)
        diff = abs(r - bk)
        if diff < best_diff:
            best_diff = diff
            best_match = r
            best_nlj = (n, l, j)
    
    n_orb, l_orb, j_orb = best_nlj
    j_num = int(2*j_orb)
    letter = ['s','p','d','f','g','h','i'][l_orb]
    orbital_name = f"{n_orb}{letter}{j_num}/2"
    
    print(f"{k:2d} | {bk:10.6f} | {orbital_name:8s} | {best_match:10.6f} | {best_diff:10.6f}")