import csv
import re

def parse_ame2020_corrected(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 🔍 Trouver la ligne contenant "0  1    1    0    1  n" (neutron)
    start = None
    for i, line in enumerate(lines):
        if '0  1    1    0    1  n' in line:
            start = i
            break

    if start is None:
        raise ValueError("Ligne de données introuvable")

    data_lines = []
    for line in lines[start:]:
        if len(line) >= 130 and line[0] in '0123456789-':
            data_lines.append(line)

    records = []

    for line in data_lines:
        # Positions exactes (0-indexé) d'après le format Fortran
        nz = line[1:4].strip()
        n = line[4:9].strip()
        z = line[9:14].strip()
        a = line[14:19].strip()
        el = line[20:23].strip()
        origin = line[23:27].strip()

        mass_exc = line[28:42].strip().replace(' ', '')
        err_mass = line[42:54].strip().replace(' ', '')
        bind_a = line[54:69].strip().replace(' ', '')
        err_bind = line[69:80].strip().replace(' ', '')
        beta_type = line[81:83].strip()
        beta_val = line[83:96].strip().replace(' ', '')
        err_beta = line[96:107].strip().replace(' ', '')

        mass_u_part1 = line[108:111].strip()
        mass_u_part2 = line[112:125].strip().replace(' ', '')
        err_mass_u = line[125:137].strip().replace(' ', '')

        # Reconstruction de la masse atomique
        if mass_u_part1 and mass_u_part2:
            mass_u = f"{mass_u_part1}{mass_u_part2}"
        else:
            mass_u = mass_u_part2

        # Reconstruction de la valeur Beta
        if beta_val == '*' or beta_val == '':
            beta_decay = beta_type
        else:
            beta_decay = f"{beta_type}{beta_val}"

        # Nettoyage des retours à la ligne résiduels
        for f in ['mass_exc', 'err_mass', 'bind_a', 'err_bind', 
                  'beta_decay', 'err_beta', 'mass_u', 'err_mass_u']:
            locals()[f] = locals()[f].replace('\n', '').replace('\r', '')

        records.append([
            nz, n, z, a, el, origin,
            mass_exc, err_mass,
            bind_a, err_bind,
            beta_decay, err_beta,
            mass_u, err_mass_u
        ])

    # 🔁 Correction post-traitement
    for row in records:
        # Supprimer les restes mal placés de 'B' dans l'erreur du binding
        if row[9].endswith('B'):
            row[9] = row[9][:-1]
        if row[10] == 'B':
            row[10] = 'B-*'

    # ✍️ Écriture du CSV final
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'N-Z', 'N', 'Z', 'A', 'El', 'Origin',
            'MassExcess_keV', 'Error_keV',
            'BindingPerA_keV', 'Error_BindingPerA_keV',
            'BetaDecay_keV', 'Error_BetaDecay_keV',
            'AtomicMass_u', 'Error_AtomicMass_u'
        ])
        writer.writerows(records)

    print(f"✅ {len(records)} lignes exportées dans {output_file}")

# Exécution
parse_ame2020_corrected('mass.mas20.txt', 'ame2020_VERIFIED.csv')