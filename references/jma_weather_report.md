# JMA weather observations for reproducible roof-snow simulation

## Bottom line

Use JMA's **Past Weather Data Download** as the primary official bulk route:
<https://www.data.jma.go.jp/risk/obsdl/>. It openly exports hourly (`aggrgPeriod=9`) and daily (`aggrgPeriod=1`) CSV for multiple stations, elements, and periods, including per-value quality information and observation-environment discontinuity information. Use JMA's **Historical Weather Data Search** pages (<https://www.data.jma.go.jp/stats/etrn/>) for human-readable spot checks and direct verification URLs.

The web tool internally submits POST requests to `/risk/obsdl/show/table`; a test request reproduced both hourly and multi-station daily CSV. This is a reproducible interface, but JMA does **not** document it as a stable, versioned public API. For publication-grade reproducibility, retain the original CSV bytes, the complete POST parameters, retrieval UTC time, response headers, SHA-256, the downloaded client JavaScript version, and the applicable terms. Do not build an unattended high-rate crawler around an undocumented interface.

## Reproducible routes

### 1. Preferred bulk CSV route

The JMA client currently uses:

```text
POST https://www.data.jma.go.jp/risk/obsdl/top/station   pd=<prefecture-area code>
POST https://www.data.jma.go.jp/risk/obsdl/top/element  aggrgPeriod=9|1
POST https://www.data.jma.go.jp/risk/obsdl/show/table
```

Core `show/table` fields observed in the official client and verified by retrieval:

```text
stationNumList   JSON array, e.g. ["s47433","s47575","a1079","a0543"]
aggrgPeriod      9 hourly; 1 daily
elementNumList   JSON array, e.g. [["201",""],["101",""],["503",""],["501",""]]
interAnnualType  1 for a continuous period
ymdList          [startYear,endYear,startMonth,endMonth,startDay,endDay]
optionNumList    JSON array; [] if no normals/comparison columns
downloadFlag     true
rmkFlag          1 to retain values requiring attention and their quality columns
disconnectFlag   1 to retain all periods and homogeneity-number columns
csvFlag          1 for numeric CSV
jikantaiFlag     0 for all 24 hours
jikantaiList     ["1","24"]
ymdLiteral       1 for date-time literals
```

The downloaded file is CP932/Shift_JIS despite an `application/octet-stream` response; preserve the original and make a separate UTF-8 derivative. The tool enforces a workload meter, so retrieve large studies in deterministic station/winter chunks and record every chunk. A four-station daily request and a 24-hour Sukayu request were successfully reproduced with these parameters.

### 2. Readable audit URLs

```text
Hourly observatory:
https://www.data.jma.go.jp/stats/etrn/view/hourly_s1.php?prec_no=PP&block_no=BBBBB&year=YYYY&month=MM&day=DD&view=p1

Hourly AMeDAS:
https://www.data.jma.go.jp/stats/etrn/view/hourly_a1.php?prec_no=PP&block_no=BBBB&year=YYYY&month=MM&day=DD&view=p1

Daily observatory:
https://www.data.jma.go.jp/stats/etrn/view/daily_s1.php?prec_no=PP&block_no=BBBBB&year=YYYY&month=MM&day=&view=p1

Daily AMeDAS:
https://www.data.jma.go.jp/stats/etrn/view/daily_a1.php?prec_no=PP&block_no=BBBB&year=YYYY&month=MM&day=&view=p1
```

Example: Sukayu hourly, 15 January 2024:
<https://www.data.jma.go.jp/stats/etrn/view/hourly_a1.php?prec_no=31&block_no=1079&year=2024&month=01&day=15&view=p1>.

## Neutral candidate station panel

`s` denotes a JMA observatory/synoptic station in the download tool; `a` denotes AMeDAS. Snow normals below are JMA 1991–2020 annual normals and establish that these are genuinely snow-rich sites; they are not simulated values.

| Contrast | Station | Download ID / `block_no` | `prec_no` | Coordinates; elevation | Annual snowfall / maximum snow depth normal |
|---|---|---:|---:|---|---:|
| Cold Hokkaido inland | Kutchan (倶知安) | `s47433` / `47433` | `16` | 42°54.0′N, 140°45.4′E; 176.1 m | 921 cm / 183 cm |
| Low-elevation maritime northern Honshu | Aomori (青森) | `s47575` / `47575` | `31` | 40°49.3′N, 140°46.1′E; 2.8 m | 567 cm / 101 cm |
| Inland Tohoku basin | Shinjo (新庄) | `s47520` / `47520` | `35` | 38°45.4′N, 140°18.7′E; 105.1 m | 637 cm / 128 cm |
| Warmer Japan-Sea lowland | Takada (高田) | `s47612` / `47612` | `54` | 37°06.4′N, 138°14.8′E; 12.9 m | 413 cm / 96 cm |
| High mountain stress case | Sukayu (酸ケ湯) | `a1079` / `1079` | `31` | 40°39.0′N, 140°51.0′E; 890 m | 1,706 cm / annual value not published |
| Very snowy Niigata upland | Tsunan (津南) | `a0543` / `0543` | `54` | 36°59.8′N, 138°41.0′E; 452 m | 1,301 cm / 271 cm |

For a model needing humidity and pressure, use the four `s` stations as the primary panel, then add Sukayu/Tsunan as stress tests only after documenting their element availability. The verified daily sample showed no humidity or global-radiation observation at Sukayu or Tsunan for the test day; missing forcings must not be invented. Global radiation is also not uniformly available at observatories, so construct a station-by-element-by-period availability matrix before freezing the panel.

## Variables, identifiers, and units

| Resolution | Element ID | JMA quantity | Unit / interpretation |
|---|---:|---|---|
| Hourly | `201` | Air temperature | °C |
| Hourly | `101` | Precipitation | mm accumulated over the preceding hour; gauge precipitation is melted liquid-water equivalent |
| Hourly | `503` | Snowfall depth | cm over the preceding hour; JMA derives snowfall depth from changes in measured snow depth |
| Hourly | `501` | Snow depth | cm, ground snow depth |
| Hourly | `301` | Wind speed and direction | m/s and 16-point direction; speed/direction represent the preceding 10-minute mean |
| Hourly | `401` | Sunshine duration | h over the preceding hour |
| Hourly | `610` | Global solar radiation | MJ/m² over the preceding hour where available |
| Hourly | `601`, `602` | Station / sea-level pressure | hPa |
| Hourly | `604`, `605`, `612` | Vapor pressure / relative humidity / dew point | hPa / % / °C |
| Daily | `201`, `202`, `203` | Mean / maximum / minimum temperature | °C |
| Daily | `101`, `105` with subparameter `1` | Total / maximum one-hour precipitation | mm |
| Daily | `501`, `503` | Maximum snow depth / total snowfall | cm |
| Daily | `301`, `302` | Mean / maximum wind | m/s, with direction fields where supplied |
| Daily | `401`, `610` | Sunshine / total global radiation | h / MJ/m² |
| Daily | `601`, `602`, `604`, `605`, `606` | Pressure, vapor pressure, mean/minimum humidity | hPa / % |

JMA AMeDAS nominal reporting resolution is 0.1 °C, 0.5 mm precipitation, 0.1 m/s wind, 0.1 h sunshine, 1 cm snow depth, and 1% relative humidity. Availability varies by station and era. For non-observatory AMeDAS sites, sunshine after **2 March 2021** is an estimate from JMA's gridded estimated meteorological distribution rather than the earlier on-site sunshine measurement.

## Quality, missingness, and discontinuities

Select numeric CSV and retain quality and homogeneity columns.

| Quality code | JMA meaning | Recommended treatment |
|---:|---|---|
| `8` | Normal; no source-data loss | Accept |
| `5` | Quasi-normal; missing source material remains within the allowed range, generally about 80% completeness | Accept only under a preregistered rule; sensitivity-test |
| `4` | Insufficient source material | Exclude from primary analysis or flag explicitly |
| `2` | Very doubtful value; hourly only | Exclude pending manual verification |
| `1` | Missing statistic | Keep null; never zero-fill |
| `0` | Not an observed/statistical item, including some reference normals | Structurally unavailable; do not impute as an observation |

The detailed Help 3 table gives the mapping above. Help 1 contains an apparent contradictory sentence stating that numeric-CSV missingness receives quality `0`; this conflicts with Help 3's explicit table (`1` missing, `0` non-item). A production parser should preserve the raw code, distinguish `0` from `1`, and include fixtures covering both before analysis.

For observatory precipitation, sunshine, or snowfall, numeric CSV can also include **phenomenon-none information** (`1` no phenomenon, `0` phenomenon occurred). Do not conflate this with missingness. Homogeneity numbers identify observation-environment regimes: values with different numbers are not simply comparable. Numbers are assigned afresh, oldest first, for each CSV retrieval, so do not join separately downloaded chunks by the number alone; retain full overlapping extraction context and align boundaries by timestamp/metadata.

## Required transformations for snow simulation

1. **Preserve provenance:** archive original bytes; store request parameters, UTC retrieval time, SHA-256, terms URL, and a separate UTF-8 derivative.
2. **Parse multirow headers:** station, variable, phenomenon-none, quality, and homogeneity are separate logical fields.
3. **Time:** label source time as JST (`Asia/Tokyo`, UTC+09:00; no daylight saving). Bulk CSV already emitted the final hourly record as next-day `00:00`; the HTML hourly view may label it `24`, which must be rolled to the following date before conversion to UTC.
4. **Intervals:** precipitation, snowfall, sunshine, and hourly radiation are preceding-hour accumulations; temperature/snow depth are state observations. Do not shift all columns identically.
5. **Snow quantities:** precipitation is liquid-water equivalent in mm; snowfall and snow depth are geometric cm. Converting either to snow mass or roof load requires an explicit, validated density/compaction/phase model. Ground snow depth is not roof snow depth and does not represent wind redistribution, sliding, or roof heat loss.
6. **Wind:** preserve the 16-point direction and calm/missing categories; if converting to degrees, document the lookup and circular treatment.
7. **Quality:** propagate all flags through resampling. Never convert blanks, `///`, quality `0`, or quality `1` to zero. Aggregate only under a declared completeness rule.
8. **Discontinuities:** do not compare across homogeneity regimes without adjustment or a regime indicator.
9. **Availability changes:** freeze a station-element-period matrix before simulation. Treat the 2021 AMeDAS sunshine-method change as a measurement-regime change.

## Scientifically neutral station and winter selection

Predeclare the algorithm before viewing simulation outcomes.

1. **Station strata:** choose at least one site from each prespecified contrast—cold Hokkaido inland, low-elevation maritime, inland basin, warmer Japan-Sea lowland—and optionally mountain/upland stress sites. Select within strata by required-variable coverage and record length, not by simulated roof load.
2. **Eligibility:** require the same core hourly variables for the entire fixed snow season (for example, 1 November–30 April), a stable or explicitly modelled homogeneity regime, and a preregistered completeness threshold. A defensible starting rule is at least 95% quality `8`/`5` values for every core forcing, with sensitivity analyses at stricter/looser thresholds and no missingness during selected peak events.
3. **Common period:** use the largest common set of eligible winters across the fixed station panel. Label a winter by its starting year and never mix calendar-year snow statistics with cross-year simulation seasons.
4. **Winter severity:** rank winters using observed JMA quantities fixed in advance—preferably station-specific percentile of seasonal maximum snow depth or cumulative snowfall. Station-relative percentiles avoid favoring intrinsically snowier climates.
5. **Contrasting winters:** if all eligible winters cannot be simulated, select deterministically nearest to prespecified percentiles (for example 50th, 85th, and 95th) with a fixed tie-break such as earliest winter. For wet-snow contrast, add mean winter temperature or rain-on-snow hours as a second prespecified axis and use a deterministic maximin selection.
6. **No outcome selection:** do not choose stations or winters because they maximize the proposed model's load, failure, or treatment effect. Report excluded seasons and repeat the primary conclusion over all eligible winters or with leave-one-winter/station-out sensitivity analysis.

## Terms

JMA states that content without a separate rights notice may be used under the **Public Data Use Terms, Version 1.0**. Cite the JMA page and URL; if data are decoded, merged, filtered, converted to UTC, or otherwise transformed, explicitly state that processing was performed and do not imply that JMA created the derivative. No DOI was shown on the official product pages inspected; cite the official product, station identifiers, exact URL/request, and retrieval date rather than inventing a DOI.

## Verification table

| Source | Identifier / DOI | Claim supported | Verification URL | Confidence |
|---|---|---|---|---|
| JMA Past Weather Data Download | No DOI shown; official JMA web product | Open multi-station, multi-element, multi-period CSV route | <https://www.data.jma.go.jp/risk/obsdl/> | High |
| JMA download Help 1 | No DOI shown; `obsdl/help1` | Tool purpose, workload limit, options, numeric CSV, availability varies by station/era | <https://www.data.jma.go.jp/risk/obsdl/top/help1> | High |
| JMA download Help 3 | No DOI shown; `obsdl/help3` | CSV structure, quality codes, phenomenon-none and homogeneity semantics | <https://www.data.jma.go.jp/risk/obsdl/top/help3> | High for the explicit table; exact missing-code documentation has an internal Help 1 conflict |
| Official download client JavaScript | No DOI shown; `top.2.1.js` | POST endpoints and parameter names used by the UI | <https://www.data.jma.go.jp/risk/obsdl/web/js/top.2.1.js> | High for current observed behavior; Medium for future stability |
| JMA station selector | Download IDs `s47433`, `s47575`, `s47520`, `s47612`, `a1079`, `a0543`; no DOI shown | Download-tool identifiers, coordinates, elevations, and station type; POST with `pd=16,31,35,54` | <https://www.data.jma.go.jp/risk/obsdl/top/station> | High for current metadata; request body must be recorded |
| JMA AMeDAS explanation | No DOI shown; official JMA explanatory page | Units, precipitation/wind/snow meanings, 2021 sunshine-method change | <https://www.jma.go.jp/jma/kishou/know/amedas/kaisetsu.html> | High |
| JMA historical search, Kutchan normal | `prec_no=16`, `block_no=47433`; no DOI shown | Station identifier; 1991–2020 snowfall and maximum-depth normals | <https://www.data.jma.go.jp/stats/etrn/view/nml_sfc_ym.php?prec_no=16&block_no=47433&year=&month=&day=&view=> | High |
| JMA historical search, Aomori normal | `prec_no=31`, `block_no=47575`; no DOI shown | Station identifier; 1991–2020 snowfall and maximum-depth normals | <https://www.data.jma.go.jp/stats/etrn/view/nml_sfc_ym.php?prec_no=31&block_no=47575&year=&month=&day=&view=> | High |
| JMA historical search, Shinjo normal | `prec_no=35`, `block_no=47520`; no DOI shown | Station identifier; 1991–2020 snowfall and maximum-depth normals | <https://www.data.jma.go.jp/stats/etrn/view/nml_sfc_ym.php?prec_no=35&block_no=47520&year=&month=&day=&view=> | High |
| JMA historical search, Takada normal | `prec_no=54`, `block_no=47612`; no DOI shown | Station identifier; 1991–2020 snowfall and maximum-depth normals | <https://www.data.jma.go.jp/stats/etrn/view/nml_sfc_ym.php?prec_no=54&block_no=47612&year=&month=&day=&view=> | High |
| JMA historical search, Sukayu normal | `prec_no=31`, `block_no=1079`; no DOI shown | Mountain station identifier and 1,706 cm annual snowfall normal | <https://www.data.jma.go.jp/stats/etrn/view/nml_amd_ym.php?prec_no=31&block_no=1079&year=&month=&day=&view=> | High |
| JMA historical search, Tsunan normal | `prec_no=54`, `block_no=0543`; no DOI shown | Upland station identifier; 1,301 cm snowfall and 271 cm maximum-depth normals | <https://www.data.jma.go.jp/stats/etrn/view/nml_amd_ym.php?prec_no=54&block_no=0543&year=&month=&day=&view=> | High |
| JMA content-use terms | Public Data Use Terms v1.0; no DOI shown | Reuse basis, attribution, and disclosure of editing/processing | <https://www.jma.go.jp/jma/kishou/info/coment.html> | High |

### Remaining limitations

- JMA exposes a web application, not a documented versioned archive API; the POST contract can change.
- Availability of humidity, pressure, radiation, sunshine, and snow varies by station and period and must be verified before locking the analysis.
- The JMA help pages conflict on quality code for missing numeric values; retain raw flags and validate the parser against observed fixtures.
- No standard JMA observation here directly supplies roof snow load or snow-water equivalent; these require a separately justified model and independent validation.

No repository files were edited.
