# AIGORA et les outils Infomaniak

AIGORA utilise l'écosystème Infomaniak à la place de Google Workspace et de Slack. Ce document
passe en revue **tous les outils Infomaniak**, dit comment AIGORA s'y connecte, puis détaille
la mise en place. Tout est optionnel : branche seulement ce dont tu as besoin.

Le plus simple : dis à AIGORA **« Connecte kSuite »**, il te guide étape par étape (skill `ksuite-setup`).

> Règle d'or : jamais le mot de passe de ton compte Infomaniak. Uniquement des
> **mots de passe d'application** et des **jetons API**, révocables à tout moment.

## Inventaire : chaque outil Infomaniak et son branchement

Légende : ✅ intégré et testé · 🟡 disponible en option · ➖ rien à brancher · ❌ non automatisable

| Outil | Ce que c'est | Comment AIGORA s'y connecte | Statut |
|---|---|---|---|
| **Mail** | Messagerie kSuite | Scripts IMAP/SMTP (lecture, **brouillons**) ; serveur MCP officiel `mcp-server-mail`. L'envoi direct est **bloqué** par une règle de sécurité | ✅ |
| **Agenda** | Calendrier kSuite | Script CalDAV (lister, créer) ; serveur MCP officiel `mcp-server-calendar` | ✅ |
| **Tâches** | Les tâches de l'Agenda | Script CalDAV (VTODO) : lister, ajouter, terminer. Elles arrivent sur ton téléphone via kSync | ✅ |
| **Contacts** | Carnets d'adresses | Script CardDAV (recherche, export CSV pour R) ; serveur MCP officiel `mcp-server-contact` (lecture) | ✅ |
| **kDrive** | Stockage de fichiers | **Dossier synchronisé** par l'application kDrive de bureau (toutes offres) ; serveur MCP officiel `mcp-server-kdrive` (recherche, partage, dépôt) | ✅ |
| **Docs, Grids, Points** | Éditeurs en ligne dans kDrive | AIGORA produit des `.docx`, `.xlsx`, `.pptx` (Quarto, R) dans le dossier kDrive : tu les ouvres et les retouches en ligne | ✅ |
| **kChat** | Messagerie d'équipe | Webhook entrant (publication) ; serveur MCP officiel `mcp-server-kchat` (lecture, publication) | ✅ |
| **kMeet** | Visioconférence | Création de salles via le serveur MCP communautaire (option) ; sinon lien créé à la main | 🟡 |
| **Chk** | Liens courts et QR codes | Serveur MCP communautaire (option) | 🟡 |
| **kPaste** | Partage chiffré de texte (ex. un mot de passe à transmettre) | Serveur MCP communautaire (option), chiffrement côté client | 🟡 |
| **AI Tools** | API de modèles open source hébergés en Suisse | Variante de la mémoire avancée ; transcription possible via le serveur communautaire | 🟡 |
| **Euria** | L'assistant IA conversationnel d'Infomaniak | Rien à brancher : AIGORA (Claude) joue ce rôle. Les deux peuvent coexister | ➖ |
| **kSync** | Application Android (dérivée de DAVx⁵) qui synchronise agenda, contacts et tâches | Rien à brancher : ce qu'AIGORA crée apparaît sur ton téléphone. Pour les tâches : kSync + jtx Board. Sur iPhone : compte CalDAV/CardDAV natif | ➖ |
| **Application kDrive de bureau** | Synchronise kDrive avec un dossier local | Base du branchement « dossier » ci-dessus | ✅ |
| **SwissTransfer** | Envoi de gros fichiers | Pas d'automatisation fiable (protection anti-robot) : AIGORA prépare le fichier dans kDrive, tu l'envoies | ❌ |
| **Newsletter** | Outil d'emailing Infomaniak | API officielle (campagnes, groupes). Proposé : AIGORA rédige la campagne avec ta voix ; création de brouillon à ajouter si tu l'utilises | 🟡 |
| **Hébergement web, domaines** | Sites, DNS | Hors assistant au quotidien ; utile pour publier un site fait avec `build-website` | 🟡 |
| **Swiss Backup** | Sauvegarde | Pour sauvegarder le dossier AIGORA (ou simplement le placer dans kDrive) | 🟡 |
| **Gestionnaire de jetons, mots de passe d'application** | Sécurité du compte | C'est par là que passent tous les accès d'AIGORA | ➖ |

## Les quatre façons de se connecter

| | Ce que c'est | Il faut | Idéal pour |
|---|---|---|---|
| **A. Serveurs MCP officiels** | Outils que Claude utilise directement (licence MIT) | Node.js + un jeton API | Le travail interactif |
| **A'. Serveur MCP communautaire** | `@henrikogard/infomaniak-mcp`, filtré sur kMeet, Chk, kPaste et tâches | Opt-in `KSUITE_EXTRA_MCP=1` | Ce qu'Infomaniak ne couvre pas encore officiellement |
| **B. Scripts locaux AIGORA** | Python, protocoles standard (IMAP, SMTP, CalDAV, CardDAV, webhook) | Mots de passe d'application | Les routines fiables, sans Node.js |
| **C. Dossier kDrive** | Les fichiers synchronisés sur ton ordinateur | Application kDrive de bureau | Lire et déposer des documents, sur toutes les offres |

## Le plus simple : `aigora_ksuite_configurer()`

Dans la console R, `aigora_ksuite_configurer()` te pose les questions une par une (agenda,
tâches et contacts ; mail ; kChat), masque les mots de passe, enregistre tout dans `.env`,
installe si besoin le paquet Python `caldav`, puis teste les connexions. Les sections
ci-dessous détaillent les mêmes réglages pour qui préfère éditer `.env` à la main.

## Étape 0 : créer le fichier .env

Dans la console R : `aigora_env()`. Le fichier `.env` est créé à partir de `.env.example` et
s'ouvre dans RStudio. Il ne quitte jamais ton ordinateur et est ignoré par git.

## 1. Mail (IMAP/SMTP)

1. Crée un **mot de passe d'appareil** pour ton adresse mail. Attention : c'est un mot de passe
   propre à l'adresse, **différent** du mot de passe d'application du compte (qui sert à l'agenda) :
   [manager.infomaniak.com](https://manager.infomaniak.com) > **Service Mail** > ton domaine > ton
   adresse > onglet **Appareils** > **Ajouter un appareil** (nom : « AIGORA »). Copie le mot de passe
   affiché : il ne sera plus visible ensuite. Autre voie : l'assistant
   [config.infomaniak.com](https://config.infomaniak.com).
2. Dans `.env` :
   ```
   KSUITE_MAIL_USER=prenom.nom@ton-domaine.ch
   KSUITE_MAIL_PASSWORD=le-mot-de-passe-d-appareil
   ```

AIGORA lit les mails sans les marquer comme lus et crée des **brouillons** que tu envoies toi-même.

## 2. Agenda, tâches et contacts (CalDAV / CardDAV)

Un seul identifiant pour les trois.

1. Sur [config.infomaniak.com](https://config.infomaniak.com) : *Mon agenda* > *Synchronisation manuelle*.
   Note l'**identifiant court** (du type `AB12345`, pas ton adresse mail).
2. Dans `.env` :
   ```
   KSUITE_DAV_USER=AB12345
   KSUITE_DAV_PASSWORD=mot-de-passe-d-application
   ```
3. Dans le terminal : `pip install caldav`

Dans R : `aigora_taches()` et `aigora_contacts()` renvoient des data.frames.
Pour que les tâches créées par AIGORA soient ta liste de tâches principale, mets
`task_manager: "ksuite"` dans `config/preferences.yaml`.

## 3. kDrive (dossier synchronisé)

1. Installe l'[application kDrive de bureau](https://www.infomaniak.com/fr/apps/download-kdrive) et laisse-la synchroniser.
2. Dans la console R : `aigora_kdrive()` (détecte `~/kDrive`), ou `aigora_kdrive("D:/kDrive")`.
3. Redémarre Claude Code (`/exit` puis `claude`).

AIGORA peut alors lire tes documents clients et y déposer ses livrables. Il ne supprime ni
n'écrase rien sans ton accord. Pour retirer l'accès : `aigora_kdrive(retirer = TRUE)`.

## 4. kChat (webhook entrant)

1. Dans kChat : clique sur l'icône **Nouveau** (+) à côté du nom de ton organisation, en haut de la
   liste des canaux > **Intégrations** > **Webhooks entrants** > **Ajouter**, choisis le canal.
   Si « Intégrations » n'apparaît pas, ton compte n'a pas les droits : demande à un administrateur.
2. Dans `.env` : `KCHAT_WEBHOOK_URL=https://...`

## 5. Serveurs MCP officiels (Mail, Agenda, kDrive, kChat, Contacts)

1. Installe [Node.js LTS](https://nodejs.org).
2. Crée un jeton : [manager.infomaniak.com > Jetons API](https://manager.infomaniak.com/v3/ng/accounts/token/list),
   avec seulement les scopes utiles : `workspace:mail`, `workspace:calendar`, `user_info`, `drive`, `kchat`, `contacts`.
3. Dans `.env` : `INFOMANIAK_TOKEN=...`, `KDRIVE_ID=123456` (le nombre dans l'URL kDrive),
   `KCHAT_TEAM_NAME=mon-equipe` (dans `https://mon-equipe.kchat.infomaniak.com`).
4. Console R : `aigora_mcp()` (simulation), puis `aigora_mcp(simulation = FALSE)`.
5. Redémarre Claude Code.

## 6. Option : kMeet, Chk, kPaste et tâches par MCP (serveur communautaire)

Infomaniak ne publie pas (encore) de serveur MCP officiel pour ces outils. Le projet
communautaire [infomaniak-mcp](https://github.com/henrikogaard/infomaniak-mcp) (licence MIT)
les couvre. Il est récent et peu utilisé : AIGORA ne l'active que si tu le demandes, et le
restreint à 18 outils (salles kMeet, liens Chk, kPaste, tâches), avec confirmation stricte
de tout envoi externe.

1. Dans `.env` : `KSUITE_EXTRA_MCP=1` (en plus de `INFOMANIAK_TOKEN` et des identifiants DAV).
2. Console R : `aigora_mcp(simulation = FALSE)`, puis redémarre Claude Code.

## Vérifier

```r
aigora_ksuite()             # ce qui est configuré
aigora_ksuite(test = TRUE)  # teste IMAP, SMTP, CalDAV et CardDAV (n'envoie rien)
```

## Qui utilise quoi

| Skill | Outils Infomaniak |
|-------|---------|
| `email-digest` | Mail (lecture + brouillons), kChat (synthèse) |
| `email-assistant` | Mail (optionnel) |
| `scrum-master` | Agenda, Tâches, kChat |
| `meeting-prep` | Agenda, Contacts, Mail, kMeet (option) |
| `research-lead` | Contacts, kChat, kDrive |
| `quarto-slides` | kDrive (dépôt de la présentation) |
| `scheduler` | Tâches, Agenda, kChat |

## Sources

- Serveurs MCP officiels : [mail](https://github.com/Infomaniak/mcp-server-mail), [calendar](https://github.com/Infomaniak/mcp-server-calendar), [kdrive](https://github.com/Infomaniak/mcp-server-kdrive), [kchat](https://github.com/Infomaniak/mcp-server-kchat), contact (`@infomaniak/mcp-server-contact` sur npm)
- [Serveur communautaire infomaniak-mcp](https://github.com/henrikogaard/infomaniak-mcp)
- [kSync pour Android](https://www.infomaniak.com/en/support/faq/2302/discover-ksync-for-android) et [synchroniser les tâches avec kSync](https://www.infomaniak.com/en/support/faq/2301/synchronize-tasks-with-ksync)
- [Offres my kSuite (outils inclus)](https://www.infomaniak.com/en/ksuite/myksuite/prices)
- [Paramètres IMAP/SMTP](https://www.infomaniak.com/en/support/faq/2427/manually-configure-your-emails-contacts-and-calendars-on-your-devices)
- [Webhooks kChat](https://www.infomaniak.com/en/support/faq/2001/connect-external-applications-to-kchat)
- [kDrive en WebDAV (non disponible sur kSuite Free/Standard)](https://www.infomaniak.com/en/support/faq/2894/sync-kdrive-via-webdav-on-linux)
- [API Newsletter Infomaniak](https://www.infomaniak.com/en/support/faq/2211/using-the-infomaniak-newsletter-api)
