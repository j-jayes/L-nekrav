---
name: viz-colour
description: >-
  Pick colour for the job it is doing in a ggplot2 chart — distinguish groups
  (Brewer Dark2 or Okabe-Ito), represent values (Blues, viridis, a balanced
  diverging scale around a real midpoint), or highlight one thing against
  grey. Use when asked to "colour by", "choose a palette", "highlight one
  series", "make it colour-blind safe", "what colour should this be", or when
  a chart has more than one colour.
---

# Colour: three jobs, three kinds of scale

Wilke: colour does one of three things. It **distinguishes** groups that
have no order, it **represents** values that do, or it **highlights** the
one thing to look at. Each job has its own kind of scale, and using the
wrong kind — a rainbow for values, a full palette when one thing matters —
is the most common way a good chart goes bad.

Setup as in `viz-index`. Both templates render with the installed packages.

## Which scale

| Job | Scale | Default | Template |
|---|---|---|---|
| Distinguish 2–6 groups | Qualitative | `viz_palette` (Brewer Dark2), keyed to the group names | see `viz-trends` |
| Distinguish up to 8, colour-blind safe for certain | Qualitative | `palette.colors(palette = "Okabe-Ito")`, base R | — |
| Represent a magnitude | Sequential | `scale_fill_viridis_c()` or `scale_fill_distiller(palette = "Blues", direction = 1)` | see `viz-amounts` heatmap |
| Represent deviation from a meaningful midpoint | Diverging | `scale_fill_distiller(palette = "RdBu", direction = 1)` with symmetric limits | [diverging-midpoint.R](reference/diverging-midpoint.R) |
| Highlight one series among many | Accent | `viz_colours[["muted"]]` for everything, `viz_colours[["highlight"]]` for the one | [highlight-one.R](reference/highlight-one.R) |
| One series only | — | `viz_colours[["single"]]` | everywhere |

## The template

The highlight idiom from `highlight-one.R`. Grey lines first, the coloured
one last so it draws on top, and its name at its end in the same colour:

```r
context <- filter(prices, city != focus)
star <- filter(prices, city == focus)

ggplot(mapping = aes(year, median, group = city)) +
  geom_line(data = context, colour = viz_colours[["muted"]], linewidth = 0.5) +
  geom_line(data = star, colour = viz_colours[["highlight"]], linewidth = 1.4) +
  geom_text(data = filter(star, year == max(year)), aes(label = city),
            hjust = 0, nudge_x = 0.3, family = viz_font(), size = 11 / .pt,
            fontface = "bold", colour = viz_colours[["highlight"]]) +
  coord_cartesian(clip = "off") +
  labs(title = paste0(viz_span(focus, viz_colours[["highlight"]]), " is the 3rd dearest of 46 markets")) +
  theme_viz()
```

## Rules that matter

**Three to five colours is the working range; eight is the ceiling.** Past
that, matching colour to category is work the reader will not do. Use direct
labels instead, and let colour carry something coarser.

**Four or fewer: the words are the legend.** `viz_span()` colours the group
names in the title or subtitle, in the palette's colours. More than four:
`theme(legend.position = "bottom")`, and the legend order must match the
visual order — top line first.

**Key the palette to names.** `setNames(viz_palette[1:4], cities)`. A
palette applied by factor position changes a group's colour when the sort
changes, and breaks the rule that the same thing has the same colour in
every chart of a set.

**Highlight means grey everything else.** One saturated colour among five
others is not a highlight. `muted` for all, `highlight` for one, and the
one drawn last. Wilke's stronger version: remove all colour except from the
highlighted element.

**A sequential scale for magnitudes, light to dark.** viridis and Brewer
Blues vary evenly in lightness, so "darker" always means "more" and the
scale survives greyscale and colour-vision deficiency. Never rainbow: its
lightness goes up and down, so it invents features.

**A diverging scale only around a midpoint that means something.** Zero
change, the average, a target. Set the limits symmetric — `limits =
c(-lim, lim)` with `lim <- max(abs(x))` — so the same depth of colour means
the same size of deviation on both sides. Without that, the side with the
larger extreme looks stronger everywhere. `diverging-midpoint.R` uses
`RdBu`; `PiYG` and `PuOr` are the other two that stay readable under
red-green colour blindness, because neither side is a pure red or green.

**A continuous scale gets a colourbar.** It is the one legend that cannot be
replaced by words. Wide, flat, at the bottom, title on top:

```r
theme(legend.position = "bottom", legend.title.position = "top",
      legend.key.width = unit(2.4, "cm"), legend.key.height = unit(0.35, "cm"))
```

**Colour needs area.** Thin lines and small points in five colours are
hard to tell apart, and harder still for the 8% of men with a colour-vision
deficiency. Thicker lines, bigger points, or fewer colours.

**Encode redundantly when it matters.** If the reader must tell groups
apart, add shape or line type to colour. Then a greyscale print still
works.

**Avoid saturated fills on large areas.** A whole panel of `#FF0000` tires
the eye; Dark2 and the muted greys are chosen to sit quietly.

## On a Nexer slide

The Nexer rule is the highlight rule made corporate: one series in
`nexer_colours[["purple"]]`, everything else `grey`, `orange` reserved for
the single fact the slide delivers. Never a second theme colour. For a
sequential fill, `scale_fill_gradient(low = nexer_colours[["grey_pale"]],
high = nexer_colours[["purple"]])`. A diverging fill on a slide is rare;
`orange` against `purple` around `grey_pale` works and stays on brand.

## What does not work

- **The ggplot2 default hue palette** for anything that leaves your screen.
  It is neither colour-blind safe nor quiet.
- **Rainbow, jet, and `terrain.colors()`** for values.
- **Red against green** to mean good against bad. Blue against orange, or
  Dark2's teal against its orange, reads for everyone.
- **A diverging scale with the midpoint at the data's mean** when the
  reader will assume zero. Say what the midpoint is in the legend title.
- **Colouring a bar chart by category** when the category is already on the
  axis. One colour, or a highlight.
- **Testing colour-blind safety by eye.** Okabe-Ito and viridis are safe by
  construction; for anything else, keep the lightness varying and add a
  second encoding.

## Before you ship

`viz-review`, with these lines first: the colour is doing one of the three
jobs and the scale matches it; four or fewer colours have no legend;
highlight means grey plus one; the diverging midpoint means something and
the limits are symmetric; the same thing has the same colour across the set.

## Related skills

`viz-index` for the palette values, `viz-trends` for named lines,
`viz-amounts` for the sequential heatmap, `viz-labels` for the coloured
words in a title, `nexer-slides` for the brand rule.
