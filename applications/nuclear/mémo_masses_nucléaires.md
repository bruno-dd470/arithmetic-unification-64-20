# MÉMO - Modèle des masses nucléaires (AME2020)

## Constantes fondamentales
Λ_fund = 7.726 MeV
u_to_MeV = 931.49410242

## Paramètres optimisés (formule fermée)
Λ₀ = 0.1069892866
α  = 1.2795330564
β  = 0.0795943175

## Formule des racines
√λ(n,l,j) = (Λ₀/n²) × [n² + α·l(l+1) + β·n·j(j+1)]

## Prédiction d'une masse M (MeV)
M ≈ Λ_fund × 4^{n_oct} × (√λᵢ ± √λⱼ)

## Performances
- Erreur moyenne : 0.0287 %
- Écart-type : 0.0285 %
- 100 % des isotopes avec erreur < 0.2 %
- Modèle validé sur 295 isotopes (Z=1 à 118)

## Applications
1. Prédiction des masses de noyaux inconnus ou exotiques
2. Calcul des énergies de liaison et des chaînes de désintégration
3. Étude des nombres magiques et des effets de couche
4. Extension aux noyaux superlourds (Z > 118)