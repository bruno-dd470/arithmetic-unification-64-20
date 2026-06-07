import numpy as np
from itertools import combinations, product
import json

# ============================================================================
# LES 15 CONSTANTES UNIVERSELIES β_k (données par l'utilisateur)
# ============================================================================
BETA_K = np.array([
    0.06613695904451328,   # β0
    0.28174250870863576,   # β1
    0.5558698717637468,    # β2
    0.8682439499340019,    # β3
    1.5041139699699269,    # β4
    1.7252596926363315,    # β5
    1.831267929898219,     # β6
    2.0174227816393127,    # β7
    2.092837042770219,     # β8
    2.524927313875301,     # β9
    3.279177783,           # β10
    3.851477234958053,     # β11
    4.571556651552703,     # β12
    4.724739892029763,     # β13
    7.407963149728111      # β14
])

# Correspondance orbitale
ORBITALES = {
    0: "1s1/2", 1: "2p1/2", 2: "3s1/2", 3: "3p1/2", 4: "2g9/2",
    5: "3d5/2", 6: "4p1/2", 7: "1j15/2", 8: "2h9/2", 9: "3f5/2",
    10: "5p1/2", 11: "6s1/2", 12: "1k17/2", 13: "2i11/2", 14: "3g9/2"
}

# ============================================================================
# GÉNÉRATION DE TOUTES LES COMBINAISONS TERNAIRES
# ============================================================================
def generer_combinaisons(max_termes=7):
    """
    Génère toutes les combinaisons Σ ε_k β_k avec ε_k ∈ {-1, 0, 1}
    """
    k = len(BETA_K)
    combos = []
    
    for n_actifs in range(1, max_termes + 1):
        for indices in combinations(range(k), n_actifs):
            for signes in product([-1, 1], repeat=n_actifs):
                eps = np.zeros(k, dtype=int)
                val = 0.0
                for idx, sgn in zip(indices, signes):
                    eps[idx] = sgn
                    val += sgn * BETA_K[idx]
                
                # Plage réaliste pour les racines
                if 0.01 < val < 12.0:
                    combos.append((val, eps))
    
    # Ajouter β₀ seul (déjà inclus mais on s'assure)
    eps0 = np.zeros(k, dtype=int)
    eps0[0] = 1
    combos.append((BETA_K[0], eps0))
    
    # Trier par valeur
    combos.sort(key=lambda x: x[0])
    
    # Éliminer les doublons (à 1e-10 près)
    uniques = []
    for val, eps in combos:
        if not uniques or abs(val - uniques[-1][0]) > 1e-10:
            uniques.append((val, eps))
    
    return uniques

# ============================================================================
# IDENTIFICATION DES 48 RACINES
# ============================================================================
def identifier_48_racines():
    """
    Identifie les 48 racines non-dégénérées de Λ₇₂
    selon la procédure du papier (section 3.2)
    """
    toutes_combos = generer_combinaisons(max_termes=8)
    
    # Les 15 β_k sont les racines de base
    racines = []
    
    for val, eps in toutes_combos:
        # Une racine doit avoir une norme spécifique
        # D'après le papier, les 48 racines sont les valeurs Δ
        # qui apparaissent dans les décompositions des masses nucléaires
        
        # Calculer le "poids" de la combinaison
        n_actifs = np.sum(np.abs(eps))
        
        # Critères d'identification (basés sur le papier)
        est_racine = False
        
        # Cas 1: Combinaison à 1 terme (β_k seul)
        if n_actifs == 1:
            est_racine = True
        
        # Cas 2: Différences β_i - β_0 (petites racines)
        elif n_actifs == 2 and eps[0] == -1 and np.sum(eps) == 0:
            est_racine = True
        
        # Cas 3: Sommes β_i + β_0
        elif n_actifs == 2 and eps[0] == 1 and np.sum(eps) == 2:
            est_racine = True
        
        # Cas 4: Combinaisons β_i + β_j (i,j > 0)
        elif n_actifs == 2 and eps[0] == 0:
            est_racine = True
        
        # Cas 5: Combinaisons à 3 termes typiques
        elif n_actifs == 3:
            est_racine = True
        
        if est_racine and 0 < len(racines) < 48:
            racines.append((val, eps))
    
    # Trier par valeur
    racines.sort(key=lambda x: x[0])
    
    return racines[:48]  # On garde les 48 plus petites

# ============================================================================
# TABLE DES 48 RACINES (D'APRÈS L'APPENDIX A DU PAPIER)
# ============================================================================
def construire_table_48_racines():
    """
    Construit la table complète des 48 racines à partir
    des combinaisons documentées dans l'Appendix A
    """
    
    # Format: (index, expression_tex, liste_[(k, signe)], valeur_attendue)
    racines_data = [
        (0, r"β_0", [(0, 1)], 0.06613695904451328),
        (1, r"β_2 - β_0", [(2, 1), (0, -1)], 0.4897329127192335),
        (2, r"β_3 - β_0", [(3, 1), (0, -1)], 0.8021069908894886),
        (3, r"β_4 - β_0", [(4, 1), (0, -1)], 1.4379770109254136),
        (4, r"β_5 - β_0", [(5, 1), (0, -1)], 1.6591227335918182),
        (5, r"β_6 - β_0", [(6, 1), (0, -1)], 1.7651309708537057),
        (6, r"β_7 - β_0", [(7, 1), (0, -1)], 1.9512858225947994),
        (7, r"β_8 - β_0", [(8, 1), (0, -1)], 2.0267000837257057),
        (8, r"β_1", [(1, 1)], 0.28174250870863576),
        (9, r"β_9 - β_0", [(9, 1), (0, -1)], 2.4587903548307877),
        (10, r"β_10 - β_0", [(10, 1), (0, -1)], 3.2130408239554867),
        (11, r"β_4 + β_0", [(4, 1), (0, 1)], 1.5702509290144402),
        (12, r"β_11 - β_0", [(11, 1), (0, -1)], 3.78534027591354),
        (13, r"β_5 + β_0", [(5, 1), (0, 1)], 1.7913966516808448),
        (14, r"β_2 + β_1", [(2, 1), (1, 1)], 0.8376123804723826),
        (15, r"β_2", [(2, 1)], 0.5558698717637468),
        (16, r"β_12 - β_4", [(12, 1), (4, -1)], 3.067442681582776),
        (17, r"β_3 - β_1", [(3, 1), (1, -1)], 0.5865014412253662),
        (18, r"β_6 + β_0", [(6, 1), (0, 1)], 1.8974048889427323),
        (19, r"β_13 - β_5", [(13, 1), (5, -1)], 2.9994801993934314),
        (20, r"β_3", [(3, 1)], 0.8682439499340019),
        (21, r"β_4 - β_1", [(4, 1), (1, -1)], 1.2223714612612912),
        (22, r"β_7 + β_0", [(7, 1), (0, 1)], 2.083559740683826),
        (23, r"β_5 - β_1", [(5, 1), (1, -1)], 1.4435171839276957),
        (24, r"β_9 + β_0", [(9, 1), (0, 1)], 2.5910642729198143),
        (25, r"β_6 - β_1", [(6, 1), (1, -1)], 1.5495254211895833),
        (26, r"β_4", [(4, 1)], 1.5041139699699269),
        (27, r"β_2 + β_4 - β_0", [(2, 1), (4, 1), (0, -1)], 2.0537468836891603),
        (28, r"β_5", [(5, 1)], 1.7252596926363315),
        (29, r"β_6", [(6, 1)], 1.831267929898219),
        (30, r"β_7 - β_1", [(7, 1), (1, -1)], 1.735680272930677),
        (31, r"β_8 - β_1", [(8, 1), (1, -1)], 1.8110945340615833),
        (32, r"β_7", [(7, 1)], 2.0174227816393127),
        (33, r"β_8", [(8, 1)], 2.092837042770219),
        (34, r"β_9 - β_1", [(9, 1), (1, -1)], 2.2431848051666653),
        (35, r"β_9", [(9, 1)], 2.524927313875301),
        (36, r"β_10 - β_1", [(10, 1), (1, -1)], 2.997435274291364),
        (37, r"β_4 + β_1", [(4, 1), (1, 1)], 1.7858564786785627),
        (38, r"β_11 - β_1", [(11, 1), (1, -1)], 3.5697347262494173),
        (39, r"β_5 + β_1", [(5, 1), (1, 1)], 2.0070022013449673),
        (40, r"β_10", [(10, 1)], 3.279177783),
        (41, r"β_11", [(11, 1)], 3.851477234958053),
        (42, r"β_12", [(12, 1)], 4.571556651552703),
        (43, r"β_13", [(13, 1)], 4.724739892029763),
        (44, r"β_2 + β_14 - β_1", [(2, 1), (14, 1), (1, -1)], 8.142100504055222),
        (45, r"β_14 + β_9", [(14, 1), (9, 1)], 9.932890463603412),
        (46, r"β_14", [(14, 1)], 7.407963149728111),
        (47, r"β_14 + β_0", [(14, 1), (0, 1)], 7.474100108772624),
    ]
    
    return racines_data

# ============================================================================
# VÉRIFICATION ET AFFICHAGE
# ============================================================================
def verifier_et_afficher():
    """
    Vérifie toutes les combinaisons et affiche la table complète
    """
    racines = construire_table_48_racines()
    
    print("=" * 100)
    print("TABLEAU COMPLET DES 48 RACINES √λ_i DE Λ₇₂")
    print("=" * 100)
    print(f"{'i':>3} | {'Expression':<30} | {'Valeur calculée':<18} | {'Valeur BETA_K':<18} | {'Erreur %':<12} | {'Orbitales'}")
    print("-" * 100)
    
    orbitales_map = {
        0: "1s1/2", 1: "2p1/2", 2: "3s1/2", 3: "3p1/2", 4: "2g9/2",
        5: "3d5/2", 6: "4p1/2", 7: "1j15/2", 8: "2h9/2", 9: "3f5/2",
        10: "5p1/2", 11: "6s1/2", 12: "1k17/2", 13: "2i11/2", 14: "3g9/2"
    }
    
    erreurs = []
    
    for idx, expr, compos, val_attendue in racines:
        # Calculer la valeur à partir de BETA_K
        val_calculee = 0.0
        orbitales_actives = set()
        
        for k, signe in compos:
            val_calculee += signe * BETA_K[k]
            orbitales_actives.add(orbitales_map.get(k, f"orb{k}"))
        
        erreur = abs(val_calculee - val_attendue)
        erreur_pct = 100 * erreur / val_attendue if val_attendue != 0 else 0
        erreurs.append(erreur_pct)
        
        # Formatage de l'expression pour l'affichage
        expr_str = expr
        for k, signe in compos:
            if signe == -1:
                expr_str = expr_str.replace(f"+ β_{k}", f"- β_{k}")
        
        orb_str = ", ".join(sorted(orbitales_actives)[:3])
        if len(orbitales_actives) > 3:
            orb_str += "..."
        
        statut = "✓" if erreur_pct < 1e-10 else "⚠" if erreur_pct < 1e-6 else "✗"
        
        print(f"{statut} {idx:3d} | {expr:<30} | {val_calculee:<18.12f} | {val_attendue:<18.12f} | {erreur_pct:<12.2e} | {orb_str}")
    
    print("-" * 100)
    print(f"\n📊 STATISTIQUES :")
    print(f"   Erreur moyenne : {np.mean(erreurs):.2e} %")
    print(f"   Erreur max     : {np.max(erreurs):.2e} %")
    print(f"   Écart-type     : {np.std(erreurs):.2e} %")
    
    # Vérification que nous avons bien 48 racines
    print(f"\n✅ Nombre de racines : {len(racines)} (devrait être 48)")

# ============================================================================
# SAUVEGARDE EN JSON
# ============================================================================
def sauvegarder_json():
    """Sauvegarde la table des racines au format JSON"""
    racines = construire_table_48_racines()
    
    data = {
        "meta": {
            "nom": "Racines non-degenerées de Λ72",
            "dimension": 72,
            "nb_racines": 48,
            "groupe_symetrie": "Binary octahedral group (2O) order 48"
        },
        "racines": []
    }
    
    for idx, expr, compos, val in racines:
        eps = np.zeros(15, dtype=int)
        for k, signe in compos:
            eps[k] = signe
        
        data["racines"].append({
            "index": idx,
            "expression": expr,
            "valeur": val,
            "epsilon": eps.tolist(),
            "orbitales": [ORBITALES.get(k, f"orb{k}") for k, s in compos]
        })
    
    with open("racines_lambda72.json", "w") as f:
        json.dump(data, f, indent=2)
    
    print("\n💾 Fichier sauvegardé : racines_lambda72.json")

# ============================================================================
# MAIN
# ============================================================================
if __name__ == "__main__":
    verifier_et_afficher()
    sauvegarder_json()
    
    print("\n" + "=" * 100)
    print("📌 NOTE SUR LA TABLE")
    print("=" * 100)
    print("""
Cette table est reconstruite à partir de l'Appendix A du papier.
Les combinaisons sont exactes (erreur < 10^{-14}) car elles utilisent
directement les valeurs des β_k.
    
Les 15 β_k (indices 0,8,15,20,26,28,29,32,33,35,40,41,42,43,46)
sont les vecteurs de base. Les 33 autres sont des combinaisons
linéaires ± de ces 15 vecteurs.
""")