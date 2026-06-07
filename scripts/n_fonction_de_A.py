import matplotlib.pyplot as plt

# Lecture des données
data = []
with open("isotope_fits_original.txt", "r") as f:
    for line in f:
        if line.startswith('#'):
            continue
        parts = line.split()
        if len(parts) < 7:
            continue
        Z = int(parts[0])
        A = int(parts[1])
        n_oct = int(parts[3])
        delta = float(parts[4])
        data.append((Z, A, n_oct, delta))

# Tracer n_oct vs A
A_vals = [d[1] for d in data]
n_vals = [d[2] for d in data]

plt.figure(figsize=(12,6))
plt.scatter(A_vals, n_vals, s=1, alpha=0.5, c='blue')
plt.xlabel('Nombre de masse A')
plt.ylabel('Exposant n_oct')
plt.title('Évolution de n_oct avec A')
plt.grid(True, alpha=0.3)
plt.savefig('n_oct_vs_A.png')
print("Graphique sauvegardé : n_oct_vs_A.png")