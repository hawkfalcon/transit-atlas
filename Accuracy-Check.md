# Santa Barbara Transit Atlas — accuracy check

**Checked October 24, 2026. Verdict: the main comparison is correct. One frequency-detail bug was found and fixed.**

This was a source audit, not just a browser test. I independently parsed both original GTFS ZIPs, recalculated the counts and intervals, checked the displayed paths against the source shapes, and extracted the performance figures directly from MTD’s PDF tables. The audit does not call the app’s calculation functions.

## The main numbers

Regular routes; departures from the first boardable stop, **10 am–2 pm**, both directions:

| Measure | October 15, 2019 | October 15, 2026 | Result |
|---|---:|---:|---|
| Regular routes running that weekday | 24 | 19 | Matches |
| Midday departures | 392 | 258 | Matches |
| Routes with a typical midday interval of 15 minutes or less | 4 | 0 | Matches |

That is **134 fewer midday departures, a 34.18% decline**. The app rounds this to 34%.

The four frequent 2019 lines were **1, 2, 28 and 30**. The six 2019 route numbers missing from the current timetable are **10, 16, 30, 34, 36 and 37**. Those dark dashed paths are correct. This is a loss of named routes, not a claim that every street along them has lost all transit.

Seasonal **33 has no weekday trips anywhere in October 2026**, not just on the chosen Thursday. Current **19X runs six trips that day, two at midday**, so its purple Limited label is correct.

## What needed fixing

### Line 10’s direction details

Line 10 ran **12 trips in 2019, with none at midday**. The main map correctly called it Limited. But the detail card calculated the long morning-to-afternoon breaks—**352 and 425 minutes**—as directional “typical” intervals because their midpoints fell inside the analysis window.

**Fixed:** a direction now needs at least two actual midday departures before it gets a midday interval. Line 10’s directions show **7 departures / 0 at midday** and **5 departures / 0 at midday** instead. The calculator, stored derived fields and display guard now agree. No source ZIP, route geometry, route-level frequency or headline count changed.

Two small labels were also clarified:
- The comparison table now includes the 2019 name when a route has been renamed.
- The funding box explicitly labels the $4.94 million as **temporary federal relief**. The student-fee proposal now includes its **0–4% annual cost-of-living adjustment**, as stated in the staff report.

## Map and source integrity

- **All 85 route profiles (46 historic and 39 current)** were checked for trip counts, activity, intervals, spans and midday departure times.
- **84 route profiles have geometry.** Every one agrees with the relevant original GTFS trip shapes to within **2.76 metres**, consistent with the map’s 2–3 metre simplification. The remaining record is the unused standby entry.
- **1,298 displayed stop records** across the two periods match their source coordinates and route assignments.
- Both GTFS ZIPs and all three planning PDFs downloaded on October 24 were **byte-for-byte identical** to the bundled sources. The current feed is still version **S1000262**, valid August 17–November 29, 2026.
- All **11 source links** in the two tabs returned HTTP 200.

## Saving MTD

All **96 numerical cells** used from the route report—24 records × annual boardings, annual productivity, quarterly boardings and quarterly productivity—match the original PDF.

| Claim | Source check |
|---|---|
| FY2025–26 fixed-route boardings: **4,524,968** | Matches the report and sum of all 24 records |
| Lowest annual boardings per revenue hour: **19X 6.4; 23 11.8; 14 11.9; 5 12.4; 3 14.4** | Matches the 19-current-regular-route ranking |
| Lines **11 / 24X / 27 / 28** carried **2,083,620 boardings**, or **46.05%** of the fixed-route total | Matches; these are all boardings on the routes, not only UCSB students |
| **6 + 11 already alternate every 15 minutes from Transit Center** toward Goleta/UCSB at midday | Matches all 16 terminal starts in the current feed |
| **$4,935,532** in temporary relief, **14%** of budgeted operating revenue; projected exhaustion **FY2028–29** | Matches the June 2026 budget, PDF p. 23 |
| UCSB fee proposal: **$18.76 → $45 per quarter**, with **0–4% annual COLA**, for a **Spring 2027 student vote** | Matches the July staff report, PDF pp. 19–24 |

The performance figures cover the fiscal year ending **June 30, 2026**, before August’s cuts. They support the ranking shown; they do not measure the loads on today’s individual departures. The app dates them correctly and does not book hypothetical savings or unapproved fee revenue.

## What the comparison measures

“Today” means the **October 15, 2026 weekday timetable**, not live arrivals. The feed was checked again on October 24 and is unchanged. The frequency is a terminal-departure median; it is not a measured wait at every stop. The 34% is a change in this four-hour departure count, not in annual service hours or funding. **2019 is the documented pre-pandemic baseline, not an established all-time maximum.**

## Sources and reproducible checks

- [Original fall 2019 GTFS](https://openmobilitydata-data.s3-us-west-1.amazonaws.com/public/feeds/santa-barbara-mtd/1156/20190819/gtfs.zip)
- [Official current GTFS](https://www.sbmtd.gov/google_transit/feed.zip)
- [MTD FY2025–26 report, pp. 2–3](https://sbmtd.gov/wp-content/uploads/2026/07/Q4_FY26Report.pdf)
- [June 2026 budget, p. 23](https://sbmtd.gov/wp-content/uploads/2026/05/20260602-Agenda-Packet.pdf#page=23)
- [July 2026 student-pass proposal, pp. 19–24](https://sbmtd.gov/wp-content/uploads/2026/07/20260721-Board-Packet-v2-1.pdf#page=19)

Audit files are in `accuracy-check/`: `audit_atlas.py`, `independent-audit.json`, `before-corrections.json`, `corrections.json`, `live-source-check.json`, `source-links.json` and `source-departures.csv`. The before/after record preserves the bug rather than overwriting its history.

To repeat the independent source audit:

```bash
python -m pip install shapely pymupdf
python accuracy-check/audit_atlas.py
```

The corrected audit reports **pass**, with no remaining differences in the checked route metrics, direction details or performance figures. All **82 browser regression checks** also pass, including mobile, offline and sandboxed use; results are in `tests/test-report.json`.
