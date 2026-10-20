# Histogram at three binwidths, side by side. A histogram has one parameter
# and it decides what you see: too fine is noise, too coarse hides the shape.
# Always draw several before choosing one.
# requires: none
source(file.path(Sys.getenv("VIZ_HELPERS", "R"), "viz.R"))
out_dir <- Sys.getenv("VIZ_OUT_DIR", tempdir())
viz_use_fonts(dpi = 300)

library(ggplot2)
library(dplyr)

# geom_histogram() takes one binwidth per plot, so to compare three the bins
# are counted here and drawn as rectangles, one panel per binwidth.
widths <- c(0.01, 0.1, 0.5)
bins <- bind_rows(lapply(widths, function(w) {
  ggplot2::diamonds |>
    filter(carat < 2.5) |>
    mutate(left = floor(carat / w) * w) |>
    count(left, name = "n") |>
    mutate(width = w, panel = paste("Binwidth", w, "carat"))
}))

p <- ggplot(bins) +
  geom_rect(aes(xmin = left, xmax = left + width, ymin = 0, ymax = n),
            fill = viz_colours[["single"]]) +
  facet_wrap(vars(panel), ncol = 1, scales = "free_y") +
  scale_x_continuous(breaks = seq(0, 2.5, 0.5)) +
  scale_y_continuous(labels = label_short(), expand = expansion(mult = c(0, 0.05))) +
  labs(
    title = "Diamonds cluster just above 1, 1.5 and 2 carats,<br>but only a fine binwidth shows it",
    subtitle = "Weight of 53,000 diamonds, same data at three binwidths",
    x = "Weight (carats)", y = "Diamonds",
    caption = "Source: ggplot2::diamonds"
  ) +
  theme_viz() +
  theme(panel.spacing.y = unit(1, "lines"))

path <- file.path(out_dir, "histogram-binwidth.png")
ggsave(path, p, width = 8, height = 7, dpi = 300, bg = "white")
message("wrote ", path)
