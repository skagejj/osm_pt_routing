# this is where I try to stock all the def of the main OSM_PT_routing.py funcitons

from qgis.core import (QgsVectorLayer, 
                        QgsCoordinateReferenceSystem, 
                        QgsVectorFileWriter,
                        QgsField,
                        QgsExpression,
                        QgsExpressionContext,
                        QgsExpressionContextUtils,
                        edit,
                        QgsUnitTypes,
                        QgsProcessingException,
                        QgsPointXY,
                        QgsFields,
                        QgsGeometry,
                        QgsFeature,
                        QgsWkbTypes

)

from qgis.analysis import (QgsVectorLayerDirector,
                           QgsNetworkDistanceStrategy,
                           QgsNetworkSpeedStrategy,
                           QgsGraphBuilder,
                           QgsGraphAnalyzer)

import pandas as pd
from qgis import processing
from qgis.PyQt.QtCore import QVariant
import re
import os
import time
import pickle
import hashlib

def if_remove(file_path):
    if os.path.exists(file_path):
                os.remove(file_path)


def save_and_stop_editing_layers(layers):
    for layer in layers:
        if layer.isEditable(): 
            if layer.commitChanges():  
                print(f"Changes saved successfully for layer: {layer.name()}")
            else:
                print(f"Failed to save changes for layer: {layer.name()}")
                if not layer.rollBack(): 
                    print(f"Failed to rollback changes for layer: {layer.name()}")
        else:
            print(f"Layer '{layer.name()}' is not in editing mode.")

# Cache pour les graphes réseau
_graph_cache = {}

def clear_graph_cache():
    """Nettoie le cache des graphes réseau"""
    global _graph_cache
    _graph_cache.clear()
    print("Graph cache cleared")

def get_cache_stats():
    """Retourne les statistiques du cache"""
    global _graph_cache
    return {
        'cached_graphs': len(_graph_cache),
        'cache_keys': list(_graph_cache.keys())
    }

def get_graph_cache_key(network_file, strategy, direction_field, speed_field, default_speed):
    """Génère une clé unique pour le cache basée sur les paramètres du réseau"""
    cache_data = f"{network_file}_{strategy}_{direction_field}_{speed_field}_{default_speed}"
    return hashlib.md5(cache_data.encode()).hexdigest()

def build_network_graph(network_file, strategy=0, direction_field='', speed_field='', default_speed=50):
    """Construit et met en cache le graphe réseau"""
    cache_key = get_graph_cache_key(network_file, strategy, direction_field, speed_field, default_speed)
    
    if cache_key in _graph_cache:
        print(f"Using cached graph for {network_file}")
        return _graph_cache[cache_key]
    
    print(f"Building network graph for {network_file}")
    
    # Charger la couche réseau
    network_layer = QgsVectorLayer(network_file, "network", "ogr")
    if not network_layer.isValid():
        raise Exception(f"Invalid network layer: {network_file}")
    
    # Créer le directeur de réseau
    # QgsVectorLayerDirector(layer, directionFieldIndex, forwardValue, backwardValue, bothValue, defaultDirection)
    director = QgsVectorLayerDirector(network_layer, -1, '', '', '', 3)
    
    # Configurer la stratégie
    if strategy == 1:  # Speed strategy
        # QgsNetworkSpeedStrategy ne prend aucun argument dans cette version de QGIS
        director.addStrategy(QgsNetworkSpeedStrategy())
    else:  # Distance strategy
        director.addStrategy(QgsNetworkDistanceStrategy())
    
    # Créer le constructeur de graphe
    builder = QgsGraphBuilder(network_layer.crs())
    
    # Construire le graphe
    director.makeGraph(builder, [])
    graph = builder.graph()
    
    # Mettre en cache
    _graph_cache[cache_key] = {
        'director': director,
        'graph': graph,
        'network_layer': network_layer
    }
    
    print(f"Graph cached for {network_file}")
    return _graph_cache[cache_key]

def find_shortest_path_cached(graph_data, start_point, end_point):
    """Trouve le plus court chemin en utilisant le graphe en cache"""
    director = graph_data['director']
    graph = graph_data['graph']
    
    # Convertir les coordonnées en points QGIS
    start_coords = start_point.split(',')
    end_coords = end_point.split(',')
    
    start_point_xy = QgsPointXY(float(start_coords[0]), float(start_coords[1]))
    end_point_xy = QgsPointXY(float(end_coords[0]), float(end_coords[1]))
    
    # Trouver les sommets les plus proches
    start_vertex = director.findVertex(start_point_xy)
    end_vertex = director.findVertex(end_point_xy)
    
    if start_vertex == -1 or end_vertex == -1:
        return None
    
    # Calculer le plus court chemin avec Dijkstra
    tree, cost = QgsGraphAnalyzer.dijkstra(graph, start_vertex, 0)
    
    if tree[end_vertex] == -1:
        return None
    
    # Reconstituer le chemin
    path = []
    current_vertex = end_vertex
    while current_vertex != start_vertex:
        path.append(current_vertex)
        current_vertex = tree[current_vertex]
    path.append(start_vertex)
    path.reverse()
    
    return path

def save_graph_to_file(graph_data, output_file):
    """Sauvegarde le chemin calculé dans un fichier GPKG"""
    path_vertices = graph_data.get('path_vertices', [])
    if not path_vertices:
        return False
    
    try:
        # Créer une nouvelle couche pour le chemin
        fields = QgsFields()
        fields.append(QgsField("id", QVariant.Int))
        
        # Créer le fichier de sortie
        writer = QgsVectorFileWriter(output_file, "UTF-8", fields, 
                                    QgsWkbTypes.LineString, 
                                    QgsCoordinateReferenceSystem("EPSG:4326"), 
                                    "GPKG")
        
        if writer.hasError() != QgsVectorFileWriter.NoError:
            return False
        
        # Créer la géométrie du chemin
        points = []
        for vertex_id in path_vertices:
            vertex_point = graph_data['graph'].vertex(vertex_id).point()
            points.append(QgsPointXY(vertex_point.x(), vertex_point.y()))
        
        if len(points) > 1:
            line_geometry = QgsGeometry.fromPolylineXY(points)
            feature = QgsFeature()
            feature.setGeometry(line_geometry)
            feature.setAttributes([1])
            writer.addFeature(feature)
        
        del writer
        return True
        
    except Exception as e:
        print(f"Erreur lors de la sauvegarde: {e}")
        return False

# Debugging the changing in field type in some step before 
def create_minitrips (OSM4rout_csv,OSM4routing_csv, lines_trips_csv ):
    OSM4rout_unsorted = pd.read_csv(OSM4rout_csv, dtype = {'trip':int,'pos':int, 'stop_id':str})
    
    # Debugging the changing in field type in some step before 
    if OSM4rout_unsorted.dtypes.pos == 'object':
        i_row = 0 
        while i_row<len(OSM4rout_unsorted):
            if OSM4rout_unsorted.loc[i_row,'pos'] == 'true':
                OSM4rout_unsorted.loc[i_row,'pos'] = 1
            if OSM4rout_unsorted.loc[i_row,'pos'] == 'false':
                OSM4rout_unsorted.loc[i_row,'pos'] = 0
            i_row +=1
    
    OSM4rout_unsorted = OSM4rout_unsorted.astype({'pos': 'int64','trip': 'int64'})
    OSM4rout = OSM4rout_unsorted.sort_values(['line_name','trip','pos']).reset_index(drop=True)

    
    # creation and adding segments
    i_row = 0
    i_row2 = 1 
    while i_row2 < len(OSM4rout):
        if OSM4rout.loc[i_row,'pos'] < OSM4rout.loc[i_row2,'pos']:
            OSM4rout.loc[i_row, 'line_trip'] = str(OSM4rout.loc[i_row,'line_name'])+'_trip'+str(OSM4rout.loc[i_row, 'trip'])
            OSM4rout.loc[i_row, 'mini_trip'] = str(OSM4rout.loc[i_row, 'GTFS_stop_id'])+' '+str((OSM4rout.loc[i_row2, 'GTFS_stop_id']))
            OSM4rout.loc[i_row, 'mini_tr_pos'] = str(OSM4rout.loc[i_row,'line_name'])+'_trip'+str(OSM4rout.loc[i_row, 'trip'])+'_pos'+str((OSM4rout.loc[i_row, 'pos']))+'-pos'+str((OSM4rout.loc[i_row2, 'pos']))
            OSM4rout.loc[i_row, 'next_lon'] = OSM4rout.loc[i_row2, 'lon']
            OSM4rout.loc[i_row, 'next_lat'] = OSM4rout.loc[i_row2, 'lat']
        i_row += 1
        i_row2 += 1
   
    OSM4routing = OSM4rout[~OSM4rout['next_lon'].isna()]
    
    # creating dataframe for the lines for the specifc trips
    ls_lines_trips = OSM4routing.line_trip.unique()
    lines_trips = pd.DataFrame(ls_lines_trips)
    lines_trips = lines_trips.rename(columns={0:'line_trip'})
    pattern = re.compile(r'(?:Bus|RegRailServ|Tram|Funicular|trnsprt)([A-Za-z0-9+]+)_')
    pattern2 = re.compile(r'^(Bus|RegRailServ|Tram|Funicular|transport)(.*)_[^_]+$')
    trip_number_pattern = re.compile(r'_trip(\d+)$')

    for idx in lines_trips.index:
        lines_trips.loc[idx,'route_short_name'] = pattern.search(str(lines_trips.loc[idx,'line_trip'])).group(1)
        
        transport_type = pattern2.match(str(lines_trips.loc[idx,'line_trip'])).group(1)  
        bus_code = pattern2.match(str(lines_trips.loc[idx,'line_trip'])).group(2)        
        lines_trips.loc[idx,'line_name'] = str(transport_type + bus_code)
        
        lines_trips.loc[idx,'trip'] = trip_number_pattern.search(str(lines_trips.loc[idx,'line_trip'])).group(1)
    

    if_remove(OSM4routing_csv)
    OSM4routing.to_csv(OSM4routing_csv, index=False )
    if_remove(lines_trips_csv)
    lines_trips.to_csv(lines_trips_csv, index = False)

def mini_routing(OSM4routing_csv, full_roads_gpgk, tram_rails_gpgk, OSM_Regtrain_gpkg, OSM_funicular_gpkg, tempfld, trnsprt_shapes):
    mini_trips_unsorted = pd.read_csv(OSM4routing_csv)
    mini_trips_to_select = mini_trips_unsorted.sort_values(['line_name','trip','pos']).reset_index(drop=True)
    
    ls_files_tempfld = os.listdir(tempfld)
    ls_mini_tr_gpkg = [file for file in ls_files_tempfld if 'gpkg' in file ]
    ls_mini_trips_done = [file[:-5] for file in ls_mini_tr_gpkg]

    mini_trips = mini_trips_to_select[~mini_trips_to_select.mini_tr_pos.isin(ls_mini_trips_done)]
    
    unique_mini_tr_name = 'uq_mini_trips'
    unique_mini_tr_csv = os.path.join(tempfld,str(unique_mini_tr_name)+'.csv')

    # Construire les graphes réseau en cache une seule fois
    print("Building network graphs...")
    graphs = {}
    
    # Graphe pour les routes principales
    graphs['roads'] = build_network_graph(full_roads_gpgk, strategy=1, 
                                         direction_field='oneway_routing', 
                                         speed_field='maxspeed_routing', 
                                         default_speed=50)
    
    # Graphe pour les rails de tram
    graphs['tram'] = build_network_graph(tram_rails_gpgk, strategy=0, default_speed=50)
    
    # Graphe pour les trains régionaux
    graphs['train'] = build_network_graph(OSM_Regtrain_gpkg, strategy=0, default_speed=50)
    
    # Graphe pour les funiculaires
    graphs['funicular'] = build_network_graph(OSM_funicular_gpkg, strategy=0, default_speed=50)
    
    print("Network graphs built and cached!")
    print("Performance optimization: Using cached graphs instead of rebuilding for each mini-trip")

    if not mini_trips.empty:
        mini_trips = mini_trips.reset_index(drop=True)
        print('There are '+str(len(mini_trips))+' mini-trips to calculate')
        tot = len(mini_trips)
        total = tot
        i_row = 0
        n_minitr = 1
        tm0 = time.time()
        if os.path.exists(unique_mini_tr_csv):
            unique_mini_tr = pd.read_csv(unique_mini_tr_csv)
        else:
            unique_mini_tr = pd.DataFrame()
        while i_row < len(mini_trips):
            start_point =  str(mini_trips.loc[i_row,'lon'])+','+str(mini_trips.loc[i_row,'lat'])
            end_point =  str(mini_trips.loc[i_row,'next_lon'])+','+str(mini_trips.loc[i_row,'next_lat'])
            if start_point == end_point:
                i_row += 1
                continue
            mini_trip_gpkg = str(tempfld)+'/'+str(mini_trips.loc[i_row,'mini_tr_pos'])+'.gpkg'
            if mini_trips.loc[i_row,'mini_tr_pos']:
                i_row_uq_tr = 0
                IDstr_end_pt = str(start_point)+' '+str(end_point)
                # check for same mini trip
                while i_row_uq_tr < len(unique_mini_tr):
                    if unique_mini_tr.loc[i_row_uq_tr,'IDstr_end_pt'] == IDstr_end_pt:
                        print('copying ' + str(mini_trips.loc[i_row,'mini_tr_pos'])+ ' from another mini trip')
                        if n_minitr != 1:
                            n_minitr = n_minitr - 1
                        total = total - 1
                        src = unique_mini_tr.loc[i_row_uq_tr,'mini_tr_path']
                        if os.name == 'nt':  # Windows
                            cmd = f'copy "{src}" "{mini_trip_gpkg}"'
                        else:  # Unix/Linux
                            cmd = f'cp "{src}" "{mini_trip_gpkg}"'
                        os.system(cmd)
                        break
                    i_row_uq_tr += 1
                # in absence of the same mini trip
                if i_row_uq_tr == len(unique_mini_tr):
                    print('creating ' + str(mini_trips.loc[i_row,'mini_tr_pos']))
                    unique_mini_tr.loc[i_row_uq_tr,'mini_tr_path'] = mini_trip_gpkg
                    unique_mini_tr.loc[i_row_uq_tr,'IDstr_end_pt'] = IDstr_end_pt
                    try:
                        # Utiliser le graphe en cache au lieu de l'algorithme QGIS
                        graph_key = None
                        if 'Tram' in str(mini_trips.loc[i_row,'line_name']):
                            graph_key = 'tram'
                        elif 'RegRailServ' in str(mini_trips.loc[i_row,'line_name']):
                            graph_key = 'train'
                        elif 'Funicular' in str(mini_trips.loc[i_row,'line_name']):
                            graph_key = 'funicular'
                        else:
                            graph_key = 'roads'
                        
                        # Calculer le chemin avec le graphe en cache
                        path_vertices = find_shortest_path_cached(graphs[graph_key], start_point, end_point)
                        
                        if path_vertices:
                            # Sauvegarder le chemin dans un fichier GPKG
                            if_remove(mini_trip_gpkg)
                            graph_data = graphs[graph_key].copy()
                            graph_data['path_vertices'] = path_vertices
                            save_graph_to_file(graph_data, mini_trip_gpkg)
                        else:
                            print(f'No path found for {mini_trips.loc[i_row,"mini_tr_pos"]}')
                            # Créer un fichier vide si aucun chemin n'est trouvé
                            if_remove(mini_trip_gpkg)
                            # Créer un fichier GPKG vide
                            fields = QgsFields()
                            fields.append(QgsField("id", QVariant.Int))
                            writer = QgsVectorFileWriter(mini_trip_gpkg, "UTF-8", fields, 
                                                        QgsWkbTypes.LineString, 
                                                        QgsCoordinateReferenceSystem("EPSG:4326"), 
                                                        "GPKG")
                            del writer
                            
                    except Exception as e:
                        if os.path.exists(mini_trip_gpkg):
                            os.remove(mini_trip_gpkg)
                        print(f'something wrong with {mini_trips.loc[i_row,"mini_tr_pos"]}: {str(e)}')
                        break
                # ls_minitrips.append(mini_trip_gpkg) 
            print('There are '+str(tot)+' mini-trips to calculate')
            tm1 = time.time()
            dtm = tm1 - tm0
            tmtot = dtm/n_minitr * (total) 
            tmrest = tmtot - dtm
            hours = int(tmrest/3600) 
            min = int(int(tmrest/60) - int(tmrest/3600)*60)
            if hours > 0:
                print ('    '+str(hours)+' hours and '+str(min)+' minutes left')
            else:
                print ('    '+str(min)+' minutes left')
            tot = tot - 1
            i_row += 1
            n_minitr += 1
        if_remove(unique_mini_tr_csv)
        unique_mini_tr.to_csv(unique_mini_tr_csv,index=False)

    
    # if_remove(trnsprt_shapes)
    # params = {'LAYERS':ls_minitrips,
    #           'CRS':QgsCoordinateReferenceSystem('EPSG:4326'),
    #           'OUTPUT':trnsprt_shapes}
    # processing.run("native:mergevectorlayers",params)    
    
    # return trnsprt_shapes
    

def trips(mini_shapes_file, trip , trip_gpkg, trip_csv, temp_folder_minitrip):
    
    ls_files_tempfld = os.listdir(temp_folder_minitrip)
    ls_mini_tr_gpkg = [file for file in ls_files_tempfld if 'gpkg' in file ]
    ls_mini_tr = [file for file in ls_mini_tr_gpkg if trip in file ]
    
    mini_tr_df_unsorted = pd.DataFrame(ls_mini_tr)

    pattern2 = r"(\d+)\.gpkg$"
    i_row = 0
    while i_row < len(mini_tr_df_unsorted):
        nd2pos = re.search(pattern2,mini_tr_df_unsorted.loc[i_row,0]).group(1)
        mini_tr_df_unsorted.loc[i_row,'nd2pos'] = int(nd2pos)
        i_row +=1

    mini_tr_df = mini_tr_df_unsorted.sort_values(['nd2pos']).reset_index(drop=True)
    mini_tr_df = mini_tr_df.rename(columns={0:'gpkg'})

    ls_minitrips_gpkg = mini_tr_df.gpkg.unique()

    ls_minitrips = [str(temp_folder_minitrip)+'/'+str(file) for file in ls_minitrips_gpkg]
    
    if_remove(trip_gpkg)
    params = {'LAYERS':ls_minitrips,
              'CRS':QgsCoordinateReferenceSystem('EPSG:4326'),
              'OUTPUT':trip_gpkg}
    processing.run("native:mergevectorlayers",params)


    # to_search = str(trip)+'%'
    # trip_selection =  '"layer" LIKE \''+ str(to_search)+'\''
    # if_remove(trip_gpkg)
    # params = {'INPUT':mini_shapes_file,
    #         'EXPRESSION':trip_selection,
    #         'OUTPUT':trip_gpkg}
    # processing.run("native:extractbyexpression", params)
    
    trip_layer = QgsVectorLayer(trip_gpkg,trip,"ogr")
    
    
                    #,QgsField("nd2pos", QVariant.Int)
    pr = trip_layer.dataProvider()
    pr.addAttributes([
                    QgsField("dist_stops", QVariant.Double)])
    trip_layer.updateFields()
    
    expression1 = QgsExpression('$length')
    #expression2 = QgsExpression('regexp_substr( "layer" ,\'(\\d+)$\')')

    context = QgsExpressionContext()
    context.appendScopes(QgsExpressionContextUtils.globalProjectLayerScopes(trip_layer))

    with edit(trip_layer):
        for f in trip_layer.getFeatures():
            context.setFeature(f)
            f['dist_stops'] = expression1.evaluate(context)
            #f['nd2pos'] = expression2.evaluate(context)
            trip_layer.updateFeature(f)
    trip_layer.commitChanges()

    lsto_keep = ['layer','dist_stops','start','end']
       
    IDto_delete = [trip_layer.fields().indexOf(field_name) for field_name in lsto_keep]
    IDto_delete = [index for index in IDto_delete if index != -1]
    
    if_remove(trip_csv)
    QgsVectorFileWriter.writeAsVectorFormat(trip_layer,trip_csv,"utf-8",driverName = "CSV",attributes=IDto_delete)

    trip_df = pd.read_csv(trip_csv,dtype={'dist_stops':'float'})

    i_row2 = -1
    i_row = 0
    while i_row< len(trip_df):
        line_trip_1st_2nd = str(trip_df.loc[i_row,'layer'])
        pattern1 = r"^(.*)_"
        pattern2 = r"(\d+)$"
        line_trip = re.match(pattern1,line_trip_1st_2nd).group(1)
        nd2pos = re.search(pattern2,line_trip_1st_2nd).group(1)
        trip_df.loc[i_row,'seq_stpID'] = str(line_trip)+'_pos'+str(nd2pos)
        if i_row2 > -1:
            trip_df.loc[i_row,'shape_dist_traveled'] = trip_df.loc[i_row,'dist_stops'] + trip_df.loc[i_row2,'shape_dist_traveled']
        else:
            trip_df.loc[i_row,'shape_dist_traveled'] = trip_df.loc[i_row,'dist_stops']
        i_row2 += 1
        i_row += 1
    
    if_remove(trip_csv)
    trip_df.to_csv(trip_csv, index=False)

