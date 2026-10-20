# Overlapping densities for two to four groups: filled, semi-transparent, and
# named in the title so no legend is needed. Wilke: densities overlap better
# than histograms, because the continuous outline keeps each group separate.
# requires: none
source(file.path(Sys.getenv("VIZ_HELPERS", "R"), "viz.R"))
out_dir <- Sys.getenv("VIZ_OUT_DIR", tempdir())
viz_use_fonts(dpi = 300)

library(ggplot2)
library(dplyr)
library(forcats)

cars <- ggplot2::mpg |>
  mutate(drive = recode(drv, f = "Front-wheel", `4` = "Four-wheel", r = "Rear-wheel"),
         drive = fct_reorder(drive, hwy, .fun = median, .desc = TRUE))

# Three groups, three colours, keyed to the group names.
palette <- setNames(viz_palette[1:3], levels(cars$drive))

# The group with the highest median is named in the title from the data.
best <- levels(cars$drive)[1]

p <- ggplot(cars, aes(hwy, fill = drive)) +
  geom_density(alpha = 0.55, colour = NA, bw = 1.5) +
  scale_fill_manual(values = palette) +
  scale_x_continuous(breaks = seq(10, 45, 5)) +
  scale_y_continuous(expand = expansion(mult = c(0, 0.05))) +
  labs(
    title = paste(viz_span(best, palette[[best]]), "drive gets the best highway mileage"),
    subtitle = paste(
      "Highway fuel economy of 234 models,",
      viz_span("front-wheel", palette[["Front-wheel"]]), "vs",
      viz_span("four-wheel", palette[["Four-wheel"]]), "vs",
      viz_span("rear-wheel", palette[["Rear-wheel"]]), "drive"
    ),
    x = "Highway fuel economy (miles per gallon)", y = "Density",
    caption = "Note: kernel density, bandwidth 1.5 mpg. Source: ggplot2::mpg (US EPA)"
  ) +
  theme_viz() +
  theme(axis.text.y = element_blank())

path <- file.path(out_dir, "densities-overlapping.png")
ggsave(path, p, width = 8, height = 5, dpi = 300, bg = "white")
message("wrote ", path)
