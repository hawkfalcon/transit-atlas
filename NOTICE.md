# Source data and third-party notices

The project's own code, scripts, tests and explanatory text are MIT-licensed; see `LICENSE`. The components and data below keep their own terms, and the MIT license does not override them.

## Santa Barbara MTD GTFS

Bus routes, service calendars, trip times and stops are Santa Barbara Metropolitan Transit District data. Historical data were retrieved from the publicly available OpenMobilityData archive; current data were retrieved from MTD’s official feed. Original ZIPs are preserved with hashes in `data/provenance.json`.

MTD provides its data as-is and retains ownership. Review the agency’s applicable [GTFS terms and developer information](https://sbmtd.gov/gtfs/) before republishing or using it operationally. No MTD logo is included and no endorsement is implied. Agency references are descriptive.

## Independent archive index

The archive URL was found in `interline-io/scrape-of-transitfeeds`, a public metadata scrape accessed by its authors in August 2021. That repository describes its metadata as CC0. This does not relicense the underlying agency GTFS content.

https://github.com/interline-io/scrape-of-transitfeeds

## Basemap

**Esri, HERE, Garmin, © OpenStreetMap contributors, and the GIS user community.**

Reference service: https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer

The atlas embeds a small-area contextual mosaic from this public service, with zoom-13 network detail, zoom-12 surrounding context, an editorial light-aqua water tint, and softened image-boundary transitions. These are cartographic styling choices; route and stop coordinates are not shifted. The contemporary basemap is not a historical street reconstruction. Geographic source attribution is shown on the map. Third-party basemap content remains subject to its providers’ applicable terms; no blanket license is implied for republishing it.

`assets/basemap-source.json` preserves the service attribution and geographic image bounds.

## Leaflet 1.9.4

Copyright © Vladimir Agafonkin and contributors. BSD-2-Clause. The full license is preserved in `assets/leaflet-license.txt` and the library’s copyright header remains in the HTML.

https://leafletjs.com

## Manrope

Copyright © the Manrope project authors. SIL Open Font License 1.1. Full license: `assets/manrope-license.txt`.

https://github.com/google/fonts/tree/main/ofl/manrope

## axe-core (tests only)

The accessibility regression test uses **axe-core 4.14.0**, Copyright © Deque Systems, Inc., licensed under MPL-2.0. It is vendored unmodified at `tests/axe/axe.min.js` with its license and is executed only by `tests/test_accessibility.py`. Nothing from axe-core is inlined into the published HTML, and it adds no runtime dependency.

https://github.com/dequelabs/axe-core

## Independent visualization

The application code and explanatory text are original work created for this project. No third-party data ownership, agency endorsement or budget forecast is claimed. The main comparison contains only the two real GTFS networks. The separate Saving MTD notebook uses published route-performance and budget reports, preserving their periods and provenance. Network changes are independent study concepts; the specifically attributed student-pass fee item is a published staff proposal, not secured new funding. No quantified savings or implementable future timetable is claimed. The prior uniform 20% model is retired as a network mode and retained only as collapsed explanatory context in the planning notebook.


## Published planning evidence

FY2025–26 route performance (PDF pp. 2–3), the June 2026 budget executive summary (PDF p. 23) and the July 2026 UCSB fee staff proposal (PDF pp. 19–24) are Santa Barbara MTD publications. Source PDFs and hashes are preserved. Numeric route-performance figures were manually transcribed and visually verified, and all boarding counts reconcile to the published system totals. Reuse of factual figures does not imply ownership of the underlying reports or agency endorsement of the independent study ideas.
