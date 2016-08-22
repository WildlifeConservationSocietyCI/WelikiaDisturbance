---
title: Modeling the Historical Disturbance Regimes of NYC
bibliography: Disturbances.bib
---

# Historical Disturbance Regimes

scale and frequency [@lorimer_age_1980; @lorimer_scale_2003; @foster_land-use_1998, @pan_age_2011]

human influence [@day_indian_1953; @russell_people_1997; @russell_people_1997; @krech_iii_ecological_1999, @patterson_indian_1988]

importance of lightning caused forest fires [@loope_human_1998]

# Fire

## Custom Fuel Models

Hardwood forest types are based on model F9 [@scott_standard_2005; @anderson_aids_1982]. Where average loads for 1 hr 10 hr and 100 hr fuels were available for northeastern forest types the values were substituted [@reinhardt_fire_2015]. The remaining fuel attributes remained the same as the base model. The USFS community types were cross-walked to the NY State Heritage community classification so fuels could be assigned for our landscape. 

## Fuel Moisture
Region specific initial fuel moistures [@reinhardt_fire_2015]. All freshwater wetland communities (marshes, shrub-swamps and forested wetlands) were initialized with a wet fuel profile, all other communities with burnable fuel types were initialized with a moist fuel profile.

| Size Class       | Very Dry | Dry | Moist | Wet |
|------------------|---------:|----:|------:|----:|
| 1 hr             |        5 |   7 |    10 |  19 |
| 10 hr            |        8 |   9 |    13 |  29 |
| 100 hr           |       12 |  14 |    17 |  22 |
| Live woody       |       89 | 105 |   135 | 140 |
| Liver herbaceous |       60 |  82 |   116 | 120 |


## Initial Conditions - Forest Age

Forest communities were initialized with ages drawn from the following normal distribution [@pan_age_2011; @loewenstein_age_2000]. All no forest types were initialized with a forest age of 0

![age class distribution](figures/northeast_forest_age_hist.jpg)

## Initial Conditions - Canopy
For community types that can have a canopy, start values were randomized (using uniform distribution) within the following canopy classes:

    * grassland 0 < canopy < 20
    * shrubland 20 < canopy < 60
    * forest 60 < canopy

Community types that do not have canopies were initialized with a value of 0.

### fire size and frequency literature
effects of fires on temperate forests [@kozlowski_fire_2012]
power law[@reed_power-law_2002; @cui_what_2008; @stephens_forest_2005]

## Modeling Expected Frequencies
A Poisson distribution is used to model expected forest fire frequency [@johnson_forest_2001; @yang_spatial_2008]. We created distributions for trail fires, garden fires and lightning fires. 

### Lightning Frequencies 
The expected frequency ($lambda$) of lighting caused fires are based on areal frequencies from USFS wildfire records in region 9 (U.S. Northeast) between 1940  and 2000 [@stephens_forest_2005]. These values were converted from the given units (frequency/400000 ha)/yr to (frequency/km^2^)/yr. 


|  Region  |  Lightning  |            |   Human    |            |
|----------|-------------|------------|------------|------------|
|          | Ha burned   | No. fires  | Ha burned  | No. fires  |
| 9        | 11.840      | 2.170      | 327.990    | 39.950     |


|             |   Lightning    |                |     Human      |                |
|-------------|----------------|----------------|----------------|----------------|
|             | Area burned    | No. Fires      | Area burned    | No. Fires      |
| 1 hectare   | 0.0000296      | 0.000005425    | 0.000819975    | 0.000099875    |
| per km²     | 0.00296        | 0.0005425      | 0.0819975      | 0.0099875      |

### Human Fire Frequency Scenarios

The extent and effect of human caused fires on the landscape prior to European settlement is debated[@day_indian_1953;@russell_indian-set_1983; @patterson_indian_1988]. We have proposed two frequency scenarios, and through simulation have attempted to measure their relative effects.   

|        | no human fire | Russell (1983) | Day (1953) |
| source |               |                |            |
|--------|---------------|----------------|------------|
| trail  |             0 |        0.00222 |    0.01778 |
| garden |             0 |        0.00028 |    0.00222 |

## Critical Rainfall

```
In the model, fire spread was stopped when it encountered one of the following conditions: (1) a non-flammable type of land cover; (2) boundaries of the region; and (3) when rainfall exceeded a certain critical amount. By assuming that a daily precipitation of 30 mm or more would stop a fire, the R Crit in Eq. (2) was estimated as 0.026 (the proportion of total number of days that has daily precipitation of 30 mm or more) from the historical precipitation data of the Edison weather station. [@li_reconstruction_2000]
```

## Tree Allometry

|  Description   |         Equation         |        Reference        |
|----------------|--------------------------|-------------------------|
| Tree Height    | $TH = 44 * ln(Age) - 93$ | [@bean_using_2008]      |
| DBH            | $DBH=(Age-34.44)/1.18$   | [@loewenstein_age_2000] |
| Crown Ratio    | $CR = 0.4$               | [@bean_using_2008]      |
| Bark Thickness | $BT = vsp * DBH$         | [@reinhardt_fire_2015]  |


* Communities to Bark Thickness * 
bark thickness multipliers for each community, for communities with co-dominate species the average bark thickness was calculated [@reinhardt_fire_2015].

| community                            | dominant tree species                     | vsp scaler  |
| ------------------------------------ | ----------------------------------------- | ----------: |
| Floodplain forest                    | avg(sliver maple, sycamore, American elm) | 0.032       |
| Red Maple Hardwood Swamp             | red maple                                 | 0.028       |
| Coastal Plain Atlantic Cedar Swamp   | Atlantic cedar                            | 0.025       |
| Pitch pine - scrub oak barrens       | avg( pitch pine, oak spp )                | 0.045       |
| Chestnut oak forest                  | avg( American chestnut, oak spp )         | 0.043       |
| Coastal oak beech forest             | avg( oak spp, beech )                     | 0.035       |
| Coastal oak hickory forest           | avg( oak spp, hickory spp )               | 0.045       |
| Oak tulip forest                     | avg( oak spp, yellow-poplar )             | 0.038       |
| Appalachian oak pine forest          | avg( oak spp, pine spp )                  | 0.038       |
| Hemlock northern hardwood forest     | hemlock                                   | 0.045       |
| Inland Atlantic Cedar Swamp          | Atlantic white cedar                      | 0.025       |
| Red maple black gum swamp            | avg( red maple, black gum )               | 0.034       |
| Red maple sweetgum swamp             | avg( red maple, sweetgum )                | 0.032       |
| Maritime holly forest                | holly                                     | 0.042       |
| Post oak black jack oak barrens      | post oak                                  | 0.044       |
| Appalachian oak hickory forest       | avg( oak spp, hickory spp )               | 0.045       |
| Beech maple mesic forest             | avg( beech, sugar maple )                 | 0.029       |
| Successional maritime hardwoods      | other hardwoods                           | 0.044       |
| Successional hardwood forest         | other hardwoods                           | 0.044       |


## Fire Mortality Equations


*Scorch Height*

**[1]**      $$SH = 3.1817(FL^{1.4503})$$
[@bean_using_2008]


*Crown Kill* 

**[2]**      $$CK= 41.961( 100(\ln({SH -CH) \over CL})) - 89.721$$
[@bean_using_2008]


*Percent Mortality*

**[3]**      $$P_{m}= {1.0 \over 1.0 + e^{-1.941 + 6.316(1.0-e^{-BT}) - 0.000535 CK^2}}$$  
[@bean_using_2008]

# Horticulture

## Archaeological Evidence for Gardening
[@kraft_lenape-delaware_2001, @cantwell_unearthing_2001, @benison_horticulture_1997]

## Ethnohistorical
[@ascher_henry_1860, @danckaerts_journal_1867]


| crop                         | yield (kg/ha)   | calories/100 g   | calories/kg | calories/ha   |
| ---------------------------- | --------------: | ---------------: | ----------: | ------------: |
| corn                         | 1720            | 365              | 3650        | 6278000       |
| beans (Phaseolus vulgaris)   | 110             | 33               | 330         | 36300         |
| squash (Indian squash)       | 80              | 16               | 160         | 12800         |


corn-bean-squash ploy-culture yields in Tabasco, Mexico [@gliessman_agroecology:_1998] pg 224 table 15.3

Caloric density [USDA Basic Reports Agricultural Research Services]

## Agricultural Dependency Scenarios

caloric requirements [@speth_energy_1983]

| Dependency     | calories/person/yr    | ha/person    | m^2^/person    |
| :------------: | --------------------: | -----------: | -------------: |
| 15%            | 94060.50              | 0.01         | 14.87          |
| 30%            | 188121.00             | 0.03         | 29.73          |
| 60%            | 376242.00             | 0.06         | 59.47          |
| 100%           | 627070.00             | 0.10         | 99.11          |

# Beaver

## Succession

We used a 4 sere sequence for the freshwater wetland pathway [@allen_habitat_1983; @hay_succession_2010; @johnston_use_1990; @logofet_succession_2016; @naiman_alteration_1988; @_ecology_1993]. Conversion from non-wetland community to active pond can occur along any perennial streams where the stream gradient is less than 15 degrees. Due to the temporal scale of our study, forested wetlands are treated as a terminal community in this series [@_ecology_1993]. This rule defines beaver caused disturbance as a unidirectional change in successional trajectory. A non-wetland communities can be converted into a wetland type but this conversion cannot be reversed.   
    
$$\mbox{active beaver pond} \rightarrow \mbox{emergent marsh} \rightarrow \mbox{shrub swamp} \rightarrow \mbox{forested wetland}$$



## Model Parameters

| Parameter                    | Value     |                | Source                                        |
| ---------------------------  | --------: | :------------- | --------------------------------------------- |
| probability of abandonment   | 0.10      |                | [@logofet_succession_2016]                    |
| colony density               | 0.4       | colonies/km^2^ | [@naiman_alteration_1988]                     |
| territory (minimum distance) | 1000      | m              | @naiman_alteration_1988; @allen_habitat_1983] |

## Analysis
time since fire [@johnson_forest_2001]
fire size frequency hist [@reed_power-law_2002; @cui_what_2008;@malamud_forest_1998]

# References
