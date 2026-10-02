# Mémoire avancée (niveau 3) : mem0 + Qdrant + Ollama, 100 % local

Par défaut, AIGORA se souvient grâce à deux couches qui ne demandent rien à installer :
la mémoire native de Claude Code et les journaux quotidiens (`memory/`).
Ce guide ajoute une troisième couche, optionnelle : une mémoire « sémantique » qui
extrait automatiquement les faits importants des conversations, supprime les doublons
et permet de retrouver une information par le sens plutôt que par mot-clé.

Le modèle d'origine utilisait OpenAI et Pinecone (deux services cloud américains
payants). AIGORA remplace les deux par des logiciels libres qui tournent sur ton
ordinateur : **rien ne sort de ta machine**.

| | Base (par défaut) | Niveau 3 AIGORA |
|---|---|---|
| Faits persistants | `MEMORY.md` (manuel) | Extraits automatiquement |
| Recherche | Lire le fichier | Recherche sémantique |
| Dédoublonnage | Manuel | Automatique (ADD / UPDATE / DELETE / NOOP) |
| Où sont les données | Fichiers locaux | Fichiers locaux (`data/qdrant/`) |
| Coût | 0 | 0 (ton processeur travaille un peu) |

## Composants

| Rôle | Logiciel | Licence |
|------|----------|---------|
| Moteur de mémoire | [mem0](https://github.com/mem0ai/mem0) | Apache 2.0 |
| Modèles (extraction + vecteurs) | [Ollama](https://ollama.com) avec `qwen3:4b` et `nomic-embed-text` | MIT / Apache 2.0 |
| Base vectorielle | [Qdrant](https://qdrant.tech) en mode embarqué (un dossier, pas de serveur) | Apache 2.0 |

## Installation (environ 15 minutes, surtout du téléchargement)

1. **Installer Ollama** depuis [ollama.com/download](https://ollama.com/download), puis dans le terminal de RStudio :
   ```bash
   ollama pull qwen3:4b
   ollama pull nomic-embed-text
   ```
   Il faut environ 4 Go de RAM libre. Sur une machine modeste, `qwen3:1.7b` fonctionne aussi
   (change alors `model` dans `.claude/skills/memory/references/mem0_config.yaml`).

2. **Installer les paquets Python** :
   ```bash
   pip install mem0ai qdrant-client ollama pyyaml python-dotenv
   ```

3. **Choisir ton identifiant** dans `.env` : `MEM0_USER_ID=ton_prenom`

4. **Activer la capture automatique** : crée (ou complète) `.claude/settings.local.json` :
   ```json
   {
     "hooks": {
       "Stop": [
         {
           "matcher": "",
           "hooks": [
             {
               "type": "command",
               "command": "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/skills/memory/scripts/auto_capture.py",
               "timeout": 120,
               "async": true
             }
           ]
         }
       ]
     }
   }
   ```

5. **Initialiser l'index de recherche** :
   ```bash
   python3 .claude/skills/memory/scripts/smart_search.py --rebuild-index
   ```

Ou plus simplement, dis à AIGORA : *« Active la mémoire avancée »*, il te guidera étape par étape.

## Variante : Infomaniak AI Tools

Si ton ordinateur est trop lent pour Ollama, tu peux confier l'extraction à
[Infomaniak AI Tools](https://www.infomaniak.com/fr/hebergement/ai-tools) : des modèles
open source (Qwen, Mistral, Llama…) hébergés en Suisse, avec une API compatible OpenAI.
Le bloc à décommenter est en bas de `mem0_config.yaml`. Il faut alors dans `.env` :

```bash
INFOMANIAK_AI_TOKEN=...          # jeton avec le scope "ai-tools"
INFOMANIAK_AI_BASE_URL=https://api.infomaniak.com/2/ai/<PRODUCT_ID>/openai/v1
```

Dans ce cas, des extraits de conversation partent chez Infomaniak (mais restent en Suisse).

## Utilisation

```bash
# Recherche (hybride mots-clés + sens, recommandée)
python3 .claude/skills/memory/scripts/smart_search.py --query "outils préférés" --limit 5
# Ajouter un fait à la main
python3 .claude/skills/memory/scripts/mem0_add.py --content "Préfère kSuite à Google Workspace"
# Lister / supprimer
python3 .claude/skills/memory/scripts/mem0_list.py --limit 50
python3 .claude/skills/memory/scripts/mem0_delete.py --memory-id "abc123"
# Journal du jour
python3 .claude/skills/memory/scripts/daily_log.py --content "Mémoire avancée activée" --type event
```

## Sauvegarde

Tout est dans `data/` (`qdrant/`, `mem0_history.db`) et `memory/`. Copier ces dossiers
(par exemple sur kDrive) suffit à sauvegarder la mémoire.
