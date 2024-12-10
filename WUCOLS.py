import pandas as pd
import geopandas as gpd
import numpy as np
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

#%%
### Read-in Data ###
water_data = pd.read_excel(r"C:\Users\Alonso\OneDrive - The University of Texas at Austin\UT\Research\03 Data\Tree\Data\WUCOLS_all_regions.xlsx")
tree_data = pd.read_csv(r"C:\Users\Alonso\OneDrive - The University of Texas at Austin\UT\Research\03 Data\Tree\Data\TS6_Growth_coefficients.csv")

#%%
### Filter tree_data to regions specific to texas ###
regions = ['GulfCo', 'Piedmt', 'InterW']
tree_data = tree_data[tree_data['Column1'].isin(regions)]

#%%
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

#%%
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

#%%
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

#%%
### Bring in monthly avg ETO data for different cities in Texas
monthly_avg_ETO = pd.read_excel(r"C:\Users\Alonso\OneDrive - The University of Texas at Austin\UT\Research\03 Data\Avg_monthly_ETO.xlsx")


### Read Tx city data
tx_cities = gpd.read_file(r'C:\Users\Alonso\OneDrive - The University of Texas at Austin\UT\Research\03 Data\Texas_Cities_1604860330021197414.geojson')
tx_cities_df = pd.DataFrame(tx_cities)
