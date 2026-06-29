import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.stats import spearmanr, pearsonr
from itertools import permutations
import matplotlib.pyplot as plt

# ================================================================
# DONNÉES
# ================================================================

# Les 15 beta_k empiriques (calibrées sur les masses nucléaires)
beta = np.array([
    0.06613695904451328,
    0.28174250870863576,
    0.5558698717637468,
    0.8682439499340019,
    1.5041139699699269,
    1.7252596926363315,
    1.831267929898219,
    2.0174227816393127,
    2.092837042770219,
    2.524927313875301,
    3.279177783,
    3.851477234958053,
    4.571556651552703,
    4.724739892029763,
    7.407963149728111
])

# Les 15 disq(E_k) de la décomposition orthogonale candidate
disq_E = np.array([
    1,      # E0: A1
    3,      # E1: A2
    2,      # E2: A3
    5,      # E3: A4
    1,      # E4: D4
    2,      # E5: D5
    -1,     # E6: D6
    -3,     # E7: E6
    -1,     # E8: E7
    1,      # E9: E8
    1,      # E10: A1^8
    81,     # E11: A2^4
    1,      # E12: A1^4
    9,      # E13: A2^2
    3       # E14: A1^2 ⊥ A2
])

n = 15
indices = np.arange(n)

print("=" * 70)
print("ANALYSE DE LA CONJECTURE : beta_k = lambda * disq(E_sigma(k)) * u_k")
print("=" * 70)
print(f"\nNombre de composantes : {n}")
print(f"beta    = {beta}")
print(f"disq(E) = {disq_E}")

# ================================================================
# 1. TEST DE CORRÉLATION
# ================================================================

print("\n" + "=" * 70)
print("1. TEST DE CORRÉLATION")
print("=" * 70)

# 1.1 Valeurs absolues
beta_abs = np.abs(beta)
disq_abs = np.abs(disq_E)

# 1.2 Corrélation de Spearman (monotonique)
rho, p_spearman = spearmanr(beta_abs, disq_abs)
print(f"\nCorrélation de Spearman (|beta|, |disq|) : rho = {rho:.6f}, p = {p_spearman:.2e}")

# 1.3 Corrélation de Pearson (linéaire)
r, p_pearson = pearsonr(beta_abs, disq_abs)
print(f"Corrélation de Pearson   (|beta|, |disq|) : r   = {r:.6f}, p = {p_pearson:.2e}")

# 1.4 Interprétation
if rho > 0.9 and p_spearman < 0.05:
    print("\n✅ Corrélation très forte. Il existe une relation monotone entre les deux vecteurs.")
else:
    print("\n⚠️ Corrélation faible. La conjecture est mise en doute.")

# ================================================================
# 2. RÉGRESSION LINÉAIRE (sans permutation)
# ================================================================

print("\n" + "=" * 70)
print("2. RÉGRESSION LINÉAIRE (sans permutation)")
print("=" * 70)

# 2.1 Régression avec intercept
from scipy.stats import linregress
slope, intercept, r2, p_value, std_err = linregress(disq_abs, beta_abs)
print(f"\nbeta = {slope:.6f} * |disq| + {intercept:.6f}")
print(f"R² = {r2**2:.6f}")

# 2.2 Régression sans intercept
lambda_ols = np.sum(disq_abs * beta_abs) / np.sum(disq_abs**2)
print(f"lambda (sans intercept) = {lambda_ols:.6f}")
beta_pred_ols = lambda_ols * disq_abs
erreur_ols = np.linalg.norm(beta_abs - beta_pred_ols) / np.linalg.norm(beta_abs)
print(f"Erreur relative = {erreur_ols*100:.2f}%")

# ================================================================
# 3. APPARIEMENT OPTIMAL (ALGORITHME HONGROIS)
# ================================================================

print("\n" + "=" * 70)
print("3. APPARIEMENT OPTIMAL (ALGORITHME HONGROIS)")
print("=" * 70)

# Matrice de coût : on minimise |beta_i - sign * disq_j| / max(|beta_i|, |disq_j|)
cost_matrix = np.zeros((n, n))
for i in range(n):
    for j in range(n):
        if disq_E[j] == 0:
            cost_matrix[i, j] = 1e6
        else:
            # Essayer les deux signes et prendre le minimum
            err_pos = abs(beta[i] - disq_E[j]) / max(abs(beta[i]), abs(disq_E[j]), 1e-10)
            err_neg = abs(beta[i] + disq_E[j]) / max(abs(beta[i]), abs(disq_E[j]), 1e-10)
            cost_matrix[i, j] = min(err_pos, err_neg)

# Appariement optimal
row_ind, col_ind = linear_sum_assignment(cost_matrix)

# Récupérer la permutation et les signes
permutation = col_ind
signs = np.zeros(n)
ratios = np.zeros(n)

print("\nAppariement optimal trouvé :")
for i, j in zip(row_ind, col_ind):
    # Déterminer le signe optimal
    err_pos = abs(beta[i] - disq_E[j]) / max(abs(beta[i]), abs(disq_E[j]), 1e-10)
    err_neg = abs(beta[i] + disq_E[j]) / max(abs(beta[i]), abs(disq_E[j]), 1e-10)
    sign = 1 if err_pos < err_neg else -1
    signs[i] = sign
    ratios[i] = beta[i] / (disq_E[j] * sign) if disq_E[j] != 0 else 0
    print(f"β_{i:2d} = {beta[i]:.6f}  ↔  disq(E_{j:2d}) = {disq_E[j]:.0f}  signe={sign:+d}  ratio={ratios[i]:.4f}")

# Statistiques des ratios
ratios_valid = ratios[ratios != 0]
mean_ratio = np.mean(ratios_valid)
std_ratio = np.std(ratios_valid)
cv_ratio = std_ratio / abs(mean_ratio) * 100

print(f"\nMoyenne des rapports (|beta| / |disq|) : {mean_ratio:.4f}")
print(f"Écart-type des rapports                : {std_ratio:.4f}")
print(f"Coefficient de variation               : {cv_ratio:.2f}%")

# Interprétation
if cv_ratio < 5:
    print("\n✅ Coefficient de variation < 5% : La conjecture est VALIDÉE.")
    print("   Les beta_k sont bien les disq(E_k) à un facteur d'échelle près.")
elif cv_ratio < 15:
    print("\n⚠️ Coefficient de variation 5-15% : La conjecture est PARTIELLEMENT VALIDÉE.")
    print("   Certaines composantes dévient significativement.")
else:
    print("\n❌ Coefficient de variation > 15% : La conjecture n'est pas validée.")
    print("   La décomposition candidate n'est pas la bonne.")

# ================================================================
# 4. ESTIMATION DU FACTEUR D'ÉCHELLE λ
# ================================================================

print("\n" + "=" * 70)
print("4. ESTIMATION DU FACTEUR D'ÉCHELLE λ")
print("=" * 70)

# Estimation par moindres carrés avec la permutation optimale
d_perm = np.array([disq_E[j] for j in permutation])
lambda_opt = np.sum(d_perm * beta) / np.sum(d_perm**2)
print(f"λ optimal (moindres carrés) = {lambda_opt:.6f}")

# Prédiction avec λ et la permutation
beta_pred = lambda_opt * d_perm
erreur = np.linalg.norm(beta - beta_pred) / np.linalg.norm(beta)
print(f"Erreur relative de la prédiction = {erreur*100:.2f}%")

# Si l'erreur est faible, afficher la correspondance finale
if erreur < 0.1:
    print("\nCorrespondance finale :")
    for i, j in enumerate(permutation):
        print(f"β_{i:2d} = {beta[i]:.6f}  ≈  {lambda_opt:.6f} * disq(E_{j:2d}) = {lambda_opt * disq_E[j]:.6f}")

# ================================================================
# 5. VÉRIFICATION DE LA MULTIPLICATIVITÉ
# ================================================================

print("\n" + "=" * 70)
print("5. VÉRIFICATION DE LA MULTIPLICATIVITÉ")
print("=" * 70)

# La multiplicativité dit : disq(E_i ⊥ E_j) = (-1)^(s) * disq(E_i) * disq(E_j)
# Si beta_k = disq(E_k), alors beta_i * beta_j doit être un autre beta (à un signe près)

multiplicative_pairs = 0
total_pairs = 0

print("\nTest des 105 paires (i < j) :")
for i in range(n):
    for j in range(i+1, n):
        total_pairs += 1
        prod = beta[i] * beta[j]
        # Chercher un k tel que prod ≈ ± beta[k]
        found = False
        for k in range(n):
            if k != i and k != j:
                if abs(abs(prod) - abs(beta[k])) / abs(beta[k]) < 1e-3:
                    multiplicative_pairs += 1
                    found = True
                    break

print(f"Paires satisfaisant la multiplicativité : {multiplicative_pairs}/{total_pairs}")
print(f"Taux de succès : {multiplicative_pairs/total_pairs*100:.1f}%")

if multiplicative_pairs/total_pairs > 0.8:
    print("✅ Taux élevé (>80%) : la structure multiplicative est cohérente.")
else:
    print("⚠️ Taux modéré : la multiplicativité n'est pas pleinement vérifiée.")

# ================================================================
# 6. VISUALISATION
# ================================================================

print("\n" + "=" * 70)
print("6. VISUALISATION (graphique en sortie)")
print("=" * 70)

plt.figure(figsize=(12, 8))

# 6.1 Scatter plot : |beta| vs |disq|
plt.subplot(2, 2, 1)
plt.scatter(disq_abs, beta_abs, color='blue', s=80)
plt.plot(disq_abs, lambda_ols * disq_abs, 'r--', label=f'λ={lambda_ols:.3f}')
plt.xlabel('|disq(E)|')
plt.ylabel('|β|')
plt.title('|β| vs |disq(E)|')
plt.legend()
plt.grid(True, alpha=0.3)

# 6.2 Scatter plot : beta vs disq (avec permutation)
plt.subplot(2, 2, 2)
beta_sorted = beta
disq_sorted = np.array([disq_E[j] for j in permutation])
plt.scatter(disq_sorted, beta_sorted, color='green', s=80)
plt.plot(disq_sorted, lambda_opt * disq_sorted, 'r--', label=f'λ={lambda_opt:.3f}')
plt.xlabel('disq(E) (réordonné)')
plt.ylabel('β')
plt.title('β vs disq(E) (après permutation optimale)')
plt.legend()
plt.grid(True, alpha=0.3)

# 6.3 Barres : rapport beta/disq
plt.subplot(2, 2, 3)
plt.bar(range(n), ratios, color='purple', alpha=0.7)
plt.axhline(y=mean_ratio, color='r', linestyle='--', label=f'moyenne = {mean_ratio:.3f}')
plt.xlabel('Indice k')
plt.ylabel('β_k / disq(E_σ(k))')
plt.title('Rapports β / disq (avec permutation optimale)')
plt.legend()
plt.grid(True, alpha=0.3)

# 6.4 Heatmap de la matrice de coût
plt.subplot(2, 2, 4)
plt.imshow(cost_matrix, cmap='hot', aspect='auto')
plt.colorbar(label='Coût')
plt.xlabel('Composante disq(E_j)')
plt.ylabel('Composante β_i')
plt.title('Matrice de coût')
# Marquer l'appariement optimal
for i, j in zip(row_ind, col_ind):
    plt.plot(j, i, 'gs', markersize=8, markeredgecolor='white', markeredgewidth=1)

plt.tight_layout()
plt.savefig('appariement_beta_disq.png', dpi=150, bbox_inches='tight')
print("\nGraphique sauvegardé dans 'appariement_beta_disq.png'")

# ================================================================
# 7. SYNTHÈSE FINALE
# ================================================================

print("\n" + "=" * 70)
print("7. SYNTHÈSE FINALE")
print("=" * 70)

print(f"""
Résultats clés :
-------------- 
1. Corrélation de Spearman   : rho = {rho:.4f} (p = {p_spearman:.2e})
2. Corrélation de Pearson    : r   = {r:.4f} (p = {p_pearson:.2e})
3. λ optimal                 : {lambda_opt:.6f}
4. Erreur relative (permutation) : {erreur*100:.2f}%
5. Coefficient de variation des ratios : {cv_ratio:.2f}%
6. Taux de multiplicativité   : {multiplicative_pairs/total_pairs*100:.1f}%
""")

# Conclusion finale
if cv_ratio < 5 and erreur < 0.05 and rho > 0.9:
    print("✅✅✅ CONCLUSION : La conjecture est FORTEMENT VALIDÉE.")
    print("    Les beta_k sont les discriminants quadratiques des composantes")
    print("    d'une décomposition orthogonale de Λ72, à un facteur d'échelle près.")
elif cv_ratio < 15 and erreur < 0.15 and rho > 0.8:
    print("✅ CONCLUSION : La conjecture est VALIDÉE de manière satisfaisante.")
    print("    Les écarts résiduels suggèrent des corrections non linéaires.")
else:
    print("⚠️ CONCLUSION : La conjecture n'est pas validée avec la décomposition candidate.")
    print("    Il faut chercher une autre décomposition orthogonale de Λ72.")
