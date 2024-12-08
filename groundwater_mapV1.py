import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
#%%
### READ IN DATA ###
main_data = pd.read_csv('C:/Users/Alonso/OneDrive - The University of Texas at Austin/UT/Research/03 Data/GWDBDownload/WellMain.txt', sep='|', low_memory=False, encoding='latin1')
main_data = main_data.dropna(subset=['StateWellNumber'])  # Drop rows where StateWellNumber couldn't be converted
main_data['StateWellNumber'] = main_data['StateWellNumber'].astype(int)  # Convert to integers

unique_wells_with_GIS = list(main_data['StateWellNumber'])
minor_data = pd.read_csv('C:/Users/Alonso/OneDrive - The University of Texas at Austin/UT/Research/03 Data/GWDBDownload/WaterQualityMinor.txt', sep='|', low_memory=False)



major_data = pd.read_csv('C:/Users/Alonso/OneDrive - The University of Texas at Austin/UT/Research/03 Data/GWDBDownload/WaterQualityMajor.txt', sep='|', low_memory=False)
minor_data = pd.read_csv('C:/Users/Alonso/OneDrive - The University of Texas at Austin/UT/Research/03 Data/GWDBDownload/WaterQualityMinor.txt', sep='|', low_memory=False)
combination_data = pd.read_csv('C:/Users/Alonso/OneDrive - The University of Texas at Austin/UT/Research/03 Data/GWDBDownload/WaterQualityCombination.txt', sep='|', low_memory=False)

major_levels = pd.read_csv('C:/Users/Alonso/OneDrive - The University of Texas at Austin/UT/Research/03 Data/GWDBDownload/WaterLevelsMajor.txt', sep='|', low_memory=False, encoding='latin1')
minor_levels = pd.read_csv('C:/Users/Alonso/OneDrive - The University of Texas at Austin/UT/Research/03 Data/GWDBDownload/WaterLevelsMinor.txt', sep='|', low_memory=False, encoding='latin1')
combination_levels = pd.read_csv('C:/Users/Alonso/OneDrive - The University of Texas at Austin/UT/Research/03 Data/GWDBDownload/WaterLevelsCombination.txt', sep='|', low_memory=False, encoding='latin1')

#%%
### CLEAN DATA ###
## Keep only TDS data, sort by most recent year first, and drop the rest
major_TDS = major_data.loc[major_data['ParameterDescription'] == 'TOTAL DISSOLVED SOLIDS , SUM OF CONSTITUENTS (MG/L)']
minor_TDS = minor_data.loc[minor_data['ParameterDescription'] == 'TOTAL DISSOLVED SOLIDS , SUM OF CONSTITUENTS (MG/L)']
combination_TDS = combination_data.loc[combination_data['ParameterDescription'] == 'TOTAL DISSOLVED SOLIDS , SUM OF CONSTITUENTS (MG/L)']

major_TDS_sorted_by_year = major_TDS.sort_values(by=['StateWellNumber', 'SampleYear'], ascending=[True, False])
minor_TDS_sorted_by_year = minor_TDS.sort_values(by=['StateWellNumber', 'SampleYear'], ascending=[True, False])
combination_TDS_sorted_by_year = combination_TDS.sort_values(by=['StateWellNumber', 'SampleYear'], ascending=[True, False])

major_TDS_v1 = major_TDS_sorted_by_year.drop_duplicates(subset='StateWellNumber', keep='first')
minor_TDS_v1 = minor_TDS_sorted_by_year.drop_duplicates(subset='StateWellNumber', keep='first')
combination_TDS_v1 = combination_TDS_sorted_by_year.drop_duplicates(subset='StateWellNumber', keep='first')

major_TDS_unique_wells = major_TDS_v1['StateWellNumber'].nunique()
minor_TDS_unique_wells = minor_TDS_v1['StateWellNumber'].nunique()
combination_TDS_unique_wells = combination_TDS_v1['StateWellNumber'].nunique()

major_levels_sorted_by_year = major_levels.sort_values(by=['StateWellNumber', 'MeasurementYear'], ascending=[True, False])
minor_levels_sorted_by_year = minor_levels.sort_values(by=['StateWellNumber', 'MeasurementYear'], ascending=[True, False])
combination_levels_sorted_by_year = combination_levels.sort_values(by=['StateWellNumber', 'MeasurementYear'], ascending=[True, False])

major_levels_drop_na = major_levels_sorted_by_year.dropna(subset=['DepthFromLSD'])
minor_levels_drop_na = minor_levels_sorted_by_year.dropna(subset=['DepthFromLSD'])
combination_levels_drop_na = combination_levels_sorted_by_year.dropna(subset=['DepthFromLSD'])

major_levels_v1 = major_levels_drop_na.drop_duplicates(subset='StateWellNumber', keep='first')
minor_levels_v1 = minor_levels_drop_na.drop_duplicates(subset='StateWellNumber', keep='first')
combination_levels_v1 = combination_levels_drop_na.drop_duplicates(subset='StateWellNumber', keep='first')

#%%
### MERGE DATA ###
well_quality = pd.concat([major_TDS_v1, minor_TDS_v1, combination_TDS_v1], ignore_index=True)
well_quality = well_quality.drop_duplicates(subset='StateWellNumber', keep='first')
well_quality_v1 = well_quality[['StateWellNumber', 'County', 'SampleYear', 'ParameterDescription', 'ParameterUnitOfMeasure', 'ParameterValue']]

well_depth = pd.concat([major_levels_v1, minor_levels_v1, combination_levels_v1], ignore_index=True)
well_depth_v1 = well_depth[["StateWellNumber", "County", "MeasurementYear", "DepthFromLSD"]]

merge_inner = pd.merge(well_quality_v1, well_depth_v1, on='StateWellNumber', how='inner')
#%%
### READ IN GIS DATA ###
groundwater_locations = gpd.read_file('C:/Users/Alonso/OneDrive - The University of Texas at Austin/UT/Research/03 Data/TWDB_Groundwater.shp')
groundwater_loc_df = pd.DataFrame(groundwater_locations)
well_location = groundwater_loc_df[['StateWellN', 'CountyName', 'WellDepth', 'CoordDDLat', 'CoordDDLon', 'geometry']]
well_location['StateWellN'] = pd.to_numeric(well_location['StateWellN'].str.lstrip('0'), errors = 'coerce').astype('Int64')

unique_wells2 = pd.to_numeric(groundwater_loc_df['StateWellN'].str.lstrip('0'), errors = 'coerce').astype('Int64')

# %%
### MERGE TRY 2 ###
merge_location = pd.merge(merge_inner, well_location, left_on='StateWellNumber', right_on='StateWellN', how='inner')
merge_location_v1 = merge_location[['StateWellNumber', 'County_x', 'ParameterDescription', 'ParameterUnitOfMeasure', 'ParameterValue', 'SampleYear', 'DepthFromLSD', 'MeasurementYear', 'WellDepth', 'CoordDDLat', 'CoordDDLon']]
merge_location_v2 = merge_location_v1.dropna(subset=['WellDepth', 'CoordDDLat', 'CoordDDLon'])

#%%
### TX GIS DATA ###
us_counties = gpd.read_file('US_COUNTY_SHPFILE/US_county_cont.shp')
tx_county = us_counties[us_counties['STATE_NAME'] == 'Texas']
tx = tx_county.dissolve(by='STATE_NAME', aggfunc='sum')

#%%
### PLOT DATA ###

well_location_gdf = gpd.GeoDataFrame(merge_location_v1, geometry=gpd.points_from_xy(merge_location_v1.CoordDDLon, merge_location_v1.CoordDDLat))
well_location_gdf = well_location_gdf.set_crs(tx_county.crs)

base = tx.boundary.plot(edgecolor='black', markersize=2)
well_location_gdf.plot(column='ParameterValue', legend = True, ax=base, markersize=3)

well_location_gdf['size'] = well_location_gdf['WellDepth'] / well_location_gdf['WellDepth'].max() * 100

plt.scatter(
    well_location_gdf.geometry.x,  # X coordinates (Longitude)
    well_location_gdf.geometry.y,  # Y coordinates (Latitude)
    s=well_location_gdf['size'],   # Size of the circles based on depth
    color='purple',                # Circle color
    alpha=0.6                      # Transparency
)
depth_legend = [500, 1000, 4000, 8000, 12000]  # Example depths
size_legend = [d / well_location_gdf['WellDepth'].max() * 100 for d in depth_legend]  # Corresponding sizes
for size, depth in zip(size_legend, depth_legend):
    plt.scatter([], [], s=size, c='purple', alpha=0.2, label=f'{depth} feet')
plt.legend(scatterpoints=1, frameon=True, labelspacing=1, title='Well Depth (feet)', loc='lower left')

# Add title and labels
plt.title('Texas Well Depth Visualization')
plt.xlabel('Longitude')
plt.ylabel('Latitude')


