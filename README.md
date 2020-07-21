# Mapping Affordable Housing and Public Transit Access in Chicago
## Summary

I made a few maps that show how public transit and affordable housing intermingle by neighborhood in Chicago using pandas, geopandas, and bokeh in Python. I also wrote up a brief piece on the maps and the process, which is posted on my website [here](https://www.annagrumman.com/mapping-affordable-housing-and-public-transit-access-in-chicago/).

## Data
- [Neighborhood Boundaries in Chicago](https://data.cityofchicago.org/Facilities-Geographic-Boundaries/Boundaries-Neighborhoods/bbvz-uum9)
   - shapefile for geometry of neighborhood boundaries
- [Affordable Rental Housing Developments](https://data.cityofchicago.org/Community-Economic-Development/Affordable-Rental-Housing-Developments/s6ha-ppgi)
   - Affordable units supported by the City of Chicago to maintain affordability in local neighborhoods
- [CTA: List of 'L' Stops](https://data.cityofchicago.org/Transportation/CTA-System-Information-List-of-L-Stops/8pix-ypme)
   - Location and basic service availability information for each place on the CTA system where a train stops

## Documents

- housing_transit_Chicago.ipynb - Jupyter notebook where I housed my code and step-by-step walkthrough
- housing_transit_Chicago.py - Python script that runs the code
- [Housing map](https://www.annagrumman.com/wp-content/uploads/2020/07/housing-bokeh.html)
- [Housing with transit stops map](https://www.annagrumman.com/wp-content/uploads/2020/07/transit-housing.html)
- [Scored housing and transit access map](https://www.annagrumman.com/wp-content/uploads/2020/07/transit-housing-score-2.html)
- [Mapping Affordable Housing and Public Transit Access](https://www.annagrumman.com/mapping-affordable-housing-and-public-transit-access-in-chicago/) - blog post that analyzes the maps and explains key steps, assumptions, and metrics I used
