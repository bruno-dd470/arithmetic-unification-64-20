import numpy as np
import sys
import matplotlib.pyplot as plt

# ------------------------------------------------------------
# 1. Les 48 racines distinctes (base canonique)
# ------------------------------------------------------------
sqrt_distinct = [
    0.066136959, 0.104861556, 0.105819546, 0.135301931, 0.171977681, 0.193286510,
    0.217318285, 0.251706536, 0.281751380, 0.308944245, 0.342536900, 0.360145691,
    0.389044757, 0.426899914, 0.539423867, 0.555869353, 0.611492405, 0.628435246,
    0.726794491, 0.783638283, 0.868248673, 0.894790972, 0.895000741, 1.181361718,
    1.388242400, 1.459652785, 1.504114125, 1.582953046, 1.725183114, 1.831271203,
    1.841477693, 1.891359664, 2.017424480, 2.092834951, 2.304598960, 2.524926754,
    2.911315620, 3.157658906, 3.158280845, 3.279177783, 3.289042432, 3.851497776,
    4.571886169, 4.724739150, 4.755055358, 5.943089000, 7.408061012, 8.102307717
]
distinct = np.array(sqrt_distinct)

# Toutes les combinaisons Δ = √λ_i ± √λ_j
combos = set()
n_vals = len(distinct)
for i in range(n_vals):
    for j in range(i+1, n_vals):
        combos.add(distinct[i] + distinct[j])
        combos.add(abs(distinct[i] - distinct[j]))
combos = np.array(sorted(combos))
print(f"Combinaisons Δ : {len(combos)}", file=sys.stderr)

Lambda_fund = 7.726          # MeV
u_to_MeV = 931.49410242      # 1 u → MeV

# ------------------------------------------------------------
# 2. Parsing corrigé du fichier mass.mas20.txt
# Format officiel AME2020 (indices 0-based) :
# Z : cols 10-14 -> line[9:14]
# A : cols 15-19 -> line[14:19]
# Masse atomique (micro-u) : cols 110-122 -> line[109:122]
# ------------------------------------------------------------
def parse_line(line):
    if len(line) < 122 or line[0] not in ('0', '1'):
        return None
    try:
        Z = int(line[9:14].strip())
        A = int(line[14:19].strip())
    except:
        return None

    # Extraction de la masse atomique (micro-u)
    # On élargit légèrement la plage pour absorber les variations d'espaces
    mass_str = line[106:125].strip().replace(' ', '')
    
    if not mass_str:
        return None
    
    # Gestion des valeurs estimées ou non calculables dans AME
    if '#' in mass_str or '*' in mass_str:
        return None
        
    try:
        mass_micro = float(mass_str)
        # Filtre de cohérence : une masse atomique en micro-u est typiquement > 1 000 000
        if 1_000_000 < mass_micro < 300_000_000:
            mass_u = mass_micro * 1e-6
            mass_MeV = mass_u * u_to_MeV
            return (Z, A, mass_MeV)
    except:
        return None
    return None

filename = "mass.mas20.txt"
isotopes = []
try:
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            if line[0] in ('0', '1'):
                res = parse_line(line)
                if res:
                    isotopes.append(res)
except FileNotFoundError:
    print(f"Erreur : fichier {filename} introuvable.", file=sys.stderr)
    sys.exit(1)

print(f"Nombre d'isotopes extraits : {len(isotopes)}", file=sys.stderr)

# ------------------------------------------------------------
# 3. Recherche de la meilleure approximation pour chaque isotope
# ------------------------------------------------------------
# Optimisation : searchsorted est O(log N) au lieu de O(N) pour argmin
def best_delta(target):
    idx = np.searchsorted(combos, target)
    if idx == 0: return combos[0]
    if idx == len(combos): return combos[-1]
    d1, d2 = combos[idx-1], combos[idx]
    return d1 if abs(target - d1) <= abs(target - d2) else d2

results = []
print("\nZ   A    M_true (MeV)    n     Δ          M_pred (MeV)   Err(%)")
print("-" * 85)

# Pré-calcul des facteurs pour éviter les pow répétitifs dans la boucle
n_range = range(-5, 16)
factors = {n: 4 ** n for n in n_range}

for Z, A, M_true in isotopes:
    best_err = float('inf')
    best_n = None
    best_d = None
    best_pred = None
    
    for n_oct in n_range:
        factor = factors[n_oct]
        needed = M_true / (Lambda_fund * factor)
        
        # Filtre physique : Δ doit rester dans une plage raisonnable pour ce modèle
        if needed < 0.01 or needed > 20:
            continue
            
        d = best_delta(needed)
        pred = Lambda_fund * factor * d
        err = abs(pred - M_true) / M_true
        
        if err < best_err:
            best_err = err
            best_n = n_oct
            best_d = d
            best_pred = pred
            
    if best_n is not None:
        results.append((Z, A, M_true, best_n, best_d, best_pred, best_err))
        if len(results) <= 30:
            print(f"{Z:3d} {A:4d}   {M_true:10.4f}   {best_n:3d}   {best_d:10.6f}   {best_pred:10.4f}   {best_err*100:8.5f}")

# Sauvegarde complète
with open('isotope_fits_full.txt', 'w') as f:
    f.write("# Z A M_true(MeV) n Delta M_pred(MeV) err(%)\n")
    for Z, A, M, n, d, Mp, e in results:
        f.write(f"{Z} {A} {M:.6f} {n} {d:.6f} {Mp:.6f} {e*100:.6f}\n")

print(f"\nTotal isotopes traités et sauvegardés : {len(results)}", file=sys.stderr)

# ------------------------------------------------------------
# 4. Graphique et statistiques
# ------------------------------------------------------------
if results:
    masses = [r[2] for r in results]
    errs = [r[6]*100 for r in results]
    
    plt.figure(figsize=(12,6))
    plt.scatter(masses, errs, s=1, alpha=0.5, c='blue')
    plt.axhline(y=0.2, color='red', linestyle='--', label='seuil 0.2%')
    plt.xscale('log')
    plt.xlabel('Masse atomique (MeV) (échelle log)')
    plt.ylabel('Erreur relative (%)')
    plt.title('Précision des masses isotopiques prédites par Λ₇₂ (AME2020)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('isotope_errors.png', dpi=150)
    print("Graphique sauvegardé : isotope_errors.png", file=sys.stderr)
    
    errs_arr = np.array(errs)
    print(f"\nStatistiques :", file=sys.stderr)
    print(f"  Erreur moyenne : {np.mean(errs_arr):.5f} %", file=sys.stderr)
    print(f"  Écart-type : {np.std(errs_arr):.5f} %", file=sys.stderr)
    print(f"  Erreur maximale : {np.max(errs_arr):.5f} %", file=sys.stderr)
    print(f"  Pourcentage d'isotopes avec erreur < 0.2% : {100 * np.sum(errs_arr < 0.2) / len(errs_arr):.1f} %", file=sys.stderr)
else:
    print("Aucun résultat généré.", file=sys.stderr)