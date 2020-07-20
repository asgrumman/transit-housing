#!/usr/bin/env python
# coding: utf-8

# In[398]:


#import packages
import pandas as pd
import geopandas as gpd
import geojson
from bokeh.io import show
from bokeh.models import (CDSView, ColorBar, ColumnDataSource,
                          CustomJS, CustomJSFilter, 
                          GeoJSONDataSource, HoverTool, BoxZoomTool, PolySelectTool,
                          WheelZoomTool,ResetTool,SaveTool,PanTool,
                          ZoomInTool, ZoomOutTool,
                          LinearColorMapper, Slider, LogColorMapper, CategoricalColorMapper,
                          FixedTicker, BasicTickFormatter, LogTicker, FuncTickFormatter,
                          PrintfTickFormatter, BasicTicker, Legend, LegendItem)
from bokeh.layouts import column, row, widgetbox
from bokeh.palettes import brewer
from bokeh.plotting import figure, output_file, save
from bokeh.resources import CDN
from bokeh.embed import file_html


# In[399]:


#import Affordable Housing file
housing = pd.read_csv("Housing.csv",sep=",")

housing.head()


# In[400]:


#Group housing data by neighborhood and count number of addresses 

housing_grouped = housing.groupby(["Community Area Name"]).count()[["Address"]].reset_index()

housing_grouped


# In[401]:


#import shapefile with neighborhood boundaries
map_nbhoods = gpd.read_file('Neighborhoods.shp')

map_nbhoods


# In[402]:


map_nbhoods.dtypes #check to be sure it's a geodataframe


# In[403]:


'''Find Mismatched Neighorhoods'''

#merge neighborhood data with housing data based on neighborhood name
housing_merged = pd.merge(map_nbhoods,housing_grouped,
                         left_on='pri_neigh',right_on='Community Area Name',
                         how='outer',indicator=True)



housing_merged


# In[404]:


#find housing units with mismatched neighborhoods
right_only = housing_merged.loc[housing_merged['_merge'] == 'right_only']

right_only


# In[405]:


'''Clean Housing Data'''

#fix typos
housing.replace({'East Garfiled Park':'East Garfield Park'},inplace=True)
housing.replace({'Lakeview':'Lake View'},inplace=True)

#match up mismatched neighborhoods
housing.replace({'West Englewood':'Englewood',
                    'Near West Side':'Little Italy, UIC',
                    'Near North Side':'River North',
                    'East Garfield Park':'Garfield Park',
                    'West Garfield Park':'Garfield Park',
                    'Greater Grand Crossing':'Grand Crossing',
                    'South Lawndale':'Little Village'},inplace=True)

#drop rows with non-affordable housing
luxury = housing[(housing["Property Type"] == 'ARO')].index
housing.drop(luxury, inplace=True)


# In[406]:


#Group cleaned housing data by neighborhood and count number of addresses 

housing_cleaned = housing.groupby(["Community Area Name"]).count()[["Address"]].reset_index()


# In[407]:


#merge cleaned neighborhood data with housing data based on neighborhood name
housing_nbhoods = pd.merge(map_nbhoods,housing_cleaned,
                         left_on='pri_neigh',right_on='Community Area Name',
                         how='outer',indicator=True)


# In[408]:


#replace NaN (neighborhoods with no matching housing units) with 0
housing_nbhoods['Address'] = housing_nbhoods['Address'].fillna(0)
housing_nbhoods['Address'] = housing_nbhoods['Address'].astype(int)
housing_nbhoods


# In[409]:


'''Create Affordable Housing by Neighborhood Map'''


#read dataframe as geodataframe

gdf = gpd.GeoDataFrame(housing_nbhoods, geometry='geometry')

#convert geodataframe to geojson
geosource = GeoJSONDataSource(geojson=gdf.to_json())


# Define color palettes
palette = brewer['BuGn'][6]
palette = palette[::-1] # reverse order of colors so higher values have darker colors

# Instantiate LogColorMapper that exponentially maps numbers in a range, into a sequence of colors.
color_mapper = LogColorMapper(palette = palette, low = 0, high = 40)

# Define custom tick labels for color bar.
tick_labels = {1.35:'0',2.5:'1-2',4.6: '3-5',8.5: '6-10', 16:'11-19',
 30:'20+'}

# Create color bar
color_bar = ColorBar(title = 'Number of Housing Units',
                     color_mapper = color_mapper, 
                     label_standoff = 6,
                     width = 500, height = 20,
                     border_line_color = None,
                     location = (0,0),
                     orientation = 'horizontal',
                     ticker=FixedTicker(num_minor_ticks=0,
                                        ticks=[1.35,2.5,4.6,8.5,16,30]),
                     major_label_overrides = tick_labels,
                     major_tick_line_color = None,
                     major_label_text_align = 'center')

# Create figure object
p = figure(title = 'Affordable Housing per Neighborhood in Chicago')


# Add patch renderer to figure
neighborhoods = p.patches('xs','ys', source = geosource,
                   fill_color = {'field' :'Address',
                                 'transform' : color_mapper},
                   line_color = "gray", 
                   line_width = 0.25, 
                   fill_alpha = 1)

# Create hover tool
p.add_tools(HoverTool(renderers = [neighborhoods],
                      tooltips = [('Neighborhood','@pri_neigh'),
                                  ('No. of Housing Units','@Address')]))

#remove axes, axis labels, and grid lines
p.xaxis.major_tick_line_color = None
p.xaxis.minor_tick_line_color = None
p.yaxis.major_tick_line_color = None
p.yaxis.minor_tick_line_color = None
p.xaxis.major_label_text_font_size = '0pt'
p.yaxis.major_label_text_font_size = '0pt'
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = None

# Specify layout
p.add_layout(color_bar, 'below')

show(p)


# In[410]:


#export map as html file
output_file("housing-bokeh.html")
save(p)


# In[411]:


#read L_stops data
L_Stops = pd.read_csv('L_Stops.csv',sep=",")

L_Stops.head()


# In[412]:


#Need to convert Location to Latitude and Longitude columns
new = L_Stops["Location"].str.split(",", n = 1, expand = True) 

#remove parentheses
new[0] = new[0].str.replace("(","") 
new[1] = new[1].str.replace(")","")

#convert type from string to float
new[0]= new[0].astype(float) 
new[1]= new[1].astype(float)

#split into 2 columns
L_Stops["Latitude"] = new[0]
L_Stops["Longitude"] = new[1]


# In[413]:


#convert Latitude and Longitude to geometry datatype

GeoStops = gpd.GeoDataFrame(
    L_Stops, geometry=gpd.points_from_xy(L_Stops.Longitude, L_Stops.Latitude))

GeoStops.head()


# In[414]:


'''Add counter for number of connecting lines per station'''

#Convert boolean to int
GeoStops["RED"] = GeoStops["RED"].astype(int)
GeoStops["BLUE"] = GeoStops["BLUE"].astype(int)
GeoStops["G"] = GeoStops["G"].astype(int)
GeoStops["Y"] = GeoStops["Y"].astype(int)
GeoStops["Pexp"] = GeoStops["Pexp"].astype(int)
GeoStops["Pnk"] = GeoStops["Pnk"].astype(int)
GeoStops["O"] = GeoStops["O"].astype(int)
GeoStops["BRN"] = GeoStops["BRN"].astype(int)

#add a column summing the number of lines that connect at each stop
GeoStops['Num_Lines'] = GeoStops[{"RED","BLUE","G","BRN","Pexp","Y","Pnk","O"}].sum(axis=1)
GeoStops_Lines = GeoStops.copy()

GeoStops_Lines.head()


# In[415]:


#drop rows with an extra direction at the ends of lines

end_lines = GeoStops_Lines[(GeoStops_Lines["STOP_ID"] == 30077) | #Forest Park end of Blue Line
                           (GeoStops_Lines["STOP_ID"] == 30171) | #O'Hare end of Blue Line
                           (GeoStops_Lines["STOP_ID"] == 30249) | #End of Brown Line
                           (GeoStops_Lines["STOP_ID"] == 30182) | #End of Orange Line
                           (GeoStops_Lines["STOP_ID"] == 30203) | #End of Purple Line
                           (GeoStops_Lines["STOP_ID"] == 30089) | #95th end of Red Line
                           (GeoStops_Lines["STOP_ID"] == 30173) | #Howard end of Red Line
                           (GeoStops_Lines["STOP_ID"] == 30176) | #Howard end of Yellow Line
                           (GeoStops_Lines["STOP_ID"] == 30026) | #end of Yellow Line
                           (GeoStops_Lines["STOP_ID"] == 30139) | #Cottage Grove end of Green Line
                           (GeoStops_Lines["STOP_ID"] == 30057) | #Ashland end of Green Line
                           (GeoStops_Lines["STOP_ID"] == 30114) | #end of Pink Line
                           (GeoStops_Lines["STOP_ID"] == 30004)].index #Harlem end of Green Line

GeoStops_Lines.drop(end_lines, inplace=True)


# In[416]:


#Group the number of lines by directions per station
Grouped_Stops = GeoStops_Lines.groupby(["STATION_NAME","MAP_ID","Latitude","Longitude"]).sum()[["Num_Lines"]].reset_index()

#must manually fix a few connectivity calculations 
Grouped_Stops.at[73, 'Num_Lines'] = 4 #fixing Howard - it was undercounted since only Purple Exp included in calculation
Grouped_Stops.at[61, 'Num_Lines'] = 3 # fixing Garfield - it branches and both branches weren't counted
Grouped_Stops.head()


# In[417]:


'''Create Affordable Housing by Neighborhood with L Stops Map'''

gdf1 = gpd.GeoDataFrame(housing_nbhoods, geometry='geometry')

#define neighborhoods/boundaries data source
geosource1 = GeoJSONDataSource(geojson=gdf1.to_json())

# Define color palettes
palette = brewer['BuGn'][6]
palette = palette[::-1] # reverse order of colors so higher values have darker colors

# Instantiate LogColorMapper that exponentially maps numbers in a range, into a sequence of colors.
color_mapper = LogColorMapper(palette = palette, low = 0, high = 40)

# Define custom tick labels for color bar.
tick_labels = {1.35:'0',2.5:'1-2',4.6: '3-5',8.5: '6-10', 16:'11-19',
 30:'20+'}


# Create color bar.
color_bar = ColorBar(title = 'Number of Affordable Housing Units',
                     color_mapper = color_mapper, 
                     label_standoff = 6,
                     width = 500, height = 20,
                     border_line_color = None,
                     location = (0,0),
                     orientation = 'horizontal',
                     ticker=FixedTicker(num_minor_ticks=0,
                                        ticks=[1.35,2.5,4.6,8.5,16,30]),
                     major_label_overrides = tick_labels,
                     major_tick_line_color = None,
                     major_label_text_align = 'center')

# Convert stops dataframe to a ColumnDataSource
source_stops = ColumnDataSource(data=dict(
                        x=list(Grouped_Stops['Longitude']), 
                        y=list(Grouped_Stops['Latitude']),
                        sizes=list(Grouped_Stops['Num_Lines']),
                        #scaled so differences b/w number of lines/station is visible
                        circle_sizes=list(Grouped_Stops['Num_Lines']*2.5), 
                        stationname=list(Grouped_Stops['STATION_NAME'])))

#Create hover tool for stops
hover = HoverTool(names = ['hoverhere'],tooltips=[
    ("Stop", "@stationname"),
    ("Connectivity", "@sizes")],attachment="right")

# Create figure object.
p = figure(tools=[hover],title = 'Affordable Housing Rapid Transit Access in Chicago')



# Add patch renderer for neighborhood boundaries
neighborhoods = p.patches('xs','ys', source = geosource1,
                   fill_color = {'field' :'Address',
                                 'transform' : color_mapper},
                   line_color = "gray", 
                   line_width = 0.25, 
                   fill_alpha = 1)



# Add patch renderer for stops
stops = p.scatter(x='x',y='y', source=source_stops,
                  size='circle_sizes', 
                  line_color="#FF0000", 
                  fill_color="#FF0000",
                  fill_alpha=0.05,
                  name = 'hoverhere')


#Add Legend that varies by size
legend1 = Legend(items=[
    LegendItem(label='1 connection', renderers=[stops])
    ],glyph_height=19, glyph_width=6, location=(22,85), border_line_color = None, label_standoff=16,
                title='L Stations',title_text_align="left", title_standoff=15)

legend2 = Legend(items=[
    LegendItem(label='4 connections', renderers=[stops])],glyph_height=25, glyph_width=25,
                      location=(13,50), border_line_color = None, label_standoff=7)

legend3 = Legend(items=[
    LegendItem(label='8 connections', renderers=[stops])],glyph_height=50, glyph_width=50,
                      location=(1,1), border_line_color = None, label_standoff=-5)

p.add_layout(legend1)
p.add_layout(legend2)
p.add_layout(legend3)


#remove axes, axis labels, and grid lines
p.xaxis.major_tick_line_color = None
p.xaxis.minor_tick_line_color = None
p.yaxis.major_tick_line_color = None
p.yaxis.minor_tick_line_color = None
p.xaxis.major_label_text_font_size = '0pt'
p.yaxis.major_label_text_font_size = '0pt'
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = None


# Specify layout
p.add_layout(color_bar, 'below')

# Add Pan, Zoom, Reset, and Save Tools
p.add_tools(PanTool(),BoxZoomTool(),ZoomInTool(),ZoomOutTool(),ResetTool(),SaveTool())

show(p)


# In[418]:


#export map as html file
output_file("transit-housing.html")
save(p)


# In[419]:


#make a copy of dataframe with L stops that has shapely geometry datatype
Stops_Geom = GeoStops_Lines.copy()
Stops_Geom.drop_duplicates(subset='MAP_ID', keep="last", inplace=True) #remove dups so there's one stop / station
Stops_Geom = Stops_Geom[["MAP_ID","geometry"]]
Stops_Geom.head()


# In[420]:


#join Stops and Grouped Stops
Full_Stops = pd.merge(Stops_Geom, Grouped_Stops, on="MAP_ID")
Full_Stops = Full_Stops[["MAP_ID","geometry","STATION_NAME","Num_Lines"]]
Full_Stops.head()


# In[421]:


#spatial join on geometry to match stops with neighborhoods
spatial_joined = gpd.sjoin(housing_nbhoods, Full_Stops, how='left',op='contains')
spatial_joined = spatial_joined[["pri_neigh","Address","MAP_ID","STATION_NAME","Num_Lines"]]
spatial_joined.head()


# In[422]:


#look at neighborhoods with no L stops
spatial_joined_null = spatial_joined[spatial_joined['MAP_ID'].isnull()]
spatial_joined_null


# In[423]:


#replace neighborhoods with no L stops with 0
spatial_joined['MAP_ID'] = spatial_joined['MAP_ID'].fillna(0)
spatial_joined['Num_Lines'] = spatial_joined['Num_Lines'].fillna(0)
spatial_joined.head()


# In[424]:


#Count number of stops per neighborhood
stops_nbhoods = spatial_joined.groupby(["pri_neigh","Address","Num_Lines"]).count()[["MAP_ID"]].reset_index()
stops_nbhoods.tail(50)


# In[425]:


#Add new metric that measures number of stops*connectivity / neighborhood
stops_nbhoods["conn_dist"] = stops_nbhoods["Num_Lines"]*stops_nbhoods["MAP_ID"]
stops_nbhoods.head()


# In[426]:


#Take summed conn_dist per neighborhood
stops_nbhoods = stops_nbhoods.groupby(["pri_neigh","Address"]).sum()[["conn_dist"]].reset_index()
stops_nbhoods.head(20)


# In[427]:


#Adjust conn_dist to weight its score equally with housing
stops_nbhoods["adj_conn_dist"] = (stops_nbhoods["conn_dist"]+1)*4.5
stops_nbhoods.head()


# In[428]:


#Calculate housing-transit score
stops_nbhoods["housing_transit_score"] = ((stops_nbhoods["Address"]+1)*(stops_nbhoods["adj_conn_dist"]))-4.5
stops_nbhoods.head()


# In[429]:


#Merge neighborhoods back with geometry so data can be mapped in Bokeh
scores = pd.merge(stops_nbhoods,housing_nbhoods, on="pri_neigh")
scores = scores[["pri_neigh","geometry","Address_x","conn_dist","housing_transit_score"]]
scores["Address_x"] = scores["Address_x"].astype(int)
scores["conn_dist"] = scores["conn_dist"].astype(int)
scores["housing_transit_score"] = scores["housing_transit_score"].astype(int)
scores.tail(45)


# In[430]:


#Rename columns and create table of the 10 best neighborhoods ranked by housing-transit score
scores_table = scores[["pri_neigh","Address_x","conn_dist","housing_transit_score"]]
scores_table.rename({'pri_neigh':'Neighborhood','Address_x':'Housing Score','conn_dist':'Transit Score',},axis='columns',inplace=True)
scores_ranked = scores_table.sort_values(by="housing_transit_score", ascending=False)
top_10_scores = scores_ranked.head(10)
top_10_scores.reset_index(drop=True, inplace=True)
top_10_scores


# In[431]:



'''Create Map that scores neighborhoods by housing and transit'''

#read dataframe as geodataframe

gdf_scores = gpd.GeoDataFrame(scores, geometry='geometry')

#convert geodataframe to geojson
geosource_scores = GeoJSONDataSource(geojson=gdf_scores.to_json())


# Define color palettes
palette = brewer['Reds'][6]
palette = palette[::-1] # reverse order of colors so higher values have darker colors

# Instantiate LogColorMapper that exponentially maps numbers in a range, into a sequence of colors.
color_mapper = LogColorMapper(palette = palette, low = 0, high = 1400)

# Define custom tick labels for color bar.
tick_labels = {1.8:'0-5',6.2:'5-20',21: '20-45',70: '45-100', 225:'100-300', 760:'300+'}

# Create color bar
color_bar = ColorBar(title = 'Housing-Transit Score',
                     color_mapper = color_mapper, 
                     label_standoff = 6,
                     width = 500, height = 20,
                     border_line_color = None,
                     location = (0,0),
                     orientation = 'horizontal',
                     major_tick_line_color = None,
                     ticker=FixedTicker(num_minor_ticks=0,ticks=[1.8,6.2,21,70,225,760]),
                     major_label_overrides = tick_labels,
                     major_label_text_align = 'center')


                     

# Create figure object
fig = figure(title = 'Optimal Neighborhoods in Chicago by Housing and Transit Access')


# Add patch renderer to figure
neighborhoods = fig.patches('xs','ys', source = geosource_scores, 
                          fill_color = {'field' :'housing_transit_score','transform' : color_mapper},
                          line_color = "gray", 
                          line_width = 0.25, 
                          fill_alpha = 1)

# Create hover tool
fig.add_tools(HoverTool(renderers = [neighborhoods],
                      tooltips = [('Neighborhood','@pri_neigh'),
                                  ('Score','@housing_transit_score'),
                                  ('No. of Housing Units','@Address_x'),
                                  ('Transit Score','@conn_dist')]))

#remove axes, axis labels, and grid lines
fig.xaxis.major_tick_line_color = None
fig.xaxis.minor_tick_line_color = None
fig.yaxis.major_tick_line_color = None
fig.yaxis.minor_tick_line_color = None
fig.xaxis.major_label_text_font_size = '0pt'
fig.yaxis.major_label_text_font_size = '0pt'
fig.xgrid.grid_line_color = None
fig.ygrid.grid_line_color = None

# Specify layout
fig.add_layout(color_bar, 'below')

show(fig)


# In[432]:


#export map as html file
output_file("transit-housing-score.html")
save(fig)


# In[ ]:




