# External Data Sources for Assignment 4

Join any external data to the database on **`province_code`** or **`amphur_code`** (Ministry of Interior codes). If a source only has province names, map them with `provinces.csv`.

Always record the **publisher, URL, date accessed, and the year the data describes**. Check each source's licence, and use the most recent year available.

## Suggested sources by problem area

| Problem area | Source | What you can get | Join level |
|---|---|---|---|
| Poverty / targeting | **TPMAP** (Thai People Map and Analytics Platform), https://www.tpmap.in.th | Number of poor people by province/district and by deprivation dimension (health, living, education, income, access to services) | province, district |
| Population size | **DOPA registration statistics** (สถิติประชากรทางการทะเบียน), https://stat.bora.dopa.go.th | Registered population by age and sex. Use it as a denominator (e.g. older people per province) | province, district |
| Income, debt, poverty line | **National Statistical Office (NSO)**, https://www.nso.go.th | Household Socio-Economic Survey: average income, expenditure and debt per household by province or region | province / region |
| Poverty line | **NESDC** (สภาพัฒน์), https://www.nesdc.go.th | Official poverty line (baht/person/month) by province; Gross Provincial Product | province |
| Older people | **Department of Older Persons**, https://www.dop.go.th | Statistics on older people and the old-age allowance | province |
| Disability | **Department of Empowerment of Persons with Disabilities**, https://dep.go.th | Number of disability-card holders by province and type of disability | province |
| Health | **Health Data Center, Ministry of Public Health**, https://hdcservice.moph.go.th | Chronic disease prevalence, bedridden older people, health facilities | province, district |
| Disasters | **Department of Disaster Prevention and Mitigation**, https://www.disaster.go.th · **GISTDA flood maps**, https://flood.gistda.or.th | Areas declared disaster zones, flood extent | province, district |
| Air pollution | **Air4Thai, Pollution Control Department**, https://air4thai.pcd.go.th | PM2.5 by monitoring station (matches PBOT4 in the north) | province (via station location) |
| Household debt | **Bank of Thailand**, https://www.bot.or.th | Household debt statistics | region / national |
| Open government data | **data.go.th**, https://data.go.th | Search for schools, welfare-card holders, child support grant recipients, etc. | varies |
| Locations of services | **OpenStreetMap** (Overpass API, https://overpass-turbo.eu) or **healthsites.io** | Hospitals, health centres, schools, district offices with lat/long | point. Compare with household `latitude`/`longitude` (see Week 9 geospatial) |

## How to load an external table into MongoDB

```python
import pandas as pd

ext = pd.read_csv("tpmap_province.csv", dtype={"province_code": str})   # keep codes as strings!
db.ext_tpmap_province.drop()
db.ext_tpmap_province.insert_many(ext.to_dict("records"))
db.ext_tpmap_province.create_index("province_code")
```

Then join:

```python
{"$lookup": {"from": "ext_tpmap_province", "localField": "province_code",
             "foreignField": "province_code", "as": "tpmap"}},
{"$unwind": "$tpmap"}
```

## Ideas for what the join can show

* **Coverage**: the logbook finds X fragile older people in a province, and DOPA says the province has Y older people. What share of the population does the logbook cover?
* **Benchmark**: compare per-capita household income from the database with the provincial poverty line from NESDC.
* **Context**: are the provinces with the most PBOT9 (flood) cases the ones that were declared disaster zones?
* **Access**: compute the distance from each household to the nearest hospital (`$geoNear` after loading OSM points), and relate it to `PBHE9` or missing treatment.
