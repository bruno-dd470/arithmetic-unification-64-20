# plot_epsilon_heatmap.py
# Heatmap of ternary coefficients ε_k ∈ {-1, 0, 1} for all isotopes

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib import rcParams

rcParams.update({
    'font.size': 10,
    'font.family': 'serif',
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'figure.figsize': (10, 8),
})

# =============================================================================
# CHARGEMENT DES COEFFICIENTS ε
# =============================================================================
def load_epsilon_table(filename='table_isotopes_en_15_racines.txt'):
    """
    Charge la table des coefficients ε_k.
    Format attendu par ligne :
    Z  A  n_oct  ε0  ε1  ...  ε14
    """
    data = []
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip().startswith('#') or not line.strip():
                continue
            parts = line.split()
            if len(parts) >= 18:  # Z, A, n + 15 ε
                Z = int(parts[0])
                A = int(parts[1])
                n_oct = int(parts[2])
                eps = [int(x) for x in parts[3:18]]
                data.append((Z, A, n_oct, eps))
    return data

# =============================================================================
# GÉNÉRATION DE LA HEATMAP
# =============================================================================
def plot_epsilon_heatmap(data, output_prefix='fig2_epsilon_heatmap'):
    """Génère la heatmap de sparité des coefficients ε_k."""
    
    # Conversion en matrice NumPy : lignes = isotopes, colonnes = β_k
    n_iso = len(data)
    n_beta = 15
    epsilon_matrix = np.array([entry[3] for entry in data])  # shape (n_iso, 15)
    Z_list = np.array([entry[0] for entry in data])
    A_list = np.array([entry[1] for entry in data])
    
    # Tri par nombre de masse A pour une visualisation cohérente
    sort_idx = np.argsort(A_list)
    epsilon_matrix = epsilon_matrix[sort_idx]
    A_sorted = A_list[sort_idx]
    Z_sorted = Z_list[sort_idx]
    
    # Colormap divergente pour {-1, 0, +1}
    # Bleu = -1, Blanc = 0, Rouge = +1
    colors = ['#2166ac', '#f7f7f7', '#b2182b']  # bleu, blanc, rouge
    cmap = mcolors.ListedColormap(colors)
    norm = mcolors.BoundaryNorm([-1.5, -0.5, 0.5, 1.5], cmap.N)
    
    fig, ax = plt.subplots(1, 1)
    
    # Heatmap
    im = ax.imshow(epsilon_matrix.T,  # transposé : β en ordonnée
                   cmap=cmap, norm=norm,
                   aspect='auto', interpolation='nearest')
    
    # Labels des axes
    beta_labels = [f'β{k}' for k in range(15)]
    ax.set_yticks(np.arange(15))
    ax.set_yticklabels(beta_labels, fontsize=9)
    ax.set_ylabel('Racine fondamentale βₖ', fontsize=11)
    
    ax.set_xlabel('Isotopes (triés par A croissant)', fontsize=11)
    ax.set_title('Matrice de sparité des coefficients εₖ ∈ {{-1, 0, +1}}', 
                 fontsize=12, pad=15)
    
    # Axe secondaire pour A (nombre de masse)
    ax2 = ax.twiny()
    ax2.set_xlim(ax.get_xlim())
    ax2.set_xticks([0, n_iso//4, n_iso//2, 3*n_iso//4, n_iso-1])
    ax2.set_xticklabels([f'A≈{A_sorted[i]}' for i in [0, n_iso//4, n_iso//2, 3*n_iso//4, n_iso-1]], 
                        fontsize=8, rotation=45, ha='right')
    
    # Colorbar avec légende explicite
    cbar = plt.colorbar(im, ax=ax, ticks=[-1, 0, 1], fraction=0.02, pad=0.04)
    cbar.ax.set_yticklabels(['−1', '0', '+1'], fontsize=10)
    cbar.set_label('Coefficient εₖ', rotation=270, labelpad=20, fontsize=10)
    
    # Grille légère
    ax.grid(False)
    
    # Statistiques de sparité
    sparsity = np.mean(epsilon_matrix == 0) * 100
    pos_ratio = np.mean(epsilon_matrix == 1) * 100
    neg_ratio = np.mean(epsilon_matrix == -1) * 100
    
    stats_text = (
        f'Sparité : {sparsity:.1f} % de zéros\n'
        f'ε = +1 : {pos_ratio:.1f} %\n'
        f'ε = −1 : {neg_ratio:.1f} %'
    )
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
            fontsize=9, verticalalignment='top', horizontalalignment='left',
            bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.4))
    
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
    print("Chargement de la table des coefficients ε...")
    data = load_epsilon_table('table_isotopes_en_15_racines.txt')
    print(f"→ {len(data)} isotopes chargés")
    
    print("Génération de la heatmap...")
    plot_epsilon_heatmap(data)
