# Sira-Assets AI — Copilote agentique de gestion des immobilisations

> Projet présenté pour le poste de **Fixed Assets & Data Analytics Officer — Ecobank Cameroun**
> Auteur : Romuald Arthur MBANA MEDJO

Sira-Assets AI est une application web (Streamlit) qui assiste la gestion du registre des immobilisations d'une banque : rapprochement d'inventaire, calcul des amortissements et de la VNC, interrogation en français courant, arbitrage CapEx/OpEx et génération des rapports de comité. Elle s'appuie sur **trois agents spécialisés pilotés par un superviseur** (LangGraph) et sur un LLM Llama servi par Groq.

La charte graphique est tirée du logo Ecobank : bleu profond `#095B81`, vert lime du swoosh `#A6CE39`, blanc glacé `#E6FFFF`, titres en italique arrondi comme le logotype. Le logo figure dans le slider d'accueil, le bandeau défilant, la barre latérale et l'en-tête du PDF.

---

## 1. Contexte et problème

Le suivi des actifs fixes repose aujourd'hui sur des extractions du PGI et un réseau de fichiers Excel : saisies manuelles, inventaires physiques annuels ou semestriels, rapprochements avec les comptes de classe 2 faits à la main, tableaux d'amortissement fragiles.

| Axe | Dysfonctionnement | Conséquence |
|---|---|---|
| Fiabilité | Saisies répétées, doublons, fautes de frappe | VNC faussée |
| Rapprochement | Pointage manuel terrain / comptable | Plusieurs semaines de délai |
| Budget | Pas d'anticipation du renouvellement | CapEx mal planifié, OpEx imprévu |
| Gouvernance | Tableaux statiques, peu de traçabilité | Clôtures tardives, audits complexes |

## 2. Ce que fait l'application

| Module | Contenu |
|---|---|
| **Accueil** | Slider de messages (avec logo), avantages de l'agent IA, comparatif avant/après |
| **Tableau de bord** | KPI (actifs, coût, VNC, dotation), filtres zone / catégorie / vétusté, graphiques interactifs |
| **Matching & Rapprochement** | Chargement CSV/Excel, rapprochement flou, statuts *Match Parfait*, *Match Probable (à valider)*, *Écart Majeur* |
| **CapEx / OpEx** | Seuil réglable, nuage OpEx vs VNC, budget de renouvellement, simulateur d'acquisition |
| **Copilote IA** | Questions en français, SQL généré visible, résultat en tableau |
| **Rapports** | PDF institutionnel et Excel multi-feuilles |
| **Paramètres** | Date d'arrêté, recalcul des VNC, réinitialisation de la démo |

Un **bandeau défilant** (logo + alertes calculées sur les données réelles de la base) reste affiché en haut de chaque page.

### Les avantages de l'agent IA
1. **Matching d'inventaire intelligent** : résolution d'entités et correspondance floue ; objectif de précision supérieur à 95 %.
2. **Requêtes en langage naturel** : la direction financière et les auditeurs interrogent la base en français.
3. **Optimisation CapEx/OpEx** : recommandation de renouvellement quand l'OpEx cumulé dépasse un seuil.
4. **Gain de productivité** : objectif de plus de 50 % de temps gagné sur les rapprochements.
5. **Conformité renforcée** : logique IFRS / IAS 16, traçabilité adaptée aux exigences COBAC.

> Les chiffres « > 95 % » et « > 50 % » sont les **objectifs du dossier de cadrage**, pas des résultats mesurés sur des données Ecobank. Sur les données de démonstration, le test interne donne environ 98 % d'appariement automatique, mais le jeu est synthétique et plus propre qu'un vrai comptage.

## 3. Architecture

```
                  ┌────────────────────────┐
                  │   AGENT SUPERVISEUR    │  routage par intention (LangGraph)
                  └───────────┬────────────┘
      ┌───────────────┬───────┴────────┬──────────────────┐
      ▼               ▼                ▼                  ▼
 Audit & Matching  Analyse financière  Données (SQL)   Maintenance prédictive
 core/matching.py  core/finance.py     core/agents.py   core/maintenance.py
```

| Couche | Technologie |
|---|---|
| Interface | Streamlit + composants HTML/CSS/JS (slider, ticker) |
| Inférence | Groq Cloud API |
| Modèle | Llama 3.x (`llama-3.3-70b-versatile` par défaut) |
| Orchestration | LangGraph (repli en dispatch direct si indisponible) |
| Données | SQLite (PostgreSQL possible, voir perspectives) |
| Rapprochement | RapidFuzz (`token_set_ratio`) |
| Rapports | ReportLab (PDF), openpyxl (Excel) |
| Déploiement | Docker / Docker Compose |

### Les agents
- **Superviseur** : classe la question (maintenance, audit, finance, données) et oriente vers le bon agent.
- **Audit & Matching** : apparie chaque ligne terrain au registre. Ordre de décision : n° de série exact (score 100), sinon similarité du libellé dans la même agence, puis dans tout le registre. Détecte localisation différente, n° de série manquant, doublon d'appariement, et actifs du registre absents du terrain.
- **Analyse financière** : amortissement linéaire ou dégressif (coefficients 1,25 / 1,75 / 2,25 selon la durée, bascule en linéaire quand il devient plus favorable), calcul mensuel, VNC, dotation de l'exercice, simulation d'acquisition.
- **Maintenance prédictive** : ratio `OpEx cumulé / VNC` (ou / coût d'origine). Au-dessus du seuil : *Remplacer (CapEx)* avec budget estimé indexé de 3 %/an ; à partir de 70 % du seuil ou 85 % de la durée de vie : *Surveiller*.

### Sécurité du Text-to-SQL
Le SQL produit par le LLM est limité à un `SELECT` unique, filtré contre les mots-clés d'écriture, et exécuté sur une **connexion SQLite en lecture seule**. Sans clé Groq, un moteur de règles (catégorie, zone, agence, indicateur) prend le relais.

## 4. Installation

Prérequis : Python 3.10+, ou Docker 20.10+ avec Compose v2. Une clé Groq est optionnelle (l'application fonctionne en mode hors-ligne, avec un copilote limité aux règles).

```bash
unzip sira-assets-ai.zip && cd sira-assets-ai
cp .env.example .env          # puis renseigner GROQ_API_KEY
```

**Docker (recommandé)**
```bash
docker compose up --build -d
docker compose ps
docker compose logs -f sira-assets-container
```
**Local**
```bash
python -m venv venv && source venv/bin/activate    # Windows : venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```
Ouvrir http://localhost:8501. Au premier lancement, 320 actifs et leurs tickets de maintenance fictifs sont générés dans `data/sira_assets.db`.

> **Modèle Groq** : le dossier cite `llama-3.2-90b-text-preview`, modèle retiré par Groq. Le fichier `.env.example` pointe vers un modèle actif ; vérifier la liste des modèles disponibles sur la console Groq si besoin.

## 5. Utilisation

1. **Copilote IA** — exemples : « Total des amortissements des serveurs de la zone Ouest », « Quels véhicules ont des réparations supérieures à 60 % de leur valeur d'origine ? », « VNC par catégorie ».
2. **Matching** — charger `data/exemple_inventaire_terrain.csv` (ou son propre fichier), ajuster les seuils, lancer, filtrer les cas à valider, exporter en CSV.
3. **CapEx / OpEx** — régler le seuil, lire le budget de renouvellement, simuler un achat.
4. **Rapports** — « Générer le Rapport Synthétique » puis télécharger PDF et Excel.
5. **Données réelles** — remplacer le seeding de `core/db.py` par un import du PGI dans les tables `actifs` et `maintenance` (colonnes listées dans `core/agents.py`, constante `SCHEMA`), puis « Recalculer VNC » dans Paramètres.

## 6. Structure du projet

```
app.py                  interface Streamlit
core/db.py              base SQLite, données de démo
core/finance.py         amortissements, VNC, simulation
core/matching.py        rapprochement flou
core/maintenance.py     arbitrage CapEx/OpEx
core/agents.py          superviseur + agents (LangGraph), Text-to-SQL
core/llm.py             client Groq
core/reports.py         PDF et Excel
core/ui.py              charte Ecobank, slider, ticker, avantages
assets/logo.jpg         logo Ecobank
tests/                  tests pytest (python -m pytest tests)
Dockerfile, docker-compose.yml, requirements.txt, .env.example
```

## 7. Limites

- **Données fictives** : les actifs, tickets et chiffres de démonstration sont générés aléatoirement. Aucune connexion au PGI Ecobank n'est incluse.
- **Pas de vectorisation** : le dossier prévoit ChromaDB pour indexer fiches techniques et procès-verbaux. Cette version utilise un rapprochement lexical (RapidFuzz) ; la recherche sémantique sur documents n'est pas implémentée.
- **Précision non validée** : le seuil > 95 % et le gain > 50 % restent des objectifs à mesurer sur de vrais comptages.
- **Amortissement simplifié** : base mensuelle, valeur résiduelle nulle par défaut, pas de composants, de réévaluation, de dépréciation (IAS 36), de cessions ni de prorata au jour. Un expert-comptable doit valider les règles avant usage officiel.
- **Données hors Cameroun** : le LLM reçoit des questions et des extraits de résultats via l'API Groq (cloud). Pour des données bancaires sensibles, cela impose une validation sécurité/conformité, ou un LLM auto-hébergé.
- **Text-to-SQL** : fiable sur les requêtes simples ; le LLM peut produire un SQL erroné. Le SQL est affiché pour contrôle, jamais exécuté en écriture.
- **Pas d'authentification** ni de rôles : à ajouter avant tout déploiement partagé. Les actions de la session (validation d'un « Match Probable ») ne sont pas persistées.
- **Rapprochement** : les libellés très divergents ou sans n° de série peuvent produire des faux négatifs ; la validation humaine reste nécessaire.
- **Seuil CapEx/OpEx** : règle à seuil unique, sans modèle statistique de panne.

## 8. Perspectives

1. Connecteur PGI / ERP (lecture planifiée) et migration vers **PostgreSQL**.
2. **ChromaDB** + embeddings pour rechercher dans fiches techniques et PV d'inventaire.
3. Application mobile de **scan code-barres / QR** pour l'inventaire terrain, avec photos.
4. Workflow de **validation** des matchs probables, avec journal d'audit horodaté (qui, quoi, quand).
5. **Authentification SSO**, rôles (comptable, auditeur, direction) et chiffrement.
6. Maintenance prédictive par **modèles de survie / gradient boosting** sur l'historique de pannes.
7. Écritures comptables automatiques d'amortissement, **IAS 36**, composants, cessions.
8. **LLM auto-hébergé** (vLLM/Ollama) pour garder les données dans le SI de la banque.
9. Multi-pays CEMAC, multi-devises, consolidation groupe.
10. Alertes proactives (e-mail / Teams) et évaluation continue de la précision du matching.

## 9. Tests

```bash
python -m pytest tests
```
Couvrent le moteur d'amortissement, la chaîne rapprochement → maintenance → copilote et le garde-fou SQL.
