# UI contract: the market panel (compare view)

The panel sits under each compare column, below the official tasks, headed "Market". It fetches
`GET /api/v1/occupations/{code}/market` once per code shown.

1. **Notice** (always): `notice` from the answer. The page holds no copy of its own.
2. **Open now**:
   - `available`: "{ads} open ads, {positions} positions on Platsbanken", then the top 5 counties
     with their counts, the rest in a `<details>`, and "no county given" if it is above 0. The
     source links to the request URL, with "fetched {time}".
   - `available` with `shared_with`: adds "Shared with {codes}: JobTech counts these codes
     together."
   - `no_concept`: "JobTech publishes no ads under this code, so there is no count."
   - `unavailable`: "The live count is unavailable ({reason})." No number.
3. **Pay by area ({regional_year}, SCB TAB5696)**: a sentence first, "These are mean salaries.
   The work-permit floor comes from the national median and is the same in every area", with
   the column's floor amount from the comparison. Then a table: Area | Mean (± margin) |
   Employees. A null cell reads "not published". With no rows: "SCB publishes no regional figures
   for this code."
4. **Ads per year**: a bar chart (one series, no legend) titled "Ads published per year
   (Platsbanken)", with a `<details>` table view and the source and build date. `no_concept`
   uses the same text as in 2.

The panel holds no thresholds or numbers of its own: the legal-literal scan still covers
`frontend/src`. It must fit 390 px with no sideways scroll and pass axe with no serious or
critical violations.
