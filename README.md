# AIGORA, Édition Locale pour RStudio

> Transforme Claude Code, lancé depuis RStudio, en assistant IA pour ton activité. 100 % local,
> branché sur **kSuite (Infomaniak)** et sur des **logiciels open source**. Pas de serveur, pas de
> déploiement, pas de service Google.

AIGORA est un projet RStudio. Tu l'ouvres, tu lances l'assistant dans l'onglet Terminal, et tu
discutes avec lui en français : il connaît ton activité, écrit avec ta voix, fait tes recherches,
gère tes tâches, travaille avec tes outils Infomaniak (Mail, Agenda, tâches, Contacts, kDrive,
kChat…), et apprend au fil du temps.

> [!NOTE]
> AIGORA est une adaptation de **AI OS (Édition Locale)** de Thomas Berton (agence Azuro AI),
> publié sous licence MIT. Voir [Origine et licence](#origine-et-licence).

---

## Sommaire

- [Ce dont tu as besoin](#ce-dont-tu-as-besoin)
- [Installation](#installation)
- [Première utilisation](#première-utilisation)
- [Ce qu'il y a dedans](#ce-quil-y-a-dedans)
- [Connecter kSuite](#connecter-ksuite)
- [Connecteurs open source](#connecteurs-open-source)
- [La mémoire](#la-mémoire)
- [En cas de souci](#en-cas-de-souci)
- [Ce qui change par rapport à l'AIOS d'origine](#ce-qui-change-par-rapport-à-laios-dorigine)

---

## Ce dont tu as besoin

| Outil | À quoi ça sert | Lien |
|-------|----------------|------|
| **RStudio** (avec R) | L'environnement dans lequel tu ouvres le projet | [posit.co/download/rstudio-desktop](https://posit.co/download/rstudio-desktop/) |
| **Python 3.9 ou plus** | Fait tourner les scripts internes | [python.org/downloads](https://www.python.org/downloads/) |
| **Claude Code** | Le cerveau, connecté à ton abonnement Claude | [Installer Claude Code](https://docs.claude.com/en/docs/claude-code/setup) |
| Node.js LTS *(optionnel)* | Les serveurs MCP officiels Infomaniak | [nodejs.org](https://nodejs.org) |

> [!IMPORTANT]
> Sous **Windows**, pendant l'installation de Python, coche **« Add python.exe to PATH »**.

> [!NOTE]
> **Coût** : rien de plus que ton abonnement Claude (Pro, Max ou Team) et ton abonnement kSuite.
> Aucune clé API Anthropic, OpenAI ou autre n'est nécessaire.

---

## Installation

1. **Décompresse** le dossier quelque part de facile à retrouver (par exemple `Documents/aigora`).
2. Dans RStudio : **File > Open Project…**, choisis **`AIGORA.Rproj`**.
3. Dans la console R :
   ```r
   aigora_verifier()   # vérifie Python, Claude Code, Node, Quarto...
   aigora_demarrer()   # ouvre un terminal "AIGORA" et lance Claude Code
   ```
   Sans le paquet `rstudioapi`, ouvre simplement l'onglet **Terminal** (Alt+Maj+R) et tape `claude`.
4. La première fois, Claude Code te demande de te connecter à ton compte Claude.

C'est prêt : Claude Code charge `CLAUDE.md`, tu parles à AIGORA dans le terminal.

Guide détaillé : [docs/SETUP.md](docs/SETUP.md).

---

## Première utilisation

Dans le terminal AIGORA, écris :

```
Configure mon business
```

L'assistant te pose quelques questions et remplit ton profil (activité, voix, préférences).
Ensuite, parle-lui normalement :

- `Recherche mes 3 principaux concurrents dans [ton secteur]`
- `Écris un post LinkedIn sur [ton sujet]`
- `Prépare mon rendez-vous de jeudi avec [personne]`
- `Fais la synthèse de mes mails des dernières 24 h`
- `Qu'est-ce que j'ai à l'agenda cette semaine ?`
- `Fais-moi une présentation de 10 diapositives sur [sujet]`
- `Écris un script R qui analyse data/ventes.csv`

Dans la console R, `aigora_aide()` rappelle les fonctions disponibles.

---

## Ce qu'il y a dedans

### Les skills (tes programmes)

| Skill | Ce qu'il fait | Il faut |
|-------|---------------|---------|
| `business-setup` | Configuration de ton profil | rien |
| `research` | Recherche approfondie (web) | rien |
| `content-writer` | Contenus avec ta voix (LinkedIn, mail, blog) | rien |
| `meeting-prep` | Recherche + points de discussion pour tes rendez-vous | rien (Agenda kSuite en option) |
| `email-assistant` | Trier, résumer, rédiger des réponses (copier-coller) | rien |
| `weekly-review` | Revue hebdomadaire et plan de la semaine | rien |
| `task-manager` | Tâches et projets (base SQLite locale) | rien |
| `scrum-master` | Stand-up quotidien, planification | rien (Agenda kSuite en option) |
| `analyst` | Audit du système et rapports | rien |
| `skill-creator` | Crée tes propres skills | rien |
| `plugin-builder` | Empaquette tes skills | rien |
| `build-website` / `build-app` | Méthodes PRISM et ATLAS | rien |
| `quarto-slides` | Présentations reveal.js, PowerPoint ou PDF avec Quarto | Quarto (fourni avec RStudio) |
| `content-pipeline` | Vidéo YouTube vers posts LinkedIn et carrousels | `yt-dlp` (optionnel) |
| **`ksuite-setup`** | Outils Infomaniak : Mail, Agenda, tâches, Contacts, kDrive, kChat (+ kMeet, Chk, kPaste en option) | mots de passe d'application / jeton |
| `email-digest` | Synthèse de la boîte kSuite, brouillons, brief kChat | kSuite Mail |
| `research-lead` | Dossier de prospection et messages d'approche, relus par toi, puis opportunité dans Odoo | rien (kChat, Odoo en option) |
| `memory` | Mémoire sémantique 100 % locale | Ollama (optionnel) |
| `scheduler` | Rappels et tâches récurrentes | rien |
| `r-session` | Travaille avec ta session R ouverte (objets, aide des paquets) | paquet btw |
| `qgis` | Pilote QGIS : couches, traitements, cartes | extension QGIS MCP + uv |
| `qfieldcloud` | Projets et données terrain QField (QFieldCloud hébergé ou auto-hébergé) | SDK qfieldcloud |
| `odoo` | CRM Odoo : pipeline, opportunités créées depuis research-lead, étapes, notes | clé API Odoo |

### Les agents, les hooks

- 3 sous-assistants : `researcher` (lecture seule), `content-writer`, `code-reviewer`.
- 3 garde-fous automatiques : blocage des commandes dangereuses (`rm -rf`, etc.), journal
  quotidien, vérification des sorties de scripts.

### Les fonctions R (`R/aigora.R`, chargées à l'ouverture du projet)

`aigora_verifier()`, `aigora_demarrer()`, `aigora_env()`, `aigora_env_ranger()`, `aigora_ksuite_configurer()`, `aigora_ksuite()`, `aigora_mcp()`, `aigora_kdrive()`,
`aigora_taches()`, `aigora_contacts()`, `aigora_leads()`, `aigora_r_mcp()`, `aigora_qgis_mcp()`,
`aigora_qfieldcloud_login()`, `aigora_qfieldcloud_projets()`, `aigora_odoo_configurer()`,
`aigora_odoo_pipeline()`, `aigora_aide()`.

---

## Connecter kSuite

Écris à AIGORA : **« Connecte kSuite »**, il te guide étape par étape. Résumé :

Le plus simple : **`aigora_ksuite_configurer()`** dans la console R. Il pose les questions,
enregistre tout et teste les connexions. À la main :

1. `aigora_env()` crée et ouvre le fichier `.env` (jamais partagé, ignoré par git). Les fonctions de configuration remplissent chaque variable à sa place dans sa section ; `aigora_env_ranger()` range un `.env` créé par une version précédente.
2. **Mail** : un mot de passe d'application, et AIGORA peut lire tes mails et préparer des **brouillons** (il n'envoie jamais rien lui-même).
3. **Agenda, tâches, contacts** : un identifiant CalDAV court + mot de passe d'application. Les tâches
   créées par AIGORA arrivent sur ton téléphone via kSync.
4. **kDrive** : `aigora_kdrive()` relie le dossier synchronisé par l'application kDrive de bureau.
5. **kChat** : un webhook entrant pour recevoir les synthèses.
6. **Optionnel** : un jeton API et `aigora_mcp(simulation = FALSE)` pour les serveurs MCP officiels
   (Mail, Agenda, kDrive, kChat, Contacts), et en option un serveur communautaire pour kMeet, Chk et kPaste.

Le tableau de **tous les outils Infomaniak** (y compris Euria, SwissTransfer, Newsletter, kSync) et
leur branchement est dans [docs/KSUITE.md](docs/KSUITE.md).

> [!WARNING]
> Jamais le mot de passe principal de ton compte Infomaniak : uniquement des mots de passe
> d'application et des jetons, révocables à tout moment.

---

## RStudio et QGIS en direct (MCP)

- **Session R** : `aigora_installer_r_mcp()` puis `aigora_r_mcp(TRUE)`. AIGORA voit les objets chargés
  dans ta session RStudio et l'aide de tes paquets (paquet btw de Posit).
- **QGIS** : installe l'extension « QGIS MCP » dans QGIS et uv, puis `aigora_qgis_mcp(TRUE)`.
  AIGORA pilote ton projet QGIS : couches, traitements, styles, cartes.

- **QFieldCloud** (relevés terrain avec QField) : `aigora_qfieldcloud_installer()` puis
  `aigora_qfieldcloud_login()`. AIGORA récupère les données terrain pour QGIS ou R, envoie les
  projets et suit leur préparation. Guide : [docs/QFIELDCLOUD.md](docs/QFIELDCLOUD.md).

Détails, réglages et sécurité : [docs/RSTUDIO-QGIS.md](docs/RSTUDIO-QGIS.md).

---

## Connecteurs open source

Chaque service propriétaire de l'AIOS d'origine a été passé en revue. Les remplacements
(Quarto pour Gamma, Ollama + Qdrant pour OpenAI + Pinecone, SearXNG pour Perplexity,
Odoo CRM pour Airtable, Vikunja pour Todoist, etc.) sont décrits, avec leur statut, dans
[docs/CONNECTEURS-OPEN-SOURCE.md](docs/CONNECTEURS-OPEN-SOURCE.md).

---

## La mémoire

1. **Mémoire native** de Claude Code, chargée à chaque session.
2. **Journaux quotidiens** dans `memory/logs/` et l'index `memory/MEMORY.md`.
3. **Mémoire sémantique** (optionnelle) : mem0 + Ollama + Qdrant, **entièrement sur ton ordinateur**. Voir [docs/MEMORY-UPGRADE.md](docs/MEMORY-UPGRADE.md).

---

## En cas de souci

<details>
<summary><strong>« claude : commande introuvable » dans le terminal RStudio</strong></summary>

Claude Code n'est pas installé ou pas dans le PATH. Installe-le, puis **redémarre RStudio**
(le terminal ne voit le nouveau PATH qu'après redémarrage).
</details>

<details>
<summary><strong>Les hooks ne se déclenchent pas (Windows)</strong></summary>

Les hooks utilisent `python3`. Réinstalle Python en cochant « Add python.exe to PATH », ou
remplace les trois `python3` par `python` dans `.claude/settings.json`. Le reste fonctionne
même sans hooks.
</details>

<details>
<summary><strong>Connexion kSuite refusée</strong></summary>

`aigora_ksuite(test = TRUE)` indique ce qui bloque. Le plus fréquent : mot de passe principal au
lieu d'un mot de passe d'application, ou adresse mail utilisée à la place de l'identifiant
CalDAV court.
</details>

<details>
<summary><strong>Les outils MCP n'apparaissent pas</strong></summary>

Après `aigora_mcp(simulation = FALSE)`, quitte Claude Code (`/exit`) et relance `claude`.
Vérifie avec `claude mcp list`. Node.js doit être installé.
</details>

---

## Ce qui change par rapport à l'AIOS d'origine

- Nom : **AIGORA**. Environnement : **RStudio** (projet `.Rproj`, fonctions R d'aide) au lieu de VS Code.
- Google Workspace et Slack remplacés par **kSuite** : nouveau skill `ksuite-setup` (Mail, Agenda, tâches, Contacts, kDrive, kChat), `email-digest` réécrit (le modèle d'origine n'en contenait pas les scripts).
- Sécurité : l'envoi direct de mail par MCP est bloqué ; AIGORA ne fait que des brouillons.
- Todoist remplacé par le gestionnaire de tâches local ; Google Agenda par l'Agenda kSuite.
- `gamma-slides` remplacé par `quarto-slides`.
- `research-lead` : les appels Relevance AI, Perplexity, OpenAI, Airtable, Google Sheets et Slack sont supprimés. Claude fait l'analyse, les données vont dans `data/leads.csv`, la revue dans kChat.
- Mémoire avancée : OpenAI + Pinecone remplacés par Ollama + Qdrant locaux.
- Corrections : chemin de sortie du rapport `research-lead`, syntaxe `task_db.py` dans `scheduler`, emplacement de la configuration MCP.

---

## Structure du projet

```
aigora/
├── AIGORA.Rproj             # Le projet RStudio
├── .Rprofile              # Charge R/aigora.R à l'ouverture
├── R/aigora.R               # Fonctions d'aide R
├── CLAUDE.md              # Le noyau : instructions du système
├── .claude/
│   ├── skills/            # Les skills (dont ksuite-setup, quarto-slides)
│   ├── agents/            # Les 3 sous-assistants
│   ├── hooks/             # Les 3 garde-fous
│   └── rules/             # Règles chargées à chaque session
├── config/                # Préférences (langue, fuseau, outils)
├── context/               # Ton activité + ta voix
├── memory/                # MEMORY.md + journaux quotidiens
├── data/                  # Bases locales (tâches, prospects, mémoire)
└── docs/                  # Les guides (SETUP, KSUITE, CONNECTEURS-OPEN-SOURCE...)
```

---

## Origine et licence

AIGORA est dérivé de **AI OS, Édition Locale**, conçu par **Thomas Berton**
([Azuro AI](https://azuro-ai.com), [chaîne YouTube](https://youtube.com/@thomasbssh)),
distribué sous licence MIT. La licence d'origine et sa mention de copyright sont conservées
dans [LICENSE](LICENSE). Les modifications d'AIGORA sont distribuées sous la même licence MIT.
