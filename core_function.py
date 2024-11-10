# this is where I try to stock all the def of the main OSM_PT_routing.py funcitons

from qgis.core import QgsProperty, QgsVectorLayer, QgsField, QgsProject, edit, QgsExpression, QgsExpressionContext, QgsExpressionContextUtils,QgsCoordinateReferenceSystem, QgsVectorFileWriter, QgsProcessingFeatureSourceDefinition,QgsFeatureRequest
import pandas as pd
from qgis import processing
from qgis.PyQt.QtCore import QVariant
import re


def create_minitrips (OSM4rout_file,output_fld,source_fld):
    OSM4rout_unsorted = pd.read_csv(OSM4rout_file)
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
    
    OSM4rout_csv = str(output_fld)+'/OSM4routing_XYminiTrips.csv'
    OSM4routing = OSM4rout[~OSM4rout['next_lon'].isna()]
    
    # creating dataframe for the lines for the specifc trips
    ls_lines_trips = OSM4routing.line_trip.unique()
    lines_trips = pd.DataFrame(ls_lines_trips)
    lines_trips = lines_trips.rename(columns={0:'line_trip'})
    for idx in lines_trips.index:
        lines_trips.loc[idx,'route_short_name'] = re.findall('[0-9]+'+lines_trips.loc[idx,'line_trip'])[0]
        if re.findall('[0-9]+_[0-9]+', lines_trips.loc[idx,'line_trip']):
            lines_trips.loc[idx,'line_name'] = re.findall('[a-z]+[0-9]+_[0-9]+',lines_trips.loc[idx,'line_trip'])
        else:
            lines_trips.loc[idx,'line_name'] = re.findall('[a-z]+[0-9]+',lines_trips.loc[idx,'line_trip'])[0]

        lines_trips.loc[idx,'trip'] = re.findall('[0-9]+'+lines_trips.loc[idx,'line_trip'])[-1]
    
    lines_trips_csv =  str(source_fld)+'/lines_trips.csv'

    OSM4routing.to_csv(OSM4rout_csv, index=False )
    lines_trips.to_csv(lines_trips_csv, index = False)

    return OSM4rout_csv, lines_trips_csv

def mini_routing(XYminiTrips,CityRoads, tempfld, output_fld):
    mini_trips_unsorted = pd.read_csv(XYminiTrips)
    mini_trips = mini_trips_unsorted.sort_values(['line_name','trip','pos']).reset_index(drop=True)
    
    ls_minitrips = []
    i_row = 0
    while i_row < len(mini_trips):
        start_point =  str(mini_trips.loc[i_row,'lon'])+','+str(mini_trips.loc[i_row,'lat'])+' [EPSG:4326]'
        end_point =  str(mini_trips.loc[i_row,'next_lon'])+','+str(mini_trips.loc[i_row,'next_lat'])+' [EPSG:4326]'
        mini_trip_gpkg = str(tempfld)+'/'+str(mini_trips.loc[i_row,'mini_tr_pos'])+'.gpkg'
        if mini_trips.loc[i_row,'mini_tr_pos']:
            params = {'INPUT':CityRoads,
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
    trnsprt_shapes = str(output_fld)+'/mini_shapes.gpkg'

    ls_minitrips

    params = {'LAYERS':ls_minitrips,
              'CRS':QgsCoordinateReferenceSystem('EPSG:4326'),
              'OUTPUT':trnsprt_shapes}
    processing.run("native:mergevectorlayers",params)    
    
    return trnsprt_shapes
    
def trips(mini_shapes_file, trip , trip_gpkg, GenevaRoads_path,temp_folder_linestrip):
    mini_shapes = QgsVectorLayer(mini_shapes_file,"Segments","ogr")
    trip_selection =  '"layer" like \''+str(trip)+'%\''
    parmas =  {'INPUT': mini_shapes,
                'EXPRESSION':trip_selection,
                'METHOD':0}
    processing.run("qgis:selectbyexpression",parmas)

    params = {'INPUT':QgsProcessingFeatureSourceDefinition(mini_shapes,
                selectedFeaturesOnly=True, 
                featureLimit=-1, 
                geometryCheck=QgsFeatureRequest.GeometryAbortOnInvalid),
                'FIELD':[],
                'SEPARATE_DISJOINT':False,
                'OUTPUT':trip_gpkg}
    processing.run("native:dissolve", params)

    GenevaRoads = QgsVectorLayer(GenevaRoads_path,'GenevaRoads_lines',"ogr")
    
    trip_layer = QgsVectorLayer(trip_gpkg,trip,"ogr")
    params = {'INPUT':GenevaRoads,
                'PREDICATE':[1,3,5,6],
                'INTERSECT':trip_layer,
                'METHOD':0}
    processing.run("native:selectbylocation", params)

    selected_csv = str(temp_folder_linestrip)+'/'+str(trip)+'_OSMways.csv'
    QgsVectorFileWriter.writeAsVectorFormat(GenevaRoads,selected_csv,"utf-8",driverName = "CSV",onlySelected=True,attributes=['full_id','osm_id'])
    selected = pd.read_csv(selected_csv)
    ls_OSMways = selected.full_id.unique()
    
    return OSMways
