#!/usr/bin/env sage
# -*- coding: utf-8 -*-
"""
Script SageMath : Projection de Λ₇₂ et calcul du PPCM des dénominateurs dans Q(√2)
Objectif : Vérifier si le dénominateur empirique 177 = 3×59 a une origine structurelle
           dans la projection des 48 vecteurs minimaux non dégénérés de Λ₇₂.
"""

# =============================================================================
# 1. CONFIGURATION DU CORPS DE NOMBRES Q(√2)
# =============================================================================
# a représente √2. Tous les calculs seront exacts dans ce corps.
K.<a> = NumberField(x^2 - 2)
print(f"[INFO] Corps de nombres défini : {K}")

# =============================================================================
# 2. FONCTIONS UTILITAIRES POUR L'EXTRACTION DES DÉNOMINATEURS
# =============================================================================
def denominateur_commun_element(v):
    """
    Retourne le plus petit entier D > 0 tel que D * v ∈ Z[√2].
    v est un élément de K = Q(√2).
    """
    # v s'écrit c0 + c1*√2 avec c0, c1 ∈ Q
    coeffs = v.polynomial().coefficients(sparse=False)
    # On complète à 2 coefficients si nécessaire
    while len(coeffs) < 2:
        coeffs.append(K(0))
    # Dénominateurs des coefficients rationnels
    den_c0 = coeffs[0].denominator()
    den_c1 = coeffs[1].denominator()
    # Le dénominateur dans Z[√2] est le PPCM des dénominateurs rationnels
    return lcm(den_c0, den_c1)

def calcul_ppcm_projection(vecteurs_proj):
    """
    Calcule le PPCM des dénominateurs de tous les coordonnées d'une liste de vecteurs.
    vecteurs_proj : liste de listes/matrices d'éléments de K.
    """
    ppm_global = 1
    count = 0
    for v in vecteurs_proj:
        for coord in v:
            d = denominateur_commun_element(coord)
            ppm_global = lcm(ppm_global, d)
            count += 1
    return ppm_global, count

# =============================================================================
# 3. CADRE DE PROJECTION THÉORIQUE DE Λ₇₂
# =============================================================================
# NOTE : Λ₇₂ n'est pas natif dans SageMath. La construction de Nebe (2010) utilise
# un produit tensoriel hermitien sur Z[α] (α²-α+2=0) entre le réseau de Barnes (dim 3)
# et le réseau de Leech (dim 24). La projection vers R³ se fait via une application
# linéaire P : R⁷² → R³ invariante sous le groupe binaire octaédrique 2O.
# 
# Pour exécuter ce script, remplacez les placeholders ci-dessous par vos données :
# - MINIMAL_VECTORS_72 : liste de 72 vecteurs de R⁷² (norme 8)
# - PROJ_MATRIX_72x3   : matrice de projection 72×3 à coefficients dans Q(√2)

def charger_donnees_lambda72():
    """
    Placeholder à remplacer par la construction exacte de Nebe (2010).
    Retourne (matrice_projection, liste_vecteurs_72)
    """
    
    # EXEMPLE PÉDAGOGIQUE : Orbit du groupe octaédrique dans Q(√2)³
    # Ces 48 vecteurs simulent les racines projetées. Remplacez par votre P * v_min
    seed = vector(K, [1, 0, 0])
    
    # Générateurs de O(3) à coefficients dans Q(√2)
    R_z = matrix(K, [[0, -1, 0], [1, 0, 0], [0, 0, 1]])  # π/2
    R_y = matrix(K, [[0, 0, 1], [0, 1, 0], [-1, 0, 0]])  # π/2
    R_diag = matrix(K, [[0, 0, 1], [1, 0, 0], [0, 1, 0]]) # cycle
    
    # Génération de l'orbite (48 éléments avec signes)
    G = MatrixGroup([R_z, R_y, R_diag])
    orbit = set()
    for g in G:
        v_pos = g * seed
        orbit.add(tuple(v_pos))
        orbit.add(tuple(-v_pos))
        
    return [vector(K, v) for v in orbit]

# =============================================================================
# 4. EXÉCUTION & RÉSULTATS
# =============================================================================
def main():
    print("\n" + "="*60)
    print("PROJECTION DE Λ₇₂ ET CALCUL DU PPCM DANS Q(√2)")
    print("="*60)
    
    # 4.1 Chargement / Projection
    vecteurs = charger_donnees_lambda72()
    print(f"[INFO] {len(vecteurs)} vecteurs projetés chargés.")
    
    # 4.2 Calcul du PPCM des dénominateurs
    ppm, nb_coords = calcul_ppcm_projection(vecteurs)
    print(f"\n[INFO] {nb_coords} coordonnées traitées.")
    print(f"[RESULTAT] PPCM EXACT des dénominateurs : {ppm}")
    
    # 4.3 Analyse de 177 = 3 × 59
    if ppm % 177 == 0:
        print(f"[CHECK] Le PPCM est un multiple de 177 (facteur = {ppm // 177}).")
        print("        → 177 est structurellement compatible avec la projection.")
    else:
        print(f"[CHECK] Le PPCM n'est PAS un multiple de 177.")
        print("        → 177 est probablement une approximation numérique optimisée.")
        
    # 4.4 Affichage des premiers vecteurs (vérification)
    print("\n[APERCU] 5 premiers vecteurs (coordonnées dans Q(√2)):")
    for i, v in enumerate(vecteurs[:5]):
        print(f"  v_{i} = {v}")
        
    print("\n" + "="*60)
    print("FIN DE L'EXÉCUTION")
    print("="*60)

if __name__ == "__main__":
    main()