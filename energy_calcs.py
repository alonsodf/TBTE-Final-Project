import pandas as pd
import geopandas as gpd
import ast

water_demand = pd.read_csv(r"C:\Users\Alonso\OneDrive - The University of Texas at Austin\UT\Research\03 Data\water_demand_daily.csv")
well_GIS = gpd.read_file(r"C:\Users\Alonso\OneDrive - The University of Texas at Austin\UT\Research\03 Data\well_GIS.geojson")
well_GIS_df = pd.DataFrame(well_GIS)
well_GIS_df = well_GIS_df[well_GIS_df['ParameterValue'] >= 500]

#%%
### Pressure Calculations ###
# Constants
water_density = 1000  # kg/m^3
grav = 9.81  # m/s^2

pressure_results = []
# Loop through each well
for _, well in well_GIS_df.iterrows():
    well_id = well['state_well_number'] 
    depth_ft = well['daily_high_water_level(ft below land surface)']
    depth_m = depth_ft * 0.3048  # Convert depth from feet to meters
    
    # Calculate static well pressure
    static_well_pressure = water_density * grav * depth_m * (1/6895)  # Convert to psi
    
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
pressure_df = pd.DataFrame(pressure_results)

#%%
### Flow Rate Calculations ###

# Convert string representation of dictionaries to actual dictionaries
water_demand['Daily_Demand_Per_Month'] = water_demand['Daily_Demand_Per_Month'].apply(ast.literal_eval)

# Operational hours per day (example value)
operational_hours_per_day = 8

# Function to calculate flow rate for each month
def calculate_flow_rate(daily_demand_dict):
    flow_rate_dict = {}
    for month, daily_demand in daily_demand_dict.items():
        flow_rate = daily_demand / (operational_hours_per_day * 3600)
        flow_rate_dict[month] = flow_rate
    return flow_rate_dict

# Apply the function to the DataFrame
water_demand['Flow_Rate_m3_per_s'] = water_demand['Daily_Demand_Per_Month'].apply(calculate_flow_rate)

#%%
### Energy Calculations ###
# Merge the DataFrames on 'Well_ID'
water_demand['Well_ID'] = water_demand['Well_ID'].astype(int)
well_GIS_df['state_well_number'] = well_GIS_df['state_well_number'].astype(int)

merged_df = pd.merge(water_demand, well_GIS_df, left_on='Well_ID', right_on='state_well_number')

# Constants
pump_efficiency = 0.6
specific_weight = 9810  # N/m^3
RO_coefficient = 1000  # N*L/m^2 mg
TDS_out = 500  # mg/L
operational_hours_per_day = 8

# Function to calculate flow rate for each month
def calculate_flow_rate(daily_demand_dict):
    flow_rate_dict = {}
    for month, daily_demand in daily_demand_dict.items():
        flow_rate = daily_demand / (operational_hours_per_day * 3600)
        flow_rate_dict[month] = flow_rate
    return flow_rate_dict

# Function to calculate pumping power
def pumping_power(pump_efficiency, specific_weight, well_depth, flow_rate):
    return (specific_weight * well_depth * flow_rate) / pump_efficiency  # Watts

# Function to calculate RO power
def RO_power(RO_coefficient, TDS_in, TDS_out, flow_rate):
    return RO_coefficient * (TDS_in - TDS_out) * flow_rate  # Watts

# Function to calculate total power
def total_power(pump_power, RO_power):
    return pump_power + RO_power  # Watts

# Calculate power for each well
power_results = []
for index, row in merged_df.iterrows():
    well_id = row['Well_ID']
    well_depth = row['daily_high_water_level(ft below land surface)'] * 0.3048  # Convert depth from feet to meters
    TDS_in = row['ParameterValue']
    flow_rates = calculate_flow_rate(row['Daily_Demand_Per_Month'])
    
    for month, flow_rate in flow_rates.items():
        pump_power = pumping_power(pump_efficiency, specific_weight, well_depth, flow_rate)
        ro_power = RO_power(RO_coefficient, TDS_in, TDS_out, flow_rate)
        total_power_consumption = total_power(pump_power, ro_power)
        
        result = {
            'Well_ID': well_id,
            'Tree_Species': row['Tree_Species'],
            'Month': month,
            'Pump_Power_W': round(pump_power) * (1/1000),
            'RO_Power_W': round(ro_power)* (1/1000),
            'Total_Power_W': round(total_power_consumption)* (1/1000)
        }
        power_results.append(result)
power_df = pd.DataFrame(power_results)

# %%
### Extract flow rates from dictonary ###
# Expand the dictionaries into rows
rows = []
for index, row in water_demand.iterrows():
    daily_demand = row['Daily_Demand_Per_Month']
    flow_rate = row['Flow_Rate_m3_per_s']
    for month in daily_demand.keys():
        rows.append({
            'Well_ID': row['Well_ID'],
            'Month': month,
            'Daily_Demand': daily_demand[month],
            'Flow_Rate': flow_rate[month]
        })

# Create a new DataFrame from the rows
water_demand_result = pd.DataFrame(rows)

# %%
# Expand the dictionaries into rows
rows = []
for index, row in water_demand.iterrows():
    daily_demand = row['Daily_Demand_Per_Month']
    flow_rate = row['Flow_Rate_m3_per_s']
    for month in daily_demand.keys():
        rows.append({
            'Well_ID': row['Well_ID'],
            'Tree_Species': row['Tree_Species'],
            'Month': month,
            'Daily_Demand': daily_demand[month],
            'Flow_Rate': flow_rate[month]
        })

# Create a new DataFrame from the rows
water_demand_result = pd.DataFrame(rows)

water_demand_result['Well_ID'] = water_demand_result['Well_ID'].astype(int)
power_df['Well_ID'] = power_df['Well_ID'].astype(int)
pressure_df['Well_ID'] = pressure_df['Well_ID'].astype(int)

# Merge the DataFrames on 'Well_ID', 'Month', 'Tree_Species'
merged_output = pd.merge(water_demand_result, power_df, on=['Well_ID', 'Tree_Species', 'Month'])
merged_output = pd.merge(merged_output, pressure_df, on='Well_ID')
# %%
