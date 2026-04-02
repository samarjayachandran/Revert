#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
nettoyer_donnees.py — Script de nettoyage des données carbone

Lit le fichier carbon_data.html, corrige toutes les séquences d'échappement
RTF (\'e9 → é, \'ea → ê, etc.) et exporte un fichier CSV propre
(carbon_data_clean.csv) prêt à être lu par l'application Streamlit.

Usage :
    python nettoyer_donnees.py

Le fichier carbon_data.html doit se trouver dans le même répertoire.
Le CSV résultant est écrit dans le même répertoire.
"""

import re
import pandas as pd
from pathlib import Path

# =========================================================
# Constantes
# =========================================================
HTML_FILE = "carbon_data.html"
OUTPUT_CSV = "carbon_data_clean.csv"

COLONNES = [
    "Categorie", "Sous_categorie", "Produit_process",
    "Unite", "Type_prestation", "Prestation", "Emissions_CO2",
]

# Dictionnaire de secours pour les cas non standard
REPL_MAP = {
    r"\'ea": "ê", r"\'e9": "é", r"\'e8": "è", r"\'b": "",
    r"\'ef": "ï", r"\'e7": "ç", r"\'e2": "â", r"\'9c": "œ",
    r"\'e0": "à", r"\'ee": "î", r"\'f4": "ô", r"\'fb": "û",
    r"\'f9": "ù", r"\'e4": "ä", r"\'f6": "ö", r"\'fc": "ü",
    r"\'eb": "ë", r"\'e6": "æ",
}


# =========================================================
# Fonctions de nettoyage
# =========================================================
def corriger_echappements_rtf(texte: str) -> str:
    """Remplace toutes les séquences RTF (\\'xx) par le caractère Unicode
    correspondant, en interprétant le code hexadécimal comme CP1252."""
    if not isinstance(texte, str):
        return texte

    def _hex_vers_caractere(m):
        try:
            return bytes.fromhex(m.group(1)).decode("cp1252")
        except (ValueError, UnicodeDecodeError):
            return m.group(0)

    # Remplacement générique par regex
    resultat = re.sub(r"\\'([0-9a-fA-F]{2})", _hex_vers_caractere, texte)

    # Secours : appliquer le dictionnaire pour les cas résiduels
    for motif, remplacement in REPL_MAP.items():
        resultat = resultat.replace(motif, remplacement)

    return resultat


def nettoyer_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Applique le nettoyage RTF à toutes les colonnes texte du DataFrame."""
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].astype(str).apply(corriger_echappements_rtf)
    return df


# =========================================================
# Programme principal
# =========================================================
def main():
    chemin_html = Path(__file__).parent / HTML_FILE
    chemin_csv = Path(__file__).parent / OUTPUT_CSV

    if not chemin_html.exists():
        print(f"ERREUR : le fichier {HTML_FILE} est introuvable dans {chemin_html.parent}")
        return

    print(f"Lecture de {HTML_FILE}...")
    tables = pd.read_html(str(chemin_html))
    if not tables:
        print("ERREUR : aucune table trouvée dans le fichier HTML.")
        return

    df = tables[0].copy()
    df.columns = COLONNES
    df = df.iloc[1:].reset_index(drop=True)

    print(f"  {len(df)} lignes trouvées.")
    print("Nettoyage des séquences d'échappement RTF...")
    df = nettoyer_dataframe(df)

    # Conversion de la colonne émissions en numérique
    df["Emissions_CO2"] = pd.to_numeric(df["Emissions_CO2"], errors="coerce")

    # Vérification : afficher quelques exemples nettoyés
    exemples = df["Produit_process"].head(10).tolist()
    print("Exemples de produits nettoyés :")
    for ex in exemples:
        print(f"  - {ex}")

    # Vérification : chercher des séquences résiduelles
    residuels = 0
    for col in COLONNES:
        if df[col].dtype == object:
            masque = df[col].str.contains(r"\\'[0-9a-fA-F]{2}", regex=True, na=False)
            residuels += masque.sum()
    if residuels > 0:
        print(f"ATTENTION : {residuels} séquence(s) RTF résiduelle(s) détectée(s).")
    else:
        print("Aucune séquence RTF résiduelle détectée.")

    print(f"Écriture de {OUTPUT_CSV}...")
    df.to_csv(chemin_csv, index=False, encoding="utf-8-sig")
    print(f"Terminé. Fichier propre enregistré : {chemin_csv}")
    print(f"  {len(df)} lignes, {len(df.columns)} colonnes.")


if __name__ == "__main__":
    main()
