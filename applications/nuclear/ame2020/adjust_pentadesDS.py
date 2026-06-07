"""
PENTADIC MASS MODEL: 80/20 OUT-OF-SAMPLE VALIDATION (AUTO-DETECT)
==================================================================
Version qui détecte automatiquement le format du fichier AME2020.
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
    for char in ['#', '*', 'x', 'n', 'B-', '--', '.']:
        s = s.replace(char, '')

    if s in ['', '-']:
        return np.nan

    try:
        return float(s)
    except Exception:
        return np.nan


def detect_format(lines):
    """
    Détecte le format du fichier AME2020.
    Retourne: 'ame2020_standard', 'ame2020_mass', 'nubase', 'unknown'
    """
    # Chercher des motifs caractéristiques
    header_line = None
    for i, line in enumerate(lines[:50]):
        line_upper = line.upper()
        if 'A' in line and 'Z' in line and 'N' in line:
            header_line = i
            if 'MASSEXCESS' in line_upper or 'MASS EXCESS' in line_upper:
                return 'ame2020_standard'
            elif 'ATOMICMASS' in line_upper or 'ATOMIC MASS' in line_upper:
                return 'ame2020_mass'
            elif 'NUBASE' in line_upper:
                return 'nubase'
    
    # Compter les colonnes numériques dans les premières lignes de données
    data_lines = [l for l in lines if l.strip() and not l.startswith(('#', 'N-Z', '1,a0'))]
    if data_lines:
        parts = data_lines[0].split(',')
        numeric_cols = sum(1 for p in parts[:10] if p.strip().replace('.', '').replace('-', '').isdigit())
        if numeric_cols >= 6:
            return 'ame2020_standard'
        elif numeric_cols >= 4:
            return 'ame2020_mass'
    
    return 'unknown'


# =============================================================================
# CHARGEMENT AME2020 (FORMATS MULTIPLES)
# =============================================================================

def load_ame2020_standard(csv_path='ame2020.csv'):
    """
    Charge le format standard AME2020 avec N-Z, N, Z, A, Element, MassExcess, etc.
    """
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

            # Ignorer les métadonnées
            skip_patterns = ['N-Z', '1,a0', '0,,,', 'DATE', 'ATOMICMASS']
            if any(line.startswith(p) for p in skip_patterns):
                continue

            parts = line.split(',')
            if len(parts) < 14:
                continue

            # Vérifier que N, Z, A sont numériques (indices 2,3,4)
            try:
                n_val = clean_numeric(parts[2])
                z_val = clean_numeric(parts[3])
                a_val = clean_numeric(parts[4])
                
                if pd.isna(n_val) or pd.isna(z_val) or pd.isna(a_val):
                    continue
                    
                if a_val <= 0 or z_val < 0 or n_val < 0:
                    continue
                    
            except:
                continue

            row = {
                'N_minus_Z': clean_numeric(parts[0]),
                'N': n_val,
                'Z': z_val,
                'A': a_val,
                'Element': parts[5].strip() if len(parts) > 5 else '',
                'Origin': parts[6].strip() if len(parts) > 6 else '',
                'MassExcess_keV': clean_numeric(parts[6]) if len(parts) > 6 else np.nan,
                'Error_MassExcess_keV': clean_numeric(parts[7]) if len(parts) > 7 else np.nan,
                'BindingPerA_keV': clean_numeric(parts[8]) if len(parts) > 8 else np.nan,
                'Error_BindingPerA_keV': clean_numeric(parts[9]) if len(parts) > 9 else np.nan,
                'BetaDecay_keV': clean_numeric(parts[10]) if len(parts) > 10 else np.nan,
                'Error_BetaDecay_keV': clean_numeric(parts[11]) if len(parts) > 11 else np.nan,
                'AtomicMass_u': clean_numeric(parts[12]) if len(parts) > 12 else np.nan,
                'Error_AtomicMass_u': clean_numeric(parts[13]) if len(parts) > 13 else np.nan,
            }
            rows.append(row)

    if not rows:
        raise RuntimeError('Aucune donnée valide trouvée dans format standard AME2020.')

    df = pd.DataFrame(rows)
    return df


def load_ame2020_simple(csv_path='ame2020.csv'):
    """
    Charge un format simplifié avec seulement A, Z, N, masse.
    """
    rows = []

    with open(csv_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            parts = line.split(',')
            
            # Chercher A, Z, N dans les champs
            numeric_vals = []
            for p in parts[:10]:
                try:
                    val = float(p.strip())
                    if 0 < val < 300:
                        numeric_vals.append(val)
                except:
                    pass
            
            if len(numeric_vals) >= 3:
                # Trier: A est le plus grand, Z est le plus petit non nul
                numeric_vals.sort()
                if len(numeric_vals) >= 3:
                    a_val = numeric_vals[-1]  # plus grand
                    n_val = numeric_vals[-2] if len(numeric_vals) >= 2 else None
                    z_val = numeric_vals[0] if numeric_vals[0] > 0 else numeric_vals[1]
                    
                    # Chercher la masse atomique (entre 1 et 300 mais différent de A)
                    mass_val = None
                    for p in parts:
                        try:
                            val = float(p.strip())
                            if 1 < val < 300 and abs(val - a_val) > 0.1:
                                mass_val = val
                                break
                        except:
                            pass
                    
                    if mass_val is None and 'AtomicMass' in line:
                        # Essayer d'extraire la masse
                        mass_match = re.search(r'(\d+\.\d+)', line.split('AtomicMass')[-1])
                        if mass_match:
                            mass_val = float(mass_match.group(1))
                    
                    row = {
                        'A': a_val,
                        'Z': z_val,
                        'N': n_val if n_val else a_val - z_val,
                        'AtomicMass_u': mass_val if mass_val else a_val,
                        'Element': f"Z{int(z_val)}",
                    }
                    rows.append(row)

    if not rows:
        raise RuntimeError('Aucune donnée valide trouvée dans format simple AME2020.')

    df = pd.DataFrame(rows)
    return df


def load_ame2020(csv_path='ame2020.csv'):
    """
    Charge automatiquement le bon format AME2020.
    """
    print(f"🔍 Lecture du fichier: {csv_path}")
    
    # Lire les premières lignes pour détecter le format
    with open(csv_path, 'r', encoding='utf-8') as f:
        lines = [line for line in f.readlines()[:100] if line.strip()]
    
    format_type = detect_format(lines)
    print(f"📋 Format détecté: {format_type}")
    
    # Essayer les différents formats
    df = None
    errors = []
    
    if format_type in ['ame2020_standard', 'unknown']:
        try:
            df = load_ame2020_standard(csv_path)
            print("✅ Chargé en format standard AME2020")
        except Exception as e:
            errors.append(f"standard: {e}")
    
    if df is None or len(df) == 0:
        try:
            df = load_ame2020_simple(csv_path)
            print("✅ Chargé en format simplifié")
        except Exception as e:
            errors.append(f"simple: {e}")
    
    if df is None or len(df) == 0:
        # Dernier recours: utiliser pandas directement
        try:
            df_raw = pd.read_csv(csv_path, skiprows=2)
            # Chercher les colonnes pertinentes
            possible_cols = {
                'A': [c for c in df_raw.columns if c in ['A', 'a', 'mass_number']],
                'Z': [c for c in df_raw.columns if c in ['Z', 'z', 'proton']],
                'N': [c for c in df_raw.columns if c in ['N', 'n', 'neutron']],
                'mass': [c for c in df_raw.columns if 'mass' in c.lower() or 'AtomicMass' in c]
            }
            
            if possible_cols['A'] and possible_cols['mass']:
                a_col = possible_cols['A'][0]
                mass_col = possible_cols['mass'][0]
                df = pd.DataFrame()
                df['A'] = pd.to_numeric(df_raw[a_col], errors='coerce')
                df['AtomicMass_u'] = pd.to_numeric(df_raw[mass_col], errors='coerce')
                
                if possible_cols['Z']:
                    df['Z'] = pd.to_numeric(df_raw[possible_cols['Z'][0]], errors='coerce')
                if possible_cols['N']:
                    df['N'] = pd.to_numeric(df_raw[possible_cols['N'][0]], errors='coerce')
                
                df = df.dropna(subset=['A', 'AtomicMass_u'])
                print("✅ Chargé via pandas avec détection auto")
        except Exception as e:
            errors.append(f"pandas: {e}")
    
    if df is None or len(df) == 0:
        raise RuntimeError(f"Impossible de charger AME2020. Erreurs: {errors}")
    
    # Nettoyer et calculer la masse en MeV
    df = df.dropna(subset=['A', 'AtomicMass_u'])
    df['mass_exp_MeV'] = df['AtomicMass_u'] * U_TO_MEV
    
    # Calculer N et Z si manquants
    if 'Z' not in df.columns or df['Z'].isna().all():
        # Inférer Z depuis A (approximation)
        df['Z'] = df['A'].apply(lambda a: int(round(a / 2.5)) if pd.notna(a) else np.nan)
    
    if 'N' not in df.columns or df['N'].isna().all():
        df['N'] = df['A'] - df['Z']
    
    # Créer identifiant
    if 'Element' not in df.columns:
        df['Element'] = df['Z'].apply(lambda z: f"Z{int(z)}" if pd.notna(z) else "?")
    
    df['particle_id'] = df['Element'].astype(str) + '-' + df['A'].astype(str)
    
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
    exponent_limit = 20

    oct_factors = np.array([
        4.0 ** min(n_base + o, exponent_limit)
        for o in octaves[:n_pent]
    ], dtype=np.float64)

    sqrt_lambdas = np.array([
        np.sqrt(lambda_eigvals[i % 72])
        for i in indices
    ])

    weighted = np.array(signs[:n_pent]) * oct_factors * sqrt_lambdas
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
            lambda r: pentadic_mass(r, Lambda, n_base, lambda_eigvals,
                                   indices_col, octaves_col, signs_col),
            axis=1
        )

        mask = (~preds.isna() & ~train_df['mass_exp_MeV'].isna())
        
        if mask.sum() < 10:
            return 1e12

        return np.sqrt(np.mean((preds[mask] - train_df.loc[mask, 'mass_exp_MeV']) ** 2))

    result = minimize(
        objective,
        x0=[7.7, 4.0],
        method='L-BFGS-B',
        bounds=[(0.001, 1000.0), (0.0, 8.0)]
    )

    return result.x[0], int(round(np.clip(result.x[1], 0, 8)))


# =============================================================================
# SEMF (BETHE-WEIZSÄCKER)
# =============================================================================

def semf_mass(Z, N):
    A = Z + N
    if A <= 0:
        return np.nan

    a_v, a_s, a_c, a_a, a_p = 15.75, 17.8, 0.711, 23.7, 11.18
    
    if A % 2 == 1:
        delta = 0
    elif Z % 2 == 0:
        delta = a_p / np.sqrt(A)
    else:
        delta = -a_p / np.sqrt(A)

    BE = (a_v * A - a_s * A**(2/3) - a_c * Z*(Z-1)/A**(1/3) 
          - a_a * (A-2*Z)**2/A + delta)

    m_p, m_n = 938.27208816, 939.56542052
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
    df_valid = df[df['mass_exp_MeV'].notna() & df['A'].notna() & (df['A'] > 0)].copy()
    
    if len(df_valid) < 20:
        print(f'⚠️ Only {len(df_valid)} valid entries. Need at least 20.')
        return None

    train, test = train_test_split(df_valid, test_size=test_size, random_state=random_state)

    L_opt, n_opt = calibrate(train, lambda_eigvals, indices_col, octaves_col, signs_col)
    print(f'✅ Λ = {L_opt:.4f} MeV | n_base = {n_opt}')

    test['mass_pred_MeV'] = test.apply(
        lambda r: pentadic_mass(r, L_opt, n_opt, lambda_eigvals,
                               indices_col, octaves_col, signs_col),
        axis=1
    )

    valid_mask = (test['mass_pred_MeV'].notna() & test['mass_exp_MeV'].notna())
    n_valid = valid_mask.sum()
    
    if n_valid < 5:
        print(f'⚠️ Pas assez de prédictions valides: {n_valid}')
        return None

    rmse = np.sqrt(mean_squared_error(test.loc[valid_mask, 'mass_exp_MeV'],
                                     test.loc[valid_mask, 'mass_pred_MeV']))
    mae = mean_absolute_error(test.loc[valid_mask, 'mass_exp_MeV'],
                             test.loc[valid_mask, 'mass_pred_MeV'])

    print(f'\n📈 TEST OUT-OF-SAMPLE ({n_valid} nuclei)')
    print(f'RMSE : {rmse:.6f} MeV')
    print(f'MAE  : {mae:.6f} MeV')

    # Comparaison SEMF
    if 'Z' in test.columns and 'N' in test.columns:
        test_valid = test[valid_mask].copy()
        test_valid['mass_semf'] = test_valid.apply(lambda r: semf_mass(r['Z'], r['N']), axis=1)
        semf_mask = test_valid['mass_semf'].notna()
        
        if semf_mask.sum() > 0:
            rmse_semf = np.sqrt(mean_squared_error(test_valid.loc[semf_mask, 'mass_exp_MeV'],
                                                   test_valid.loc[semf_mask, 'mass_semf']))
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
    
    try:
        LAMBDA_72 = np.loadtxt('eigvals_72.txt')
        print(f'✅ Loaded {len(LAMBDA_72)} eigenvalues')
    except FileNotFoundError:
        print('⚠️ eigvals_72.txt not found, using dummy eigenvalues')
        LAMBDA_72 = np.exp(-np.arange(72)/10)

    print('🚀 Loading AME2020...')
    
    try:
        df = load_ame2020('ame2020.csv')
        
        # Générer des configurations pentadiques dummy si nécessaire
        if 'pentad_indices' not in df.columns or df['pentad_indices'].isna().all():
            print('🔧 Generating pentadic configurations...')
            df['pentad_indices'] = df['A'].apply(
                lambda a: [(int(a) + i) % 72 for i in range(5)] if pd.notna(a) else None
            )
            df['pentad_octaves'] = df['A'].apply(
                lambda a: [int(np.log2(a)) % 5 for _ in range(5)] if pd.notna(a) else None
            )
            df['pentad_signs'] = df['A'].apply(
                lambda a: [1 if (int(a) + i) % 2 == 0 else -1 for i in range(5)] if pd.notna(a) else None
            )
            print('✅ Pentadic configurations generated')
        
        results = run_validation(df, LAMBDA_72)
        
        if results is not None:
            results.to_csv('validation_results_80_20.csv', index=False)
            print('\n✅ Results saved to validation_results_80_20.csv')
        else:
            print('\n❌ Validation failed - insufficient data')
            
    except Exception as e:
        print(f'\n❌ Error: {e}')
        print('\n💡 Suggestions:')
        print('1. Vérifiez que ame2020.csv existe dans le répertoire courant')
        print('2. Affichez les premières lignes du fichier: head -20 ame2020.csv')
        print('3. Exécutez le script de diagnostic pour analyser le format')