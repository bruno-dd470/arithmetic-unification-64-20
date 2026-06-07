import pandas as pd
import numpy as np

def enrich_ame2020_with_pentads(csv_in='ame2020.csv', csv_out='ame2020_pentads.csv'):
    # Chargement robuste (ignore les lignes méta)
    def is_data(line):
        s = line.strip()
        return s and not s.startswith(('N-Z', '1,a0', '0,', '0  0', '0  1N-Z')) and s[0].isdigit()

    rows = []
    with open(csv_in, 'r', encoding='utf-8') as f:
        for line in f:
            if not is_data(line): continue
            parts = [p.strip() for p in line.split(',')]
            if len(parts) >= 14:
                try:
                    rows.append({
                        'N': int(parts[2]) if parts[2] else np.nan,
                        'Z': int(parts[3]) if parts[3] else np.nan,
                        'A': int(parts[4]) if parts[4] else np.nan,
                        'El': parts[5],
                        'MassExcess_keV': float(parts[6]) if parts[6] else np.nan,
                        'AtomicMass_u': float(parts[12]) if parts[12] else np.nan
                    })
                except: continue

    df = pd.DataFrame(rows).dropna(subset=['A','Z','N'])
    
    # 1. Attribution des feuilles spectrales (mod 6)
    leaf_Z = df['Z'] % 6
    leaf_N = df['N'] % 6
    
    # 2. Règles de sélection d'indices (base heuristique Λ₇₂)
    def get_indices(row):
        base = (row['Z'] * 7 + row['N'] * 11) % 72
        if row['A'] <= 60:  # Régime triplet Merkabah
            return [base, (base+5)%72, (base+12)%72]
        elif row['A'] <= 200:  # Régime paire/transition
            return [base, (base+18)%72]
        else:  # Régime superlourd (seuil S₇)
            return [(base+36)%72]  # Projection Ke dominante
            
    df['pentad_indices'] = df.apply(get_indices, axis=1)
    
    # 3. Octave relative (échelle de masse)
    df['pentad_octaves'] = df['A'].apply(lambda a: [max(0, int(np.floor(np.log(a/10)/np.log(4))))] * len(get_indices({'A':a, 'Z':1, 'N':1})))
    
    # 4. Signes (polarité Sheng → Ke)
    df['pentad_signs'] = df['A'].apply(lambda a: [1]*(len(get_indices({'A':a, 'Z':1, 'N':1}))-1) + ([-1] if a >= 280 else [1]))
    
    # Formatage pour CSV (listes en string)
    for col in ['pentad_indices','pentad_octaves','pentad_signs']:
        df[col] = df[col].apply(lambda x: str(x).replace(' ', ''))
        
    df.to_csv(csv_out, index=False)
    print(f"✅ {len(df)} isotopes enrichis → {csv_out}")
    return df

# Exécution
enrich_ame2020_with_pentads()
