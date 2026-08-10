# \# IrishPropertyPrices

# 

# Analysing Irish residential property prices using the Property Price Register and SEAI BER data. Covers data cleaning, geospatial analysis, price modelling and a Streamlit valuation tool.

# 

# \*\*Status:\*\* in progress

# 

# \## Overview

# 

# \[One paragraph - fill in once the shape is clear]

# 

# \## Data Sources

# 

# \- \*\*Property Price Register\*\* - every residential sale in Ireland since 2010. Actual sale prices, not asking prices. https://www.propertypriceregister.ie

# \- \*\*SEAI BER Research Tool\*\* - property characteristics including floor area, dwelling type, year built and energy rating. https://ndber.seai.ie

# \- \*\*CSO Residential Property Price Index\*\* - used for time-adjusting historical prices. https://data.cso.ie

# 

# \## Planned Approach

# 

# 1\. Data collection and schema inspection

# 2\. Cleaning - VAT adjustment on new builds, filtering non-market sales, address normalisation

# 3\. Exploratory analysis - price trends by county and Eircode routing key over time

# 4\. Price modelling

# 5\. Streamlit valuation tool

# 6\. Automated monthly data refresh via GitHub Actions

# 

# \## Notes on the Data

# 

# \- New build prices in the PPR are listed \*\*excluding VAT\*\* at 13.5%. A flag identifies these.

# \- Sales flagged as "not full market price" are non-arms-length transactions and are excluded.

# \- Eircode coverage in the PPR is incomplete, particularly in earlier years.

# \- Analysis is conducted at \*\*Eircode routing key\*\* level (the first three characters). Full Eircodes are unique per property and the complete address database is licensed.

# 

# \## Setup

# 

# \[To follow]

# 

# \## Author

# 

# David Heffernan | \[GitHub](https://github.com/DavidHeffernan94) | \[LinkedIn](https://www.linkedin.com/in/david-heffernan-871a85192/)

# 

# \## License

# 

# MIT

