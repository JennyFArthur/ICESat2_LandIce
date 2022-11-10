"""
@author: jennifer.arthur@npolar.no
Modified from IcePyx documentation https://icepyx.readthedocs.io/en/latest/example_notebooks/IS2_data_access.html

This script subsets and orders ICESat-2 data from NASA Earthdata, then reads in and visualises the data and converts to shapefile.
"""

import icepyx as ipx
import os
import shutil
from pprint import pprint
import numpy
import pandas as pd
from shapely.geometry import Point
import geopandas
import os
# matplotlib inline

#######Create an ICESat-2 data object with the desired search parameters ############################

## Option 1: define a bounding box
# short_name = 'ATL06'
# spatial_extent = [36.02, -78.25, 41.98, -76.97]
# date_range = ['2018-12-31','2018-12-31']

## Option 2: polygon geospatial file (metadata match but no subset match)
# short_name = 'ATL06'
# spatial_extent = './supporting_files/data-access_PineIsland/glims_polygons.kml'
# date_range = ['2018-12-31','2018-12-31']

## Option 3: polygon geospatial file (subset and metadata match)
short_name = 'ATL06'
spatial_extent = "StudyArea.shp"
date_range = ['2020-01-01','2020-02-28']
#version = '005' #if not specified, most recent product version used

##Create the data object using inputs and orbital parameters with one of the above data products + spatial parameters
region_a = ipx.Query(short_name, spatial_extent, date_range)

#region_a = ipx.Query(short_name, spatial_extent,
#   cycles=['03','04','05','06','07'], tracks=['0849','0902'])

print('Product:', region_a.product)
print('Product version:', region_a.product_version)
print('Cycles:', region_a.cycles) #orbital cycle = 91-day repeat period of the ICESat-2 orbit.
print('Tracks:', region_a.tracks) #Which Reference Ground Track (RGT) to use.
print('Spatial extent:', region_a.spatial_extent)
region_a.visualize_spatial_extent()

##Get info about data product and confirm latest version is selected
region_a.product_summary_info()
#print(region_a.latest_version())



#######Query ICESat-2 data object with desired search parameters  ################################

#build and view the parameters that will be submitted in our query
region_a.CMRparams

#search for available granules and provide basic summary info about them
region_a.avail_granules()

#get a list of granule IDs for the available granules
region_a.avail_granules(ids=True)

#print detailed information about the returned search results
print('Available granules:', region_a.granules.avail)

#Log in to NASA Earthdata
earthdata_uid = 'enter Earthdata username'
email = 'enter email' #will be prompted for password
region_a.earthdata_login(earthdata_uid, email)

print(region_a.reqparams)
# region_a.reqparams['page_size'] = 9 #9 granules to be processed in each zipped request
# print(region_a.reqparams)

region_a.subsetparams() #default subsetting of ATL06 product
region_a._geom_filepath




#######Select desired ICESat-2 data variables ###############################################

#show all variable + path combinations as a dictionary to increase readability
print('ICESat-2 path+variable strings:', region_a.order_vars.parse_var_list(region_a.order_vars.avail()))  

#build wanted variables list
region_a.order_vars.wanted #this is where the variable request list is stored
region_a.order_vars.append(defaults=True,var_list=['latitude','longitude'])#append..\
    #..new variables to list across all six beam groups. Time and spacecraft orientation included by default.
region_a.order_vars.append(defaults=True,var_list=['atl06_quality_summary','cycle_number','rgt','sc_orient']) 
region_a.order_vars.append(defaults=True,var_list=['h_li','h_li_sigma','sigma_geo_h']) 
region_a.order_vars.append(defaults=True,var_list=['start_geoseg','end_geoseg'])
region_a.order_vars.append(defaults=True,var_list=['dh_fit_dx','dh_fit_dy','dh_fit_dx_sigma'])
pprint(region_a.order_vars.wanted)
region_a.subsetparams(Coverage=region_a.order_vars.wanted)
#Use wanted variables list within icepyx object
print('ICESat-2 subset parameters:', region_a.subsetparams(Coverage=region_a.order_vars.wanted))




#######Order ICESat-2 data object with the desired search parameters #################################

region_a.order_granules(verbose=True, subset=True, email=True)

region_a.granules.orderIDs #view a short list of order IDs

##Order and download desired ICESat-2 data granules
path = 'File path for file download location'
region_a.download_granules(path)

#region_a.visualize_spatial_extent()




#######Read in ICESat-2 data  #################################

path_root = 'Filepath for downloaded files'


##Create a filename pattern for data files
pattern = "processed_ATL{product:2}_{datetime:%Y%m%d%H%M%S}_{rgt:4}{cycle:2}{orbitsegment:2}_{version:3}_{revision:2}.h5"

##Create an icepyx read object
reader = ipx.Read(data_source=path_root, product="ATL06", filename_pattern=pattern) # or ipx.Read(filepath, "ATLXX") if your filenames match the default pattern
reader._filelist

##Specify variables to be read in
#reader.vars.avail() #long list of all available path + variable combinations that can be read in
reader.vars.append(var_list=['h_li', 'latitude', 'longitude', 'atl06_quality_summary', 'cycle_number','rgt'])

##View dictionary of variables to read in
reader.vars.wanted

##Read IceSat2 data into memory (reads in multiple variables at once)
ds = reader.load() #loads data by creating an Xarray DataSet for each input granule and then merging them.
ds
ds.plot.scatter(x="longitude", y="latitude", hue="h_li", vmin=-100, vmax=2000)

##Convert IceSat2 merged Xarray dataset to shapefile for visualising in GIS
df = ds.to_dataframe() #convert dataset to a tidy dataframe
pdf = pd.DataFrame(df) # convert dataframe into a numpy array
pdf
pdf['geometry'] = df.apply(lambda x: Point((float(x.longitude), float(x.latitude))), axis=1) #create new geometry column in dataframe combining lat/lon into a shapely point() object
pdf = geopandas.GeoDataFrame(df, geometry='geometry') #convert pandas DataFrame into a GeoDataFrame
pdf['data_end_utc'] = pdf['data_end_utc'].dt.strftime("%Y-%m-%d") #convert datetime information to a string
pdf['delta_time'] = pdf['delta_time'].dt.strftime("%Y-%m-%d") 
pdf['atlas_sdp_gps_epoch'] = pdf['atlas_sdp_gps_epoch'].dt.strftime("%Y-%m-%d") 
#pdf.to_file('Shapefile filepath', driver='ESRI Shapefile') #convert GeoDataFrame into shapefile
output_path = 'Enter output filepath'

pdf.to_file((os.path.join(output_path, 'shapefile name.shp')), driver='ESRI Shapefile') #convert GeoDataFrame into shapefile
