import os
import pandas as pd
import geopandas as gpd
import numpy as np
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import math
import PySAM.Pvwattsv8 as Pvwattsv8

### Read-in Data ###
water_data = pd.read_excel(r"C:\Users\Alonso\OneDrive - The University of Texas at Austin\UT\Research\03 Data\Tree\Data\WUCOLS_all_regions.xlsx")
tree_data = pd.read_csv(r"C:\Users\Alonso\OneDrive - The University of Texas at Austin\UT\Research\03 Data\Tree\Data\TS6_Growth_coefficients.csv")

### Filter tree_data to regions specific to texas ###
regions = ['GulfCo', 'Piedmt', 'InterW']
tree_data = tree_data[tree_data['Column1'].isin(regions)]

### Fuzzy match tree_data to water_data ###
tx_trees = tree_data['Scientific Name'].unique().tolist()
tx_trees.sort(reverse=False) 
tx_trees = pd.Series(tx_trees)
WUCOLS_trees = water_data['Botanical Name'].tolist()

def fuzzy_filter(WUCOLS_trees, tx_trees, threshold=80):
    matched_names = []
    for name in tx_trees:
        matches = process.extract(name, WUCOLS_trees, limit=None)  # Get all matches
        # Filter matches by threshold
        matched_names.extend([match[0] for match in matches if match[1] >= threshold])
    return list(matched_names)  # Return unique matched names

### Find approximate matches
matches = fuzzy_filter(WUCOLS_trees, tx_trees, threshold=90)
matches = list(matches)
matches.sort(reverse=False)
matches = pd.Series(matches)

### Trees that did not match
not_matches = ~tx_trees.isin(matches)
check_tress = tx_trees[not_matches]

### Trees that are good for tx but marked wrong by fuzz.  PLus list of potential add-ons 
list_of_good_trees = [
    "Butia capitata",
    "Carya illinoinensis",
    "Fraxinus angustifolia",
    "Fraxinus pennsylvanica",
    "Fraxinus angustifolia",
    "Fraxinus pennsylvanica",
    "Lagerstroemia indica",
    "Lagerstroemia spp.",
    "Malus spp.",
    "Platanus occidentalis",
    "Prunus spp.",
    "Pyrus calleryana"
]
for_sure_not_trees = check_tress[~check_tress.isin(list_of_good_trees)]

list_of_maybe_trees = [
    "Pinus echinata",
    "Platanus x acerifolia",
    "Populus angustifolia",
    "Prunus cerasifera",
    "Prunus yedoensis",
    "Quercus laurifolia",
    "Quercus nigra"
]


### Now we can drop these from tx_trees 
tx_trees = tx_trees[~tx_trees.isin(for_sure_not_trees)]
tx_trees = tx_trees[~tx_trees.isin(list_of_maybe_trees)]

### Growth equations and coefficients
growth_eqs = pd.read_csv(r"C:\Users\Alonso\OneDrive - The University of Texas at Austin\UT\Research\03 Data\Tree\Data\TS4_Growth_eqn_forms.csv")
tx_tree_data = tree_data[tree_data['Scientific Name'].isin(tx_trees)]

### Water demand data
tree_water_demand_data = water_data[water_data["Botanical Name"].isin(matches)]

### Only use region 1 data
tree_regional_data = tree_water_demand_data[["Type(s)", "Botanical Name", "Common Name", "Region 1 ET0", "Region 1 Water Use"]]

### Drop "Unknown" and assign ETO using a dictionary to trees
tree_regional_data = tree_regional_data[tree_regional_data["Region 1 Water Use"] != "Unknown"]
water_use_mapping = {
    "Very Low": 0.10,
    "Low": 0.20,
    "Moderate": 0.50,
    "High": 0.80
}
tree_regional_data['ETO'] = tree_regional_data['Region 1 Water Use'].map(water_use_mapping)


### Bring in monthly avg ETO data for different cities in Texas
monthly_avg_ETO = pd.read_excel(r"C:\Users\Alonso\OneDrive - The University of Texas at Austin\UT\Research\03 Data\Avg_monthly_ETO.xlsx")
monthly_avg_ETO.at[3, 'City'] = 'Brownsville'

### Read Tx city data
tx_cities = gpd.read_file(r'C:\Users\Alonso\OneDrive - The University of Texas at Austin\UT\Research\03 Data\Texas_Cities_1604860330021197414.geojson')
tx_cities_df = pd.DataFrame(tx_cities)

### Get the cities that are in the monthly_avg_ETO data
eto_city_names = monthly_avg_ETO['City'].tolist()
tx_city_names = tx_cities.loc[tx_cities['CITY_NM'].isin(eto_city_names), 'CITY_NM'].tolist()

tx_cities_filtered = tx_cities.loc[tx_cities['CITY_NM'].isin(tx_city_names)]
tx_cities_filtered = tx_cities_filtered[['CITY_NM', 'geometry']]
tx_cities_filtered_df = pd.DataFrame(tx_cities_filtered)

### Read in well data
well_GIS = gpd.read_file(r"C:\Users\Alonso\OneDrive - The University of Texas at Austin\UT\Research\03 Data\well_GIS.geojson")
well_GIS_df = pd.DataFrame(well_GIS)

#%%
### Calculating water demand for each tree at each well ###
### Apply water_demand for a 1 acre plot, 550 trees ###
num_trees_per_acre = 550
acres = 1
total_trees = num_trees_per_acre * acres
def calculate_water_demand(monthly_avg_ETO, tree_regional_data, well_GIS_df, total_trees):
    water_demand_results = []

    for _, well in well_GIS_df.iterrows():
        nearest_city = well['nearest_city']
        city_eto = monthly_avg_ETO[monthly_avg_ETO['City'] == nearest_city].iloc[0, 1:] # Get the ETO data for the city

        for _, tree in tree_regional_data.iterrows():
            tree_species = ['Botanical Name']
            tree_factor = tree['ETO']

            monthly_demand = city_eto * tree_factor * total_trees * (1/12) # Monthly demand in acre-feet
            monthly_demand = monthly_demand.round()

            monthly_demand_results = {
                'Well_ID': well['state_well_number'],
                'Nearest_City': nearest_city,
                "Distance": round(well['distance']),
                'Species': tree['Botanical Name'],
                'Monthly_Demand': monthly_demand.to_dict()
            }
            water_demand_results.append(monthly_demand_results)
    
    water_demand_results_df = pd.DataFrame(water_demand_results)
    return water_demand_results_df

water_demand_results_df = calculate_water_demand(monthly_avg_ETO, tree_regional_data, well_GIS_df, total_trees)


#%%
### Convert to daily consumption m^3/day ###
def convert_acre_ft_to_m3_per_day(water_demand_results_df):
    # Conversion factor
    acre_ft_to_m3 = 1233.48
    
    # Initialize an empty list to store the results
    results = []

    # Loop through each row in the water_demand_results_df
    for _, row in water_demand_results_df.iterrows():
        monthly_demand = row['Monthly_Demand']
        monthly_demand_m3_per_day = {}
        
        # Loop through each month and convert the demand
        for month, demand_acre_ft in monthly_demand.items():
            days_in_month = pd.Period(month, freq='M').days_in_month
            demand_m3_per_day = (demand_acre_ft * acre_ft_to_m3) / days_in_month
            monthly_demand_m3_per_day[month] = demand_m3_per_day
        
        # Store the result
        result = {
            'Well_ID': row['Well_ID'],
            'Tree_Species': row['Species'],
            'Nearest_City': row['Nearest_City'],
            'Distance': row['Distance'],
            'Daily_Demand_Per_Month': monthly_demand_m3_per_day
        }
        results.append(result)
    
    # Convert the results to a dataframe
    results_df = pd.DataFrame(results)
    return results_df

# Example usage
# Assuming water_demand_results_df is already created
water_demand_m3_per_day_df = convert_acre_ft_to_m3_per_day(water_demand_results_df)

# %%
### Merge tree data with energy schedule data ###
energy_schedule = pd.read_csv(r"C:\Users\Alonso\OneDrive - The University of Texas at Austin\UT\Research\03 Data\energy_schedule.csv")
energy_schedule = energy_schedule.drop(columns=['Unnamed: 0'])

# Filter tree data to only include trees in the energy schedule
tree_data = tree_data[tree_data['Scientific Name'].isin(energy_schedule['Tree_Species'])]
energy_schedule = energy_schedule[energy_schedule['Tree_Species'].isin(tree_data['Scientific Name'])]


#%%

def weather_file_match(nearest_city, monthly_kW_demand):
    model = Pvwattsv8.default('PVWattsNone')
    model.SystemDesign.system_capacity = 1 # kw
    model.SolarResource.solar_resource_file = os.path.join('Weather', f'{nearest_city}.epw')
    model.execute()
    model.Outputs.ac_monthly
    model.Outputs.monthly_energy
    model.Outputs.ac_annual
    model.Outputs.gen
    model.Outputs.capacity_factor
    model.Outputs.gh
    model.Outputs.solrad_monthly
    


for (well_id, species), wdata in energy_schedule.groupby(['Well_ID', 'Tree_Species']):
    nearest_city = well_GIS_df[well_GIS_df['state_well_number']==str(well_id)]['nearest_city'].iloc[0]
    monthly_kW_demand = wdata['Total_Power_kW'].tolist()
    weather_file_match(nearest_city, monthly_kW_demand)


# %%
### Generate growth equations for each tree ###

mse = #Sigma column ^2

def loglogw1_dbh(a, b, age, mse):
    return math.exp(a + b * math.log(math.log(age) + (mse / 2)))

def loglogw1_age(a, b, dbh, mse):
    return math.exp(a + b * math.log(math.log(dbh + 1) + (mse / 2)))

def loglogw2_dbh(a, b, age, mse):
    return math.exp(a + b * math.log(math.log(age)) + (math.sqrt(age) * (mse / 2)))

def loglogw2_age(a, b, dbh, mse):
    return math.exp(a + b * math.log(math.log(dbh + 1)) + (math.sqrt(dbh) * (mse / 2)))

def loglogw3_dbh(a, b, age, mse):
    return math.exp(a + b * math.log(math.log(age)) + age + (mse / 2))

def loglogw3_age(a, b, dbh, mse):
    return math.exp(a + b * math.log(math.log(dbh + 1)) + dbh + (mse / 2))

def loglogw4_dbh(a, b, age, mse):
    return math.exp(a + b * math.log(math.log(age)) + (age**2) + (mse / 2))

def loglogw4(a, b, dbh, mse):
    return math.exp(a + b * math.log(math.log(dbh + 1)) + (dbh**2) + (mse / 2))

def lin_dbh(a, b, age):
    return a + b * age

def lin_age(a, b, dbh):
    return a + b * dbh

def quad(a, b, c, x):
    return a + b * x + c * (x**2)

def cub(a, b, c, d, x):
    return a + b * x + c * (x**2) + d * (x**3)

def quart(a, b, c, d, e, x):
    return a + b * x + c * (x**2) + d * (x**3) + e * (x**4)

def expow1_dbh(a, b, age, mse):
    return math.exp(a + b * age + (mse / 2))

def expow1_age(a, b, dbh, mse):
    return math.exp(a + b * dbh + (mse / 2))

def expow2_dbh(a, b, age, mse):
    return math.exp(a + b * age + math.sqrt(age) + (mse / 2))

def expow2_age(a, b, dbh, mse):
    return math.exp(a + b * dbh + math.sqrt(dbh) + (mse / 2))

def expow3_dbh(a, b, age, mse):
    return math.exp(a + b * age + age + (mse / 2))

def expow3_age(a, b, dbh, mse):
    return math.exp(a + b * dbh + dbh + (mse / 2))

def expow4_dbh(a, b, age, mse):
    return math.exp(a + b * age + (age**2) + (mse / 2))

def expow4_age(a, b, dbh, mse):
    return math.exp(a + b * dbh + (dbh**2) + (mse / 2))
