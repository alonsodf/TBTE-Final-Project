# TBTE-Final-Project
Contains all the work done for the final project in my python data analytics class.
Below are brief descriptions of each script.

**groundwater_mapV1.py**
This is the first script I created, mostly data cleaning, irrelevant.
Should probably be removed because groundwater_database.py is pretty much the same but with better data.

**groundwater_database.py**
This script takes in brackish water data from the Texas Water Development Board and well GIS from Water Data for Texas.
Merges the two data frames combining well GIS, quality (TDS) and depth.
Plots the wells on a Texas map categorizing the nodes by TDS content (lower is better) and depth (shallow is better).

**PV_GHI_functions.py**
Pull Global Horizontal Irradiance (GHI) from NREl api for well locations.
Subsitute for solar_map.py in case I cannot get it to work.

**solar_map.py**
This script generates solar curves or 8760 data and capacity factor for a PV at each well location.
Although, the Ninja.Renewables API has a limit of 50 requests per hour and I have 130 lattitude and longitude coordinates.
Tried to implement a time.sleep loop but cannot get it to work.  Also they have not responded to my request for a higher limit for weeks now...

**WUCOLS.py**
Takes in data from two sources: WUCOLS and Urban Tree Database.
WUCOLS contains a water-demand factor for multiple tree species that is multipled by a regional value to estimate water demand per (week/month/year).
Urban Tree Database has growth (allometric) equations and carbon sequestration equations for multiple tree species.
Clean data to get trees that are good in Texas and have data in both datasets.

