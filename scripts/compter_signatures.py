from collections import defaultdict

signatures = defaultdict(list)

with open("isotope_fits_original.txt", "r") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        parts = line.split()
        if len(parts) < 7:   # 7 colonnes numériques
            continue
        try:
            Z = int(parts[0])
            A = int(parts[1])
            n_oct = int(parts[3])
            delta = float(parts[4])
        except ValueError:
            continue
        signatures[(n_oct, delta)].append((Z, A))

print(f"Nombre de signatures distinctes : {len(signatures)}")
print("\nSignatures les plus fréquentes :")
sorted_items = sorted(signatures.items(), key=lambda x: len(x[1]), reverse=True)
for (n_oct, delta), isotopes in sorted_items[:15]:
    print(f"n={n_oct:3d}, Δ={delta:.6f} → {len(isotopes):3d} isotopes")
    # Afficher quelques exemples
    for Z, A in isotopes[:3]:
        print(f"      → {Z:3d} {A:3d}")
    if len(isotopes) > 3:
        print("      ...")