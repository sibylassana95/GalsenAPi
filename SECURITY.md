# Politique de sécurité

## Versions supportées

| Version | Support |
|---|---|
| 2.0.x | ✅ |
| 1.x | ❌ (fin de vie) |

## Signaler une vulnérabilité

**N'ouvrez pas d'issue publique pour une vulnérabilité.**

Contactez le mainteneur en privé :

- Email : [sibyamara95@gmail.com](mailto:sibyamara95@gmail.com)
- Ou via un message GitHub vers [@sibylassana95](https://github.com/sibylassana95)

Incluez si possible : description, impact, étapes de reproduction, preuve de concept,
suggestions de correction.

Vous recevrez une réponse sous **72 heures**. Après correction et diffusion, le
signalement sera crédité (sauf demande contraire).

## Mesures en place

- Secrets hors dépôt (`.env` ignoré, `.env.example` documenté)
- `ALLOWED_HOSTS` et `CORS_ALLOWED_ORIGINS` explicites en production
- Throttling DRF (60 req/min anonyme, 120 authentifié)
- Requêtes ORM exclusivement (pas de SQL brut concaténé)
- Dépendances épinglées dans `requirements.txt` (audit automatisé prévu en CI — Phase 10)

## Périmètre

Sont dans le périmètre : l'application Django (web + API), la configuration de
déploiement du dépôt, les scripts d'ingestion. Ne sont pas dans le périmètre :
l'infrastructure d'hébergement cPanel gérée par l'hébergeur.
