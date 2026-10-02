# Connecteurs : de l'AIOS d'origine aux alternatives kSuite et open source

Ce document passe en revue **chaque service externe** cité par le modèle d'origine
(AI OS de Thomas Berton) et propose son remplaçant dans AIGORA. On privilégie, dans l'ordre :

1. **kSuite (Infomaniak)**, déjà payé et hébergé en Suisse ;
2. **ce que Claude Code sait faire seul** (zéro service en plus) ;
3. **un logiciel open source**, de préférence avec un serveur MCP officiel, sinon un protocole ouvert (IMAP, CalDAV, WebDAV, REST).

Légende du statut : **✅ intégré** dans ce dossier · **🟡 proposé** (documenté, à activer si besoin) · **❌ retiré**.

## Vue d'ensemble

| Service d'origine | Utilisé par | Remplaçant AIGORA | Licence | Connexion | Statut |
|---|---|---|---|---|---|
| Gmail | email-digest, email-assistant | **kSuite Mail** | service Infomaniak | IMAP/SMTP (scripts) ou MCP officiel `@infomaniak/mcp-server-mail` (MIT) | ✅ |
| Google Calendar | scrum-master, meeting-prep | **kSuite Agenda** | service Infomaniak | CalDAV (script) ou MCP officiel `@infomaniak/mcp-server-calendar` (MIT) | ✅ |
| Google Drive | connecteurs Claude | **kDrive** | service Infomaniak | dossier synchronisé (app kDrive de bureau) + MCP officiel `@infomaniak/mcp-server-kdrive` (MIT) | ✅ |
| Google Contacts | connecteurs Claude | **Contacts kSuite** | service Infomaniak | CardDAV (script) + MCP officiel `@infomaniak/mcp-server-contact` (MIT) | ✅ |
| Google Meet | meeting-prep | **kMeet** | service Infomaniak | MCP communautaire (opt-in) | 🟡 |
| Slack | email-digest, research-lead | **kChat** | service Infomaniak | webhook entrant (script) ou MCP officiel `@infomaniak/mcp-server-kchat` (MIT) | ✅ |
| Google Sheets | research-lead | **CSV local** `data/leads.csv` (lisible en R) | - | script `save_lead.py` | ✅ |
| Airtable (suivi des leads) | research-lead | **Odoo CRM** (Community auto-hébergé, ou Odoo Online) | LGPL-3 (Community) | API officielle JSON-2 / XML-RPC, script `odoo.py` | ✅ |
| Todoist | scrum-master | **task-manager local** (SQLite) | - | script `task_db.py` | ✅ |
| Todoist (multi-appareils) | scrum-master | **Tâches de l'Agenda kSuite** (synchronisées sur téléphone par kSync) | service Infomaniak | CalDAV (script) | ✅ |
| Todoist (équipe, kanban) | scrum-master | **Vikunja** | AGPL-3.0 | API REST ; serveurs MCP communautaires | 🟡 |
| OpenAI (analyses de leads, sentiment) | research-lead, email-digest | **Claude lui-même** dans la session | - | aucune clé | ✅ |
| OpenAI (mémoire : extraction + vecteurs) | memory | **Ollama** (`qwen3`, `nomic-embed-text`) | MIT | local, `localhost:11434` | ✅ (config) |
| OpenAI (variante hébergée) | memory | **Infomaniak AI Tools** (modèles open source en Suisse) | modèles open source | API compatible OpenAI | 🟡 |
| Pinecone | memory | **Qdrant** en mode embarqué | Apache-2.0 | dossier `data/qdrant/`, pas de serveur | ✅ (config) |
| Helicone (observabilité OpenAI) | research-lead | retiré (plus d'appel OpenAI) ; si besoin : **Langfuse** | MIT (cœur) | SDK / API | ❌ |
| Perplexity | research, research-lead, meeting-prep | **WebSearch / WebFetch** de Claude Code ; en option **SearXNG** | AGPL-3.0 | MCP `mcp-searxng` (MIT) | ✅ / 🟡 |
| Firecrawl | research | **Crawl4AI** (ou Firecrawl auto-hébergé) | Apache-2.0 | script Python / API | 🟡 |
| Relevance AI (scraping LinkedIn) | research-lead | retiré : profil collé par l'utilisateur + recherche web publique | - | - | ❌ |
| YouTube Analytics MCP | content-pipeline | **yt-dlp** (sous-titres) | Unlicense | ligne de commande | ✅ |
| Gamma | gamma-slides | **Quarto** (fourni avec RStudio) : reveal.js, PowerPoint, PDF | MIT | ligne de commande `quarto render` | ✅ |
| Notion | MCP-SERVERS | Markdown + Quarto dans le projet ; pour un wiki d'équipe : **Docmost** ou **Nextcloud** (Notes, Collectives) | AGPL-3.0 | API REST / WebDAV | 🟡 |
| Canva | connecteurs Claude | **Penpot** (maquettes), **Inkscape** | MPL-2.0 / GPL | API / fichiers | 🟡 |
| Linear / GitHub | MCP-SERVERS | **Forgejo** ou **GitLab CE** | GPL-3.0 / MIT | API REST | 🟡 |
| n8n | MCP-SERVERS | **Node-RED** ou **Activepieces** (n8n est « fair-code », pas open source au sens OSI) | Apache-2.0 / MIT | webhooks / API | 🟡 |
| Telegram (version serveur d'origine) | scheduler | kChat + `/schedule` de Claude Code | - | - | ✅ |
| Filesystem MCP | MCP-SERVERS | inchangé (serveur MCP officiel, open source) | MIT | MCP | ✅ |

## Détail des propositions open source à activer

### SearXNG : recherche web sans traçage (remplace Perplexity)
- **Quoi** : métamoteur open source qui interroge plusieurs moteurs, sans pistage.
- **Installer** : une instance Docker (`docker run -p 8080:8080 searxng/searxng`) ou une instance de confiance ; activer le format JSON dans `settings.yml`.
- **Brancher** : `SEARXNG_URL=http://localhost:8080` dans `.env`, puis
  `python3 .claude/skills/ksuite-setup/scripts/register_mcp.py --only searxng` (serveur `mcp-searxng`).
- **Intérêt** : modéré. WebSearch intégré suffit le plus souvent ; SearXNG sert surtout si tu veux maîtriser les moteurs utilisés.

### Odoo CRM : suivi des leads et opportunités (remplace Airtable)
- **Quoi** : le module CRM d'Odoo (pipeline par étapes, activités, relances, historique), inclus
  dans l'édition **Community**, open source (LGPL-3). Odoo Online est l'édition Enterprise, propriétaire.
- **Brancher** : `aigora_odoo_configurer()` dans la console R (clé API Odoo). Détails : `docs/ODOO.md`.
- **Pourquoi pas une base de données générique** : Baserow a été écarté (vue Kanban et plusieurs
  fonctions réservées aux offres payantes) ; NocoDB n'est plus open source.

### Vikunja : gestion de tâches (remplace Todoist)
- **Quoi** : listes, kanban, échéances, application mobile, auto-hébergeable.
- **Brancher** : jeton API Vikunja dans `.env` ; serveur MCP communautaire (vérifier la maintenance avant installation), ou petit script REST dans `task-manager/scripts/`.
- **Intérêt** : faible maintenant que les tâches kSuite (avec kSync) donnent déjà les tâches sur téléphone. Utile seulement pour du kanban d'équipe.
- **Variante kSuite** : les tâches de l'agenda Infomaniak (CalDAV VTODO) ; le serveur communautaire [henrikogaard/infomaniak-mcp](https://github.com/henrikogaard/infomaniak-mcp) les gère, mais il est jeune (peu d'utilisateurs) : à tester avec prudence.

### Ollama + Qdrant : mémoire sémantique locale (remplace OpenAI + Pinecone)
- Déjà configuré par défaut dans `mem0_config.yaml`. Activation : `docs/MEMORY-UPGRADE.md`.
- **Infomaniak AI Tools** est la variante hébergée en Suisse si l'ordinateur est trop lent.
- Serveur MCP officiel optionnel : [`mcp-server-qdrant`](https://github.com/qdrant/mcp-server-qdrant) (Apache-2.0), utile si tu veux que Claude interroge directement la base vectorielle.

### Nextcloud / Docmost : notes et wiki (remplace Notion)
- Pour un usage solo, les fichiers Markdown et Quarto du projet sont déjà le meilleur « Notion » : versionnables, lisibles par Claude, rendus par RStudio.
- Pour une équipe : Docmost (wiki) ou Nextcloud (fichiers, notes, agenda) avec API REST / WebDAV. Les serveurs MCP existants sont communautaires : à évaluer au cas par cas.

## Recommandation de priorité

1. **kSuite** (fait) : c'est là que sont tes mails, ton agenda et tes fichiers.
2. **Mémoire locale Ollama + Qdrant** si tu veux qu'AIGORA se souvienne finement de tout (rien ne sort de ta machine).
3. **Odoo CRM** dès que tu suis des prospects dans la durée (pipeline, relances).
4. **SearXNG / Vikunja** : confort, pas nécessité.

## Règles de sécurité pour tout nouveau connecteur

- Préférer un serveur MCP **officiel** de l'éditeur ; pour un serveur communautaire, regarder licence, date du dernier commit, nombre d'utilisateurs et permissions demandées.
- Enregistrer les serveurs avec `--scope local` (jamais de jeton dans `.mcp.json`).
- Jetons à portée minimale, révocables ; jamais de mot de passe principal.
- Chaque serveur MCP ajoute des milliers de jetons de contexte : n'activer que ceux qu'on utilise.

## Sources

- Serveurs MCP officiels Infomaniak : [mail](https://github.com/Infomaniak/mcp-server-mail), [calendar](https://github.com/Infomaniak/mcp-server-calendar), [kdrive](https://github.com/Infomaniak/mcp-server-kdrive), [kchat](https://github.com/Infomaniak/mcp-server-kchat)
- [Infomaniak AI Tools, API compatible OpenAI](https://developer.infomaniak.com/docs/api/post/2/ai/%7Bproduct_id%7D/openai/v1/chat/completions)
- [Serveur MCP Qdrant officiel](https://github.com/qdrant/mcp-server-qdrant)
- [Odoo 19 : API externe JSON-2](https://www.odoo.com/documentation/19.0/developer/reference/external_api.html)
- [NocoDB n'est plus open source (discussion Cloudron)](https://forum.cloudron.io/topic/14918/heads-up-nocodb-is-no-longer-open-source.)
- [mcp-searxng](https://www.npmjs.com/package/mcp-searxng)
- [Discussion sur un serveur MCP officiel Vikunja](https://community.vikunja.io/t/official-mcp-server/4490)
