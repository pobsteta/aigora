# QFieldCloud avec AIGORA

[QFieldCloud](https://github.com/opengisch/QFieldCloud) (licence MIT, éditeur OPENGIS.ch)
synchronise tes projets QGIS avec l'application de terrain **QField** : tu prépares le projet
dans QGIS, les équipes saisissent sur tablette ou téléphone, les données reviennent au bureau.

Il n'existe pas (encore) de serveur MCP pour QFieldCloud. AIGORA s'y connecte par le **SDK et
la ligne de commande officiels** (`qfieldcloud-sdk`, MIT), à travers une enveloppe de sécurité
(skill `qfieldcloud`).

## Deux façons d'avoir QFieldCloud

| | Service hébergé | Ton propre serveur (auto-hébergé) |
|---|---|---|
| Adresse | app.qfield.cloud | ex. `https://qfield.ton-domaine.ch` |
| Mise en place | Créer un compte | Serveur Linux + Docker, nom de domaine, certificat SSL |
| Maintenance | Aucune | Mises à jour, sauvegardes, supervision à ta charge |
| Pour qui | La plupart des usages | Données qui doivent rester chez toi, gros volumes, équipe technique |

AIGORA fonctionne avec les deux : seule l'adresse change.

### Auto-hébergement : ce qu'il faut savoir

QFieldCloud ne s'installe pas sur ton poste de travail : c'est un **serveur** (application
Django, base PostgreSQL/PostGIS, stockage objet compatible S3, worker QGIS, Nginx), lancé avec
`docker compose`. Les mainteneurs indiquent que la base de données, le stockage objet et l'envoi
de mails doivent être des services gérés à part : un déploiement « tout dans un seul serveur »
n'est pas pris en charge par eux.

Une piste cohérente avec le reste d'AIGORA : un serveur (VPS ou Public Cloud) chez Infomaniak,
avec leur base de données et leur stockage objet. Vérifie les offres et la compatibilité S3
au moment de te lancer. C'est un projet d'infrastructure à part entière : AIGORA peut t'aider à
le préparer (fichier `.env`, `docker compose`, sauvegardes) si tu le décides.

Instructions officielles : [dépôt QFieldCloud](https://github.com/opengisch/QFieldCloud) et
[documentation d'auto-hébergement](https://docs.qfield.org/reference/qfieldcloud/self_hosted/).

## Connecter AIGORA

Dans la console R du projet :

```r
aigora_qfieldcloud_installer()   # une fois : installe le SDK Python
aigora_qfieldcloud_login()       # service hébergé
# ou, serveur à toi :
aigora_qfieldcloud_login("https://qfield.ton-domaine.ch/api/v1/")
aigora_qfieldcloud_projets()     # tes projets, en data.frame
```

La connexion te demande ton identifiant et ton mot de passe **dans RStudio** : le mot de passe
n'est ni enregistré ni transmis à AIGORA. Seul un **jeton** est gardé dans `.env`. Pour le révoquer,
demande à AIGORA une déconnexion (`logout`, avec confirmation).

## Ce que tu peux demander

- *« Quels sont mes projets QFieldCloud ? »*
- *« Récupère les relevés du projet Inventaire_arbres et ouvre-les dans QGIS »*
  (téléchargement dans `data/qfield/`, puis ajout de la couche via le connecteur QGIS)
- *« Charge les données terrain dans R et fais-moi un résumé par espèce »*
  (`sf::st_read()` sur le GeoPackage téléchargé)
- *« Envoie la nouvelle version du projet et prépare-la pour les tablettes »*
  (envoi des fichiers puis tâche `package`)
- *« Qui a accès au projet ? »*

## Sécurité

- Les commandes qui suppriment des données ou changent des droits d'accès (suppression de
  projet ou de fichiers, ajout ou retrait de collaborateurs, membres, équipes) sont **bloquées**
  tant qu'AIGORA n'a pas obtenu ton accord explicite.
- L'envoi de fichiers remplace la version en ligne pour toute l'équipe terrain : AIGORA te le
  dit avant.
- Les données terrain restent dans `data/qfield/` (exclu de git) ou dans ton dossier kDrive,
  jamais dans la mémoire d'AIGORA ni dans kChat.
- Pour préparer un projet complexe (couches hors ligne, pièces jointes), le plugin
  **QFieldSync** dans QGIS reste l'outil de référence ; AIGORA prend le relais pour le suivi,
  la récupération des données et l'analyse.

## Ce qui a été testé

L'enveloppe a été testée contre une imitation locale de l'API : connexion depuis R
(jeton enregistré, mot de passe non conservé), liste des projets et des fichiers, refus des
commandes sensibles sans confirmation, et détection des erreurs serveur. Le SDK officiel peut
en effet terminer « sans erreur » alors que le serveur a refusé l'opération : l'enveloppe le
détecte. Le test sur ton vrai compte reste à faire : `aigora_qfieldcloud_projets()`.

## Sources

- [QFieldCloud (GitHub, licence MIT)](https://github.com/opengisch/QFieldCloud)
- [SDK et CLI officiels](https://github.com/opengisch/qfieldcloud-sdk-python) et [référence de la CLI](https://opengisch.github.io/qfieldcloud-sdk-python/cli/)
- [Auto-hébergement QFieldCloud](https://docs.qfield.org/reference/qfieldcloud/self_hosted/)
