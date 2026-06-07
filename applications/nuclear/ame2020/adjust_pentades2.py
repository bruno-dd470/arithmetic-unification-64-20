"""
PENTADIC MASS MODEL: 80/20 OUT-OF-SAMPLE VALIDATION (FIXED LOADER)
==================================================================
Corrections appliquées :
1. Suppression du filtre erroné 'startswith("0")' qui rejetait 99% des isotopes.
2. Détection robuste des lignes de données via conversion float de N, Z, A.
3. Nettoyage automatique des champs AME2020 (espaces, caractères parasites).
4. Gestion fallback des configurations pentadiques.
"""
import re
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
from scipy.optimize import minimize

# =============================================================================
# CONSTANTES
# =============================================================================
U_TO_MEV = 931.49410242

# =============================================================================
# UTILITAIRES
# =============================================================================
def clean_numeric(value):
    """Nettoie les champs AME2020 et retourne un float ou NaN."""
    if pd.isna(value):
        return np.nan
    s = str(value).strip()
    # Retire préfixes/parasites courants dans AME
    s = re.sub(r'^[B-\*\#x]', '', s)
    if s in ['', '.', '-', '--', 'n', 'ssk', 'w']:
        return np.nan
    try:
        return float(s)
    except ValueError:
        return np.nan

# =============================================================================
# CHARGEMENT AME2020 (FORMAT BRUT ROBUSTE)
# =============================================================================
def load_ame2020(csv_path='ame2020.csv'):
    columns = [
        'N_minus_Z', 'N', 'Z', 'A', 'Element', 'Origin',
        'MassExcess_keV', 'Error_MassExcess_keV',
        'BindingPerA_keV', 'Error_BindingPerA_keV',
        'BetaDecay_keV', 'Error_BetaDecay_keV',
        'AtomicMass_u', 'Error_AtomicMass_u'
    ]
    rows = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # Sauter métadonnées évidentes
            if any(line.startswith(p) for p in ['N-Z', '1,a0', '1N-Z', '0,,,,']) or \
               any(kw in line for kw in ['DATE', 'ATOMICMASS', 'OMASS', 'ssk']):
                continue

            parts = line.split(',')
            if len(parts) < 14:
                continue

            # Test décisif : N, Z, A (indices 2, 3, 4) doivent être numériques
            try:
                n_val = float(parts[2])
                z_val = float(parts[3])
                a_val = float(parts[4])
            except (ValueError, IndexError):
                continue

            # Si N, Z, A sont valides, c'est une ligne de données
            row = {
                'N_minus_Z': parts[0].strip(),
                'N': n_val, 'Z': z_val, 'A': a_val,
                'Element': parts[5].strip(),
                'MassExcess_keV': parts[6].strip(),
                'Error_MassExcess_keV': parts[7].strip(),
                'BindingPerA_keV': parts[8].strip(),
                'Error_BindingPerA_keV': parts[9].strip(),
                'BetaDecay_keV': parts[10].strip(),
                'Error_BetaDecay_keV': parts[11].strip(),
                'AtomicMass_u': parts[12].strip(),
                'Error_AtomicMass_u': parts[13].strip(),
            }
            rows.append(row)

    df = pd.DataFrame(rows, columns=columns)
    if df.empty:
        raise RuntimeError("Aucune donnée valide trouvée. Vérifiez le format du CSV.")

    # Conversion propre des colonnes numériques
    for col in columns[2:]:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Masse en MeV
    df['mass_exp_MeV'] = df['AtomicMass_u'] * U_TO_MEV
    df['particle_id'] = df['Element'].astype(str) + '-' + df['A'].astype(str)

    print(f'✅ Loaded {len(df)} nuclei from {csv_path}')
    return df

# =============================================================================
# MASSE PENTADIQUE
# =============================================================================
def pentadic_mass(row, Lambda_fund, n_base, lambda_eigvals,
                  idx_col='pentad_indices', octaves_col='pentad_octaves',
                  signs_col='pentad_signs'):
    try:
        indices = row[idx_col]
        octaves = row[octaves_col]
        signs = row[signs_col]
        if isinstance(indices, str): indices = eval(indices)
        if isinstance(octaves, str): octaves = eval(octaves)
        if isinstance(signs, str): signs = eval(signs)
    except Exception:
        return np.nan

    if indices is None or len(indices) == 0:
        return np.nan

    n_pent = len(indices)
    exponent_limit = 20
    oct_factors = np.array([4.0 ** min(n_base + o, exponent_limit) for o in octaves[:n_pent]], dtype=np.float64)
    sqrt_lambdas = np.array([np.sqrt(lambda_eigvals[i % 72]) for i in indices])
    weighted = np.array(signs[:n_pent]) * oct_factors * sqrt_lambdas
    norm = np.linalg.norm(weighted) / np.sqrt(10)
    return Lambda_fund * norm

# =============================================================================
# CALIBRATION
# =============================================================================
def calibrate(train_df, lambda_eigvals, idx_col='pentad_indices',
              octaves_col='pentad_octaves', signs_col='pentad_signs'):
    def objective(params):
        Lambda, n_base_float = params
        n_base = int(round(np.clip(n_base_float, 0, 8)))
        preds = train_df.apply(lambda r: pentadic_mass(r, Lambda, n_base, lambda_eigvals, idx_col, octaves_col, signs_col), axis=1)
        mask = ~preds.isna() & ~train_df['mass_exp_MeV'].isna()
        if mask.sum() < 10:
            return 1e12
        return np.sqrt(np.mean((preds[mask] - train_df.loc[mask, 'mass_exp_MeV']) ** 2))

    result = minimize(objective, x0=[7.7, 4.0], method='L-BFGS-B', bounds=[(0.001, 1000.0), (0.0, 8.0)])
    return result.x[0], int(round(np.clip(result.x[1], 0, 8)))

# =============================================================================
# SEMF (BETHE-WEIZSÄCKER)
# =============================================================================
def semf_mass(Z, N):
    A = Z + N
    if A <= 0: return np.nan
    a_v, a_s, a_c, a_a, a_p = 15.75, 17.8, 0.711, 23.7, 11.18
    delta = 0 if A % 2 == 1 else (a_p / np.sqrt(A) if Z % 2 == 0 else -a_p / np.sqrt(A))
    BE = a_v*A - a_s*A**(2/3) - a_c*Z*(Z-1)/A**(1/3) - a_a*(A-2*Z)**2/A + delta
    m_p, m_n = 938.27208816, 939.56542052
    return Z * m_p + N * m_n - BE

# =============================================================================
# VALIDATION
# =============================================================================
def run_validation(df, lambda_eigvals, idx_col='pentad_indices',
                   octaves_col='pentad_octaves', signs_col='pentad_signs',
                   test_size=0.2, random_state=42):
    df_valid = df[df['mass_exp_MeV'].notna() & df['A'].notna() & (df['A'] > 0)].copy()
    if len(df_valid) < 50:
        print(f'⚠️ Only {len(df_valid)} valid entries. Split may be unstable.')

    train, test = train_test_split(df_valid, test_size=test_size, random_state=random_state)

    L_opt, n_opt = calibrate(train, lambda_eigvals, idx_col, octaves_col, signs_col)
    print(f'✅ Λ = {L_opt:.4f} MeV | n_base = {n_opt}')

    test['mass_pred_MeV'] = test.apply(
        lambda r: pentadic_mass(r, L_opt, n_opt, lambda_eigvals, idx_col, octaves_col, signs_col), axis=1
    )
    valid_mask = test['mass_pred_MeV'].notna() & test['mass_exp_MeV'].notna()
    if valid_mask.sum() < 10:
        print('⚠️ Pas assez de prédictions valides')
        return None

    rmse = np.sqrt(mean_squared_error(test.loc[valid_mask, 'mass_exp_MeV'], test.loc[valid_mask, 'mass_pred_MeV']))
    mae = mean_absolute_error(test.loc[valid_mask, 'mass_exp_MeV'], test.loc[valid_mask, 'mass_pred_MeV'])
    print(f'\n📈 TEST OUT-OF-SAMPLE')
    print(f'RMSE : {rmse:.6f} MeV')
    print(f'MAE  : {mae:.6f} MeV')

    # Comparaison SEMF
    if 'Z' in test.columns and 'N' in test.columns:
        test_valid = test[valid_mask].copy()
        test_valid['mass_semf'] = test_valid.apply(lambda r: semf_mass(r['Z'], r['N']), axis=1)
        rmse_semf = np.sqrt(mean_squared_error(test_valid['mass_exp_MeV'], test_valid['mass_semf']))
        gain = (1 - rmse/rmse_semf)*100 if rmse_semf > 0 else 0
        print(f'\n🔍 BASELINE COMPARISON (SEMF)')
        print(f'SEMF RMSE : {rmse_semf:.6f} MeV')
        print(f'Pentadic improvement: {gain:+.1f}%')

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

    # Fallback pentadique si colonnes absentes
    if 'pentad_indices' not in df.columns:
        print('⚠️ Dummy pentadic configurations inserted')
        df['pentad_indices'] = df['A'].apply(lambda a: [int(a) % 72] if pd.notna(a) else None)
        df['pentad_octaves'] = df['A'].apply(lambda a: [0] if pd.notna(a) else None)
        df['pentad_signs'] = df['A'].apply(lambda a: [1] if pd.notna(a) else None)

    results = run_validation(df, LAMBDA_72)
    if results is not None:
        results.to_csv('validation_results_80_20.csv', index=False)
        print('\n✅ Results saved to validation_results_80_20.csv')
