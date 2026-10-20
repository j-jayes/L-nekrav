---
name: viz-index
description: >-
  Choose the right ggplot2 chart for a question and apply the house
  conventions — numbers, units, titles, colour, fonts, sizes — with the R/viz.R
  helpers. The entry point to the viz-* skills. Use when asked to "make a
  chart", "plot this", "visualise this data", "which chart should I use", or
  before starting any ggplot figure.
---

# Charts in ggplot2, the house way

These skills codify how Jonathan makes charts: Claus Wilke's rules
(*Fundamentals of Data Visualization* and his SDS375 course) plus habits from
the blog — the categorical variable on the y-axis sorted largest at top,
numbers written `1,000` and `5m`, coloured words in the title instead of a
legend, Brewer palettes, ridgelines. Every chart runs on one helper file and
follows the conventions below; the family skills carry the templates.

Two things this family does not do. Charts for the web in HTML or JavaScript
are Anthropic's built-in `dataviz` skill. Box-and-arrow exhibits (operating
models, process flows) are `ggplot-diagrams`.

## Get the helpers

Copy [reference/viz.R](reference/viz.R) into the project as `R/viz.R` — from
this repo, or from the installed plugin under
`~/.claude/plugins/cache/j-jayes/slides/<version>/skills/viz-index/reference/`.
Then the setup chunk is:

```r
source("R/viz.R")
viz_use_fonts(dpi = 300)   # equal to the ggsave dpi; 96 inside a Quarto chunk
library(ggplot2)
library(dplyr)
library(forcats)
```

| Helper | What it gives you |
|---|---|
| `theme_viz(base_size = 14, grid = "h")` | The house theme. `grid = "v"` for horizontal bars, `"both"` for scatterplots |
| `viz_use_fonts(dpi)` | Registers Inter via showtext; returns FALSE quietly when offline |
| `viz_font()` | `"Inter"` once registered, else `""` — use it in `geom_text(family =)` |
| `viz_span(text, colour)` | A coloured, bold word for a markdown title or subtitle |
| `label_short()` | `1,000 · 25,000 · 5m · 1.2bn` for scales and value labels |
| `label_pct()` | `12%`; `label_pct(accuracy = 0.1)` for `12.5%` |
| `viz_colours` | `single`, `highlight`, `muted`, `ink`, `text`, `grey_text`, `grid`, `reference` |
| `viz_palette` | Brewer Dark2, eight hexes |

Needs ggplot2, ggtext and scales; showtext and sysfonts for the font. Nothing
else. Each family skill names at most one extra package and says how to
install it.

## Which chart

Wilke organises charts by the question asked, not by the data type. Find the
question, then open that skill.

| The question | Reach for | Not | Skill |
|---|---|---|---|
| How much, per category | Horizontal bars sorted largest at top; dots when the axis cannot start at zero; facets when there is a second category; a heatmap when there are too many for bars | Vertical bars with rotated labels; grouped bars; a truncated bar axis | `viz-amounts` |
| How is it spread | A histogram with a chosen binwidth; overlapping densities; violin plus points; ridgelines for many groups or over time | Stacked histograms; a point with error bars standing in for a distribution | `viz-distributions` |
| What share of the whole | Stacked bars with `position = "fill"` for a few parts across conditions; side-by-side bars to compare the fractions; a pie only for one simple fraction of one small whole | Pies with more than three slices; stacked bars with more than three parts to compare | `viz-proportions` |
| How did it change | Lines with labels at their ends; an index rebased to 100; a log axis for growth; a slope graph for a few paired values | A legend for four lines; area from a non-zero base; a connected scatterplot | `viz-trends` |
| How do x and y relate | Scatter with alpha and a stated smooth; 2-D bins when points pile up; an x = y line for paired data | Bubble sizes; a correlogram before the raw data has been shown | `viz-associations` |
| How sure are we | A coefficient plot with intervals; a ribbon around a fit; SD, SE and CI drawn as what they are | Error bars that do not say what they are; overlap rules of thumb | `viz-uncertainty` |
| Where | A choropleth of a rate, 4–6 bins, equal-area projection | A choropleth of counts; Mercator for a data map | `viz-maps` |
| Several charts at once | Facets with shared scales, or patchwork panels with tags | Panels with silently different axes | `viz-compound` |
| A table, not a chart | Wilke's six table rules in gt | Vertical rules, lines between rows | `viz-tables` |

Colour has its own skill because it cuts across all of them: `viz-colour`.
Titles, annotations and point labels are `viz-labels`. When the chart is
drawn, `viz-review` is the checklist.

## Conventions every chart follows

| | Rule |
|---|---|
| Numbers | `label_short()` on every axis and value label: `1,000`, `25,000`, `5m`, `1.2bn`. Never `25000`, never `1e+06`. Percentages via `label_pct()`: `12%` |
| Units | Always in the axis title: `Sales volume (USD)`, `Share of adults (%)`. `labs(y = NULL)` only when the category labels themselves are the axis |
| Title | Depends on where the chart goes — see below |
| Legend | Four colours or fewer: no legend; name the colours as words in the title or subtitle with `viz_span()`. More than four: a legend, at the bottom. A continuous scale: a wide horizontal colourbar at the bottom |
| Colour | One series: `viz_colours[["single"]]` (midnightblue). Highlight: everything `muted` (grey80) and the one thing `highlight` (#D95F02). Two to six categories: `viz_palette` (Dark2). Colour-blind safety must be certain: `palette.colors(palette = "Okabe-Ito")` |
| Sort | Categories on the y-axis, largest at the top, unless the order is natural (age bands, months). A lumped "Other" is always the bottom bar, in grey |
| Bars | Start at zero; `expand = expansion(mult = c(0, 0.05))` so the bar base touches the axis |
| Grid | One direction only: horizontal for most charts, vertical for horizontal bars. No ticks, no minor grid |
| Font | Inter for everything, including `geom_text(family = viz_font())`. Text sizes in `geom_text` are millimetres and are not inherited: write `size = 11 / .pt` for 11 pt |
| Caption | `Source: <where the data came from>`. Add `Note: <method>` only when the reader needs it to trust the chart |
| Size | Blog or report: `width = 8, height = 5`, `base_size = 14`. Slide: `fig-width: 12, fig-height: 3.7` full width or `8 × 4.6` in a column, `base_size = 20` |

## Standalone chart or slide chart

The same data gets two different titles.

**Standalone** (blog post, report, a PNG sent on its own): the title is the
takeaway — a sentence someone could disagree with — and the coloured words in
it are the legend. The subtitle says what is measured.

```r
labs(
  title = paste(viz_span("Houston", viz_palette[1]), "pulled away from",
                viz_span("Dallas", viz_palette[2]), "after 2011"),
  subtitle = "Median sale price, 2000–2015",
  x = NULL, y = "Median price (USD)",
  caption = "Source: ggplot2::txhousing"
)
```

**On a slide**: the slide's `###` already carries the claim, so the chart
title is a short noun phrase or absent, and the coloured words move to the
subtitle. Repeating the claim inside the figure makes the slide say it twice.

```r
labs(
  title = "Median sale price",
  subtitle = paste(viz_span("Houston", viz_palette[1]), "and",
                   viz_span("Dallas", viz_palette[2])),
  x = NULL, y = "USD"
)
```

`viz-labels` ships both as one script.

## On a Nexer slide

The Nexer kit has its own theme and palette; the conventions above still
apply, with these substitutions:

| Here | In a Nexer deck |
|---|---|
| `theme_viz()` | `theme_nexer()` from `R/nexer-ggplot.R` |
| `viz_use_fonts()` | `nexer_use_fonts()` (Outfit and Inter) |
| `viz_span()` | `nexer_span()` |
| `viz_colours[["single"]]` | `nexer_colours[["purple"]]` |
| `viz_colours[["highlight"]]` | `nexer_colours[["orange"]]` — the one thing on the slide |
| `viz_colours[["muted"]]` | `nexer_colours[["grey"]]` |
| `viz_palette` | `nexer_palette` |
| Units in the axis title | `theme_nexer()` blanks axis titles; put the units in the `::: {.units}` rail under the chart |
| `caption = "Source: …"` | The `::: {.source}` rail |

`label_short()` and `label_pct()` exist in `nexer-ggplot.R` too, so nothing
needs sourcing twice. The `nexer-slides` skill has the placement rules for the
rails and the sizes that survive the PowerPoint export.

## Running a template

Every family skill's `reference/*.R` is a complete script. It sources the
helpers from `R/viz.R` by default and writes its PNG to a temp directory:

```bash
VIZ_HELPERS=skills/viz-index/reference VIZ_OUT_DIR=out \
  "/c/Program Files/R/R-4.5.1/bin/Rscript.exe" skills/viz-amounts/reference/bars-sorted.R
```

`VIZ_HELPERS` points at the folder holding `viz.R` (omit it once the file is
copied to `R/`); `VIZ_OUT_DIR` is where the PNG lands, printed on the last
line so you can Read it. The kit's test suite runs every template the same
way: `python -m unittest tests.test_viz_templates -k amounts` from `slides/`.

## What does not work

- **`Rscript -e` with a multi-line expression segfaults on Windows**, and a
  `<span>` inside `-e` is eaten by the shell as a redirection. Put the code in
  a file and run the file.
- **showtext's dpi must equal the render dpi.** `viz_use_fonts(dpi = 96)` with
  `ggsave(dpi = 300)` draws every label at a third of its size, with no
  warning. Pass the same number to both.
- **`coord_flip()` for horizontal bars.** Map the category to `y` directly;
  every scale and label then refers to the axis it is on.
- **`geom_hex()` needs the hexbin package.** Use `geom_bin2d()` unless it is
  installed.
- **`label.size` on `geom_label()` is deprecated** in ggplot2 4.0 and warns;
  use `linewidth = 0` to drop the border.
- **`print(p)` under Rscript writes `Rplots.pdf`** into the working directory.
  Always `ggsave()`.
- **A transparent PNG on a dark viewer** is unreadable; `theme_viz()` paints
  the plot background white and the templates pass `bg = "white"` as well.

## Related skills

The nine chart-family skills above, then `viz-colour`, `viz-labels` and
`viz-review`. `nexer-slides` is the skin for a Nexer deck, `jonathan-slides`
the deck structure, `mckinsey-slides` the rigour, `ggplot-diagrams` the
box-and-arrow exhibits.
