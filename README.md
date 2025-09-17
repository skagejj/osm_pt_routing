# OSM PT Routing - Plugin QGIS

[![QGIS](https://img.shields.io/badge/QGIS-3.0+-green.svg)](https://qgis.org/)
[![License](https://img.shields.io/badge/License-GPL%20v2-blue.svg)](https://www.gnu.org/licenses/gpl-2.0.html)
[![Python](https://img.shields.io/badge/Python-3.x-yellow.svg)](https://python.org/)

Un plugin QGIS pour créer automatiquement les tracés des transports publics à partir de données OSM et de fichiers CSV contenant les séquences d'arrêts et leurs coordonnées.

## 📋 Description

**OSM PT Routing** est un plugin QGIS qui génère automatiquement les chemins des transports publics (bus, tram, train, funiculaire) en utilisant les données OpenStreetMap et des fichiers CSV contenant les informations sur les arrêts et leurs séquences.

Ce plugin est étroitement lié au plugin **OSMtocheck** et fonctionne avec les données préparées par celui-ci.

## ✨ Fonctionnalités

- 🚌 **Support multi-transports** : Bus, Tram, Train régional, Funiculaire
- 🗺️ **Routing intelligent** : Calcul automatique des plus courts chemins
- ⚡ **Performance optimisée** : Système de cache pour les graphes réseau
- 📊 **Format GTFS compatible** : Génération de fichiers compatibles GTFS
- 🔄 **Gestion des aller-retour** : Support des trajets bidirectionnels
- 📍 **Coordonnées précises** : Support EPSG:4326 (WGS84)

## 🚀 Installation

### Prérequis

- **QGIS** 3.0 ou version ultérieure
- **Plugin OSMtocheck** (doit être exécuté en premier)
- **Python 3.x** avec les modules :
  - pandas
  - PyQt5
  - qgis

### Installation du Plugin

1. **Télécharger le plugin** :
   ```bash
   git clone https://github.com/your-repo/osm_pt_routing.git
   ```

2. **Copier dans le répertoire des plugins QGIS** :
   ```bash
   # Linux
   cp -r osm_pt_routing ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/
   
   # Windows
   # Copier vers : C:\Users\[username]\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\
   ```

3. **Compiler les ressources** (si nécessaire) :
   ```bash
   cd osm_pt_routing
   make  # ou utiliser pb_tool
   ```

4. **Activer le plugin** :
   - Ouvrir QGIS
   - Aller dans `Extensions` → `Gestionnaire d'extensions`
   - Rechercher "OSM PT Routing"
   - Cocher la case pour activer le plugin

## 📖 Utilisation

### Workflow Complet

1. **Préparation des données** (avec OSMtocheck) :
   - Télécharger les données OSM
   - Préparer les fichiers CSV avec les arrêts
   - Générer les couches de réseau (routes, rails, etc.)

2. **Configuration du plugin** :
   - Ouvrir le plugin via `Extensions` → `OSM PT Routing`
   - Sélectionner le dossier de téléchargement (sortie d'OSMtocheck)
   - Sélectionner le dossier de sortie pour les résultats

3. **Exécution** :
   - Cliquer sur "OK" pour démarrer le processus
   - Attendre la fin du traitement (peut prendre du temps selon la taille des données)
   - Vérifier les résultats dans le dossier de sortie

### Structure des Données d'Entrée

Le plugin attend une structure spécifique dans le dossier de téléchargement :

```
download_folder/
├── OSM_data/
│   ├── full_city_roads.gpkg      # Réseau routier principal
│   ├── OSM_tram.gpkg             # Rails de tram
│   ├── OSM_Regtrain.gpkg         # Voies ferrées régionales
│   └── OSM_funicular.gpkg        # Funiculaires
├── temp/
│   └── temp_OSM_forrouting/
│       ├── [ligne1].gpkg         # Données par ligne de transport
│       ├── [ligne2].gpkg
│       └── ...
└── lines_trips.csv               # Fichier de correspondance lignes/trajets
```

### Format CSV Requis

Les fichiers CSV doivent contenir les colonnes suivantes :
- `line_name` : Nom de la ligne
- `trip` : Numéro du trajet (aller/retour)
- `pos` : Position de l'arrêt dans la séquence
- `GTFS_stop_id` : Identifiant GTFS de l'arrêt
- `lon`, `lat` : Coordonnées géographiques (EPSG:4326)

## 🔧 Optimisations de Performance

### Système de Cache des Graphes

Le plugin utilise un système de cache intelligent pour améliorer les performances :

- **Construction unique** : Les graphes réseau sont construits une seule fois
- **Réutilisation** : Le même graphe est utilisé pour tous les mini-trips du même type
- **Gains de performance** : 70-90% de réduction du temps de traitement

### Types de Réseaux Optimisés

- 🛣️ **Routes principales** : Stratégie de vitesse avec sens unique
- 🚋 **Tram** : Stratégie de distance
- 🚂 **Train régional** : Stratégie de distance
- 🚠 **Funiculaire** : Stratégie de distance

## 📁 Structure des Fichiers de Sortie

```
output_folder/
├── OSM4routing.gpkg              # Couche consolidée des mini-trips
├── OSM4routing.csv               # Données tabulaires des mini-trips
├── OSM4routing_XYminiTrips.csv   # Mini-trips avec coordonnées
├── mini_shapes.gpkg              # Formes consolidées des mini-trips
├── [ligne_trip1].gpkg            # Trajet complet par ligne
├── [ligne_trip1].csv
├── [ligne_trip2].gpkg
├── [ligne_trip2].csv
└── shapes/                       # Dossier des formes GTFS
```

## 🛠️ Développement

### Structure du Code

```
osm_pt_routing/
├── __init__.py                   # Point d'entrée du plugin
├── OSM_PT_routing.py            # Classe principale du plugin
├── OSM_PT_routing_dialog.py     # Interface utilisateur
├── OSM_PT_routing_dialog_base.ui # Fichier UI Qt Designer
├── core_function.py              # Fonctions principales et optimisations
├── resources.py                  # Ressources compilées
├── metadata.txt                  # Métadonnées du plugin
└── README.md                     # Ce fichier
```

### Fonctions Principales

- `create_minitrips()` : Création des segments de mini-trips
- `mini_routing()` : Calcul des chemins avec cache optimisé
- `trips()` : Consolidation des mini-trips en trajets complets
- `build_network_graph()` : Construction et cache des graphes réseau
- `find_shortest_path_cached()` : Calcul de chemin avec graphe en cache

### Tests

```bash
# Exécuter les tests
make test

# Ou utiliser pb_tool
pb_tool test
```

## 🐛 Dépannage

### Problèmes Courants

1. **Erreur "Plugin OSMtocheck requis"** :
   - Installer et exécuter d'abord le plugin OSMtocheck
   - Vérifier que les données sont dans le bon format

2. **Performance lente** :
   - Le plugin utilise maintenant un système de cache optimisé
   - Les graphes sont construits une seule fois au début

3. **Erreurs de coordonnées** :
   - Vérifier que les coordonnées sont en EPSG:4326
   - S'assurer que les fichiers CSV ont les bonnes colonnes

4. **Fichiers manquants** :
   - Vérifier la structure des dossiers d'entrée
   - S'assurer que tous les fichiers .gpkg sont présents

### Logs et Debug

Le plugin affiche des messages informatifs dans la console Python de QGIS :
- Construction des graphes réseau
- Utilisation du cache
- Progression du traitement
- Statistiques de performance

## 📄 Licence

Ce projet est sous licence **GNU General Public License v2.0**.

Voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 👥 Auteurs

- **Luigi Dal B.** / FlowRide
- Email : luigi.dalbosco@gmail.com

## 🤝 Contribution

Les contributions sont les bienvenues ! Pour contribuer :

1. Fork le projet
2. Créer une branche pour votre fonctionnalité (`git checkout -b feature/AmazingFeature`)
3. Commit vos changements (`git commit -m 'Add some AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## 📞 Support

- **Email** : luigi.dalbosco@gmail.com
- **Issues** : Utiliser le système d'issues GitHub
- **Documentation** : Consulter le fichier `PERFORMANCE_OPTIMIZATION.md` pour les détails techniques

## 🔗 Liens Utiles

- [QGIS Documentation](https://docs.qgis.org/)
- [PyQGIS Developer Cookbook](https://docs.qgis.org/latest/en/docs/pyqgis_developer_cookbook/)
- [OpenStreetMap](https://www.openstreetmap.org/)
- [GTFS Specification](https://developers.google.com/transit/gtfs/reference)

---

**Note** : Ce plugin est expérimental. Pour toute question ou problème, n'hésitez pas à contacter l'auteur par email.
