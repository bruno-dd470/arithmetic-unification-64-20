import numpy as np
import sys
import matplotlib.pyplot as plt
import csv

# ------------------------------------------------------------
# 1. Les 48 racines distinctes (base canonique)
# ------------------------------------------------------------
sqrt_distinct = [
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
# 2. Parsing du fichier CSV
# ------------------------------------------------------------
def clean_mass(mass_str):
    """Nettoie la chaîne de masse atomique (supprime espaces)"""
    if not mass_str:
        return None
    # Supprimer les espaces
    cleaned = mass_str.replace(' ', '')
    # Remplacer '#' par '' (valeur estimée)
    cleaned = cleaned.replace('#', '')
    if not cleaned:
        return None
    try:
        return float(cleaned) / 1_000_000
    except ValueError:
        return None        

filename = "ame2020_VERIFIED.csv"
isotopes = []

try:
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        print(f"En-tête : {header[:6]} ... {header[12:14]}", file=sys.stderr)
        
        for row in reader:
            if len(row) < 13:
                continue
            
            # Les colonnes selon votre diagnostic
            # row[2] = Z, row[3] = A, row[12] = AtomicMass_u
            try:
                Z = int(row[2])
                A = int(row[3])
            except (ValueError, IndexError):
                continue
            
            mass_u = clean_mass(row[12])
            if mass_u is None:
                continue
            
            # Conversion u → MeV
            mass_MeV = mass_u * u_to_MeV
            
            # Ne garder que les valeurs raisonnables (A entre 1 et 295)
            if 1 <= A <= 295 and mass_MeV > 0:
                isotopes.append((Z, A, mass_MeV))
                
except FileNotFoundError:
    print(f"Erreur : fichier {filename} introuvable.", file=sys.stderr)
    sys.exit(1)

print(f"Nombre d'isotopes extraits : {len(isotopes)}", file=sys.stderr)

# ------------------------------------------------------------
# 3. Recherche de la meilleure approximation pour chaque isotope
# ------------------------------------------------------------
def best_delta(target):
    idx = np.argmin(np.abs(combos - target))
    return combos[idx]

results = []
print("\nZ   A    M_true (MeV)    n     Δ          M_pred (MeV)   Err(%)", file=sys.stderr)
print("-" * 85, file=sys.stderr)

for Z, A, M_true in isotopes:
    best_err = float('inf')
    best_n = None
    best_d = None
    best_pred = None
    
    for n_oct in range(-5, 16):
        factor = 4 ** n_oct
        needed = M_true / (Lambda_fund * factor)
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
            print(f"{Z:3d} {A:4d}   {M_true:10.4f}   {best_n:3d}   {best_d:10.6f}   {best_pred:10.4f}   {best_err*100:8.5f}",
                  file=sys.stderr)

# Sauvegarde complète
with open('isotope_fits_full.txt', 'w') as f:
    f.write("# Z A M_true(MeV) n Delta M_pred(MeV) err(%)\n")
    for Z, A, M, n, d, Mp, e in results:
        f.write(f"{Z} {A} {M:.6f} {n} {d:.6f} {Mp:.6f} {e*100:.6f}\n")

print(f"\nTotal isotopes traités : {len(results)}", file=sys.stderr)

# ------------------------------------------------------------
# 4. Graphique et statistiques
# ------------------------------------------------------------
if results:
    masses = [r[2] for r in results]
    errs = [r[6]*100 for r in results]
    
    plt.figure(figsize=(12,6))
    plt.scatter(masses, errs, s=1, alpha=0.5, c='blue')
    plt.axhline(y=0.2, color='red', linestyle='--', label='seuil 0.2%')
    plt.axhline(y=0.5, color='orange', linestyle=':', alpha=0.7, label='seuil 0.5%')
    plt.xscale('log')
    plt.xlabel('Masse atomique (MeV) (échelle log)')
    plt.ylabel('Erreur relative (%)')
    plt.title('Précision des masses isotopiques prédites par Λ₇₂ (AME2020)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig('isotope_errors.png', dpi=150)
    print("Graphique sauvegardé : isotope_errors.png", file=sys.stderr)
    
    errs_arr = np.array(errs)
    print(f"\nStatistiques :", file=sys.stderr)
    print(f"  Erreur moyenne : {np.mean(errs_arr):.5f} %", file=sys.stderr)
    print(f"  Écart-type : {np.std(errs_arr):.5f} %", file=sys.stderr)
    print(f"  Erreur maximale : {np.max(errs_arr):.5f} %", file=sys.stderr)
    print(f"  Pourcentage d'isotopes avec erreur < 0.2% : {100 * np.sum(errs_arr < 0.2) / len(errs_arr):.1f} %", file=sys.stderr)
    
    # Statistiques par intervalle de masse
    low_mass = [errs[i] for i, m in enumerate(masses) if m < 10000]
    mid_mass = [errs[i] for i, m in enumerate(masses) if 10000 <= m < 50000]
    high_mass = [errs[i] for i, m in enumerate(masses) if m >= 50000]
    
    print(f"\nStatistiques par intervalle de masse :", file=sys.stderr)
    if low_mass:
        print(f"  M < 10 GeV : n={len(low_mass)}, erreur moyenne={np.mean(low_mass):.5f}%", file=sys.stderr)
    if mid_mass:
        print(f"  10 ≤ M < 50 GeV : n={len(mid_mass)}, erreur moyenne={np.mean(mid_mass):.5f}%", file=sys.stderr)
    if high_mass:
        print(f"  M ≥ 50 GeV : n={len(high_mass)}, erreur moyenne={np.mean(high_mass):.5f}%", file=sys.stderr)
        
else:
    print("Aucun résultat.", file=sys.stderr)
