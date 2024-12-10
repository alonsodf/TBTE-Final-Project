import pandas as pd
import numpy as np
import json
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import contextily as ctx
import requests, time
import shapely.geometry import Point

# This is using well depth and geospatial data from https://waterdatafortexas.org/groundwater
# And TDS data from  http://www.twdb.texas.gov/groundwater/data/gwdbrpt.asp

#%%
### READ IN DATA ###
well_depths = pd.read_csv('C:/Users/Alonso/OneDrive - The University of Texas at Austin/UT/Research/03 Data/recent-conditions.csv')
well_metadata = gpd.read_file('C:/Users/Alonso/OneDrive - The University of Texas at Austin/UT/Research/03 Data/well-metadata.geojson')

major_data = pd.read_csv('C:/Users/Alonso/OneDrive - The University of Texas at Austin/UT/Research/03 Data/GWDBDownload/WaterQualityMajor.txt', sep='|', low_memory=False)
minor_data = pd.read_csv('C:/Users/Alonso/OneDrive - The University of Texas at Austin/UT/Research/03 Data/GWDBDownload/WaterQualityMinor.txt', sep='|', low_memory=False)
combination_data = pd.read_csv('C:/Users/Alonso/OneDrive - The University of Texas at Austin/UT/Research/03 Data/GWDBDownload/WaterQualityCombination.txt', sep='|', low_memory=False)

#%%
### WORK FLOW ###
well_metadataDF = pd.DataFrame(well_metadata) # Convert geopandas dataframe to pandas dataframe
#well_metadataDF = well_metadataDF[well_metadataDF['status'] == 'Active']  # Remove inactive wells
well_metadataDF['well_number'] = well_metadataDF['well_number'].str.lstrip('0') # Remove leading zeros from well_number

## Filter the TDS data
major_TDS = major_data.loc[major_data['ParameterDescription'] == 'TOTAL DISSOLVED SOLIDS , SUM OF CONSTITUENTS (MG/L)']
minor_TDS = minor_data.loc[minor_data['ParameterDescription'] == 'TOTAL DISSOLVED SOLIDS , SUM OF CONSTITUENTS (MG/L)']
combination_TDS = combination_data.loc[combination_data['ParameterDescription'] == 'TOTAL DISSOLVED SOLIDS , SUM OF CONSTITUENTS (MG/L)']

# Sort data by most recent year first for TDs data
major_TDS = major_TDS.sort_values(by=['StateWellNumber', 'SampleYear'], ascending=[True, False])
minor_TDS = minor_TDS.sort_values(by=['StateWellNumber', 'SampleYear'], ascending=[True, False])
combination_TDS = combination_TDS.sort_values(by=['StateWellNumber', 'SampleYear'], ascending=[True, False])

# Keep only the most recent samples taken for TDS data
major_TDS = major_TDS.drop_duplicates(subset='StateWellNumber', keep='first')
minor_TDS = minor_TDS.drop_duplicates(subset='StateWellNumber', keep='first')
combination_TDS = combination_TDS.drop_duplicates(subset='StateWellNumber', keep='first')

## Merging data
well_TDS = pd.concat([major_TDS, minor_TDS, combination_TDS], ignore_index=True)
well_TDS = well_TDS.drop_duplicates(subset='StateWellNumber', keep='first')
well_TDS = well_TDS[['StateWellNumber', 'County', 'SampleYear', 'ParameterDescription', 'ParameterUnitOfMeasure', 'ParameterValue']]

# Get the wells that had geospatial data and well depth data by merging inner
well_depths['state_well_number'] = well_depths['state_well_number'].astype(str)  # Convert to string
merge_inner = pd.merge(well_depths, well_metadataDF, left_on='state_well_number', right_on='well_number', how='inner')
merge_inner.drop('well_number', axis=1, inplace=True)  # Drop the well_number column

# Get the wells that only have geospatial and TDS data by merging inner
well_TDS['StateWellNumber'] = well_TDS['StateWellNumber'].astype(str)  # Convert to string
merge_inner2 = pd.merge(merge_inner, well_TDS, left_on='state_well_number', right_on='StateWellNumber', how='inner')

# Get all the geospatial data wells and add TDS data to those that have them
merge_left = pd.merge(merge_inner, well_TDS, left_on='state_well_number', right_on='StateWellNumber', how='left')
merge_left = merge_left.drop(['StateWellNumber', 'County', 'SampleYear'], axis=1)  # Drop columns that are not needed

## Convert to geodataframes
wells_geo_with_TDS = gpd.GeoDataFrame(merge_inner2)
wells_geo_with_TDS = wells_geo_with_TDS.drop(['StateWellNumber'], axis=1)
wells_all_geo = gpd.GeoDataFrame(merge_left)


# Get Texas GIS data
us_counties = gpd.read_file(r'c:\Users\Alonso\OneDrive - The University of Texas at Austin\UT\Research\03 Data\US_COUNTY_SHPFILE\US_county_cont.shp')
tx_county = us_counties[us_counties['STATE_NAME'] == 'Texas']
tx = tx_county.dissolve(by='STATE_NAME', aggfunc='sum')


#%%
### Plotting ###
wells_all_geo = wells_all_geo.to_crs(epsg=3857)
tx = tx.to_crs(epsg=3857)
fig1, ax1 = plt.subplots(figsize=(12, 13))
tx.plot(ax=ax1, color='white', edgecolor='black')

# Define bins and labels for well depth
bins_depth = [100, 250, 500, 750, 1000, 1250]
labels_depth = ['100 - 250 feet', '251 - 500 feet', '501 - 750 feet', '751 - 1000 feet', '1001 - 1250 feet']

# Use pd.cut to categorize the 'daily_high_water_level(ft below land surface)' column
wells_all_geo['depth_category'] = pd.cut(wells_all_geo['daily_high_water_level(ft below land surface)'], bins=bins_depth, labels=labels_depth)

for category in wells_all_geo['depth_category'].unique():
    well_category = wells_all_geo[wells_all_geo['depth_category'] == category]
    well_category.plot(
        ax=ax1, 
        markersize=well_category['daily_high_water_level(ft below land surface)'] / 1,
        color='blue', edgecolor='black', 
        label=category, 
        alpha=0.6,
    )

# Customize legend for well depth
handles, labels = ax1.get_legend_handles_labels()
sorted_handles_labels1 = sorted(zip(handles, labels), key=lambda x: int(x[1].split()[0]))
sorted_handles1, sorted_labels1 = zip(*sorted_handles_labels1)

# Update the legend with sorted handles and labels
ax1.legend(sorted_handles1, sorted_labels1, title="Well Depth", title_fontsize='xx-large', fontsize='xx-large', loc='lower left')

# Display the plot
plt.axis('off')
#plt.show()

#%%
### Plotting ###
wells_all_geo = wells_all_geo.to_crs(epsg=3857)
tx = tx.to_crs(epsg=3857)
fig, ax = plt.subplots(figsize=(12, 13))
tx.plot(ax=ax, color='white', edgecolor='black')

wells_all_geo['tds_category'] = pd.cut(wells_all_geo['ParameterValue'],
    bins=[0, 300, 600, 900, 1200, 1800, 2700],
    labels=['0 - 300 TDS', '300 - 600 TDS', '600 - 900 TDS', '900 - 1200 TDS', '1200  - 1800 TDS', '1800 - 2700 TDS'])

for category in wells_all_geo['tds_category'].unique():
    well_category = wells_all_geo[wells_all_geo['tds_category'] == category]
    well_category.plot(
        ax=ax, 
        markersize=well_category['ParameterValue'] / 1,
        color='red', edgecolor='black', 
        label=category, 
        alpha=0.6,
        )
# Customize legend
sorted_handles_labels2 = sorted(zip(handles, labels), key=lambda x: int(x[1].split()[0]))
sorted_handles2, sorted_labels2 = zip(*sorted_handles_labels2)

# Update the legend with sorted handles and labels
ax.legend(sorted_handles2, sorted_labels2, title="TDS Levels", title_fontsize='xx-large', fontsize='xx-large')

# Display the plot
plt.axis('off')
#plt.show()

# %%
### Getting coordinates ###
tx_city_coords = gpd.read_file(r'c:\Users\Alonso\OneDrive - The University of Texas at Austin\UT\Research\03 Data\tx_cities_filtered.geojson')

## Matching wells with cities to pair with monthly ETo data
wells_geo_with_TDS = wells_geo_with_TDS.to_crs("EPSG:3857")
tx_city_coords = tx_city_coords.to_crs("EPSG:3857")

wells_with_nearest_city = gpd.sjoin_nearest(wells_geo_with_TDS, tx_city_coords, how="left", distance_col="distance")
df_wells_with_nearest_city = pd.DataFrame(wells_with_nearest_city)

wells_geo_with_TDS['nearest_city'] = wells_with_nearest_city['CITY_NM']
wells_geo_with_TDS['distance'] = wells_with_nearest_city['distance'] * 0.000621371  # Convert meters to miles

df_wells_GIS = pd.DataFrame(wells_geo_with_TDS)


#lat = wells_geo_with_TDS.geometry.x
#lon = wells_geo_with_TDS.geometry.y
#lat = list(lat)
#lon = list(lon)
