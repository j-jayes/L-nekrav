# Boxplots with the raw points beside them, one row per group, sorted by
# median. The box summarises; the points show how many observations stand
# behind each box, which a box alone hides.
# requires: none
source(file.path(Sys.getenv("VIZ_HELPERS", "R"), "viz.R"))
out_dir <- Sys.getenv("VIZ_OUT_DIR", tempdir())
viz_use_fonts(dpi = 300)

library(ggplot2)
library(dplyr)
library(forcats)

# The group size goes into the axis label, where it cannot collide with the
# points. Sort by median so the rows read as a ranking.
cars <- ggplot2::mpg |>
  add_count(class) |>
  mutate(label = paste0(class, "  (n = ", n, ")"),
         label = fct_reorder(label, hwy, .fun = median))

# The title names the widest and narrowest middle half, from the data.
spread <- cars |>
  group_by(class) |>
  summarise(iqr = IQR(hwy), .groups = "drop")
widest <- spread$class[which.max(spread$iqr)]
narrowest <- spread$class[which.min(spread$iqr)]

p <- ggplot(cars, aes(hwy, label)) +
  geom_boxplot(fill = viz_colours[["muted"]], colour = viz_colours[["text"]],
               outlier.shape = NA, width = 0.55, linewidth = 0.4) +
  # Jitter along the category axis only (height, since the category is on y)
  # and never along the value axis, or the points would misreport the data.
  geom_point(position = position_jitter(width = 0, height = 0.18, seed = 1),
             colour = viz_colours[["single"]], alpha = 0.6, size = 1.6) +
  scale_x_continuous(breaks = seq(10, 45, 5)) +
  labs(
    title = paste0("Highway mileage varies most within the ", widest,
                   " class<br>and least within the ", narrowest, " class"),
    subtitle = "Highway fuel economy by vehicle class; box is the middle half, line the median",
    x = "Highway fuel economy (miles per gallon)", y = NULL,
    caption = "Source: ggplot2::mpg (US EPA)"
  ) +
  theme_viz(grid = "v")

path <- file.path(out_dir, "boxplot-strip.png")
ggsave(path, p, width = 8, height = 5, dpi = 300, bg = "white")
message("wrote ", path)
