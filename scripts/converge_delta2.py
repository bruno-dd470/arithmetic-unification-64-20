import numpy as np

# ----------------------------------------------------------------------
# Paramètres optimisés pour la formule des racines (AME2020)
# ----------------------------------------------------------------------
Lambda0 = 0.1069892866      # paramètre d'échelle
alpha   = 1.2795330564      # couplage orbital
beta    = 0.0795943175      # couplage spin-orbite
n_fixed = 7                 # couche la plus haute dans le jeu de données

# Nombre d'argent au carré
delta_s = 1 + np.sqrt(2)
delta_s2 = delta_s ** 2      # ≈ 5.82842712474619

# ----------------------------------------------------------------------
# Formule originale pour √λ (avec n fixé, j = l + 1/2)
# ----------------------------------------------------------------------
def sqrt_lambda_original(l):
    j = l + 0.5
    term = n_fixed**2 + alpha * l*(l+1) + beta * n_fixed * j*(j+1)
    return (Lambda0 / n_fixed**2) * term

# ----------------------------------------------------------------------
# Formule asymptotique : on remplace α par γ·δ_s² (β gardé pour le couplage)
# Le paramètre γ est ajusté pour raccorder à l=7
# ----------------------------------------------------------------------
def sqrt_lambda_extrapolated(l, gamma):
    j = l + 0.5
    term = n_fixed**2 + gamma * delta_s2 * l*(l+1) + beta * n_fixed * j*(j+1)
    return (Lambda0 / n_fixed**2) * term

# ----------------------------------------------------------------------
# 1. Valeurs aux petits l (vérification)
# ----------------------------------------------------------------------
print("📊 Comparaison aux petites valeurs de l")
print("-----------------------------------------------------")
for l in [1, 2, 3, 4, 5, 6, 7]:
    orig = sqrt_lambda_original(l)
    print(f"l = {l:2d} | √λ original = {orig:.8f}")

# ----------------------------------------------------------------------
# 2. Ajustement du paramètre γ pour que la formule extrapolée
#    coïncide avec l=7 (dernière racine de la couche n=7 dans les données)
# ----------------------------------------------------------------------
l_ref = 7
orig_l7 = sqrt_lambda_original(l_ref)

# Résoudre γ pour que sqrt_lambda_extrapolated(l_ref, γ) = orig_l7
j_ref = l_ref + 0.5
l2_ref = l_ref * (l_ref + 1)
j2_ref = j_ref * (j_ref + 1)

gamma = (orig_l7 * (n_fixed**2 / Lambda0) - n_fixed**2 - beta * n_fixed * j2_ref) / (delta_s2 * l2_ref)

print("\n🔧 Ajustement du paramètre γ")
print(f"  Pour l = {l_ref}, √λ original = {orig_l7:.8f}")
print(f"  γ ajusté = {gamma:.8f}")

# ----------------------------------------------------------------------
# 3. Extrapolation à l = 20 (et comparaison)
# ----------------------------------------------------------------------
l20 = 20
j20 = l20 + 0.5
l2_20 = l20 * (l20 + 1)
j2_20 = j20 * (j20 + 1)

# Valeur extrapolée
pred20 = (Lambda0 / n_fixed**2) * (n_fixed**2 + gamma * delta_s2 * l2_20 + beta * n_fixed * j2_20)

# Valeur originale si on prolongeait la formule (sans asymptote)
orig20 = sqrt_lambda_original(l20)

# Rapport entre extrapolation et valeur à l=7
ratio_vs_l7 = pred20 / orig_l7

print("\n🚀 Extrapolation à l = 20")
print(f"  √λ original (formule prolongée) = {orig20:.8f}")
print(f"  √λ extrapolé (avec γ·δ_s²)      = {pred20:.8f}")
print(f"  Rapport prédit / original       = {pred20 / orig20:.6f}")
print(f"  Rapport (l=20) / (l=7)          = {ratio_vs_l7:.6f}")

# ----------------------------------------------------------------------
# 4. Comparaison avec δ_s² et δ_s
# ----------------------------------------------------------------------
print("\n📐 Comparaison avec les constantes")
print(f"  δ_s                           = {delta_s:.8f}")
print(f"  δ_s²                          = {delta_s2:.8f}")
print(f"  Rapport (l=20)/(l=7) ≈ {ratio_vs_l7:.4f}")

if abs(ratio_vs_l7 - delta_s2) < 0.01:
    print("  ✅ Le rapport est très proche de δ_s² !")
elif abs(ratio_vs_l7 - delta_s) < 0.01:
    print("  ✅ Le rapport est très proche de δ_s !")
else:
    print("  ⚠️ Le rapport ne correspond ni à δ_s ni à δ_s².")
    print(f"     Écart à δ_s²  : {abs(ratio_vs_l7 - delta_s2):.6f}")
    print(f"     Écart à δ_s   : {abs(ratio_vs_l7 - delta_s):.6f}")

# ----------------------------------------------------------------------
# 5. Option : prédiction pour l = 100 (asymptote théorique)
# ----------------------------------------------------------------------
l100 = 100
j100 = l100 + 0.5
l2_100 = l100 * (l100 + 1)
j2_100 = j100 * (j100 + 1)

pred100 = (Lambda0 / n_fixed**2) * (n_fixed**2 + gamma * delta_s2 * l2_100 + beta * n_fixed * j2_100)
print(f"\n🌌 Prédiction pour l = 100 : √λ ≈ {pred100:.4f}")

# ----------------------------------------------------------------------
# 6. Sauvegarde des résultats
# ----------------------------------------------------------------------
with open("extrapolation_delta_s2.txt", "w") as f:
    f.write("# Extrapolation des racines √λ avec le nombre d'argent\n")
    f.write(f"delta_s     = {delta_s:.10f}\n")
    f.write(f"delta_s2    = {delta_s2:.10f}\n")
    f.write(f"gamma ajusté = {gamma:.10f}\n")
    f.write(f"√λ(l=7)      = {orig_l7:.10f}\n")
    f.write(f"√λ(l=20) ext = {pred20:.10f}\n")
    f.write(f"√λ(l=20) orig = {orig20:.10f}\n")
    f.write(f"√λ(l=100)    = {pred100:.10f}\n")

print("\n✅ Résultats sauvegardés dans 'extrapolation_delta_s2.txt'")