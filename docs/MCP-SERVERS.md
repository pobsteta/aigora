# Serveurs MCP

Les serveurs MCP (Model Context Protocol) donnent à Claude Code des outils pour agir sur
des services externes. AIGORA fonctionne sans aucun serveur MCP : ce sont des options.

## Comment les ajouter (bonne méthode)

Avec la commande `claude mcp add`, en portée **local** (propre à ce projet, stockée dans
ta configuration utilisateur, jamais dans un fichier partagé) :

```bash
claude mcp add-json --scope local <nom> '{"type":"stdio","command":"npx","args":["-y","<paquet>"],"env":{"CLE":"valeur"}}'
# Windows natif : "command":"cmd","args":["/c","npx","-y","<paquet>"]
claude mcp list        # vérifier
claude mcp remove --scope local <nom>
```

Pour kSuite, inutile de taper ces commandes : `aigora_mcp(simulation = FALSE)` dans la console R
(ou `register_mcp.py`) les génère à partir de `.env`. Après tout ajout, redémarre Claude Code
(`/exit` puis `claude`).

> Le modèle d'origine indiquait de mettre les serveurs dans `.claude/settings.local.json` :
> Claude Code ne lit pas les serveurs MCP à cet endroit. Utilise `claude mcp add` (ou un
> fichier `.mcp.json` sans secret si tu veux partager une configuration d'équipe).

## Serveurs recommandés

### kSuite (officiels Infomaniak, licence MIT) : voir `docs/KSUITE.md`

| Nom AIGORA | Paquet | Variables |
|---|---|---|
| `ksuite-mail` | `@infomaniak/mcp-server-mail` | `MAIL_TOKEN` |
| `ksuite-calendar` | `@infomaniak/mcp-server-calendar` | `CALENDAR_TOKEN` |
| `ksuite-kdrive` | `@infomaniak/mcp-server-kdrive` | `KDRIVE_TOKEN`, `KDRIVE_ID` |
| `ksuite-kchat` | `@infomaniak/mcp-server-kchat` | `KCHAT_TOKEN`, `KCHAT_TEAM_NAME` |
| `ksuite-contact` | `@infomaniak/mcp-server-contact` (lecture seule) | `CONTACT_TOKEN` |
| `ksuite-extra` *(communautaire, opt-in)* | `@henrikogard/infomaniak-mcp`, filtré sur kMeet, Chk, kPaste, tâches | `INFOMANIAK_TOKEN`, `DAV_USER`, `DAV_PASSWORD` |

### Applications locales : voir `docs/RSTUDIO-QGIS.md`

| Nom AIGORA | Projet | Activer |
|---|---|---|
| `r-session` | btw + mcptools (Posit, CRAN) : session R en direct | `aigora_r_mcp(TRUE)` |
| `qgis` | qgis-mcp v0.15.0 (serveur MIT, extension GPL-2) | `aigora_qgis_mcp(TRUE)` |

### Open source (optionnels) : voir `docs/CONNECTEURS-OPEN-SOURCE.md`

| Usage | Serveur | Remarque |
|---|---|---|
| Recherche web | `mcp-searxng` | nécessite une instance SearXNG (`SEARXNG_URL`) |
| Mémoire vectorielle | `mcp-server-qdrant` (officiel Qdrant) | utile seulement avec la mémoire avancée |
| Fichiers locaux avancés | `@modelcontextprotocol/server-filesystem` | officiel, MIT |

## Budget de contexte

Chaque serveur ajoute des milliers de jetons de description d'outils à chaque échange.
N'active que ceux que tu utilises vraiment. Pour une opération répétitive et toujours
identique, un script Python (comme ceux de `ksuite-setup`) est plus économique.

| Utiliser un serveur MCP quand... | Utiliser un script quand... |
|---|---|
| Claude doit choisir quoi chercher | La requête est toujours la même |
| Exploration interactive | Traitement par lots |
| Opérations ponctuelles | Opérations fréquentes ou planifiées |
