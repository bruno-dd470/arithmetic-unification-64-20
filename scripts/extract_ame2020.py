"""
PENTADIC MASS MODEL: 80/20 OUT-OF-SAMPLE VALIDATION
=====================================================
Format: AME2020 Atomic Mass Evaluation standard columns
Columns: N-Z, N, Z, A, El, Orig, MassExcess_keV, Error_keV, 
         BindingPerA_keV, Error_BindingPerA_keV, 
         BetaDecay_keV, Error_BetaDecay_keV, 
         AtomicMass_u, Error_AtomicMass_u

This script validates the pentadic mass formula on unseen data.
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
from scipy.optimize import minimize

# =============================================================================
# CONSTANTS
# =============================================================================
U_TO_MEV = 931.49410242  # 1 atomic mass unit in MeV/c² (CODATA 2018)

# =============================================================================
# 1. DATA LOADER: AME2020 FORMAT
# =============================================================================
def load_ame2020(csv_path='ame2020.csv'):
    """
    Load AME2020 atomic mass evaluation file.
    
    Expected columns:
    N-Z, N, Z, A, El, Orig, MassExcess_keV, Error_keV, 
    BindingPerA_keV, Error_BindingPerA_keV, 
    BetaDecay_keV, Error_BetaDecay_keV, 
    AtomicMass_u, Error_AtomicMass_u
    """
    # Skip metadata lines (starting with '1,a0' or '0,')
    def is_data_line(line):
        stripped = line.strip()
        if not stripped: return False
        if stripped.startswith('1,a0') or stripped.startswith('0,'): return False
        # Data lines start with space+digit or digit+space
        return stripped[0].isdigit() or (len(stripped) > 1 and stripped[1].isdigit())
    
    # Read file, filtering metadata
    with open(csv_path, 'r') as f:
        lines = [line for line in f if is_data_line(line)]
    
    # Define column names for AME2020
    columns = [
        'N_minus_Z', 'N', 'Z', 'A', 'Element', 'Origin',
        'MassExcess_keV', 'Error_MassExcess_keV',
        'BindingPerA_keV', 'Error_BindingPerA_keV',
        'BetaDecay_keV', 'Error_BetaDecay_keV',
        'AtomicMass_u', 'Error_AtomicMass_u'
    ]
    
    # Parse data
    data = []
    for line in lines:
        parts = line.strip().split(',')
        if len(parts) >= 14:
            try:
                row = {
                    'N_minus_Z': int(parts[0].strip()) if parts[0].strip() else None,
                    'N': int(parts[1].strip()) if parts[1].strip() else None,
                    'Z': int(parts[2].strip()) if parts[2].strip() else None,
                    'A': int(parts[3].strip()) if parts[3].strip() else None,
                    'Element': parts[4].strip(),
                    'Origin': parts[5].strip(),
                    'MassExcess_keV': float(parts[6].strip()) if parts[6].strip() else np.nan,
                    'Error_MassExcess_keV': float(parts[7].strip()) if parts[7].strip() else np.nan,
                    'BindingPerA_keV': float(parts[8].strip()) if parts[8].strip() else np.nan,
                    'Error_BindingPerA_keV': float(parts[9].strip()) if parts[9].strip() else np.nan,
                    'BetaDecay_keV': float(parts[10].strip()) if parts[10].strip() else np.nan,
                    'Error_BetaDecay_keV': float(parts[11].strip()) if parts[11].strip() else np.nan,
                    'AtomicMass_u': float(parts[12].strip()) if parts[12].strip() else np.nan,
                    'Error_AtomicMass_u': float(parts[13].strip()) if parts[13].strip() else np.nan,
                }
                data.append(row)
            except (ValueError, IndexError):
                continue
    
    df = pd.DataFrame(data)
    
    # Convert atomic mass to MeV
    df['mass_exp_MeV'] = df['AtomicMass_u'] * U_TO_MEV
    
    # Add particle identifier
    df['particle_id'] = df['Element'].astype(str) + '-' + df['A'].astype(str)
    
    print(f"✅ Loaded {len(df)} entries from {csv_path}")
    return df

# =============================================================================
# 2. PENTADIC MASS FUNCTION (simplified for validation)
# =============================================================================
def pentadic_mass(row, Lambda_fund, n_base, lambda_eigvals, indices_col='pentad_indices', 
                   octaves_col='pentad_octaves', signs_col='pentad_signs'):
    """
    Compute pentadic mass for a single nucleus.
    
    Parameters:
    - row: DataFrame row with pentadic configuration columns
    - Lambda_fund: fundamental scale (MeV)
    - n_base: base octave (integer)
    - lambda_eigvals: array of 72 eigenvalues from G72
    - indices_col, octaves_col, signs_col: column names for pentadic config
    """
    # Parse pentadic configuration from row
    try:
        indices = eval(row[indices_col]) if isinstance(row[indices_col], str) else row[indices_col]
        octaves = eval(row[octaves_col]) if isinstance(row[octaves_col], str) else row[octaves_col]
        signs = eval(row[signs_col]) if isinstance(row[signs_col], str) else row[signs_col]
    except:
        return np.nan  # Skip if configuration invalid
    
    n_pent = len(indices)
    if n_pent == 0:
        return np.nan
    
    # Octave scaling: 4^(n_base + n_rel)
    oct_factors = np.array([4**(n_base + o) for o in octaves[:n_pent]])
    
    # Spectral weights from Lambda72 eigenvalues
    sqrt_lambdas = np.array([np.sqrt(lambda_eigvals[i % 72]) for i in indices])
    
    # Combine with signs and normalize
    weighted = np.array(signs[:n_pent]) * oct_factors * sqrt_lambdas
    norm = np.linalg.norm(weighted) / np.sqrt(10)  # 10D latent space normalization
    
    return Lambda_fund * norm

# =============================================================================
# 3. CALIBRATION ON TRAINING SET
# =============================================================================
def calibrate(train_df, lambda_eigvals, indices_col='pentad_indices', 
              octaves_col='pentad_octaves', signs_col='pentad_signs'):
    """
    Calibrate Lambda_fund and n_base on training set only.
    """
    def objective(params):
        Lambda, n_base_float = params
        n_base = int(round(np.clip(n_base_float, 0, 8)))
        
        preds = train_df.apply(
            lambda r: pentadic_mass(r, Lambda, n_base, lambda_eigvals, 
                                   indices_col, octaves_col, signs_col), 
            axis=1
        )
        # Filter valid predictions
        mask = ~preds.isna() & ~train_df['mass_exp_MeV'].isna()
        if mask.sum() < 10:
            return 1e10  # Penalize insufficient data
        return np.sqrt(np.mean((preds[mask] - train_df.loc[mask, 'mass_exp_MeV'])**2))
    
    # Initial guess: Lambda ~7.7 MeV, n_base ~4
    res = minimize(objective, x0=[7.7, 4.0], method='Nelder-Mead',
                   bounds=[(1.0, 20.0), (0.0, 8.0)])
    
    return res.x[0], int(round(res.x[1]))

# =============================================================================
# 4. BASELINE: SEMF (BETHE-WEIZSÄCKER)
# =============================================================================
def semf_mass(Z, N):
    """Semi-empirical mass formula (Bethe-Weizsäcker) in MeV."""
    A = Z + N
    if A == 0: return np.nan
    
    # Coefficients (MeV)
    a_v, a_s, a_c, a_a, a_p = 15.75, 17.8, 0.711, 23.7, 11.18
    
    # Pairing term
    if A % 2 == 1:
        delta = 0
    elif Z % 2 == 0:
        delta = a_p / np.sqrt(A)
    else:
        delta = -a_p / np.sqrt(A)
    
    # Binding energy
    BE = (a_v * A - a_s * A**(2/3) - a_c * Z*(Z-1)/A**(1/3) 
          - a_a * (A - 2*Z)**2 / A + delta)
    
    # Atomic mass = Z*m_p + N*m_n - BE
    m_p, m_n = 938.27208816, 939.56542052  # MeV/c²
    return Z * m_p + N * m_n - BE

# =============================================================================
# 5. VALIDATION PIPELINE
# =============================================================================
def run_validation(df, lambda_eigvals, indices_col='pentad_indices', 
                   octaves_col='pentad_octaves', signs_col='pentad_signs',
                   test_size=0.2, random_state=42):
    """
    Run 80/20 out-of-sample validation.
    """
    # Filter rows with valid mass and pentadic config
    df_valid = df[
        df['mass_exp_MeV'].notna() & 
        df[indices_col].notna() &
        df[octaves_col].notna() &
        df[signs_col].notna()
    ].copy()
    
    if len(df_valid) < 50:
        print(f"⚠️ Only {len(df_valid)} valid entries; validation may be unreliable")
    
    # 80/20 split
    train, test = train_test_split(
        df_valid, test_size=test_size, random_state=random_state, stratify=None
    )
    print(f"\n📊 Split: {len(train)} Train | {len(test)} Test")
    
    # Calibrate ONLY on training set
    L_opt, n_opt = calibrate(train, lambda_eigvals, indices_col, octaves_col, signs_col)
    print(f"✅ Calibrated on Train: Λ_fund = {L_opt:.3f} MeV, n_base = {n_opt}")
    
    # Predict on Test
    test['mass_pred_MeV'] = test.apply(
        lambda r: pentadic_mass(r, L_opt, n_opt, lambda_eigvals, 
                               indices_col, octaves_col, signs_col), 
        axis=1
    )
    
    # Filter valid predictions for metrics
    valid_mask = test['mass_pred_MeV'].notna() & test['mass_exp_MeV'].notna()
    if valid_mask.sum() < 10:
        print("⚠️ Too few valid predictions for reliable metrics")
        return None
    
    # Compute metrics
    rmse = np.sqrt(mean_squared_error(
        test.loc[valid_mask, 'mass_exp_MeV'], 
        test.loc[valid_mask, 'mass_pred_MeV']
    ))
    mae = mean_absolute_error(
        test.loc[valid_mask, 'mass_exp_MeV'], 
        test.loc[valid_mask, 'mass_pred_MeV']
    )
    rel_err = (mae / test.loc[valid_mask, 'mass_exp_MeV'].mean()) * 100
    max_err = np.max(np.abs(
        test.loc[valid_mask, 'mass_exp_MeV'] - 
        test.loc[valid_mask, 'mass_pred_MeV']
    ))
    
    print("\n📈 OUT-OF-SAMPLE TEST RESULTS (20% UNSEEN)")
    print(f"   RMSE      : {rmse:.4f} MeV")
    print(f"   MAE       : {mae:.4f} MeV ({rel_err:.4f}%)")
    print(f"   Max Error : {max_err:.4f} MeV")
    print(f"   Valid predictions: {valid_mask.sum()}/{len(test)}")
    
    # SEMF baseline comparison
    if 'Z' in test.columns and 'N' in test.columns:
        test_semf = test[valid_mask].copy()
        test_semf['mass_semf'] = semf_mass(test_semf['Z'], test_semf['N'])
        rmse_semf = np.sqrt(mean_squared_error(
            test_semf['mass_exp_MeV'], test_semf['mass_semf']
        ))
        gain = (1 - rmse/rmse_semf) * 100 if rmse_semf > 0 else 0
        print(f"\n🔍 BASELINE COMPARISON (SEMF)")
        print(f"   SEMF RMSE : {rmse_semf:.4f} MeV")
        print(f"   Pentadic improvement: {gain:+.1f}%")
    
    return test

# =============================================================================
# 6. MAIN EXECUTION
# =============================================================================
if __name__ == "__main__":
    # Eigenvalues from Nebe Λ72 Gram matrix diagonalization
    # (first 18 shown; full 72 should be loaded from file)
    LAMBDA_72 = np.array([
        0.0043740973516556257583, 0.0043740973516556258844,
        0.010995546215077851813, 0.010995546215077851848,
        0.011197776487850081092, 0.018306563103388413523,
        0.018306563103388413687, 0.029576322793137380691,
        0.037359874463993147761, 0.037359874463993147996,
        0.047227060779061605995, 0.063356180109664584017,
        0.063356180109664584215, 0.079378841213435711453,
        0.079378841213435712007, 0.095442748560291922283,
        0.11732778393430706981, 0.11732778393430706997,
        # ... load full 72 from eigvals_72.txt
    ])
    
    # If full eigenvalues file exists, load it
    try:
        LAMBDA_72 = np.loadtxt('eigvals_72.txt')
        print(f"✅ Loaded {len(LAMBDA_72)} eigenvalues from eigvals_72.txt")
    except FileNotFoundError:
        print("⚠️ Using partial eigenvalues; please provide eigvals_72.txt")
    
    print("🚀 Starting 80/20 Out-of-Sample Validation...")
    
    # Load AME2020 data
    df = load_ame2020('ame2020.csv')
    
    # Check if pentadic configuration columns exist
    config_cols = ['pentad_indices', 'pentad_octaves', 'pentad_signs']
    if not all(col in df.columns for col in config_cols):
        print(f"⚠️ Pentadic configuration columns {config_cols} not found.")
        print("   Please add them to your CSV or use a separate config file.")
        # For demo: add dummy configs (NOT for real validation!)
        df['pentad_indices'] = df['A'].apply(lambda a: [a % 72] if pd.notna(a) else None)
        df['pentad_octaves'] = df['A'].apply(lambda a: [0] if pd.notna(a) else None)
        df['pentad_signs'] = df['A'].apply(lambda a: [1] if pd.notna(a) else None)
        print("   Added dummy configurations for testing only!")
    
    # Run validation
    results = run_validation(df, LAMBDA_72)
    
    if results is not None:
        results.to_csv('validation_results_80_20.csv', index=False)
        print("\n✅ Done. Full test predictions saved to 'validation_results_80_20.csv'")
