---
name: viz-review
description: >-
  Review a finished ggplot2 chart against the house checklist — message,
  encoding, axes and numbers, colour, text, layout — by looking at the rendered
  PNG before it ships. Use as the last step of every viz-* skill, or when asked
  to "review this chart", "check the figure", "is this chart OK", "does this
  plot follow the rules".
---

# Review a chart before it ships

Wilke sorts bad figures into three bins. **Ugly** has aesthetic problems but
is clear. **Bad** has perception problems: unclear, confusing, misleading.
**Wrong** has mathematical problems: a truncated bar axis, a 3-D pie. This
checklist catches all three, in the order they matter.

Render the chart, then **Read the PNG**. Every line below is answered by
looking, not by reading the code. A *no* is a fix to the chart, not a note in
the report. Fix, re-render, look again.

## Message

- The title states a claim someone could disagree with — or, on a slide, the
  `###` does and the chart title is a short noun phrase or absent.
- One chart, one claim. If the chart supports two claims, it is two charts.
- The claim is true of the data drawn. `Twice` means twice.
- Every coloured word in the title or subtitle matches a colour actually drawn,
  and nothing drawn in colour is left unnamed.

## Encoding

- The chart family matches the question: amounts as bars or dots,
  distributions as densities or ridgelines, shares as filled bars, change as
  lines, relationships as points.
- Bars start at zero. A bar axis that does not is *wrong*; use dots.
- Categories run down the y-axis, largest at the top, unless the order is
  natural (age bands, months, Likert levels), in which case the natural order
  is kept.
- A lumped "Other" is the bottom bar, in grey.
- No rotated axis labels. Long labels mean horizontal bars.
- No pie unless it shows one simple fraction of one small whole.
- Lines only where the series is dense; dots where it is sparse; dots and
  lines where spacing is uneven.
- A filled area starts at zero.
- Nothing is encoded as bubble size that could be encoded as position.

## Axes and numbers

- Units are in the axis title. `Median price (USD)`, not `price`.
- Numbers read `1,000`, `25,000`, `5m`, `1.2bn`, `12%`. No `25000`, no
  `1e+06`, no `0.12`.
- A log axis is labelled in the real values, and the title says what the
  variable is, not "log of".
- An index says its base: `2000 = 100`.
- The bar base touches the axis (`expansion(mult = c(0, 0.05))`).
- A percentage whose base matters carries the base in the caption.

## Colour

- Four colours or fewer: no legend, the words in the title or subtitle carry
  the colours. More than four: a legend at the bottom.
- A highlight is one colour against grey80, not one bright colour among
  others.
- The same thing has the same colour in every panel and every chart in the
  set.
- No rainbow scale. No large saturated areas.
- Magnitudes use a sequential scale; a diverging scale only around a midpoint
  that means something (zero, the average, a target).
- If colour-vision safety must be certain, the palette is Okabe-Ito or
  viridis.

## Text

- Inter is drawn. The run printed no "font family not found" warnings.
- `base_size` fits the destination: 14–16 for a blog or report figure at
  8 × 5 in, 20 for a slide.
- Nothing is clipped at the panel edge; no labels overlap.
- Lines are labelled at their ends, not in a legend.
- An annotation crossing a line has a white backing (`annotate("label",
  fill = "white", linewidth = 0)`).
- Reference lines are dashed and grey.
- The caption starts `Source:`; a `Note:` is there only if the method needs
  stating.

## Uncertainty

- Every interval says what it is: SD, SE, or a 95% CI.
- A smooth says its method: `Note: line is a linear fit` or
  `loess, span 0.75`.
- No claim rests on whether two error bars overlap.

## Layout

- Grid in one direction only: horizontal for most charts, vertical for
  horizontal bars, both for a scatterplot. No ticks, no minor grid.
- The title is flush with the left edge of the plot, not of the panel.
- Facets share scales, or the caption says they do not, and the panels are in
  a meaningful order.
- The figure size matches where it is going, and the text is still readable
  when the PNG is viewed at half size.

## On a Nexer slide only

- `theme_nexer()`, `nexer_use_fonts()`, `nexer_span()`.
- Units in the `::: {.units}` rail, source in `::: {.source}` — the theme
  blanks axis titles.
- One series in purple, the rest grey, orange for the single fact the slide
  exists to deliver.
- `fig-width: 12` full width or `8` in a column, and the deck rendered to
  both formats before anyone looks at the PowerPoint.

## Last

- The run left no `Rplots.pdf` behind.
- The PNG is larger than 10 KB — an empty panel is not.
- You looked at it. Not the code: the picture.

## What this checklist actually catches

Every one of the thirty templates in the `viz-*` skills was built, rendered,
and read against the list above. Six faults came up again and again, and
none of them is visible in the code:

| Fault | What it looked like |
|---|---|
| **A title that outran the data** | "Houston sold twice what Dallas did" against a 1.4× gap; "rose by half" against 75%; "a third more in summer" against 27%. Fix: compute the figure and paste it in, so the claim cannot drift |
| **A title clipped at the right edge** | Seven of thirty. A markdown title does not wrap; past the panel it is cut with no warning. Fix: `<br>` at a clause boundary |
| **A claim naming the wrong thing** | A heatmap crediting Austin for a row that was Collin County; a coefficient plot saying "move" over a single term. Fix: derive the name from the same ordering the chart draws |
| **Colour keyed to sort order** | The line chart gave San Antonio the colour Austin had in the chart beside it, because the palette was indexed by factor position. Fix: `setNames(palette, names)` |
| **Labels colliding** | Two end labels overprinting on the indexed lines; group sizes landing on the outlier points. Fix: nudge them apart, or move them into the axis labels |
| **A layer the theme does not reach** | `coord_sf()`'s graticule survives `theme_viz(grid = "none")`; a pie kept its bar-chart axis title. Fix: look, then blank what you see |

Read the picture. Every one of these renders without a warning.

## Related skills

`viz-index` holds the conventions this checklist enforces; each family skill
holds the template the chart came from. For a chart on a slide,
`nexer-slides` has the export rules and `mckinsey-slides` the chart
conventions of a consulting deck.
