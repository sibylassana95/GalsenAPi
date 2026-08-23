# Contribuer à GalsenAPI

Merci de votre intérêt ! Toutes les contributions sont bienvenues : code, données,
documentation, design, signalements.

## Signaler un problème

- **Bug** : modèle « Bug report » — décrivez l'URL, la requête, le résultat attendu/obtenu.
- **Donnée incorrecte ou manquante** : modèle « Data correction » — citez **la source officielle**
  qui prouve la correction (règle du projet : aucune donnée sans provenance).
- **Nouveau dataset** : modèle « Dataset request » — indiquez la source, la licence et le lien.

## Environnement de développement

```bash
git clone https://github.com/sibylassana95/GalsenAPi.git
cd GalsenAPi
python -m venv venv && venv\Scripts\activate   # ou source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                            # DB_ENGINE=sqlite suffit pour commencer
python manage.py migrate
python manage.py test                           # doit être vert avant ET après vos changements
```

Pour les données complètes, voir les commandes `import_*` dans le README.

## Règles du projet

1. **Jamais de données inventées.** Toute valeur importée est tracée (source, licence, date).
2. **Ne pas casser l'existant** : les anciennes routes `/api/*` restent fonctionnelles.
3. **Tests obligatoires** pour tout nouveau endpoint, modèle ou commande d'import
   (`python manage.py test` — les tests tournent sur PostgreSQL si configuré).
4. **Style** : Python sobre et typé quand c'est pertinent ; templates en français correct
   (accents) ; pas de dépendance Node — Tailwind est compilé via `tools/tailwindcss.exe`
   (lancer `.\build_css.ps1` après avoir ajouté des classes utilitaires).
5. **Commits atomiques** au format conventionnel : `feat:`, `fix:`, `docs:`, `chore:`…
6. Ne jamais commiter de secrets (`.env`, clés, mots de passe).

## Processus

1. Forkez et créez une branche (`feat/ma-fonctionnalite`).
2. Développez + tests.
3. `python manage.py test` vert.
4. Pull request décrivant le **quoi**, le **pourquoi** et les **données/sources** le cas échéant.
5. Revue puis merge sur `develop`.

## Ajouter un nouveau domaine de données

1. Vérifier la disponibilité et **la licence** de la source (redistribution autorisée ?).
2. Créer l'app (`models`, `api/`, `management/commands/import_<domaine>`).
3. Tracer la provenance (`meta`, `datasets.DataSource`, entrée catalogue).
4. Tests (fixtures locales, jamais de réseau).
5. Documenter dans README (tableau des sources) et CHANGELOG.
