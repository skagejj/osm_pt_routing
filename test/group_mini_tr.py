import pandas as pd
import os
import shutil

def computation_trip(mini_trips, mini_trip_gpkg, tram_rails_gpgk, OSM_Regtrain_gpkg, OSM_funicular_gpkg, full_roads_gpgk, start_point, end_point):
    if 'Tram' in str(mini_trips.loc[0,'line_name']):
        if_remove(mini_trip_gpkg)
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
    elif 'RegRailServ' in str(mini_trips.loc[0,'line_name']):
        if_remove(mini_trip_gpkg)
        params = {'INPUT':OSM_Regtrain_gpkg,
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
    elif 'Funicular' in str(mini_trips.loc[0,'line_name']):
        if_remove(mini_trip_gpkg)
        params = {'INPUT':OSM_funicular_gpkg,
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
        if_remove(mini_trip_gpkg)
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
            

def mini_routing(OSM4routing_csv, full_roads_gpgk, tram_rails_gpgk, OSM_Regtrain_gpkg, OSM_funicular_gpkg, tempfld, trnsprt_shapes):
    mini_trips_unsorted = pd.read_csv(OSM4routing_csv)
    mini_trips_to_select = mini_trips_unsorted.sort_values(['line_name','trip','pos']).reset_index(drop=True)
    
    ls_mini_tr_gpkg = os.listdir(tempfld)
    ls_mini_trips_done = [file[:-5] for file in ls_mini_tr_gpkg]

    mini_trips = mini_trips_to_select[~mini_trips_to_select.mini_tr_pos.isin(ls_mini_trips_done)]
    mini_trips = mini_trips.reset_index(drop=True)

    i_row = 0
    while i_row < len(mini_trips):
        mini_trips.loc[i_row,'start_end_coord'] = str(mini_trips.loc[i_row,'lon'])+','+str(mini_trips.loc[i_row,'lat'])+' - '+str(mini_trips.loc[i_row,'next_lon'])+','+str(mini_trips.loc[i_row,'next_lat'])
        i_row +=1

    ls_start_end = mini_trips.start_end_coord.unique()

    ls_minitrips = ls_mini_trips_done
    print('There are '+str(len(ls_start_end))+' mini-trips to calculate')
    tot = len(ls_start_end)

    for coord in ls_start_end:
        mini_trips_coord = mini_trips[mini_trips['start_end_coord'] == coord]
        mini_trips_coord = mini_trips_coord.reset_index(drop=True)
        
        start_point =  str(mini_trips_coord.loc[0,'lon'])+','+str(mini_trips_coord.loc[0,'lat'])+' [EPSG:4326]'
        end_point =  str(mini_trips_coord.loc[0,'next_lon'])+','+str(mini_trips_coord.loc[0,'next_lat'])+' [EPSG:4326]'
        if start_point == end_point:
            i_row += 1
            continue
        i_row_init =0
        mini_trip_gpkg = str(tempfld)+'/'+str(mini_trips_coord.loc[i_row_init,'mini_tr_pos'])+'.gpkg'
        if not coord == '':
            computation_trip(mini_trips_coord, mini_trip_gpkg, tram_rails_gpgk, OSM_Regtrain_gpkg, OSM_funicular_gpkg, full_roads_gpgk, start_point, end_point)
            ls_minitrips.append(mini_trip_gpkg) 
            i_row = 1
            while i_row < len (mini_trips_coord):
                mini_trip_gpkg_copy = str(tempfld)+'/'+str(mini_trips_coord.loc[i_row,'mini_tr_pos'])+'.gpkg'
                shutil.copyfile(mini_trip_gpkg,mini_trip_gpkg_copy)
                ls_minitrips.append(mini_trip_gpkg_copy)
        tot = tot - 1
        print('There are '+str(tot)+' mini-trips to calculate')
        
    

