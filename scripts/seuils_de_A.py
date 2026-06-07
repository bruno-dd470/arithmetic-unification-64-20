import numpy as np
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

# Trier par A
data.sort(key=lambda x: x[1])

# Parcourir et détecter les changements de n_oct
prev_n = None
for Z, A, n_oct, delta in data:
    if prev_n != n_oct:
        print(f"n_oct = {n_oct} : A ≈ {A}")
        prev_n = n_oct