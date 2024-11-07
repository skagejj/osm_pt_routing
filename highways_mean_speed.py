import pandas as pd
import statistics as stat

GenevaRoads = pd.read_csv('/home/luigi/Downloads/881/manual_edited_map/GenevaRoads.csv',low_memory=False)

ls_highway = GenevaRoads.highway.unique()

highway_speed = pd.DataFrame(ls_highway)

highway_speed = highway_speed.rename(columns={0:'highway'})

i_hgw = 0
while i_hgw < len(highway_speed):
    ls_speeds = []
    Roads = GenevaRoads[GenevaRoads['highway'] == highway_speed.loc[i_hgw,'highway']].reset_index(drop=True)
    all_speeds = list(Roads['maxspeed'])
    i_row = 0
    while i_row < len(all_speeds):
        if str(all_speeds[i_row]).isnumeric():
            ls_speeds.append(int(all_speeds[i_row]))
        i_row += 1
    if ls_speeds: 
        highway_speed.loc[i_hgw,'average_speed'] = stat.mean(ls_speeds)
    i_hgw += 1
    del Roads, i_row, ls_speeds, all_speeds

highway_speed.to_csv('',index=Famse)
