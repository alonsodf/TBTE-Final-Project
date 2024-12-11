import pandas as pd
import geopandas as gpd

water_demand = pd.read_csv(r"C:\Users\Alonso\OneDrive - The University of Texas at Austin\UT\Research\03 Data\water_demand_daily.csv")
well_GIS = gpd.read_file(r"C:\Users\Alonso\OneDrive - The University of Texas at Austin\UT\Research\03 Data\well_GIS.geojson")
well_GIS_df = pd.DataFrame(well_GIS)
well_GIS_df = well_GIS_df[well_GIS_df['ParameterValue'] >= 500]

#%%
### Pressure Calculations ###
# Constants
water_density = 1000  # kg/m^3
grav = 9.81  # m/s^2

# Initialize an empty list to store the results
pressure_results = []

# Loop through each well
for _, well in well_GIS_df.iterrows():
    well_id = well['state_well_number'] 
    depth_ft = well['daily_high_water_level(ft below land surface)']
    depth_m = depth_ft * 0.3048  # Convert depth from feet to meters
    
    # Calculate static well pressure
    static_well_pressure = water_density * grav * depth_m
    
    # Calculate osmotic pressure
    TDS_concentration = well['ParameterValue']
    osmotic_pressure = TDS_concentration / 100  # Unit is psi
    
    # Calculate more pressure
    more_pressure = 0.20 * osmotic_pressure  # SF for pressure rating
    
    # Calculate total pressure
    total_pressure = static_well_pressure + osmotic_pressure + more_pressure
    
    # Store the result in a dictionary
    result = {
        'Well_ID': well_id,
        'Static_P': round(static_well_pressure),
        'Osmotic_P': osmotic_pressure,
        'Total_P': round(total_pressure)
    }
    pressure_results.append(result)

# Convert the results to a dataframe
pressure_df = pd.DataFrame(pressure_results)