#!/usr/bin/env python3
# plot_error_distribution_safe.py
# Version sécurisée : gestion des erreurs, bins non chevauchants, rendu léger

import numpy as np
import matplotlib.pyplot as plt
import os
import sys

# Configuration légère pour éviter la saturation mémoire
plt.rcParams.update({
    'font.size': 10,
    'font.family': 'sans-serif',
    'figure.dpi': 150,          # Réduit pour test, monter à 300 pour publication
    'savefig.dpi': 300,
    'figure.figsize': (6, 4),
    'axes.linewidth': 0.8,
    'mathtext.fontset': 'stix',
})

def load_errors(filename='isotope_fits_full.txt'):
    """Charge les erreurs relatives avec vérifications robustes."""
    if not os.path.exists(filename):
        print(f"❌ Fichier non trouvé : {filename}")
        sys.exit(1)
    
    errors = []
    with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split()
            if len(parts) >= 7:
                try:
                    err = abs(float(parts[6]))  # valeur absolue, colonne erreur %
                    if err < 10:  # filtre les valeurs aberrantes
                        errors.append(err)
                except ValueError:
                    continue
    if not errors:
        print("❌ Aucune erreur valide chargée. Vérifiez le format du fichier.")
        sys.exit(1)
    return np.array(errors)

def plot_error_histogram_safe(errors, output_prefix='fig1_error_dist'):
    """Génère l'histogramme avec bins sûrs et échelle adaptée."""
    
    fig, ax = plt.subplots(1, 1)
    
    # Bins non chevauchants : utiliser np.hstack avec exclusion des bornes dupliquées
    bins_part1 = np.linspace(0, 0.05, 11)[:-1]      # 0 → 0.05 (exclut 0.05)
    bins_part2 = np.linspace(0.05, 0.10, 6)[:-1]    # 0.05 → 0.10 (exclut 0.10)
    bins_part3 = np.linspace(0.10, 0.26, 9)         # 0.10 → 0.26 (inclut fin)
    bins = np.hstack([bins_part1, bins_part2, bins_part3])
    
    # Filtrer les erreurs hors plage pour éviter les warnings
    errors_plot = errors[(errors >= 0) & (errors <= 0.26)]
    
    n, bins_edges, patches = ax.hist(
        errors_plot, bins=bins,
        edgecolor='black', linewidth=0.4,
        color='steelblue', alpha=0.8,
        density=False
    )
    
    # Statistiques
    mean_err = np.mean(errors)
    std_err = np.std(errors)
    max_err = np.max(errors)
    pct_02 = np.sum(errors < 0.2) / len(errors) * 100
    
    stats_text = (
        f'N = {len(errors)} isotopes\n'
        f'Moy. : {mean_err:.4f} %\n'
        f'σ : {std_err:.4f} %\n'
        f'Max : {max_err:.3f} %\n'
        f'< 0.2 % : {pct_02:.1f} %'
    )
    
    ax.text(0.97, 0.97, stats_text, transform=ax.transAxes,
            fontsize=8, va='top', ha='right',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.4))
    
    # Échelle log SÉCURISÉE : ajouter un petit offset pour éviter log(0)
    ax.set_yscale('log')
    ax.set_ylim(bottom=0.8)  # évite les valeurs < 1 en log
    
    ax.set_xlabel('Erreur relative absolue (%)', fontsize=10)
    ax.set_ylabel('Nombre d\'isotopes (log)', fontsize=10)
    ax.set_title('Distribution des erreurs (AME2020)', fontsize=11, pad=12)
    
    ax.grid(axis='y', linestyle=':', alpha=0.5)
    ax.set_xlim(0, 0.26)
    
    # Ligne seuil 0.2%
    ax.axvline(x=0.2, color='red', linestyle='--', linewidth=0.8, 
               label='Seuil 0.2 %', zorder=5)
    ax.legend(fontsize=8, loc='upper right', frameon=True)
    
    # tight_layout avec padding explicite pour éviter les calculs infinis
    plt.tight_layout(pad=2.0)
    
    # Sauvegarde progressive
    for fmt in ['png', 'pdf']:
        try:
            filepath = f'{output_prefix}.{fmt}'
            plt.savefig(filepath, bbox_inches='tight')
            print(f'✓ Sauvé : {filepath}')
        except Exception as e:
            print(f'⚠ Échec sauvegarde {fmt} : {e}')
    
    plt.close(fig)  # Libère la mémoire
    print("✓ Graphique généré avec succès")
    return True

if __name__ == '__main__':
    print("🔍 Chargement des erreurs...")
    errors = load_errors('isotope_fits_full.txt')
    print(f"→ {len(errors)} valeurs chargées")
    
    print("📊 Génération de l'histogramme...")
    try:
        plot_error_histogram_safe(errors)
        print("✅ Terminé.")
    except KeyboardInterrupt:
        print("\n⚠ Interruption par l'utilisateur")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Erreur critique : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
