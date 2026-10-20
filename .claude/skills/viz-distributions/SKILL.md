---
name: viz-distributions
description: >-
  Show how a variable is spread in ggplot2 — a histogram with a chosen
  binwidth, overlapping densities for a few groups, boxplots with the raw
  points, ridgelines for many groups or for change over time. Use when asked
  for a "histogram", "distribution", "spread", "density plot", "boxplot",
  "violin", "ridgeline", or when the question is about shape rather than a
  single number.
---

# Distributions: the shape of a variable

An amount is one number; a distribution is all of them. Wilke's escalation
runs histogram → density → boxplot → violin → ridgeline as the number of
groups grows, and his warning applies to every rung: each has a smoothing
parameter that decides what the reader sees, so the choice is yours and must
be stated.

Setup as in `viz-index`. ggridges is installed; nothing else is needed.

## Which chart

| Situation | Reach for | Template |
|---|---|---|
| One variable, first look | Histogram; draw three binwidths before choosing | [histogram-binwidth.R](reference/histogram-binwidth.R) |
| Two to four groups compared in shape | Overlapping densities, filled, named in the title | [densities-overlapping.R](reference/densities-overlapping.R) |
| Five to ten groups compared in centre and spread | Boxplots with the points beside them, sorted by median | [boxplot-strip.R](reference/boxplot-strip.R) |
| Many groups, or one group over time | Ridgelines, single fill | [ridgelines.R](reference/ridgelines.R) |

Violins sit between boxplots and ridgelines: use `geom_violin()` in place of
`geom_boxplot()` when a group may be bimodal (a boxplot cannot show two
peaks) and every group has enough points to justify a smooth outline —
around thirty or more. With fewer, the violin invents shape; show the points.

## The template

The ridgeline idiom from `ridgelines.R`, the chart this family is best known
for:

```r
prices <- ggplot2::txhousing |>
  filter(!is.na(median), year %in% seq(2000, 2015, 3)) |>
  mutate(year = fct_rev(factor(year)))       # earliest year on the top row

ggplot(prices, aes(median, year)) +
  geom_density_ridges(scale = 3, rel_min_height = 0.01, bandwidth = 8000,
                      fill = viz_colours[["single"]], colour = "white", alpha = 0.9) +
  scale_x_continuous(labels = label_short()) +
  scale_y_discrete(expand = expansion(add = c(0.2, 2.2))) +   # headroom for the top ridge
  labs(x = "Median sale price (USD)", y = NULL,
       caption = "Note: kernel density, bandwidth 8,000 USD. Source: ggplot2::txhousing") +
  theme_viz(grid = "v")
```

## Rules that matter

**Always explore several binwidths.** Too fine is noise, too coarse hides
the shape, and the right one depends on the data. `histogram-binwidth.R`
counts the bins itself and draws three panels because `geom_histogram()`
takes one binwidth per plot. The diamond data shows why: the spikes just
above the round carat weights exist only at 0.01.

**State the bandwidth.** A density is a histogram with a smoother; its `bw`
(`bandwidth` in ggridges) is the binwidth's cousin. Set it explicitly and
write it in the Note, so nobody mistakes a smoothing artefact for a feature.
Check that the curve does not run into impossible values — a density of ages
below zero is the classic.

**Densities overlap; histograms do not.** Semi-transparent filled densities
keep two to four groups apart because each has a continuous outline. Stacked
histograms are Wilke's "best avoided": no shared baseline, no readable
heights. Overlapping histograms read as a third colour where they cross.

**Name the groups in the title, not a legend.** Four colours or fewer means
`viz_span()` in the title or subtitle; `densities-overlapping.R` does both.
Key the palette to the group names, not the factor order.

**Show the points behind the box.** A boxplot with five observations looks
like one with fifty. `boxplot-strip.R` draws the raw points beside each box
and writes `(n = 47)` into the axis label so the count cannot collide with
the data. Jitter only along the category axis — `position_jitter(width = 0,
height = 0.18)` with the category on `y` — and never along the value axis, or
the points misreport the data.

**Sort groups by median.** `fct_reorder(class, hwy, .fun = median)`. Rows
then read as a ranking, and the title can say which group sits where.

**Ridgelines: one fill, white outline, time top to bottom.** Colour would only
distract from the shapes. `scale = 3` lets ridges overlap enough to read as
a landscape; `rel_min_height = 0.01` trims the flat tails that would
otherwise cross the neighbouring rows. `fct_rev()` on the year puts the
earliest at the top, since time reads down the page. Leave headroom for the
top ridge with `expansion(add = c(0.2, 2.2))` on the y-scale.

**Never a point with error bars for a distribution.** Error bars mean
uncertainty about an estimate, not the spread of a population, and symmetric
bars misreport any skew. Show the shape.

**Filled shapes, not outlines.** Wilke: solid shapes read as objects,
outlines create ambiguity about which side is inside. Fill histograms,
densities and boxes; draw the box in a light grey so the median line and the
points stand out.

## On a Nexer slide

`theme_nexer()`, fills in `nexer_colours[["purple"]]` with `alpha = 0.6` for
overlapping densities, `grey_pale` for the box and `purple` for the points.
Ridgelines at `fig-width: 12, fig-height: 5` hold about eight rows at
`base_size = 20`; more than that, sample every second or third period as the
template does. The bandwidth note goes in the `::: {.source}` rail.

## What does not work

- **`geom_histogram()` with the default 30 bins.** It prints a message
  telling you to pick a binwidth; do.
- **Stacked histograms**, or overlapping ones with alpha.
- **A violin on a group of five.** The smooth outline claims density where
  there are two points.
- **Jitter in both directions.** `geom_jitter()`'s default moves points
  along the value axis too.
- **A boxplot with outliers drawn twice.** With points beside the box, set
  `outlier.shape = NA` or every outlier appears once as a box marker and
  once as a point.
- **Ridge fill mapped to the row.** Eight colours for eight years is a
  legend for something the axis already says.

## Before you ship

`viz-review`, with these lines first: the binwidth or bandwidth is stated,
groups are sorted by median, the coloured words match the fills, the points
are jittered along the category axis only, and no smooth runs into
impossible values.

## Related skills

`viz-index` for the conventions, `viz-uncertainty` when the question is how
sure an estimate is rather than how spread the data are, `viz-amounts` when
one number per group is enough, `viz-compound` for one panel per group.
