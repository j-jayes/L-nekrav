# UI contract: Your number

## Steps (App)

A nav of three numbered steps: "1 Find your code" (`search`), "2 Your number" (`number`) and
"3 The rules" (`legal`). Steps 1 and 2 end with a button to the next step: "Next: your number"
(disabled with no code selected) and "Next: the rules". The advisor button stays in the header.

## 1 Find your code

- The search box, status and ad passages are unchanged.
- **Result card**: code and English title, the Swedish title, the matched passage, the flags and
  "Add" / "Added". The rank chips (`ScoreStrip`) sit in `<details>` "How this was matched".
- **Selected**: a chip per code with ×, and the "Next: your number" button. No chart here.

## 2 Your number (replaces Compare)

Top to bottom:

1. **Inputs**, in one row on desktop and stacked on a phone:
   - "Your number (SEK a month)", numeric;
   - "Age" (none + six bands);
   - "Where the job is" (none + eight national areas).

   Below them, `<details>` "Offer details (for the floor check)" holds `OfferForm` minus the salary
   field.
2. **The honest-fit statement**, once.
3. **One card per code**, in selection order and never ranked:
   - **Title line**: code, English title, Swedish title, ×.
   - **Headline**: "SCB {year}: the middle half earn {P25}–{P75} SEK; median {median}." The suppressed
     form names the missing figure.
   - **Position** (with a number): "Your {n} SEK is between the {lower} and the {upper}." Other
     forms are "at the {p}", "below the 10th percentile", "above the 90th percentile", and "SCB
     publishes no {missing}, so the nearest published figures are used." Percentile names read
     "10th percentile", "25th percentile", "median", "75th percentile" and "90th percentile".
   - **Estimate chip** (with an age band or an area): "Estimate for {age}{, in area}: {low}–{high}
     SEK · not an SCB figure", with a `<details>` for the formula and inputs. Each factor left out
     is shown with its reason.
   - **Floor check**: the existing `EligibilityResult` in compact form, with the source link and
     the checked-on date.
   - **`<details>` "What the work is"**: the official tasks in Swedish and English.
   - **`<details>` "Market"**: the existing `MarketPanel`, whose notice moves out of the card.
4. **The market notice**, once, above the first "Market" section.
5. **The salary chart** (below).
6. **Legal sources** and the disclaimer, as today.

Empty state with no codes: "Pick the code that matches your duties first", linking to step 1.

## Salary chart

Per row:
- a light P10–P90 bar;
- a strong P25–P75 bar;
- a median tick;
- a dashed outline for the estimate (P25–P75 simulated);
- a dashed muted floor line with the label "floor" on the first row.

A number line in the accent colour runs across all rows, labelled "your {n}" once. The scale is
padded around the drawn values (research R6). The legend lists only the marks drawn.
- **Table view**: Code | P10 | P25 | Median | P75 | P90 | Estimate P25–P75 | Floor | Your number.
- **Caption**: the sources, as today, plus "Estimates are not SCB figures."

Every mark stays focusable, and its value and source are read out. There is no sideways scroll at
390 px, and axe reports no serious or critical violations. The legal-literal scan still covers
`frontend/src`: copy and tests hold no floor amounts.
