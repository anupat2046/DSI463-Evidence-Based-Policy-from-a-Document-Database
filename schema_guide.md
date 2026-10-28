# MSO-Logbook Database: Schema Guide (English)

This guide explains the database you will explore in Assignment 4. It is an English companion to the official Thai data dictionary `MSO-Logbook Data Dictionary.xlsx`. When this guide and the dictionary disagree, the dictionary wins.

> **The data is synthetic.** It was generated to follow the real MSO-Logbook structure (the case-management system used by the Ministry of Social Development and Human Security, พม., to record fragile households). No record describes a real person. National IDs start with `99`, and image URLs point to `example.invalid`.

## 1. The big picture

```
mso_household  (2,000 docs)      one household = one dwelling
    │  _id
    ├──< mso_family  (2,217 docs)  hh_id → mso_household._id
    │        │  _id
    └──< mso_member  (7,518 docs)  hh_id → mso_household._id
                                   fam_id → mso_family._id
```

* A **household** (ครัวเรือน) is everyone living in one dwelling. It holds the location and housing condition.
* A **family** (ครอบครัว) is a family unit inside a household. Most households have one family, and extended households can have two.
* A **member** (สมาชิก) is one person. This is the richest collection, with about 90 top-level fields covering income, debt, health, welfare received, problems, and help plans.

Location fields (`province_code` … `village_code`) are **copied into all three collections**, so you can group members by area without a `$lookup`.

**Database name:** `mso`  **Snapshot date:** compute ages relative to **2024-06-30**:

```python
AGE = {"$dateDiff": {"startDate": "$birthdate", "endDate": datetime(2024, 6, 30), "unit": "year"}}
```

## 2. Data-quality notes (read before you count anything)

| Issue | What to do |
|---|---|
| `status: "removed"` records are deleted cases that are still in the database | Exclude them: `{"status": {"$ne": "removed"}}` |
| `vital_status: 0` means the person has died | Exclude them when counting living people |
| Optional fields are **missing** rather than empty | Use `$ifNull` before `$size` / `$in`, e.g. `{"$ifNull": ["$welf_eldery.code", []]}` |
| A small number of `SUM_INCOME` values do not match the detail fields | Check outliers, and decide whether to recompute from `pri_occ_income + sec_occ_income + subsidy_amount` |
| Problems are under-recorded: a person can lack a welfare benefit without the matching problem code | Compare *facts* (fields) against *recorded problems* (`prob_*`). The gap is often a finding in itself. |
| Children under 15 have no income or expenditure fields | Analyse the economy at **household** level by grouping members on `hh_id` |
| `debt.amount` and `SUM_DEBT` are described as "per month" in the dictionary | Treat them as monthly repayment, and say so in your report |

## 3. mso_household

| Field | Type | Meaning |
|---|---|---|
| `_id` | ObjectId | Household key |
| `hh_head` | string | National ID of the household head (matches `mso_member.national_id`) |
| `latitude`, `longitude` | number | Location of the dwelling |
| `hh_type.code` | HHT1–3 | HHT1 lives alone · HHT2 nuclear (parents + children) · HHT3 extended |
| `have_num` | 0/1 | Has an official house number. **No number usually means trouble registering for benefits.** |
| `hnum`, `hh_code`, `moo`, `soi`, `road`, `postcode` | string | Address details |
| `village_*`, `tumbol_*`, `amphur_*`, `province_*` | string | Village / subdistrict / district / province code and name |
| `mso_osm` | string | Regional technical support office number (illustrative) |
| `house_type.code` | HT1–5 | HT1 own land · HT2 someone else's land · HT3 public land (encroached) · HT4 rented · HT5 other |
| `house_type.hiring_cost` / `rental_fee` | number | Monthly land rent (HT2) / house rent (HT4), baht |
| `house_type.public_land_type.code` | PL1–5 | For HT3: PL1 forest reserve · PL2 national park · PL3 Marine Dept. land · PL4 mangrove · PL5 other |
| `house_solid` | 0/1 | Dwelling is structurally sound |
| `env_suitable` | 0/1 | Surroundings are suitable for children, older people and people with disabilities |
| `house_images[]`, `consent[]` | array | Photo and consent-form metadata |
| `status` | string | created · approved · modified · removed |
| `created_by`, `createdAt`, `modifiedAt` | | Who recorded it and when |
| `case_manager.{uid,title,name,surname}` | object | พม. officer responsible |
| `volunteer.{uid,…}` | object | อพม. social-development volunteer responsible |

## 4. mso_family

| Field | Type | Meaning |
|---|---|---|
| `_id`, `hh_id` | ObjectId | Family key, and its household |
| `fam_head` | string | National ID of the family head |
| `fam_type.code` | FT1–9 | FT1 nuclear · **FT2 skipped-generation (grandparents + grandchildren only)** · **FT3 single parent** · FT4 teenage family (<20) · FT5 older couple alone · FT6 same-sex couple · FT7 blended · FT8 alone · FT9 extended |
| address fields | | Same as household |
| `status`, `created_*`, `case_manager`, `volunteer` | | Same as household |
| `familyTree.node[]` | array | One node per person, with `relationWithParent` (คู่สมรส spouse, บุตร child, หลาน grandchild, บิดา/มารดา parent) |

## 5. mso_member

### 5.1 Identity and links

| Field | Meaning |
|---|---|
| `hh_id`, `fam_id` | Links to household and family |
| `is_hh_head`, `is_fam_head` | 1 if this person is the head |
| `title`, `name`, `surname`, `national_id` | Identity (fake) |
| `birthdate`, `sex` (ชาย male / หญิง female) | Use `birthdate` to compute age |
| `nationality` (ไทย / อื่นๆ), `nationality_other` | `อื่นๆ` + `ไร้สัญชาติ` = stateless |
| `religion`, `marital_status`, `vital_status`, `mobile_num` | |
| `father`, `mother` | Parent details (recorded for children) |
| `edu_status.code` | ES1 never studied · ES2 studying · ES3 dropped out · ES4 graduated |
| `edu_level.code` | EL1 none · EL2 primary · EL3 lower secondary · EL4 upper secondary/vocational · EL5 diploma · EL6 bachelor · EL7 postgraduate |
| `attend_socact[].code` | SA1 none · SA2 savings group · SA3 welfare group · SA4 recreation · SA5 volunteer |
| `msoid` | System-generated de-duplication ID |

### 5.2 Income, spending, assets, savings, debt (baht per month)

| Field | Meaning |
|---|---|
| `occup_status` | 1 works · 0 does not work |
| `get_subsidy`, `subsidy_amount` | If not working: 1 supported by others (amount) · 2 lives on welfare |
| `primary_occup.code`, `pri_occ_income` | OC1 general labour · OC2 farming · OC3 private employee · OC4 civil servant · OC5 state officer · OC6 state enterprise · OC7 own business/trade · OC8 pensioner · OC9 other |
| `secondary_occup[]`, `sec_occ_income` | Second job(s) and income |
| `expenditure[].{code,amount}` | XP1 food · XP2 household goods · XP3 health · XP4 caring for family · XP5 social · XP6 education · XP7 leisure · **XP8 gambling · XP9 rotating credit (แชร์) · XP10 lottery · XP11 alcohol** · XP12 other |
| `asset.{land[],gold,livestock[],building[],machinery[]}` | Land in rai (`type`: อาศัย residential / เพื่อทำกิน farmland) |
| `saving[].{code,amount}` | SV1 cash · SV2 bank · SV3 cooperative · SV4 savings group · SV5 funds · SV6 life insurance · SV7 other |
| `have_debt`, `debt[].{type,amount}` | `type`: ในระบบ formal · **นอกระบบ informal (loan sharks)** |
| `SUM_INCOME`, `SUM_EXPENDITURE`, `SUM_SAVING`, `SUM_DEBT` | Totals computed by the form |

### 5.3 Health

| Field | Meaning |
|---|---|
| `chronic_disease[].code` | CD1 cancer · CD2 hypertension · CD3 heart · CD4 lung · CD5 diabetes · CD6 stroke · CD7 kidney · CD8 other |
| `med_scheme[].code` | MS1 social security · MS2 universal coverage (30 baht) · MS3 civil servant · MS4 private · MS5 community fund · MS6 disability gold card (ท.74) · **MS7 no coverage** |
| `is_disabled`, `have_pwd_card` | Disabled? Holds the official disability card? **The card is the gateway to disability benefits.** |
| `disability[].code` | DA1 visual · DA2 hearing/communication · DA3 physical/mobility · DA4 mental/behavioural · DA5 intellectual · DA6 learning · DA7 autism |

### 5.4 Welfare received

| Field | Key codes |
|---|---|
| `welf_children_youth[]` | WFCY1 counselling · **WFCY2 cash subsidy** · WFCY3 medical rights · WFCY4 vaccination · WFCY5 age-appropriate schooling |
| `cy_subsidy[].{code,amount}` | CYSU1 newborn child support grant · CYSU2/3 poor-family child grant · CYSU4 foster family … |
| `cy_education.{code,name}` | CYED1 child development centre · CYED2 school · CYED3 ปอเนาะ (Islamic boarding school) |
| `welf_disability[]` | **WFDA14 disability allowance** · WFDA1 home adaptation · WFDA4 assistive devices · WFDA8 personal assistant … |
| `welf_women[]` | WFWM2 short vocational course · WFWM4 counselling · WFWM6 cash support … |
| `welf_eldery[]` *(sic)* | **WFEL9 old-age allowance (เบี้ยยังชีพ)** · WFEL2 hardship grant · WFEL6 home adaptation · WFEL7 elderly school … |
| `welf_helpless_persons[]` | WFHP1 counselling · WFHP2 cash · WFHP4 temporary shelter … |
| `welf_others[]` | WFOT1 house repair · **WFOT4 state welfare card (บัตรสวัสดิการแห่งรัฐ)** · WFOT5 relief bags … |

### 5.5 Problems recorded (each is an array of `{code, desc}`)

| Field | Domain | Example codes |
|---|---|---|
| `prob_accessibility` | Access to rights | PBAC1 cannot reach state services · **PBAC2 has not applied for a disability card** · PBAC3 no civil registration · **PBAC8 not registered for old-age/disability allowance** |
| `prob_education` | Education | PBED1 lacks opportunity · PBED2 no scholarship · **PBED3 dropped out** · PBED4 not in school |
| `prob_family` | Family | PBFA6 must care for a family member · PBFA9 teenage pregnancy · **PBFA11 lives alone without a carer** · PBFA18 family debt · PBFA20 carer is poor · PBFA21 poor family · PBFA25/PBFA14 single mother/father |
| `prob_health` | Health | PBHE2 dementia · **PBHE4 bedridden** · PBHE5 serious illness · PBHE6 chronic illness · PBHE7 lacks assistive devices · PBHE8 cannot self-care · PBHE13 no medical coverage |
| `prob_housing` | Housing | PBHO1 no ownership · PBHO2 unsuitable · PBHO3 homeless · PBHO4 unstable house |
| `prob_occupation` | Work and income | PBOC3 income below spending · **PBOC6 debt** · PBOC7 no savings · PBOC8 unemployed · PBOC13 no farmland · PBOC14 irregular income |
| `prob_violence` | Violence | PBVI2 physical abuse · PBVI3 psychological abuse · PBVI5 stigma |
| `prob_human_trafficking` | Trafficking | PBHT5 deceived · PBHT8 forced labour |
| `prob_others` | Other | PBOT2 southern unrest · PBOT4 pollution · PBOT6 drought · PBOT9 flood · PBOT10 fire |

The data dictionary has the full code lists.

### 5.6 Case management: `prob_summary`

`prob_summary` is an **object** with up to five keys (`prob_health`, `prob_family`, `prob_education`, `prob_occupation`, `prob_accessibility`). Each key holds an array of problems:

```json
"prob_summary": {
  "prob_accessibility": [
    { "code": "PBAC8", "desc": "...", "status": 2,
      "plans": [ { "sol_type": "ประสานส่งต่อ", "sol_code": "TR47", "sol_des": "เบี้ยยังชีพผู้สูงอายุ",
                   "plan_duration": "short", "status": 1, "main_org_name": "กระทรวงมหาดไทย",
                   "activities": [ { "act_date": "...", "act_progression": "พอเพียง" } ] } ] }
  ]
}
```

* Problem `status`: 0 no plan yet · 1 plan made, not followed up · 2 followed up · 3 case closed
* `plans[].sol_type`: ให้คำแนะนำ advice · ช่วยเหลือ direct assistance · ประสานส่งต่อ referral
* `plans[].sol_code`: see the sheet *Codelist แนวทางการแก้ไข* (SGxx advice, ASxx assistance, TRxx referral)
* `plans[].plan_duration`: critical · short · continuous
* `activities[].act_progression`: อยู่รอด survive · พอเพียง sufficient · ยั่งยืน sustainable · อื่นๆ other

To work with it, use `$unwind` on one key (`"$prob_summary.prob_health"`), or concatenate the five arrays with `$concatArrays`.

## 6. Locations in this dataset

Province and district codes follow the Ministry of Interior (DOPA) numbering, so you can join external statistics **at province or district level**. Subdistrict and village codes and names are illustrative. Do not join on them.

| province_code | Province | amphur_code / District |
|---|---|---|
| 10 | Bangkok (กรุงเทพมหานคร) | 1033 Khlong Toei · 1003 Nong Chok |
| 14 | Phra Nakhon Si Ayutthaya | 1401 Phra Nakhon Si Ayutthaya · 1402 Tha Ruea |
| 30 | Nakhon Ratchasima | 3001 Mueang Nakhon Ratchasima · 3002 Khon Buri |
| 40 | Khon Kaen | 4001 Mueang Khon Kaen · 4005 Chum Phae |
| 50 | Chiang Mai | 5001 Mueang Chiang Mai · 5003 Mae Chaem |
| 58 | Mae Hong Son | 5801 Mueang Mae Hong Son · 5803 Pai |
| 94 | Pattani | 9401 Mueang Pattani · 9402 Khok Pho |

`provinces.csv` holds the same table, ready to load as a lookup collection.

## 7. Query patterns you will need

```python
# members + their household (one-to-one after $unwind)
{"$lookup": {"from": "mso_household", "localField": "hh_id", "foreignField": "_id", "as": "hh"}},
{"$unwind": "$hh"}

# does an array of {code: ...} contain a code?   (safe when the field is missing)
{"$in": ["WFEL9", {"$ifNull": ["$welf_eldery.code", []]}]}

# household-level totals from members
{"$group": {"_id": "$hh_id", "hh_income": {"$sum": "$SUM_INCOME"}, "size": {"$sum": 1}}}

# per-capita income → compare with a poverty line from external data
{"$addFields": {"per_capita": {"$divide": ["$hh_income", "$size"]}}}

# join an external table you loaded yourself (e.g. ext_province) on province_code
{"$lookup": {"from": "ext_province", "localField": "_id", "foreignField": "province_code", "as": "ext"}}
```
