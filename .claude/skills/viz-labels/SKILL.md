---
name: viz-labels
description: >-
  Title, annotate and label a ggplot2 chart — the takeaway title with coloured
  words for a standalone chart against the short title on a slide, axis
  titles with units, white-backed annotations, dashed reference lines,
  arrows to a point, and ggrepel for point labels. Use when asked "what
  should the title say", "label the points", "add an annotation", "add a
  reference line", "mark the peak", or when a chart is drawn but not yet
  explained.
---

# Labels: the words on the chart

Wilke's rule for a title is that it should assert something, and his rule
for everything else is that the chart should need no legend. The words on a
chart therefore do two jobs: the title makes the claim, and the labels put
the names where the eye already is.

Setup as in `viz-index`. Two templates need nothing extra; the third needs
ggrepel (`install.packages("ggrepel")`) and says so if it is missing.

## Which template

| Situation | Template |
|---|---|
| Deciding what the title says, and how it changes on a slide | [title-standalone-vs-slide.R](reference/title-standalone-vs-slide.R) (writes two PNGs) |
| Marking a date, an average, or a peak on a line chart | [annotate-reference-lines.R](reference/annotate-reference-lines.R) |
| Naming every point on a scatter without overlaps | [point-labels-ggrepel.R](reference/point-labels-ggrepel.R) |

## The template

The two title modes, from `title-standalone-vs-slide.R`. Same plot
function, different words and sizes:

```r
# Standalone: the claim, with the series named in colour inside it.
chart(
  title = paste(viz_span("Dallas", palette[["Dallas"]]), "homes now cost",
                label_short()(gap), "more than", viz_span("Houston", palette[["Houston"]]), "homes"),
  subtitle = "Median sale price by year, 2000 to 2015",
  base_size = 14
)                                             # ggsave(width = 8, height = 5)

# Slide: the ### above the chart carries the claim; the chart says what it shows.
chart(
  title = "Median sale price",
  subtitle = paste(viz_span("Dallas", palette[["Dallas"]]), "and",
                   viz_span("Houston", palette[["Houston"]])),
  base_size = 20
)                                             # fig-width: 12, fig-height: 3.7
```

## Rules that matter

**The standalone title is a sentence someone could disagree with.** "Median
sale price" is a label; "Dallas homes now cost 24,800 more than Houston
homes" is a claim. The subtitle then says what is measured, over what, for
whom. Cover the chart and read the title: if it still tells you something,
it is doing its job.

**On a slide the claim is the `###`, not the chart title.** Repeating it in
the figure makes the slide say it twice in two fonts. Keep a short noun
phrase or no title, and move the coloured words to the subtitle so the
series are still named. `base_size = 20` so the text survives the scale to
1600 × 900.

**Coloured words are the legend, up to four colours.** `viz_span(text,
colour)` wraps a word in a markdown span; `theme_viz()` renders the title,
subtitle and caption as markdown. Every coloured word must match a colour
drawn, and every colour drawn must be named.

**Compute the number in the title.** `gap`, `peak`, the ratio between two
cars: derive it from the data and `paste()` it in. The templates do this
without exception, and the first drafts of three of them had claims that
did not survive the check. Format with `label_short()` and `label_pct()`,
never `round()` alone.

**Break a long title with `<br>`.** The markdown title does not wrap; past
the figure's right edge it is clipped, silently. Two lines at full size
beat one line at a smaller size.

**Units in the axis title.** `Unemployed persons`, `Median price (USD)`,
`Highway fuel economy (miles per gallon)`. `labs(x = NULL)` only when the
tick labels are self-evident — years, category names.

**An annotation crossing a line gets a white backing.** `annotate("label",
fill = "white", linewidth = 0, label.padding = unit(0.25, "lines"))` draws
the text on a plate the line passes behind. `annotate("text")` in the same
place is struck through. `linewidth`, not `label.size`: the old argument is
deprecated in ggplot2 4.0 and warns.

**Reference lines are dashed, grey, and drawn first.** `geom_hline()` and
`geom_vline()` with `linetype = "dashed"` and `viz_colours[["reference"]]`,
before the data layer, so the data draws over them. Label what the line is:
`1967–2015 average 7.8m`, `Lehman Brothers fails`.

**An arrow from a comment to its point.** `annotate("curve", ..., curvature
= 0.25, arrow = arrow(length = unit(0.18, "cm"), type = "closed"))`, with
the text at the tail end and the head stopping just short of the point.

**Point labels: ggrepel, and rank them.** `geom_text_repel(max.overlaps =
Inf, box.padding = 0.35, seed = 1)` labels every point and pushes the
labels apart; the seed makes the layout reproducible. Colour the two or
three labels the title is about with `viz_colours[["highlight"]]` and the
rest `grey_text`, so the reader finds the ones that matter first. With more
than about forty points, label a subset.

**Text sizes are in millimetres and are not inherited from the theme.**
`size = 10 / .pt` for 10 pt. Match `family = viz_font()` or the label draws
in the device font.

## On a Nexer slide

`theme_nexer()`, `nexer_span()`. No chart title; subtitle with the coloured
words in `nexer_colours[["purple"]]` and `grey`. Annotations in
`nexer_font_body()`. The kit's `mckinsey-slides` skill has the grammar for
the `###` itself — 14–20 words, a number where possible, tense keyed to the
section.

## What does not work

- **A title that describes.** "Unemployment over time" tells the reader to
  work it out themselves, and they will work out something else.
- **A legend for a chart with three colours.** The words can carry it.
- **`geom_text()` for point labels** without `check_overlap = TRUE` or
  ggrepel: labels pile on each other.
- **`annotate("text")` across a line.** Struck through.
- **A title claim typed from memory.** It drifts the first time the data
  changes.
- **`str_wrap()` on a markdown title.** It inserts `\n`, which ggtext
  ignores; use `<br>`.

## Before you ship

`viz-review`, with these lines first: the title is a claim (standalone) or
short (slide); every coloured word matches a drawn colour; units are in the
axis titles; annotations are backed and reference lines labelled; nothing
is clipped at the right edge.

## Related skills

`viz-index` for the conventions, `viz-colour` for which colour the words
take, `viz-trends` for labels at line ends, `jonathan-slides` and
`mckinsey-slides` for the `###` the chart sits under.
