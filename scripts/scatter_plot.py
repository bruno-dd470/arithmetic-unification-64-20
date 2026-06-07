# scatter_plot.py (VERSION CORRIGÉE)
# Scatter plot: predicted vs experimental masses (AME2020)

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams
from scipy import stats

# Configuration stable pour éviter les erreurs de rendu mathtext
rcParams.update({
    'font.size': 11,
    'font.family': 'serif',
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'figure.figsize': (6.5, 6),
    'axes.linewidth': 0.8,
    'mathtext.fontset': 'stix',  # Utilisation de la police STIX (native, pas besoin de LaTeX)
    'mathtext.default': 'it',
})

# =============================================================================
# CHARGEMENT DES DONNÉES
# =============================================================================
def load_predictions(filename='isotope_fits_full.txt'):
    """Charge les masses vraies et prédites."""
    M_true, M_pred, labels = [], [], []
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip().startswith('#') or not line.strip():
                continue
            parts = line.split()
            if len(parts) >= 6:
                Z = int(parts[0])
                A = int(parts[1])
                true_val = float(parts[2])
                pred_val = float(parts[5])
                M_true.append(true_val)
                M_pred.append(pred_val)
                labels.append(f"{Z}-{A}")
    return np.array(M_true), np.array(M_pred), labels

# =============================================================================
# GÉNÉRATION DU SCATTER PLOT
# =============================================================================
def plot_pred_vs_exp(M_true, M_pred, labels, output_prefix='fig3_pred_vs_exp'):
    """Génère le graphique de corrélation prédit vs expérimental."""
    
    fig, ax = plt.subplots(1, 1)
    
    # Points avec transparence pour éviter la surcharge
    ax.scatter(M_true, M_pred, s=12, c='steelblue', 
               alpha=0.6, edgecolors='black', linewidth=0.3,
               label='Isotopes AME2020')
    
    # Ligne d'identité y = x (parfaite prédiction)
    min_M, max_M = M_true.min(), M_true.max()
    ax.plot([min_M, max_M], [min_M, max_M], 
            'r--', linewidth=1, label='Ligne d\'identité (y = x)')
    
    # Bande ±0.2% autour de l'identité
    ax.fill_between([min_M, max_M], 
                    [min_M*0.998, max_M*0.998], 
                    [min_M*1.002, max_M*1.002],
                    color='gray', alpha=0.1, label='±0.2 %')
    
    # Régression linéaire et statistiques
    slope, intercept, r_value, p_value, std_err = stats.linregress(M_true, M_pred)
    
    # Métriques d'erreur
    rel_errors = np.abs(M_pred - M_true) / M_true * 100
    mean_err = np.mean(rel_errors)
    std_err_val = np.std(rel_errors)
    max_err = np.max(rel_errors)
    
    # Texte des statistiques (sans commande LaTeX problématique)
    stats_text = (
        f'$R^2$ = {r_value**2:.6f}\n'
        f'Pente : {slope:.6f}\n'
        f'Ordonnée : {intercept:.3f} MeV\n\n'
        f'Erreur moyenne : {mean_err:.4f} %\n'
        f'Écart-type : {std_err_val:.4f} %\n'
        f'Erreur max : {max_err:.3f} %'
    )
    
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
            fontsize=9, verticalalignment='top', horizontalalignment='left',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.4))
    
    # Labels corrigés : \mathrm{} est nativement supporté par Matplotlib
    ax.set_xlabel('Masse expérimentale $M_{\\mathrm{exp}}$ (MeV)', fontsize=11)
    ax.set_ylabel('Masse prédite $M_{\\mathrm{pred}}$ (MeV)', fontsize=11)
    ax.set_title('Prédiction vs Expérience (295 isotopes AME2020)', 
                 fontsize=12, pad=15)
    
    # Échelle logarithmique pour mieux voir l'ensemble du spectre
    ax.set_xscale('log')
    ax.set_yscale('log')
    
    # Grille
    ax.grid(True, linestyle='--', alpha=0.3, which='both')
    
    # Légende
    ax.legend(frameon=True, fontsize=9, loc='lower right')
    
    # Format des ticks
    ax.tick_params(axis='both', which='major', labelsize=9)
    
    plt.tight_layout()
    
    # Sauvegarde
    for fmt in ['png', 'pdf']:
        plt.savefig(f'{output_prefix}.{fmt}', bbox_inches='tight')
        print(f'✓ Sauvé : {output_prefix}.{fmt}')
    
    plt.show()
    return fig, ax

# =============================================================================
# EXÉCUTION
# =============================================================================
if __name__ == '__main__':
    print("Chargement des masses prédites et expérimentales...")
    M_true, M_pred, labels = load_predictions('isotope_fits_full.txt')
    print(f"→ {len(M_true)} isotopes chargés")
    
    print("Génération du scatter plot...")
    plot_pred_vs_exp(M_true, M_pred, labels)