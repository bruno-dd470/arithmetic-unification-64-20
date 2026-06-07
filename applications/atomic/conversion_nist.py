#!/usr/bin/env python3
# convertir_nist.py

import csv
import re

def clean_nist_value(val):
    """Nettoie les valeurs du format NIST comme '="1"'"""
    if not val or val == '':
        return ''
    val = val.strip()
    if val.startswith('="') and val.endswith('"'):
        val = val[2:-1]
    elif val.startswith('"') and val.endswith('"'):
        val = val[1:-1]
    return val

def extract_number_from_spectrum(sp_name):
    """Extrait le numéro atomique du nom du spectre comme 'Ds CVIII'"""
    # Cherche le symbole chimique dans le dictionnaire
    # Pour l'instant, retourne None si pas trouvé
    return None

input_file = "ionisations_nist.csv"
output_file = "ionisations_simplifie.csv"

converted = 0
errors = 0
lines_ignored = 0

with open(input_file, 'r', encoding='utf-8') as f_in:
    reader = csv.reader(f_in)
    header = next(reader)  # Ignorer l'en-tête
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f_out:
        writer = csv.writer(f_out)
        writer.writerow(['Z', 'k', 'E_eV'])
        
        for line_num, row in enumerate(reader, start=2):
            if not row:
                lines_ignored += 1
                continue
            
            # Vérifier qu'on a assez de colonnes
            if len(row) < 10:
                print(f"Ligne {line_num}: ignorée (seulement {len(row)} colonnes)")
                lines_ignored += 1
                continue
            
            # Nettoyer les valeurs essentielles
            Z_val = clean_nist_value(row[0]) if len(row) > 0 else ''
            k_val = clean_nist_value(row[2]) if len(row) > 2 else ''
            sp_name = clean_nist_value(row[1]) if len(row) > 1 else ''
            E_val = clean_nist_value(row[9]) if len(row) > 9 else ''
            
            # Ignorer les lignes vides essentielles
            if not Z_val or not k_val or not E_val:
                # Pour Ds CVIII, essayer d'extraire k du nom
                if 'CVIII' in sp_name:
                    # CVIII = 108? Non, c'est le degré d'ionisation
                    match = re.search(r'C([IVX]+)', sp_name)
                    if match:
                        roman = match.group(1)
                        # Convertir romain en nombre
                        roman_values = {'I': 1, 'V': 5, 'X': 10}
                        k = 0
                        for c in roman:
                            k += roman_values.get(c, 0)
                        print(f"Ligne {line_num}: extrait k={k} de {sp_name}")
                        k_val = str(k)
                    else:
                        print(f"Ligne {line_num}: valeurs manquantes - Z='{Z_val}', k='{k_val}', E='{E_val}'")
                        errors += 1
                        continue
                else:
                    print(f"Ligne {line_num}: valeurs manquantes - Z='{Z_val}', k='{k_val}', E='{E_val}'")
                    errors += 1
                    continue
            
            # Convertir
            try:
                # Pour Z, gérer les cas comme 'Ds'
                if Z_val.isdigit():
                    Z = int(Z_val)
                else:
                    # Essayer de trouver le numéro atomique pour les symboles chimiques
                    # Dictionnaire simple pour les éléments lourds
                    symbol_to_Z = {
                        'Ds': 110, 'Rg': 111, 'Cn': 112, 'Nh': 113, 'Fl': 114,
                        'Mc': 115, 'Lv': 116, 'Ts': 117, 'Og': 118
                    }
                    Z = symbol_to_Z.get(Z_val, None)
                    if Z is None:
                        print(f"Ligne {line_num}: Z inconnu '{Z_val}'")
                        errors += 1
                        continue
                
                # Pour k, gérer les charges positives comme '+107'
                if k_val.startswith('+'):
                    k = int(k_val[1:])
                else:
                    k = int(float(k_val)) if k_val else 0
                
                E = float(E_val)
                
                # Vérifier que c'est une énergie positive et raisonnable
                if 0 < E < 1000000:  # Max 1 MeV
                    writer.writerow([Z, k, E])
                    converted += 1
                    if converted % 100 == 0:
                        print(f"Converti: {converted} lignes...")
                else:
                    print(f"Ligne {line_num}: énergie invalide E={E} eV")
                    errors += 1
                    
            except (ValueError, TypeError) as e:
                print(f"Ligne {line_num}: erreur conversion - {e}")
                print(f"  Z='{Z_val}', k='{k_val}', E='{E_val}'")
                errors += 1
                continue

print(f"\n{'='*50}")
print(f"Conversion terminée!")
print(f"✓ Lignes converties: {converted}")
print(f"✗ Erreurs: {errors}")
print(f"ℹ Lignes ignorées: {lines_ignored}")
print(f"📁 Fichier créé: {output_file}")
print(f"\nVous pouvez maintenant utiliser:")
print(f"python ionisations_successives.py {output_file}")