"""
PENTADIC MASS MODEL: 80/20 OUT-OF-SAMPLE VALIDATION
===================================================
Version corrigée pour le vrai format AME2020.

Corrections principales :
- Lecture robuste du fichier AME2020.
- Suppression correcte des lignes de métadonnées.
- Gestion des symboles non numériques (#, *, x, n...).
- Évite les KeyError quand certaines colonnes manquent.
- Chargement fiable des 72 valeurs propres.
"""

import re
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
from scipy.optimize import minimize


# =============================================================================
# CONSTANTS
# =============================================================================

U_TO_MEV = 931.49410242


# =============================================================================
# UTILITAIRES
# =============================================================================

def clean_numeric(value):
    """
    Nettoie les champs AME2020 contenant des caractères parasites.
    """

    if pd.isna(value):
        return np.nan

    s = str(value).strip()

    if s == "":
        return np.nan

    # Retire caractères parasites fréquents dans AME2020
    s = s.replace('#', '')
    s = s.replace('*', '')
    s = s.replace('x', '')
    s = s.replace('n', '')

    # Retire préfixes type B-
    s = s.replace('B-', '')

    # Cas impossibles
    if s in ['.', '-', '--']:
        return np.nan

    try:
        return float(s)
    except Exception:
        return np.nan


# =============================================================================
# CHARGEMENT AME2020
# =============================================================================

def load_ame2020(csv_path='ame2020.csv'):
    """
    Charge correctement le format réel AME2020.
    """

    columns = [
        'N_minus_Z',
        'N',
        'Z',
        'A',
        'Element',
        'Origin',
        'MassExcess_keV',
        'Error_MassExcess_keV',
        'BindingPerA_keV',
        'Error_BindingPerA_keV',
        'BetaDecay_keV',
        'Error_BetaDecay_keV',
        'AtomicMass_u',
        'Error_AtomicMass_u'
    ]

    rows = []

    with open(csv_path, 'r', encoding='utf-8') as f:

        for line in f:

            line = line.strip()

            if not line:
                continue

            # Ignore entêtes et métadonnées
            if line.startswith('N-Z'):
                continue

            if line.startswith('1,a0'):
                continue

            if line.startswith('0,,,,'):
                continue

            if 'DATE' in line:
                continue

            if 'ATOMICMASS' in line:
                continue

            parts = line.split(',')

            if len(parts) < 14:
                continue

            # Les vraies lignes de données commencent par 0 xx
            first_field = parts[0].strip()

            if not first_field.startswith('0'):
                continue

            try:
                row = {
                    'N_minus_Z': clean_numeric(parts[0]),
                    'N': clean_numeric(parts[2]),
                    'Z': clean_numeric(parts[3]),
                    'A': clean_numeric(parts[4]),
                    'Element': str(parts[5]).strip(),
                    'Origin': '',
                    'MassExcess_keV': clean_numeric(parts[6]),
                    'Error_MassExcess_keV': clean_numeric(parts[7]),
                    'BindingPerA_keV': clean_numeric(parts[8]),
                    'Error_BindingPerA_keV': clean_numeric(parts[9]),
                    'BetaDecay_keV': clean_numeric(parts[10]),
                    'Error_BetaDecay_keV': clean_numeric(parts[11]),
                    'AtomicMass_u': clean_numeric(parts[12]),
                    'Error_AtomicMass_u': clean_numeric(parts[13]),
                }

                rows.append(row)

            except Exception:
                continue

    df = pd.DataFrame(rows)

    if len(df) == 0:
        raise RuntimeError('Aucune donnée valide trouvée dans AME2020.')

    # Conversion en MeV
    df['mass_exp_MeV'] = df['AtomicMass_u'] * U_TO_MEV

    # Identifiant noyau
    df['particle_id'] = (
        df['Element'].astype(str) + '-' + df['A'].astype(str)
    )

    print(f'✅ Loaded {len(df)} nuclei from {csv_path}')

    return df


# =============================================================================
# MASSE PENTADIQUE
# =============================================================================

def pentadic_mass(
    row,
    Lambda_fund,
    n_base,
    lambda_eigvals,
    indices_col='pentad_indices',
    octaves_col='pentad_octaves',
    signs_col='pentad_signs'
):

    try:
        indices = row[indices_col]
        octaves = row[octaves_col]
        signs = row[signs_col]

        if isinstance(indices, str):
            indices = eval(indices)

        if isinstance(octaves, str):
            octaves = eval(octaves)

        if isinstance(signs, str):
            signs = eval(signs)

    except Exception:
        return np.nan

    if indices is None or len(indices) == 0:
        return np.nan

    n_pent = len(indices)

    # Protection contre overflow numérique
    exponent_limit = 20

    oct_factors = np.array([
        4.0 ** min(n_base + o, exponent_limit)
        for o in octaves[:n_pent]
    ], dtype=np.float64)

    sqrt_lambdas = np.array([
        np.sqrt(lambda_eigvals[i % 72])
        for i in indices
    ])

    weighted = (
        np.array(signs[:n_pent])
        * oct_factors
        * sqrt_lambdas
    )

    norm = np.linalg.norm(weighted) / np.sqrt(10)

    return Lambda_fund * norm


# =============================================================================
# CALIBRATION
# =============================================================================

def calibrate(
    train_df,
    lambda_eigvals,
    indices_col='pentad_indices',
    octaves_col='pentad_octaves',
    signs_col='pentad_signs'
):

    def objective(params):

        Lambda, n_base_float = params

        n_base = int(round(np.clip(n_base_float, 0, 8)))

        preds = train_df.apply(
            lambda r: pentadic_mass(
                r,
                Lambda,
                n_base,
                lambda_eigvals,
                indices_col,
                octaves_col,
                signs_col
            ),
            axis=1
        )

        mask = (
            ~preds.isna()
            & ~train_df['mass_exp_MeV'].isna()
        )

        if mask.sum() < 10:
            return 1e12

        return np.sqrt(np.mean(
            (preds[mask] - train_df.loc[mask, 'mass_exp_MeV']) ** 2
        ))

    result = minimize(
        objective,
        x0=[7.7, 4.0],
        method='L-BFGS-B',
        bounds=[
            (0.001, 1000.0),
            (0.0, 8.0)
        ]
    )

    return result.x[0], int(round(np.clip(result.x[1], 0, 8)))


# =============================================================================
# SEMF
# =============================================================================

def semf_mass(Z, N):

    A = Z + N

    if A <= 0:
        return np.nan

    a_v = 15.75
    a_s = 17.8
    a_c = 0.711
    a_a = 23.7
    a_p = 11.18

    if A % 2 == 1:
        delta = 0
    elif Z % 2 == 0:
        delta = a_p / np.sqrt(A)
    else:
        delta = -a_p / np.sqrt(A)

    BE = (
        a_v * A
        - a_s * A ** (2 / 3)
        - a_c * Z * (Z - 1) / A ** (1 / 3)
        - a_a * (A - 2 * Z) ** 2 / A
        + delta
    )

    m_p = 938.27208816
    m_n = 939.56542052

    return Z * m_p + N * m_n - BE


# =============================================================================
# VALIDATION
# =============================================================================

def run_validation(
    df,
    lambda_eigvals,
    indices_col='pentad_indices',
    octaves_col='pentad_octaves',
    signs_col='pentad_signs',
    test_size=0.2,
    random_state=42
):

    df_valid = df[
        df['mass_exp_MeV'].notna()
    ].copy()

    if len(df_valid) < 50:
        print(f'⚠️ Only {len(df_valid)} valid entries')

    train, test = train_test_split(
        df_valid,
        test_size=test_size,
        random_state=random_state
    )


    L_opt, n_opt = calibrate(
        train,
        lambda_eigvals,
        indices_col,
        octaves_col,
        signs_col
    )

    print(f'✅ Λ = {L_opt:.4f} MeV | n_base = {n_opt}')

    test['mass_pred_MeV'] = test.apply(
        lambda r: pentadic_mass(
            r,
            L_opt,
            n_opt,
            lambda_eigvals,
            indices_col,
            octaves_col,
            signs_col
        ),
        axis=1
    )

    valid_mask = (
        test['mass_pred_MeV'].notna()
        & test['mass_exp_MeV'].notna()
    )

    if valid_mask.sum() < 10:
        print('⚠️ Pas assez de prédictions valides')
        return None

    rmse = np.sqrt(mean_squared_error(
        test.loc[valid_mask, 'mass_exp_MeV'],
        test.loc[valid_mask, 'mass_pred_MeV']
    ))

    mae = mean_absolute_error(
        test.loc[valid_mask, 'mass_exp_MeV'],
        test.loc[valid_mask, 'mass_pred_MeV']
    )

    print('\n📈 TEST OUT-OF-SAMPLE')
    print(f'RMSE : {rmse:.6f} MeV')
    print(f'MAE  : {mae:.6f} MeV')

    return test


# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':

    print('🚀 Loading eigenvalues...')

    LAMBDA_72 = np.loadtxt('eigvals_72.txt')

    print(f'✅ Loaded {len(LAMBDA_72)} eigenvalues')

    print('🚀 Loading AME2020...')

    df = load_ame2020('ame2020.csv')

    # Configurations factices de test
    if 'pentad_indices' not in df.columns:

        df['pentad_indices'] = df['A'].apply(
            lambda a: [int(a) % 72] if pd.notna(a) else None
        )

        df['pentad_octaves'] = df['A'].apply(
            lambda a: [0] if pd.notna(a) else None
        )

        df['pentad_signs'] = df['A'].apply(
            lambda a: [1] if pd.notna(a) else None
        )

        print('⚠️ Dummy pentadic configurations inserted')

    results = run_validation(df, LAMBDA_72)

    if results is not None:

        results.to_csv(
            'validation_results_80_20.csv',
            index=False
        )

        print('\n✅ Results saved to validation_results_80_20.csv')

