"""Curateur des indicateurs économiques World Bank Indicators (Sénégal).

Liste maintenue à la main : chaque code a été vérifié en ligne contre
l'API World Bank (https://api.worldbank.org/v2/country/SEN/indicator/<code>)
avant inclusion ; les codes morts ou arrêtés pour le Sénégal sont retirés
(GC.DOD.TOTL.GD.ZS : aucune donnée SEN ; FR.INR.RINR : dernière valeur 2016).
Les noms officiels EN ne sont pas dupliqués ici : ils proviennent de la méta
de l'API au moment de l'import (champ indicator.value -> nom_officiel).

Licence : CC BY 4.0 (https://www.worldbank.org/en/about/legal/terms-of-use-for-datasets).
"""

API_BASE = (
    'https://api.worldbank.org/v2/country/SEN/indicator/{code}'
    '?format=json&per_page=25000&date=1960:2026'
)

# (code WB, nom_fr court, categorie, unite)
INDICATEURS = [
    # --- PIB ---
    ('NY.GDP.MKTP.CD', 'PIB courant', 'pib', 'US$'),
    ('NY.GDP.MKTP.KD.ZG', 'Croissance du PIB réel', 'pib', '%'),
    ('NY.GDP.MKTP.PP.CD', 'PIB en parité de pouvoir d’achat', 'pib', 'US$ PPA'),
    ('NY.GDP.PCAP.CD', 'PIB par habitant', 'pib', 'US$'),
    # --- Prix & inflation ---
    ('FP.CPI.TOTL.ZG', 'Inflation (IPC)', 'prix', '%'),
    ('FP.CPI.TOTL', 'Indice des prix à la consommation', 'prix', 'indice'),
    # --- Emploi ---
    ('SL.UEM.TOTL.ZS', 'Chômage (estimation OIT)', 'emploi', '%'),
    ('SL.EMP.TOTL.SP.ZS', 'Taux d\u2019emploi', 'emploi', '%'),
    # --- Commerce ---
    ('NE.EXP.GNFS.CD', 'Exportations de biens et services', 'commerce', 'US$'),
    ('NE.IMP.GNFS.CD', 'Importations de biens et services', 'commerce', 'US$'),
    (
        'TX.VAL.TECH.MF.ZS',
        'Exportations de haute technologie (% export. manufacturières)',
        'commerce', '%',
    ),
    ('BX.KLT.DINV.CD.WD', 'Investissements directs étrangers, entrées nettes',
     'commerce', 'US$'),
    # --- Dette & finance publique ---
    ('DT.DOD.DPPG.CD', 'Stock de dette extérieure', 'dette', 'US$'),
    ('GC.XPN.TOTL.GD.ZS', 'Dépenses publiques totales', 'dette', '% du PIB'),
    ('GC.REV.XGRT.GD.ZS', 'Recettes hors dons', 'dette', '% du PIB'),
    ('GC.NLD.TOTL.GD.ZS', 'Solde budgétaire', 'dette', '% du PIB'),
    ('FS.AST.PRVT.GD.ZS', 'Crédit au secteur privé', 'dette', '% du PIB'),
    # --- Structure économique (valeur ajoutée sectorielle + accès énergie) ---
    ('NV.AGR.TOTL.ZS', 'Agriculture, valeur ajoutée', 'secteurs', '% du PIB'),
    ('NV.IND.MANF.ZS', 'Industrie manufacturière, valeur ajoutée', 'secteurs',
     '% du PIB'),
    ('NV.SRV.TOTL.ZS', 'Services, valeur ajoutée', 'secteurs', '% du PIB'),
    ('EG.ELC.ACCS.ZS', 'Accès à l\u2019électricité', 'secteurs', '%'),
]

INDICATEURS_PAR_CODE = {code: (nom, cat, unite)
                        for code, nom, cat, unite in INDICATEURS}


def url_indicateur(code):
    """URL API officielle pour un indicateur (Sénégal, 1960:2026)."""
    return API_BASE.format(code=code)


SOURCE_DEFAULTS = {
    'nom': 'Banque mondiale',
    'slug': 'worldbank',
    'url': 'https://data.worldbank.org',
    'publisher': 'World Bank Group',
    'license_nom': 'CC BY 4.0',
    'license_url': (
        'https://www.worldbank.org/en/about/legal/terms-of-use-for-datasets'
    ),
    'redistribuable': True,
}
