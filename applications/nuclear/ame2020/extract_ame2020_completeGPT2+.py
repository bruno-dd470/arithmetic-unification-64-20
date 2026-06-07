#!/usr/bin/env python3

import pandas as pd

u_to_MeV = 931.49410242

# --- colonnes fixes AME2020 ---
colspecs = [
    (0,1),    # cc
    (1,4),    # NZ
    (4,9),    # N
    (9,14),   # Z
    (14,19),  # A
    (20,23),  # El
    (23,27),  # O
    (28,42),  # mass excess
    (42,54),  # unc
    (54,67),  # binding
    (67,78),  # unc
    (79,81),  # B
    (81,94),  # beta
    (94,105), # beta unc
    (106,119),# atomic mass (micro-u)
    (119,131) # atomic mass unc
]

columns = [
    "cc","NZ","N","Z","A","El","O",
    "mass_excess","me_unc",
    "binding","be_unc",
    "B","beta","beta_unc",
    "atomic_mass","am_unc"
]

def load_ame2020(filename):
    print("Lecture du fichier...")

    df = pd.read_fwf(
        filename,
        colspecs=colspecs,
        names=columns,
        dtype=str
    )

    print("Lignes totales :", len(df))

    # --- conversion robuste ---
    df["Z"] = pd.to_numeric(df["Z"], errors="coerce")
    df["A"] = pd.to_numeric(df["A"], errors="coerce")

    # --- nettoyage masse ---
    df["estimated"] = df["atomic_mass"].str.contains("#", na=False)

    clean_mass = (
        df["atomic_mass"]
        .str.replace("#","", regex=False)
        .str.replace("*","", regex=False)
        .str.replace(" ","", regex=False)
    )

    df["mass_u"] = pd.to_numeric(clean_mass, errors="coerce") / 1e6
    df["mass_MeV"] = df["mass_u"] * u_to_MeV

    # --- suppression des lignes invalides ---
    df = df.dropna(subset=["Z","A","mass_u"])

    # conversion finale
    df["Z"] = df["Z"].astype(int)
    df["A"] = df["A"].astype(int)

    # filtre physique minimal
    df = df[(df["Z"] >= 1) & (df["A"] >= df["Z"])]

    print("Isotopes valides :", len(df))

    return df


# --- programme principal ---
if __name__ == "__main__":

    df = load_ame2020("mass.mas20.txt")

    print("\nAperçu :")
    print(df[["Z","A","El","mass_MeV","estimated"]].head(10))

    # test U-235
    u235 = df[(df.Z == 92) & (df.A == 235)]

    print("\nU-235 :")
    if not u235.empty:
        print(u235[["Z","A","El","mass_MeV"]])
    else:
        print("NON TROUVÉ")

    # export CSV
    df[["Z","A","El","mass_MeV","estimated"]].to_csv(
        "ame2020_clean.csv", index=False
    )

    print("\n✅ Export terminé : ame2020_clean.csv")
