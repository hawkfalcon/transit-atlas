# Santa Barbara Transit Atlas

An independent, offline-capable comparison of Santa Barbara MTD’s original **fall 2019** fixed-route network and **October 2026** service, with service and funding options in a separate **Saving MTD** tab.

## Open it

Open **`Santa-Barbara-Transit-Atlas.html`** in a modern browser. The identical **`index.html`** is ready for static hosting. Both include the data, basemap, font and code—no account, API key, server or internet is required. Source links need internet when clicked.

## Publishing (GitHub Pages)

`.github/workflows/atlas.yml` runs on every push and pull request:

1. rebuilds `index.html` from `assets/` and fails if the committed build is stale;
2. starts a local server and runs the browser suite in `tests/test_atlas.py`;
3. on a push to `main`, uploads the finished `index.html` and publishes it with GitHub Pages.

Pages has to be switched on once, by a repository admin: **Settings → Pages → Source: GitHub Actions**. Pages on a private repository needs a paid plan, so keep the repository private but unpublished, or make it public and the next push to `main` publishes at `https://<owner>.github.io/transit-atlas/`. Until then the deploy job only posts a notice and skips publishing; the test job still runs and must stay green.

The published page is only `index.html`. It is self-contained—CSS, JavaScript, font, basemap and route data are inlined—so no other file is uploaded and no server-side code is involved. `NOTICE.md` is published alongside it for source credits.

Only `main` deploys. To publish a change, merge it to `main`; branch pushes and pull requests get the tests but not a deployment.

### Tab 1: 2019 ↔ Today

- Only **two actual GTFS networks**, with original paths and comparable weekday frequency metrics.
- Click routes or badges for the two-period interval, full gap range, directions and trip counts.
- Use **Layers** for historical lines absent today, school/other extras, Amtrak shuttles and stops. Stops appear at zoom 13+.
- **Compare lines** includes all 48 unique route records across the two snapshots when extras are included.
- The 20% calculation appears only in a collapsed note under **Saving MTD**, separate from the map, route comparisons and CSV.

### Tab 2: Saving MTD

Four service and funding options, with supporting data and the checks needed before making changes:

1. **Busy routes:** review crowding, school connections and minimum operating hours and coverage.
2. **Route overlaps:** compare paid vehicle and driver hours on shared corridors. Lines 6 and 11 are an example to study; they already alternate 15-minute midday departures from Transit Center toward Goleta/UCSB.
3. **Trip-level review:** use official boardings per revenue hour to identify where to request trip-level evidence first. It is not a cancellation list.
4. **Recurring funding:** show the actual budgeted federal-relief bridge and the specifically attributed UCSB fee staff proposal, without assuming that a future vote or new revenue is secured.

The performance table has **Lowest rates / Highest rates / All 19 lines** filters. Its values are published annual FY2025–26 boardings and boardings per revenue hour—not inferred demand from GTFS frequency. Every row can trace the unchanged current route on the map. Group study links show existing paths and frequencies; they never draw an invented merger or proposed cancellation. Network-wide map statistics remain unchanged by a study focus.

The former blanket-cut arithmetic survives only as a **collapsed context note** on this second tab, explaining why uniform cuts are not an evidence-based savings plan. It is not a third network, default forecast or future timetable.

## The verified historical feed

**Working public ZIP, no subscription required:**

https://openmobilitydata-data.s3-us-west-1.amazonaws.com/public/feeds/santa-barbara-mtd/1156/20190819/gtfs.zip

Located using [Interline’s public 2021 TransitFeeds URL index](https://github.com/interline-io/scrape-of-transitfeeds/blob/master/json-scrape/feedVersionS3Urls.csv). The archive date path is **20190819**, not Transitland’s later fetch date.

Local copy: `sources/historic-feed-20190819.zip` (971,757 bytes).

- Validity: **August 19–December 1, 2019**.
- Publisher/version: Santa Barbara MTD / `190819 August 19_20190712`.
- SHA-1: **`9babdd55bd0af8e510597e6906d896365f24cfcb`**.
- Exact hash match to the [independently indexed Transitland archive](https://www.transit.land/feeds/f-9q4g-santabarbaramtd/versions/9babdd55bd0af8e510597e6906d896365f24cfcb).

Current saved input: `sources/current-feed.zip`, from [MTD’s official feed](https://www.sbmtd.gov/google_transit/feed.zip). Validity **August 17–November 29, 2026**, version **S1000262**, SHA-1 **`27d4bbfde509193669f1c01ce30d045f9ef3585d`**. The live feed URL will change; the bundled ZIP preserves this comparison. Full SHA-256 hashes, source URLs and service IDs are in `data/provenance.json`.

## Factual map results

Regular fixed-route service; starts in **[10:00 am, 2:00 pm)**; both directions combined:

| Measure | Fall 2019 | October 2026 |
|---|---:|---:|
| Active regular lines, entire weekday | 24 | 19 |
| Midday departures | 392 | 258 |
| Difference in midday departures vs. 2019 | Benchmark | −34.18% |
| Lines with typical midday interval ≤15 minutes | 4 | 0 |

This is not a percentage change in annual hours, budget, ridership or every rider’s available service. Shared-corridor frequencies are not summed. Some lines, including 12X, are more frequent in the selected current schedule.

- Historical sample: **Tuesday, October 15, 2019**. 46 source records; 45 active: 24 general lines, 3 Amtrak shuttles and 18 school/other extras. Standby record 1001 has no trips.
- Current sample: **Thursday, October 15, 2026**. 39 source records; 38 active: 19 general lines, 3 Amtrak shuttles and 16 school boosters. Seasonal 33 does not operate that day.
- School-in-session calendars and exceptions are applied. Line 10 is explicitly limited/peak-oriented, with no midday departures, rather than being misrepresented as all-day service.
- Dark dashed routes show the losses since 2019. Other routes can still use the same streets. Other lines and The Wave on-demand service may provide access; on-demand service has no fixed headway and is outside this fixed-route comparison. See MTD’s [The Wave announcement](https://sbmtd.gov/mtd_news/santa-barbara-mtds-on-demand-microtransit-servicethe-wave-expands-to-carpinteria/).

### Frequency method

Select the first boardable stop for each active trip. Within each direction, sort departures and calculate positive consecutive gaps. Retain intervals whose **midpoint** is in [10:00, 14:00). The displayed typical interval is the median of those direction-specific gaps, pooled across directions. At least two actual starts in the window in a direction are required; otherwise service is labeled **Limited**. Direction medians and complete gap ranges remain available.

This is a line-level terminal-departure measure, not a guaranteed wait at every stop. Branches, short turns, uneven timetables and travel time matter. The separate departure-count metric simply counts actual first-boardable starts in [10:00, 14:00), rather than counting intervals.

### Why 2019, rather than an absolute “historic maximum”?

It is an actual, documented high-service pre-pandemic network with a verified feed and [official schedule guide](https://sbmtd.gov/wp-content/uploads/2019/08/MTD-August-2019-Schedule-Guide_complete-final.pdf), not an invented best-ever-per-line composite. It is **not proven to be the absolute all-time maximum**. Today’s data include the [adopted August 2026 cuts](https://sbmtd.gov/servicechanges/). This is a dated comparison, not an automatically updating journey planner.

## Planning evidence and limits

### Official annual route performance

[MTD FY2025–26 system report](https://sbmtd.gov/wp-content/uploads/2026/07/Q4_FY26Report.pdf), **PDF pp. 2–3, YTD columns**, for July 1, 2025–June 30, 2026.

Published tables were manually transcribed into `sources/fy2025-26-route-performance.csv`, visually verified against rendered source pages, and checked against the published totals. All **24 nonzero fixed-route records** reconcile to **4,524,968 annual boardings** and **1,172,298 fourth-quarter boardings**. Reproducible joins and checks are in `scripts/prepare_planning.py`.

The comparable ranking includes the **19 current regular lines**. Seasonal 33, three timed Amtrak services with partial-year operation and the aggregate school-booster record are preserved in the source export, but not mixed into that ranking.

| Lower annual productivity screen | Published boardings / revenue hour |
|---|---:|
| 19X | 6.4 |
| 23 | 11.8 |
| 14 | 11.9 |
| 5 | 12.4 |
| 3 | 14.4 |

These are **not recommended cancellations**. The figures cover all fiscal-year operating days/times and **predate August 2026’s service reductions**. They cannot identify the weakest individual departures, establish post-cut performance, quantify equity effects or predict financial savings. Ranking by total riders alone would also ignore differences in service supplied.

High annual productivity on 28 (65.5), 27 (60.7), 24X (39.8) and 11 (33.9) is a capacity-protection signal, not permission to abandon neighborhoods with fewer alternatives. School boosters as an aggregate had 64.8 boardings/hour. The 25.9 system reference includes all fixed-route services; it is not a cancellation threshold.

### Published budget and funding option

- [June 2, 2026 budget packet, PDF p. 23](https://sbmtd.gov/wp-content/uploads/2026/05/20260602-Agenda-Packet.pdf#page=23): FY2026–27 uses **$4,935,532** of temporary federal relief, stated as **14% of operating revenue**; staff forecast exhaustion by FY2028–29.
- [July 21, 2026 staff report, PDF pp. 19–24](https://sbmtd.gov/wp-content/uploads/2026/07/20260721-Board-Packet-v2-1.pdf#page=19): staff proposed pursuing a Spring 2027 UCSB student vote on a fee of **$45/quarter**, compared with the **$18.76/quarter** described in that report. This atlas does not assert approval or book anticipated revenue.

All other service and funding ideas are independent study concepts, not adopted MTD proposals. Merging line numbers does not by itself save a bus, driver shift or operating dollar. The application calls for trip-level loads, vehicle/crew blocks, net cost estimates, accessible alternatives, essential-trip protection, applicable equity review, public input and a reversible trial before recommending changes.

## Rebuild

Python 3.10+ and Shapely 2.x are enough; opening the HTML requires no installation:

```bash
python -m pip install -r requirements.txt
python scripts/prepare_data.py
python scripts/prepare_planning.py
python scripts/build_atlas.py
```

This uses bundled originals and local assets. It does not fetch an updated feed, rely on an authenticated archive, or OCR a live report. The transcribed report CSV and captured PDF are preserved together for audit.

Optional preview:

```bash
python -m http.server 8000 --bind 0.0.0.0
```

Route geometry is source GTFS, dissolved within each line and simplified by approximately 2–3 meters. Stops use source coordinates. The embedded contemporary basemap is a reference, not a historic street reconstruction; water tint and softened contextual-image transitions are cartographic styling only.

### Update the data

The atlas is a frozen snapshot, not a live feed. Every date in it is recorded in `data/provenance.json`; rebuilding with newer sources means changing those dates deliberately.

1. Replace the inputs in `sources/`: the two GTFS ZIPs (`historic-feed-20190819.zip`, `current-feed.zip`), the captured PDFs and `fy2025-26-route-performance.csv`. Keep the file names or update them in the scripts and in `scripts/package_project.py`.
2. Run `python scripts/prepare_data.py` and `python scripts/prepare_planning.py`. They record source URLs, SHA-1/SHA-256 hashes, feed versions, sample dates and the calendar of active services in `data/provenance.json` and `data/planning.json`.
3. Update the dates and wording that are written into the markup, not derived from the data:
   - `assets/index.template.html`: the two scenario labels, `#focusBanner` (“Existing routes · October 2026 timetable”), the snapshot dates in the intro and footer, and the `June 30, 2026` performance period;
   - `assets/saving-tab.html`: the same snapshot and performance dates;
   - `assets/app.js`: the current-period label (`October 2026`);
   - regenerated `data/*.json` labels, if the scripts expose them as options.
4. Re-run `python scripts/build_atlas.py`, then `python tests/test_atlas.py` with the preview server running.
5. Expect the integrity checks to fail until the new baseline is recorded: `tests/timetable-fingerprint.json` pins the route data and geometry, `accuracy-check/independent-audit.json` records the published-source audit, and several tests assert exact counts and figures (`19` regular lines, `258` midday departures, the `4,524,968` boardings total, the five-line performance ordering). Re-run `python accuracy-check/audit_atlas.py`, review its output, and update those baselines only after confirming the new numbers against the source documents by hand.
6. `python scripts/package_project.py` rebuilds the downloadable project ZIP once `tests/test-report.json` is regenerated without errors.

Do not edit `index.html` or `Santa-Barbara-Transit-Atlas.html` by hand: the build overwrites both from `assets/`, and CI fails when they do not match.

### Tests and package

`tests/test_atlas.py` checks the two factual views, removal of modeled columns, all route records, the planning options and evidence, links back to unchanged current geometry, legacy cut-URL migration, CSV downloads, mobile layout, offline use and a scripts-only opaque iframe. Current results: `tests/test-report.json`.

To rerun browser tests: install `playwright`, install Chromium with `python -m playwright install chromium` (and dependencies if needed), start the preview server, then run `python tests/test_atlas.py`.

GitHub Actions runs exactly that sequence on every push and pull request (`.github/workflows/atlas.yml`), uploads `tests/test-report.json` as an artifact, and blocks publication when the suite fails or `index.html` is out of date.

`python scripts/package_project.py` creates **`Santa-Barbara-Transit-Atlas-Project.zip`**, with the app, source files and data. It also refreshes the older `SBMTD-Atlas-Project.zip` download as an identical copy. A pre-revision backup is retained separately under `revisions/`; it is not included in the current deliverable.

## Important files

- `Santa-Barbara-Transit-Atlas.html` / `index.html` — identical self-contained app / static-host entry.
- `data/route-comparison.csv` — all 48 route records; actual 2019/today metrics only.
- `data/route-performance-fy2025-26.csv` — 24 published annual/quarterly evidence records, with scope, period and source-page fields.
- `data/network.json` / `data/provenance.json` — factual routes, calendars, stops, metrics and integrity hashes.
- `data/planning.json` — separate planning evidence, definitions, limits, source metadata and current GTFS trunk-departure check.
- `sources/` — original GTFS ZIPs, captured official performance/budget/funding PDFs and verified transcription.
- `assets/app.*` — factual-map source; `assets/saving.*` and `assets/saving-tab.html` — the independent notebook.
- `scripts/` — reproducible data, build and package scripts.
- `NOTICE.md` — source terms and third-party credits.

Independent civic visualization, not affiliated with or endorsed by MTD. Consult official timetables for travel. Snapshot date: **October 15, 2026**.

### Reading limited service versus reference paths

- **Solid purple + clock-marked badge:** scheduled limited/timed trips run on the selected sample weekday, but no regular midday headway can be estimated. A route may operate only outside 10 am–2 pm. Directory labels, line details and purple table cells explicitly say that trips run.
- **Bold, dark dashes:** no active trips in the selected view; the path shows where that route ran, rather than current service. By default these are 2019 lines with no trips on the current sample date. Selecting a line present only in the other snapshot also shows that snapshot’s reference geometry. The missing-route key leads the legend and follows the paths actually drawn, including when the lost-lines overlay is off.

The difference uses both color and stroke pattern, not color alone. Source data, route geometry, actual counts, dates and the separate Saving MTD notebook are unchanged.

### Map emphasis and copy

Missing routes are drawn above current service with **4.2 px charcoal dashes, 97% opacity, white dashed halos and dark route badges**. They remain visible where old and current routes overlap. Limited service stays solid purple with a clock badge. Selecting a route still dims the others so its path is easy to follow.

Both tabs use descriptive headings instead of slogans. The map and Saving MTD use shorter explanations; source dates, scope and calculation details live in Sources & method and the expandable table note. Route annotations have been rewritten in the same voice. The original geometry and every historic/current timetable field are checked against `tests/timetable-fingerprint.json`.

## Accuracy audit — October 24, 2026

See **`Accuracy-Check.md`** for the source audit. A separate parser checked both ZIPs, all 85 route records, 84 shape-bearing route profiles, 1,298 stop records and 96 numerical performance-table cells against the original PDFs. The source files downloaded again on October 24 match the bundled originals.

The headline results hold: 392 → 258 midday departures; six missing 2019 route numbers. One detail bug was corrected: line 10’s 352- and 425-minute morning-to-afternoon breaks were being displayed as directional midday intervals despite zero midday trips. Direction intervals now require two actual midday departures. Main counts, route-level frequencies and geometry did not change. Historical route-name aliases and the fee proposal’s annual 0–4% COLA were clarified.

Repeat the independent check with `python -m pip install shapely pymupdf`, then `python accuracy-check/audit_atlas.py`. It does not import the production calculation functions. Before/after findings, exact corrections, live-source hashes, source-link checks and source departure records are preserved in `accuracy-check/`.

