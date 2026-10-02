# Odoo CRM avec AIGORA

AIGORA range tes prospects dans **Odoo CRM** : le skill `research-lead` prépare le dossier,
tu le valides, et AIGORA crée l'**opportunité** dans ton pipeline (contact, entreprise,
fonction, LinkedIn, résumé, accroche, premier message proposé, score). Il peut aussi afficher
le pipeline, retrouver un prospect, changer l'étape et ajouter une note.

## Quelle installation d'Odoo ?

| | Odoo Community auto-hébergé | Odoo Online (odoo.com) |
|---|---|---|
| Licence | LGPL-3, open source, CRM inclus | Édition Enterprise, propriétaire |
| Coût | Gratuit, mais une machine à faire tourner | Abonnement ; l'accès à l'API externe peut exiger une offre précise (à vérifier avant) |
| Où | Ton ordinateur (Docker) ou un serveur (par ex. VPS Infomaniak) | Chez Odoo SA |

AIGORA fonctionne avec les deux. Il utilise l'API officielle : **JSON-2** pour Odoo 19 et plus,
**XML-RPC** pour les versions précédentes (dépréciée depuis la 19, suppression annoncée en 22).
Le choix est automatique.

### Essayer Odoo Community en local (Docker)

```yaml
# docker-compose.yml
services:
  db:
    image: postgres:16
    environment: { POSTGRES_USER: odoo, POSTGRES_PASSWORD: odoo, POSTGRES_DB: postgres }
    volumes: [odoo-db:/var/lib/postgresql/data]
  odoo:
    image: odoo:19
    depends_on: [db]
    ports: ["8069:8069"]
    environment: { HOST: db, USER: odoo, PASSWORD: odoo }
    volumes: [odoo-data:/var/lib/odoo]
volumes: { odoo-db: {}, odoo-data: {} }
```

`docker compose up -d`, puis http://localhost:8069 : crée une base, installe l'application
**CRM**. Pour un usage durable (sauvegardes, accès depuis l'extérieur), un serveur est préférable.

## Connecter AIGORA

1. **Crée une clé API** dans Odoo : clique sur ton avatar (en haut à droite) > **Mon profil** /
   **Préférences** > onglet **Sécurité du compte** > **Nouvelle clé API**. Donne-lui un nom
   (« AIGORA ») et copie-la : elle ne sera plus affichée.
2. Dans la console R :
   ```r
   aigora_odoo_configurer()
   ```
   Il te demande l'adresse (ex. `http://localhost:8069` ou `https://monentreprise.odoo.com`),
   le nom de la base, ton identifiant (souvent ton e-mail) et la clé API (saisie masquée),
   puis teste la connexion et affiche les étapes de ton pipeline.
3. Vérifier à tout moment : `aigora_odoo_pipeline()` (data.frame des opportunités).

## Ce que tu peux demander

- *« Montre-moi mon pipeline Odoo »*, *« Qu'est-ce qui est en Proposition ? »*
- après une recherche de prospect : *« Crée l'opportunité dans Odoo, étape Qualifié »*
- *« Passe l'opportunité Géo-Conseil en Proposition »*, *« Ajoute une note : relancé le 6 »*

## Sécurité

- Toute écriture (création, changement d'étape, note) est d'abord **présentée** ; rien n'est
  écrit dans Odoo sans ton « oui ».
- Les doublons probables (même e-mail, ou même contact + entreprise) sont **refusés** et affichés.
- AIGORA ne supprime rien et ne touche ni aux devis, ni aux factures, ni aux fiches partenaires.
- La clé API reste dans `.env` (ignoré par git). Tu peux la révoquer dans Odoo à tout moment.

## Ce qui a été testé

Le connecteur a été testé contre une simulation d'Odoo reproduisant le contrôle d'arguments
réel de l'API JSON-2 (lu dans le code source d'Odoo 19) et l'API XML-RPC (mode « Odoo 18 ») :
statut, étapes, pipeline, recherche, création avec étape et étiquettes, refus des doublons,
changement d'étape, note, erreurs de clé et de connexion. Le premier essai sur ton vrai Odoo
reste à faire : `aigora_odoo_configurer()`.

## Sources

- [Odoo 19 : API externe JSON-2](https://www.odoo.com/documentation/19.0/developer/reference/external_api.html)
- [JSON-2 et calendrier de retrait de XML-RPC](https://www.odin.ist/blog/odoo-json-2-api.html)
- [Odoo Community vs Enterprise](https://aidoo.ai/en/blog/odoo-community-vs-enterprise-comparatif-2026)
- [Image Docker officielle Odoo](https://hub.docker.com/_/odoo)
