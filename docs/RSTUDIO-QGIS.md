# Connecteurs MCP pour RStudio et QGIS

Deux serveurs MCP permettent à AIGORA de travailler **dans** tes applications, pas seulement
à côté :

| Serveur AIGORA | Ce qu'il permet | Projet | Licence |
|---|---|---|---|
| `r-session` | Voir ta session R ouverte dans RStudio : objets en mémoire (data frames, modèles), aide des paquets installés, infos de session, CRAN | [btw](https://posit-dev.github.io/btw/) et [mcptools](https://posit-dev.github.io/mcptools/) de Posit (sur CRAN) | MIT |
| `qgis` | Piloter QGIS : projet, couches, entités, sélection, édition, styles, traitements, rendu de cartes, mises en page | [qgis-mcp](https://github.com/nkarasiak/qgis-mcp) de Nicolas Karasiak, version figée 0.15.0 | serveur MIT, extension GPL-2 |

Les deux sont **optionnels** et s'activent depuis la console R.

## Pourquoi c'est utile

Sans ces serveurs, AIGORA ne voit que des fichiers. Quand il lance `Rscript` dans le terminal,
c'est une session R **vide et séparée** : il ne voit pas le data frame `ventes` que tu viens
de charger. Avec `r-session`, il peut te dire « `ventes` a 12 430 lignes et une colonne `date`
au format texte » avant d'écrire le code. Il lit aussi l'aide des paquets **dans la version
installée chez toi**.

Avec `qgis`, tu peux demander « fais un tampon de 500 m autour des écoles et compte les
parcelles dedans », « applique une symbologie graduée sur la population » ou « exporte une
carte A4 en PDF », et AIGORA le fait dans ton QGIS ouvert.

## 1. Session R (RStudio)

Dans la console R du projet AIGORA :

```r
aigora_installer_r_mcp()   # une fois : installe btw et mcptools depuis le CRAN
aigora_r_mcp(TRUE)         # active : .env + session visible + enregistrement dans Claude Code
```

Puis dans le terminal AIGORA : `/exit` et relance `claude`.

À chaque ouverture du projet, `.Rprofile` rend la session visible automatiquement
(message « Session R visible par AIGORA »). Pour désactiver : `aigora_r_mcp(FALSE)`.

### Ce qu'AIGORA peut faire, et ne pas faire

Par défaut, les groupes d'outils sont `docs, pkg, env, sessioninfo, cran` : **lecture seule**.
AIGORA regarde, mais ne modifie pas ta session. Tu peux ajouter le groupe `run`, qui exécute du
code R **dans ta session** (il peut alors modifier ou supprimer tes objets) :

```
AIGORA_R_MCP_TOOLS=docs,pkg,env,sessioninfo,cran,run
```

dans `.env`, puis `aigora_mcp(simulation = FALSE)`. À réserver aux moments où tu veux vraiment
qu'il agisse dans ta session ; Claude Code te demandera ton accord à chaque exécution.

## 2. QGIS

Prérequis : QGIS 3.28 ou plus récent, et [uv](https://docs.astral.sh/uv/getting-started/installation/)
(installe-le, puis redémarre RStudio).

1. **Dans QGIS** : *Extensions > Installer/Gérer les extensions*, cherche **QGIS MCP**, installe.
   Clique sur son bouton dans la barre d'outils pour démarrer le serveur (port 9876, accessible
   seulement depuis ton ordinateur).
2. **Dans la console R** : `aigora_qgis_mcp(TRUE)`
3. **Dans le terminal AIGORA** : `/exit` puis `claude`.
4. Test : demande à AIGORA *« Quelles couches sont ouvertes dans QGIS ? »*

Le premier lancement télécharge le serveur (quelques secondes). Ensuite tout reste local.

### Réglages

| Variable `.env` | Rôle | Défaut |
|---|---|---|
| `AIGORA_QGIS_TOOL_MODE` | `compound` : 27 outils groupés (consomme peu de contexte) ; `granular` : 125 outils détaillés | `compound` |
| `AIGORA_QGIS_PORT` | Port de l'extension QGIS | `9876` |
| `AIGORA_QGIS_TOKEN` | Secret partagé, utile sur un ordinateur partagé. Mettre la même valeur dans QGIS : *Préférences > Options > Système > Environnement*, variable `QGIS_MCP_TOKEN`, puis redémarrer QGIS | vide |

Après un changement : `aigora_mcp(simulation = FALSE)` puis redémarrer Claude Code.

### Sécurité

- Les modifications (édition d'entités, suppression de couches, sauvegarde du projet) et l'outil
  `code` (exécution de PyQGIS) passent par la demande d'autorisation de Claude Code. AIGORA doit
  t'expliquer ce qui va changer avant. Ne les autorise pas « pour toujours ».
- Avant une série de modifications, demande un point de restauration (checkpoint).
- AIGORA écrit ses résultats dans de nouvelles couches (GeoPackage), sans écraser tes données.

## Vérifier

```r
aigora_verifier()   # lignes « uv (uvx) » et « Paquet R btw »
aigora_ksuite()     # section mcp_registered : r-session, qgis
```

Ou dans le terminal : `claude mcp list`.

## Ce qui a été testé

- `qgis` : le serveur s'installe depuis la version figée, démarre et expose ses 27 outils
  (125 en mode détaillé) ; enregistrement dans Claude Code vérifié. La liaison avec l'extension
  dans un vrai QGIS reste à tester chez toi.
- `r-session` : configuration conforme à la documentation officielle de btw ; non exécuté dans
  l'environnement de préparation (CRAN inaccessible). À tester chez toi avec `aigora_r_mcp(TRUE)`.

## Sources

- [btw : serveur MCP pour R](https://posit-dev.github.io/btw/reference/mcp.html)
- [mcptools : R comme serveur MCP](https://posit-dev.github.io/mcptools/articles/server.html)
- [Annonce mcptools (Tidyverse)](https://tidyverse.org/blog/2025/07/mcptools-0-1-0/)
- [qgis-mcp (GitHub)](https://github.com/nkarasiak/qgis-mcp)
- [Extension QGIS MCP (dépôt officiel des extensions QGIS)](https://plugins.qgis.org/plugins/qgis_mcp_plugin/)
