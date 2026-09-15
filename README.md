# IrishPropertyPrices

Analysing 750,000 Irish residential property sales from 2010 to present, and testing whether sale prices can be predicted from publicly available data.

**[Explore the data →](https://irish-property-prices.streamlit.app)**

**Headline finding:** they can't, at property level. Around 61% of price variation occurs *within* Eircode routing keys rather than between them, and no public dataset provides the property-level characteristics needed to explain it. Models reach 25.4% median absolute percentage error against a theoretical ceiling of 25.1% - the available features are effectively exhausted.

This is a privacy constraint rather than a data quality problem, and the analysis quantifying it is the substance of the project.

## Overview

The Property Price Register records every residential sale in Ireland with address and price. The SEAI BER register records dwelling characteristics - floor area, dwelling type, year built, energy rating. Joining them at property level would support genuine hedonic price modelling.

That join is not possible from public data. A BER assessment includes the property address and MPRN, making it personal data under GDPR, and the public research extract removes both. The `SA_Code` field that would have provided CSO Small Area geography is present in the schema but entirely null across all 1.4 million records.

BER data can therefore only be joined at area level, where it adds nothing a location identifier does not already encode. The project documents this constraint, establishes what the data *does* support, and scopes its output accordingly.

## Key Findings

**Market trend.** Prices fell 31% from 2010 to a 2013 trough of €149,796, then rose 161% to €390,440 by 2026. Growth peaked at 15.8% in 2017 and has settled at 8-10% annually since 2021.

**Geography matters more than county.** Within Dublin, the dearest routing key is 2.34 times the cheapest. Dublin 14 has a median of €711,000 against Dublin 10 at €324,500. County-level analysis treats these as the same location.

**Price per square metre spans 5.3 to 1**, from €7,439 in Dublin 6 to €1,396 in Donegal - considerably wider than the 2.7 to 1 range on headline price, because Dublin's higher prices come attached to smaller dwellings.

**The new build premium is genuine, not composition.** Comparing new against second-hand within the same routing key gives a 25% premium, close to the 27% national figure. It has compressed from over 50% in the late 2010s as construction output recovered.

**Seasonality is strong on volume, weak on price.** December runs 41% above the average month and January 29% below; every one of the ten busiest months in the dataset is a December. Detrended prices vary only 7.6% across the calendar.

**Dublin and the rest of the country have diverged.** Since 2021 the ex-Dublin price index rose 57.7% against Dublin's 41.1%.

## Application

An interactive Streamlit application presents the area-level findings:

- **Area explorer** - price trends, distribution, housing stock characteristics and recent sales for any of 137 Eircode routing keys
- **Compare areas** - two or three areas side by side, with overlaid trends showing whether gaps are widening or closing
- **National trends** - the full 2010 to present series, county rankings, the Dublin divergence, new build premium and seasonality
- **Method and limitations** - the variance decomposition, model results, and why a valuation tool is not possible from this data

The app is deliberately scoped to area-level statistics. It does not offer per-property valuation, for the reasons set out in Results below.

Data is pre-aggregated to 264 KB of Parquet files, so the app loads instantly and requires no database or runtime data fetching.

## Repository Contents

IrishPropertyPrices/
├── App/
│ ├── IrishPropertyPrices_App.py # the deployed application
│ └── data/ # pre-aggregated, 264 KB
├── Notebooks/
│ ├── 01 - Data Exploration.ipynb # schema inspection, quality assessment
│ ├── 02 - Cleaning.ipynb # cleaning pipeline, BER join
│ ├── 03 - Exploratory Analysis.ipynb # trends, geography, energy efficiency
│ └── 04 - Modelling.ipynb # modelling and the accuracy ceiling
├── Data/
│ ├── Raw/ # downloaded sources, not tracked
│ └── Processed/ # cleaned outputs, not tracked
├── .gitignore
├── README.md
├── LICENSE
└── requirements.txt


## Data Sources

- **Property Price Register** - every residential sale since 2010, actual prices filed for stamp duty. 799,067 records. https://www.propertypriceregister.ie
- **SEAI National BER Research Tool** - anonymised domestic energy assessments. 1,430,031 records, 252 columns. https://ndber.seai.ie
- **CSO Residential Property Price Index** - table HPM09 via the PxStat API, used to express all prices in common money. https://data.cso.ie

## Data Notes

Several issues required handling and are documented in full in notebooks 01 and 02.

**New builds are filed excluding VAT** at 13.5%. Without adjustment their prices are systematically understated by that margin. The adjustment keys off the VAT flag rather than the property description, since 2,365 sales described as new are not flagged VAT-exclusive and their price distribution indicates they are not gross-priced new sales.

**The BER floor area columns are inverted relative to their names.** `GroundFloorArea(sq m)` contains total dwelling floor area and `FloorArea` contains the ground floor footprint. The ratio between them tracks storey count almost exactly - 1.00 for single-storey, 1.89 for two-storey, 2.34 for three-storey - and apartments show a footprint of zero while retaining a total area. Taking the schema at face value would produce systematically wrong size figures.

**Eircode coverage changes sharply in 2021**, from under 1% through 2020 to 51% in 2021 and 74-77% thereafter. Analysis requiring routing keys uses the 2021 onward window; trend analysis uses the full series.

**The county field contains data entry errors.** 611 sales are filed against a county accounting for under 1% of their routing key's transactions - a Blessington, Co. Wicklow address filed under Westmeath, a Clane address under Clare rather than Kildare. In each case the address text and Eircode agree and contradict the county field. These are flagged rather than dropped.

**Routing keys legitimately span counties.** They follow postal delivery patterns rather than administrative boundaries. A92 covering Drogheda is 66% Louth and 34% Meath. Each key is assigned its dominant county for joining purposes.

**Price bounds of €20,000 to €2,000,000** scope the dataset to individual dwellings. This is a scoping decision rather than error correction - the excluded high-value sales are genuine arms-length transactions of apartment blocks and development sites, the largest being €388m. Only 14% of excluded rows carry the non-market flag.

## Method

**Cleaning** removes non-arms-length sales, applies VAT adjustment, harmonises Irish-language category duplicates, validates Eircode format including the Dublin 6W exception, and logs every row dropped with a reason. 750,660 of 799,067 sales retained.

**Price indexing** expresses all sales in June 2026 money using the CSO index, applied separately for Dublin and the rest of the country given their divergence. This reduces the spread in annual medians from 36% to 3.9%.

**Modelling** compares a routing key median baseline against Ridge regression and LightGBM on a log-transformed target, with a temporal train/test split. Evaluation uses median absolute percentage error rather than RMSE, since a fixed euro error means very different things at different price points.

**Quantile regression** produces calibrated prediction intervals, achieving 80.3% coverage against an 80% target.

## Results

| Model | MdAPE | Within 10% | Median error |
| --- | --- | --- | --- |
| Routing key median | 25.6% | 21.2% | €92,496 |
| Ridge | 25.5% | 21.0% | €92,090 |
| LightGBM | 25.4% | 21.3% | €91,185 |
| Perfect area knowledge | 25.1% | - | - |

The models sit 0.3 percentage points from the ceiling achievable with perfect area knowledge and no property detail. Prediction intervals are well calibrated but span 113% of the predicted value - statistically honest, practically unusable as a valuation.

## Setup

Requires free registration for the SEAI BER Research Tool and manual download of both source files.

```bash
pip install -r requirements.txt
```

Place `ppr_raw.csv` and `BERPublicsearch.txt` in `Data/Raw/`, then run the notebooks in order. The CSO index is fetched automatically via the PxStat API.

To run the app locally:

```bash
streamlit run App/IrishPropertyPrices_App.py
```

## What Would Change the Conclusion

A property-level join between sale prices and dwelling characteristics. The full BER data file contains exactly what is needed but access is restricted under S.I. No. 243/2012 to the BER assessor, a subsequent assessor, or the building owner. Commercial address databases licensed from Eircode would permit geocoding but at prohibitive cost across 750,000 records.

## Technologies

Python, pandas, scikit-learn, LightGBM, Streamlit, matplotlib, seaborn, requests, pyarrow

## Author

David Heffernan | [GitHub](https://github.com/DavidHeffernan94) | [LinkedIn](https://www.linkedin.com/in/david-heffernan-871a85192/)

## License

MIT