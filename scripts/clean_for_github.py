
#!/usr/bin/env python3
"""
Script de nettoyage automatique pour préparer un dépôt GitHub propre
à partir d'un répertoire de travail contenant de nombreux fichiers temporaires.
"""

import os
import shutil
import sys
from pathlib import Path
from datetime import datetime
import json

# ============================================================
# CONFIGURATION - À MODIFIER SELON VOS BESOINS
# ============================================================

SOURCE_DIR = Path("/home/bruno_dd/Téléchargements/isotopes_ionisation_L72")
TARGET_DIR = Path("/home/bruno_dd/Desktop/mass_unification_L72_clean")

# Fichiers et dossiers à EXCLURE systématiquement
EXCLUDE_PATTERNS = [
    # Temporaires et vérouillages
    ".*.swp", ".*.swo", ".*~", "*.bak", ".*.lock*", ".~lock.*",
    
    # Anciennes versions et trash
    "Trash/", "archive/", "*_old*", "*_bak*", "*_copy*", "*copie*",
    
    # Fichiers binaires lourds (optionnels - ajuster)
    "*.ods", "*.xlsx",
    "*.pdf",
    
    # Doublons évidents
    "*_FINAL_*.csv", "*_FINAL.csv", "*_FINAL_CORRECT*.csv",
    "*_VERIFIED.csv", "*_CLEAN*.csv", "*_CORRECT*.csv", "*_PROPER*.csv",
    "*_fixed.csv", "*_corrected.csv",
    
    # Fichiers de debug / tests non finis
    "test_*.py", "*_test.py", "*_bof*", "*_fracassant*",
    "mémo_*.md", "memo_*.md", "*_novice.md",
    
    # Générés à l'exécution (reproductibles)
    "*.png", "*.jpg", "*.pdf",
    "*.pyc", "__pycache__/",
    
    # Résultats intermédiaires
    "temp_*", "tmp_*", "*_temp.*",
    
    # Fichiers de configuration personnels
    ".DS_Store", "Thumbs.db",
]

# Fichiers à GARDER ABSOLUMENT
KEEP_PATTERNS = [
    "mass_unification_EN.pdf",
    "mass_unification_FR.pdf",
    "mass_unification_EN.md",
    "references.bib",
    "mass.mas20.txt",
    "ionisations_nist.csv",
    "ame2020_VERIFIED.csv",
    "ionisations_simplifie.csv",
    "beta_precise_results.csv",
    "beta_constants.csv",
    "optimized_parameters.txt",
    "isotope_fits_full.txt",
    "isotope_fits.csv",
    "resultats_ionisations.csv",
    "predictions_superheavy.csv",
    "racines_lambda72.json",
    "48_racines_dans_15_beta.csv",
    "isotopes4.py",
    "ionisations_successives3.py",
    "train_ternary_nn.py",
    "randomization_test.py",
    "cross_validation_final.py",
]

# Dossiers à garder
KEEP_DIRS = [
    "article/",
    "IA_autres/",
]

# ============================================================
# FONCTIONS
# ============================================================

def should_exclude(path: Path) -> bool:
    """Détermine si un fichier/dossier doit être exclu."""
    rel_path = str(path)
    name = path.name
    
    for pattern in EXCLUDE_PATTERNS:
        if pattern.endswith('/'):
            if pattern in rel_path:
                return True
        else:
            if pattern in name or pattern[1:] in name:
                return True
    
    if path.is_file() and path.stat().st_size == 0:
        return True
    
    return False

def should_keep(path: Path) -> bool:
    """Vérifie si un fichier est explicitement marqué comme à garder."""
    name = path.name
    for pattern in KEEP_PATTERNS:
        if pattern is None:
            continue
        if pattern in name:
            return True
    return False

def is_script(path: Path) -> bool:
    """Détecte les scripts Python."""
    return path.suffix == '.py'

def clean_script(content: str) -> str:
    """Nettoie un script (enlève les prints de debug)."""
    lines = content.split('\n')
    cleaned = []
    for line in lines:
            continue
            continue
        cleaned.append(line)
    return '\n'.join(cleaned)

def copy_clean(source: Path, target: Path):
    """Copie un fichier proprement."""
    target.parent.mkdir(parents=True, exist_ok=True)
    
    if source.suffix == '.py':
        with open(source, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        cleaned = clean_script(content)
        with open(target, 'w', encoding='utf-8') as f:
            f.write(cleaned)
        print(f"  ✓ Script nettoyé : {source.name}")
    else:
        shutil.copy2(source, target)
        print(f"  ✓ Copié : {source.name}")

def analyze_directory(root: Path) -> dict:
    """Analyse le répertoire et retourne les fichiers à garder."""
    to_keep = []
    to_ignore = []
    
    for path in root.rglob('*'):
        if path.is_dir():
            continue
        
        rel = path.relative_to(root)
        
        if should_exclude(path):
            to_ignore.append(str(rel))
            continue
        
        if should_keep(path):
            to_keep.append(path)
            continue
        
        if is_script(path):
            name = path.name
            if any(x in name for x in ['final', 'FINAL', 'clean', 'proper', 'v2', '3', '4']):
                to_keep.append(path)
            elif any(x in name for x in ['test', 'debug', 'temp', 'old']):
                to_ignore.append(str(rel))
            else:
                to_keep.append(path)
                print(f"  ⚠ Script non catégorisé : {rel}")
        elif path.suffix in ['.csv', '.txt', '.json', '.md']:
            if any(x in path.name for x in ['clean', 'final', 'verified', 'simplifie', 'full']):
                to_keep.append(path)
            elif 'raw' not in str(rel).lower():
                to_keep.append(path)
        else:
            to_ignore.append(str(rel))
    
    return {'keep': to_keep, 'ignore': to_ignore}

def generate_report(analysis: dict, target_dir: Path):
    """Génère un rapport des actions effectuées."""
    report_path = target_dir.parent / "clean_report.json"
    report = {
        'timestamp': datetime.now().isoformat(),
        'source': str(SOURCE_DIR),
        'target': str(target_dir),
        'files_kept': [str(p.relative_to(SOURCE_DIR)) for p in analysis['keep']],
        'files_ignored': analysis['ignore'],
    }
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"\n📄 Rapport généré : {report_path}")

def create_gitignore(target_dir: Path):
    """Crée un .gitignore basique."""
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*.so
.Python

# OS
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/

# Temporary
*.tmp
*.temp
"""
    with open(target_dir / '.gitignore', 'w') as f:
        f.write(gitignore_content)
    print("  ✓ .gitignore créé")

def create_readme(target_dir: Path):
    """Crée un README.md basique si absent."""
    readme_path = target_dir / 'README.md'
    if not readme_path.exists():
        content = """# Mass Unification via Exceptional Lattice Λ72

## Overview
This repository contains the cleaned data and scripts for the paper  
*"Arithmetic unification of masses and energies..."* (De Dominicis, 2026).

## Structure
- `data/` - Experimental data (AME2020, NIST)
- `scripts/` - Python scripts for fitting and analysis
- `results/` - Output tables and predictions
- `article/` - Final paper (PDF)

## Quick start
```bash
pip install numpy pandas matplotlib scikit-learn
python scripts/fit_isotopes.py
```

## License
[Specify license]
"""
        with open(readme_path, 'w') as f:
            f.write(content)
        print("  ✓ README.md créé")

# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 60)
    print("🧹 Nettoyage automatique pour GitHub")
    print("=" * 60)
    
    if not SOURCE_DIR.exists():
        print(f"❌ Répertoire source introuvable : {SOURCE_DIR}")
        sys.exit(1)
    
    print(f"📁 Source : {SOURCE_DIR}")
    print(f"📁 Cible  : {TARGET_DIR}")
    print()
    
    if TARGET_DIR.exists():
        response = input(f"⚠ Le répertoire {TARGET_DIR} existe déjà. L'écraser ? (o/N) ")
        if response.lower() != 'o':
            print("Abandon.")
            sys.exit(0)
        shutil.rmtree(TARGET_DIR)
    
    TARGET_DIR.mkdir(parents=True)
    
    print("🔍 Analyse du répertoire source...")
    analysis = analyze_directory(SOURCE_DIR)
    
    print(f"\n📊 Fichiers à garder : {len(analysis['keep'])}")
    print(f"📊 Fichiers ignorés  : {len(analysis['ignore'])}")
    
    print("\n📦 Copie des fichiers...")
    for src_path in analysis['keep']:
        rel = src_path.relative_to(SOURCE_DIR)
        dst_path = TARGET_DIR / rel
        copy_clean(src_path, dst_path)
    
    print("\n📝 Création des fichiers de configuration...")
    create_gitignore(TARGET_DIR)
    create_readme(TARGET_DIR)
    
    generate_report(analysis, TARGET_DIR)
    
    print("\n" + "=" * 60)
    print("✅ Nettoyage terminé !")
    print("=" * 60)
    print(f"\n📁 Dépôt propre : {TARGET_DIR}")
    print("\nProchaines étapes :")
    print(f"  cd {TARGET_DIR}")
    print("  git init")
    print("  git add .")
    print('  git commit -m "Initial clean version"')
    print("  git remote add origin <votre-repo-github>")
    print("  git push -u origin main")

if __name__ == "__main__":
    main()




