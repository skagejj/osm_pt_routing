# Optimisations de Performance - OSM PT Routing

## Problème Identifié

Le script Python QGIS était très lent lors du routing car l'algorithme `native:shortestpathpointtopoint` était appelé pour chaque mini-trip individuellement, ce qui signifiait que le graphe réseau était reconstruit à chaque fois.

## Solution Implémentée

### 1. Système de Cache pour les Graphes Réseau

- **Cache global** : Les graphes réseau sont construits une seule fois et mis en cache
- **Clé de cache unique** : Basée sur les paramètres du réseau (fichier, stratégie, champs de direction/vitesse)
- **Réutilisation** : Le même graphe est réutilisé pour tous les mini-trips du même type de réseau

### 2. Nouvelles Fonctions Ajoutées

#### `build_network_graph()`
- Construit le graphe réseau une seule fois
- Met en cache le graphe pour réutilisation ultérieure
- Gère différents types de réseaux (routes, tram, train, funiculaire)

#### `find_shortest_path_cached()`
- Calcule le plus court chemin en utilisant le graphe en cache
- Utilise l'algorithme de Dijkstra de QGIS
- Beaucoup plus rapide que la reconstruction du graphe

#### `save_graph_to_file()`
- Sauvegarde le chemin calculé dans un fichier GPKG
- Compatible avec le format attendu par le reste du script

#### Fonctions utilitaires
- `clear_graph_cache()` : Nettoie le cache si nécessaire
- `get_cache_stats()` : Affiche les statistiques du cache

### 3. Optimisation de la Fonction `mini_routing()`

**Avant :**
```python
# Pour chaque mini-trip
processing.run("native:shortestpathpointtopoint", params)
```

**Après :**
```python
# Construction des graphes une seule fois au début
graphs = {}
graphs['roads'] = build_network_graph(full_roads_gpgk, ...)
graphs['tram'] = build_network_graph(tram_rails_gpgk, ...)
# etc.

# Pour chaque mini-trip
path_vertices = find_shortest_path_cached(graphs[graph_key], start_point, end_point)
save_graph_to_file(graph_data, mini_trip_gpkg)
```

## Améliorations de Performance Attendues

1. **Construction du graphe** : Une seule fois au lieu de N fois (où N = nombre de mini-trips)
2. **Calcul des chemins** : Utilisation directe du graphe en mémoire au lieu de reconstruction
3. **Réduction de la charge I/O** : Moins d'accès aux fichiers réseau
4. **Optimisation mémoire** : Réutilisation des objets graphiques

## Impact Estimé

- **Temps de traitement** : Réduction de 70-90% du temps total
- **Charge CPU** : Réduction significative de la charge de calcul
- **Mémoire** : Utilisation plus efficace de la mémoire (cache intelligent)

## Compatibilité

- ✅ Compatible avec l'interface existante
- ✅ Même format de sortie (fichiers GPKG)
- ✅ Gestion des erreurs améliorée
- ✅ Messages informatifs pour le suivi

## Utilisation

Le système de cache fonctionne automatiquement. Aucune modification de l'interface utilisateur n'est nécessaire. Les améliorations sont transparentes pour l'utilisateur final.

## Monitoring

Le script affiche maintenant :
- "Building network graphs..." au début
- "Network graphs built and cached!"
- "Performance optimization: Using cached graphs instead of rebuilding for each mini-trip"
- "Using cached graph for [filename]" pour les réutilisations
