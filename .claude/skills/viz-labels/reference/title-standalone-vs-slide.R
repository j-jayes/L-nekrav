# The same chart titled two ways. Standalone (a blog, a report, a PNG on its
# own): the title is the takeaway and the coloured words are the legend. On a
# slide the ### already carries the claim, so the chart title is a short noun
# phrase and the coloured words move to the subtitle. Writes two PNGs.
# requires: none
source(file.path(Sys.getenv("VIZ_HELPERS", "R"), "viz.R"))
out_dir <- Sys.getenv("VIZ_OUT_DIR", tempdir())
viz_use_fonts(dpi = 300)

library(ggplot2)
library(dplyr)

prices <- ggplot2::txhousing |>
  filter(city %in% c("Houston", "Dallas")) |>
  group_by(city, year) |>
  summarise(median = median(median, na.rm = TRUE), .groups = "drop")

palette <- c(Houston = viz_palette[1], Dallas = viz_palette[2])

# The gap the title talks about, computed.
gap <- prices |>
  filter(year == max(year)) |>
  summarise(gap = median[city == "Dallas"] - median[city == "Houston"]) |>
  pull(gap)

# One plot function; only the words and the sizes differ between the two.
chart <- function(title, subtitle, base_size) {
  ggplot(prices, aes(year, median, colour = city)) +
    geom_line(linewidth = 1.2) +
    scale_colour_manual(values = palette) +
    scale_x_continuous(breaks = seq(2000, 2015, 5)) +
    scale_y_continuous(labels = label_short()) +
    labs(title = title, subtitle = subtitle, x = NULL, y = "Median price (USD)",
         caption = "Source: ggplot2::txhousing (Texas A&M Real Estate Center)") +
    theme_viz(base_size = base_size)
}

# Standalone: a claim, with the two series named in colour inside it.
standalone <- chart(
  title = paste(viz_span("Dallas", palette[["Dallas"]]), "homes now cost",
                label_short()(gap), "more than", viz_span("Houston", palette[["Houston"]]), "homes"),
  subtitle = "Median sale price by year, 2000 to 2015",
  base_size = 14
)
path <- file.path(out_dir, "title-standalone.png")
ggsave(path, standalone, width = 8, height = 5, dpi = 300, bg = "white")
message("wrote ", path)

# Slide: the ### above the chart would read "Dallas homes now cost 25,000
# more than Houston homes"; the chart itself only says what it shows.
slide <- chart(
  title = "Median sale price",
  subtitle = paste(viz_span("Dallas", palette[["Dallas"]]), "and",
                   viz_span("Houston", palette[["Houston"]])),
  base_size = 20
)
path <- file.path(out_dir, "title-slide.png")
ggsave(path, slide, width = 12, height = 3.7, dpi = 300, bg = "white")
message("wrote ", path)
