# Installation détaillée : AIGORA dans RStudio

Ce guide t'amène de zéro à un AIGORA fonctionnel dans RStudio. Pas de serveur, pas de
déploiement : tout tourne sur ton ordinateur. Compte une dizaine de minutes.

## 1. Prérequis (une seule fois)

| Outil | Pourquoi | Obligatoire |
|---|---|---|
| **R + RStudio** | L'environnement dans lequel tu travailles | oui |
| **Python 3.9+** | Les scripts internes et les garde-fous | oui |
| **Claude Code** | Le cerveau, connecté à ton abonnement Claude (Pro, Max, Team) | oui |
| **Node.js LTS** | Les serveurs MCP Infomaniak (Mail, Agenda, kDrive, kChat) | si tu veux les MCP |
| **Quarto** | Les présentations (déjà fourni avec RStudio) | pour `quarto-slides` |
| **Ollama** | La mémoire avancée 100 % locale | optionnel |

- Python : [python.org/downloads](https://www.python.org/downloads/). Sous Windows, coche **« Add python.exe to PATH »**.
- Claude Code : [docs.claude.com/en/docs/claude-code/setup](https://docs.claude.com/en/docs/claude-code/setup). Connecte-toi avec ton compte Claude ; **aucune clé API** n'est nécessaire.
- Node.js : [nodejs.org](https://nodejs.org) (version LTS).

## 2. Ouvrir le projet

1. Décompresse le dossier (par exemple dans `Documents/aigora`).
2. Dans RStudio : **File > Open Project…** et choisis `AIGORA.Rproj`.
3. La console affiche : *« AIGORA chargé. aigora_demarrer() pour lancer l'assistant… »*.

## 3. Vérifier

```r
aigora_verifier()
```

Un tableau indique ce qui est installé. Seuls Python et Claude Code sont indispensables.

## 4. Lancer AIGORA

```r
aigora_demarrer()
```

Un onglet **Terminal « AIGORA »** s'ouvre et lance `claude`. Tu peux aussi le faire à la main :
onglet **Terminal** (Alt+Maj+R), puis `claude`. Claude Code charge automatiquement `CLAUDE.md` :
tu parles à AIGORA.

Astuce de mise en page : *Tools > Global Options > Pane Layout* pour placer le terminal à côté
de ton script, et garder la console R visible.

## 5. Personnaliser

Dans le terminal AIGORA, écris : `Configure mon business`. L'assistant `business-setup` pose
quelques questions et remplit `context/my-business.md`, `context/my-voice.md` et
`config/preferences.yaml`.

## 6. Connecter kSuite (optionnel)

Écris `Connecte kSuite`, ou suis `docs/KSUITE.md`. En résumé : `aigora_env()` pour créer
`.env`, des mots de passe d'application pour le Mail et l'Agenda, un webhook kChat, et
éventuellement un jeton API pour les serveurs MCP (`aigora_mcp(simulation = FALSE)`).

## Windows : les garde-fous (hooks)

Les trois hooks sont appelés avec `python3`. Sous Windows, si `python3` ouvre le
Microsoft Store ou n'existe pas :
- réinstalle Python depuis python.org en cochant « Add python.exe to PATH » (le lanceur `py` est installé), **ou**
- ouvre `.claude/settings.json` et remplace les trois `python3` par `python`.

Le reste fonctionne même sans hooks, mais ils sont recommandés.

Dans le terminal RStudio sous Windows, choisis de préférence **Git Bash** ou **PowerShell**
(*Tools > Global Options > Terminal > New terminals open with*).

## Où sont les choses

| Dossier | Contenu |
|---|---|
| `R/aigora.R` | Fonctions d'aide R (`aigora_verifier()`, `aigora_demarrer()`...) |
| `.claude/skills/` | Les skills (programmes) |
| `.claude/agents/` | Les sous-assistants |
| `.claude/hooks/` | Les garde-fous |
| `.claude/rules/` | Les règles chargées à chaque session |
| `config/preferences.yaml` | Langue, fuseau, outils |
| `context/` | Ton business et ta voix |
| `memory/` | `MEMORY.md` et journaux quotidiens |
| `data/` | Bases locales (tâches, prospects, mémoire) |
| `docs/` | Ces guides |

Ferme RStudio : tes données restent dans le dossier. Rouvre le projet : tu reprends où tu en étais.
