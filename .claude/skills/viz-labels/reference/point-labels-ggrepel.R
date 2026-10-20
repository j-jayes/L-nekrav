# Labelled points with ggrepel: every point named, labels pushed off each
# other and off the points. The one template in this family that needs an
# extra package.
# requires: ggrepel
source(file.path(Sys.getenv("VIZ_HELPERS", "R"), "viz.R"))
out_dir <- Sys.getenv("VIZ_OUT_DIR", tempdir())
viz_use_fonts(dpi = 300)

if (!requireNamespace("ggrepel", quietly = TRUE)) {
  stop("This template needs ggrepel: install.packages('ggrepel')")
}

library(ggplot2)
library(dplyr)

cars <- datasets::mtcars |>
  tibble::rownames_to_column("car") |>
  mutate(weight = wt * 1000)   # thousands of pounds -> pounds

# Name the outliers in colour and the rest in grey, so the labels rank
# themselves: the eye reads the coloured ones first.
lightest <- cars |> slice_min(weight, n = 1)
heaviest <- cars |> slice_max(weight, n = 1)
cars <- cars |>
  mutate(colour = if_else(car %in% c(lightest$car, heaviest$car),
                          viz_colours[["highlight"]], viz_colours[["grey_text"]]))

p <- ggplot(cars, aes(weight, mpg)) +
  geom_point(colour = viz_colours[["single"]], size = 2.4, alpha = 0.8) +
  ggrepel::geom_text_repel(
    aes(label = car, colour = colour),
    family = viz_font(), size = 9 / .pt,
    max.overlaps = Inf, box.padding = 0.35, point.padding = 0.3,
    segment.colour = viz_colours[["muted"]], seed = 1
  ) +
  scale_colour_identity() +
  scale_x_continuous(labels = label_short()) +
  labs(
    title = paste0("The ", lightest$car, " goes ",
                   round(lightest$mpg / heaviest$mpg, 1),
                   " times as far per gallon<br>as the ", heaviest$car),
    subtitle = "Fuel economy against weight, 32 cars from the 1974 Motor Trend test",
    x = "Weight (pounds)", y = "Fuel economy (miles per gallon)",
    caption = "Source: datasets::mtcars (Motor Trend, 1974)"
  ) +
  theme_viz(grid = "both")

path <- file.path(out_dir, "point-labels-ggrepel.png")
ggsave(path, p, width = 8, height = 6, dpi = 300, bg = "white")
message("wrote ", path)
