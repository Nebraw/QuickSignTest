- [Test Technique : Data Engineer](#test-technique--data-engineer)
  - [Disclaimer !](#disclaimer-)
  - [Introduction](#introduction)
  - [Bonnes pratiques](#bonnes-pratiques)
  - [Objectif](#objectif)
  - [Contexte](#contexte)
  - [Objectifs](#objectifs)
    - [Collecte et stockage des données](#collecte-et-stockage-des-données)
    - [Exemples de sources d’images à utiliser](#exemples-de-sources-dimages-à-utiliser)
  - [| Scanned printed text     | Texte dactylographié, contenant le texte `Wikipedia`               | https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQvc9YzVQCGKRAu7LMZObym4YElk59PqVWlHg\&s |](#-scanned-printed-text------texte-dactylographié-contenant-le-texte-wikipedia----------------httpsencrypted-tbn0gstaticcomimagesqtbnand9gcqvc9yzvqcgkrau7lmzobym4yelk59pqvwlhgs-)
    - [Monitoring de la qualité des prédictions](#monitoring-de-la-qualité-des-prédictions)
  - [Exigences techniques](#exigences-techniques)
  - [Déroulement](#déroulement)
  - [Livrables](#livrables)
  - [Durée estimée](#durée-estimée)
  - [Exécution](#exécution)
    - [Ubuntu](#ubuntu)
  - [Analyse du rendu](#analyse-du-rendu)
  - [Bien démarrer](#bien-démarrer)

# Test Technique : Data Engineer

## Disclaimer !

Le test est conçu pour évaluer votre approche et votre capacité à résoudre des problèmes de manière pratique. Nous comprenons que le temps et les ressources sont limités, et il est normal de ne pas pouvoir compléter chaque partie du test. Ce qui nous intéresse avant tout, c'est votre raisonnement, la façon dont vous abordez les problèmes et les choix que vous faites pour résoudre les différentes étapes.

Nous ne recherchons pas de solution parfaite, ni à l'état de l'art, mais plutôt une solution fonctionnelle, claire et bien documentée. Il est important d’expliquer vos choix dans un fichier dédié ou directement dans les commentaires du code. Nous préférons un code simple, mais qui fonctionne, plutôt qu'un code plus complexe, mais difficile à exécuter.

N’hésitez pas à simplifier certaines parties du test si nécessaire (par exemple, gérer uniquement des fichiers spécifiques ou vous concentrer sur une approche plus rapide), mais veillez à bien documenter vos décisions.

Le téléchargement des poids peut prendre un certain temps. Lors de vos développements en local, nous vous conseillons de lancer le service hors d'un docker (par exemple `poetry run python -m app.main`). Une autre solution plus pérenne, serait de télécharger les modèles dans un dossier tampon, type `.models`, et de monter ce dossier dans le DockerFile. 

Bonne chance, et surtout, amusez-vous avec ce test !

## Introduction

Chez QuickSign, nous traitons des dizaines de milliers de documents tous les mois. L'équipe Document Recognition (DocReco) a pour rôle de créer des algorithmes permettant de classifier et de lire ces documents. Ces différents algorithmes sont ensuite appelés via une API.

L'ensemble de nos librairies et nos services sont développés avec l'outil [poetry](https://python-poetry.org/). Cela nous permet de les versionner, de développer plusieurs services / librairies sur la même machine en utilisant des environnements virtuels et de gérer les dépendances de nos services / librairies en fixant les versions des packages dont ils dépendent.

## Bonnes pratiques

L'utilisation de poetry est primordiale et nous permet de tester le code reçu en quelques lignes. Un environnement à jour est indispensable afin de nous permettre de tester le code.

Certaines conventions sur le code sont établies au sein de notre équipe. Nous appliquons `ruff` pour formater le code et respecter les normes définies. Nous attendons la même rigueur pour votre rendu. Nous utilisons également `mypy` pour la gestion du typage.

Le script `lint_module.sh` permet d'automatiser l'application de ces outils.

Nous accordons par ailleurs une forte importance à la réalisation de tests unitaires, et au coverage de ceux-ci. Pour les lancer et avoir un rapport de coverage, utilisez le script `run_tests.sh`

Nous vous conseillons, avant même de poursuivre, de nous assurer que vous avez sur votre machine :

- [poetry](https://python-poetry.org/)
- [docker](https://docs.docker.com/engine/install/)

et que vous êtes en capacité de lancer les commandes dont vous aurez besoin tout au long du test

```
poetry install
./lint_module.sh
./run_tests.sh
docker-compose up --build
```

---

## Objectif

Ce test technique vise à évaluer votre capacité à :

- Créer une pipeline d'ingestion de données complète.
  - Récupération depuis une URL,
  - Stockage de la donnée, de manière sécurisée,
  - Indexation de la donnée dans une base de donnée,
- Assurer la qualité de votre code via des tests et de la documentation.
- Maintenir la conteneurisation de la solution à l'aide de Docker.

---

## Contexte

Les data scientists sont en charge d’une API FastAPI qui expose un modèle d'océrisation à partir d'une image d'une ligne de texte. Le modèle actuellement en production est jugé **très peu performant** d'un point de vue produit. 
Votre mission est de mettre en place une **pipeline de collecte de données** pour permettre aux data scientists d’entraîner un nouveau modèle, tout en assurant un **monitoring de la qualité des prédictions** afin d'avoir des chiffres pour nourir les discussions avec les équipes produit.

En résumé :
- L’API FastAPI est déjà en place et retourne des prédictions de texte à partir d’une image d'une ligne de texte.
- Le modèle utilisé est un modèle pré-entraîné, mais ses performances sont jugées mauvaises.
- Vous ne disposez d’aucune donnée d’entraînement pour le moment.
- Vous devez trouver des données (annotées ou non) et les stocker pour qu'elles puissent être annotées et utilisées par les data scientists pour ré-entraîner un modèle.
- Vous avez accès à :
  - **MinIO** (compatible S3) pour stocker les images
  - **MongoDB** pour stocker les métadonnées et les résultats
  - **Prometheus** et **Grafana** pour le monitoring

---

## Objectifs

### Collecte et stockage des données

Mettre en place une **pipeline de collecte de données** à partir des requêtes reçues par l’API :

- Télécharger l’image à partir d’une **URL**
- Sauvegarder l’image dans **MinIO**
- Sauvegarder les métadonnées associées dans **MongoDB** :
  - Le timestamp
  - L'annotation si disponible
  - La prédiction du modèle associée à l'image
  - Le chemin de l’image dans MinIO
  - l'URL source de l’image pour des raisons réglementaires

### Exemples de sources d’images à utiliser

| Source                     | Description                        | Exemple d’URL                                                                 |
|----------------------------|------------------------------------|-------------------------------------------------------------------------------|
| IAM Handwriting Database | Écriture manuscrite réelle, contenant le texte `industrie`        | https://fki.tic.heia-fr.ch/static/img/a01-122-02-00.jpg                      |
| Scanned printed text     | Texte dactylographié, contenant le texte `Wikipedia`               | https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQvc9YzVQCGKRAu7LMZObym4YElk59PqVWlHg&s |
---

---

### Monitoring de la qualité des prédictions

Des exemples de dashboards sont disponibles sur le port 9004.


Mettre en place un système de **métriques Prometheus** exposées par l’API :

- Score moyen des prédictions
- Nombre de prédictions par minute
- Nombre de scores < seuil (ex: 0.5)

Créer un **dashboard Grafana** avec au moins :

- Un graphique de l’évolution du score moyen dans le temps
- Une alerte si le score moyen passe sous un seuil critique

---

## Exigences techniques

- Utiliser le service FastAPI et y ajouter des métriques.
- Utiliser Docker pour conteneuriser votre application.
- Vous pouvez utiliser n'importe quelle librairie mais votre `pyproject.toml` doit être à jour et fonctionnel sur un système linux (debian / ubuntu).
- Implémenter des tests.
- Implémenter les fichier de configuration de Grafana et Prometheus

---


## Déroulement

1. **Récupération de la donnée** : Utilisez un ou plusieurs jeux de données publics ou générez-les si nécessaire.
2. **Ingestion de la donnée** : Implémentez un système qui permet d'ingérer de la donnée en batch à partir d'une URL. L'implémentation de ce système est laissé libre, ça peut être implémenté directement dans le service donné, dans un autre service ou tout autre moyen, tant qu'il utilise le service pour récupérer les prédictions du modèle.
3. **Mise en place des métriques** : Implémentez les métriques et le(s) dashboard(s) associé(s).
4. **Conteneurisation** : Modifiez le Dockerfile si nécessaire pour inclure vos dépendances. Vérifiez que le service fonctionne avec `docker compose up --build`.
5. **Testing** : Vérifier que tout est fonctionnel à l'aide de tests.

---

## Livrables

Un dossier contenant :

- Votre code source dans le dossier `app/`.
- Le nécéssaire pour générer un environnement virtuel faisant tourner l'application à l'aide de poetry.
- Vos fichiers de configuration Docker.
- Des tests unitaires vérifiant les fonctionnalités de votre API.

---

## Durée estimée

Le test ne devrait pas prendre plus d'une demi-journée.

## Exécution

### Ubuntu

Ce setup a été pensé pour une machine GNU/Linux (Ubuntu par exemple). Si vous n'avez pas accès directement à cet OS, nous vous conseillons d'utiliser une VM ou Docker.

Les fichiers `Dockerfile` et `docker-compose.yml` permettent de lancer :

- le web service sur le port `8080`
- le grafana sur port `3000`
- le prometheus sur port `9000`
- le mongo sur le port `27017`
- le minio :
  - API sur le port `9002`
  - console sur le port `9003`

via la commande :

```
docker compose up --build
```

## Analyse du rendu

Nous accorderons beaucoup d'importance aux respects des consignes et à la méthodologie scientifique, assez peu, voire aucune importance aux résultats statistiques.

Tout rendu doit impérativement permettre l'exécution des quatre actions suivantes sans erreur.

```
poetry install
./lint_module.sh
./run_tests.sh
docker-compose up --build
```

## Bien démarrer

Pour commencer, nous vous conseillons de lancer les services tels quel, afin de vous familiariser avec ceux ci. 
* Connectez vous à grafana
  * login et mot de passe par défaut : `admin`/`admin` puis
  * Configurez les Connections à prometheus (`Connections` -> `Add new connection` -> `prometheus` -> `Add new data source` et mettre l'adresse du serveur `http://prometheus:9090`)
  * Créez ensuite votre premier dashboard : `Dashboards` -> `Create Dashboards` -> `Import Dashboard` -> vous pouvez utiliser le grafana ID `193` pour ajouter [ce dashboard](https://grafana.com/grafana/dashboards/193-docker-monitoring/)). Vous aurez là des informations de base de vos services (CPU, mémoire, réseau)
  * A noter que pour le rendu final, la connexion Grafana/Prometheus et les dashboards Grafana devront être dans des fichiers de configuration
* Connectez vous à minio
  * login et mot de passe par défaut : `minioadmin`/`minioadmin`
* Connectez vous à la mongoDB en utilisant par exemple [mongodb compass](https://www.mongodb.com/products/tools/compass), en utilisant l'adresse `mongodb://localhost:27017/`