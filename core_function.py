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
                        QgsFeature

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


def create_minitrips (OSM4rout_csv,OSM4routing_csv, lines_trips_csv ):
    OSM4rout_unsorted = pd.read_csv(OSM4rout_csv)
    OSM4rout = OSM4rout_unsorted.sort_values(['line_name','trip','pos']).reset_index(drop=True)

    # creation and adding segments
    i_row = 0
    i_row2 = 1
    i_max = len(OSM4rout) -1 
    while i_row < i_max:
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
    for idx in lines_trips.index:
        lines_trips.loc[idx,'route_short_name'] = re.findall('[0-9]+',lines_trips.loc[idx,'line_trip'])[0]
        if re.findall('[0-9]+_[0-9]+', lines_trips.loc[idx,'line_trip']):
            lines_trips.loc[idx,'line_name'] = re.findall('[a-zA-Z]+[0-9]+_[0-9]+',lines_trips.loc[idx,'line_trip'])
        else:
            lines_trips.loc[idx,'line_name'] = re.findall('[a-zA-Z]+[0-9]+',lines_trips.loc[idx,'line_trip'])[0]

        lines_trips.loc[idx,'trip'] = re.findall('[0-9]+',lines_trips.loc[idx,'line_trip'])[-1]
    


    OSM4routing.to_csv(OSM4routing_csv, index=False )
    lines_trips.to_csv(lines_trips_csv, index = False)

def mini_routing(OSM4routing_csv, full_roads_gpgk, tram_rails_gpgk, tempfld, trnsprt_shapes):
    mini_trips_unsorted = pd.read_csv(OSM4routing_csv)
    mini_trips = mini_trips_unsorted.sort_values(['line_name','trip','pos']).reset_index(drop=True)
    
    ls_minitrips = []
    i_row = 0
    pattern = '[a-zA-Z]+'
    while i_row < len(mini_trips):
        start_point =  str(mini_trips.loc[i_row,'lon'])+','+str(mini_trips.loc[i_row,'lat'])+' [EPSG:4326]'
        end_point =  str(mini_trips.loc[i_row,'next_lon'])+','+str(mini_trips.loc[i_row,'next_lat'])+' [EPSG:4326]'
        mini_trip_gpkg = str(tempfld)+'/'+str(mini_trips.loc[i_row,'mini_tr_pos'])+'.gpkg'
        if mini_trips.loc[i_row,'mini_tr_pos']:
            if re.findall(pattern,mini_trips.loc[i_row,'line_name'])[0]=='Tram':
                params = {'INPUT':tram_rails_gpgk,
                        'STRATEGY':0,
                        'DIRECTION_FIELD':'',
                        'VALUE_FORWARD':'',
                        'VALUE_BACKWARD':'',
                        'VALUE_BOTH':'','DEFAULT_DIRECTION':2,
                        'SPEED_FIELD':'',
                        'DEFAULT_SPEED':50,
                        'TOLERANCE':0,
                        'START_POINT':start_point,
                        'END_POINT':end_point,
                        'OUTPUT':mini_trip_gpkg}
                processing.run("native:shortestpathpointtopoint", params)
            else:
                params = {'INPUT':full_roads_gpgk,
                        'STRATEGY':1,
                        'DIRECTION_FIELD':'oneway_routing',
                        'VALUE_FORWARD':'forward',
                        'VALUE_BACKWARD':'backward',
                        'VALUE_BOTH':'','DEFAULT_DIRECTION':2,
                        'SPEED_FIELD':'maxspeed_routing',
                        'DEFAULT_SPEED':50,
                        'TOLERANCE':0,
                        'START_POINT':start_point,
                        'END_POINT':end_point,
                        'OUTPUT':mini_trip_gpkg}
                processing.run("native:shortestpathpointtopoint", params)
            ls_minitrips.append(mini_trip_gpkg) 
        i_row += 1
    

    ls_minitrips

    params = {'LAYERS':ls_minitrips,
              'CRS':QgsCoordinateReferenceSystem('EPSG:4326'),
              'OUTPUT':trnsprt_shapes}
    processing.run("native:mergevectorlayers",params)    
    
    return trnsprt_shapes
    

def trips(mini_shapes_file, trip , trip_gpkg, trip_csv):
    
    to_search = str(trip)+'%'
    trip_selection =  '"layer" LIKE \''+ str(to_search)+'\''
    params = {'INPUT':mini_shapes_file,
            'EXPRESSION':trip_selection,
            'OUTPUT':trip_gpkg}
    processing.run("native:extractbyexpression", params)
    
    trip_layer = QgsVectorLayer(trip_gpkg,trip,"ogr")
       
    pr = trip_layer.dataProvider()
    pr.addAttributes([
                    QgsField("dist_stops", QVariant.Double)])
    trip_layer.updateFields()
    
    expression1 = QgsExpression('$length')

    context = QgsExpressionContext()
    context.appendScopes(QgsExpressionContextUtils.globalProjectLayerScopes(trip_layer))

    with edit(trip_layer):
        for f in trip_layer.getFeatures():
            context.setFeature(f)
            f['dist_stops'] = expression1.evaluate(context)
            trip_layer.updateFeature(f)
    trip_layer.commitChanges()

    lsto_keep = ['layer','dist_stops','start','end']
       
    IDto_delete = [trip_layer.fields().indexOf(field_name) for field_name in lsto_keep]
    IDto_delete = [index for index in IDto_delete if index != -1]
    
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
    
    trip_df.to_csv(trip_csv, index=False)
