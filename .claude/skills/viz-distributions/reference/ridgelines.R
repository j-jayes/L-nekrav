# Ridgelines: many distributions stacked, one per row, for a change in shape
# over time. Single fill, white outline; colour would only distract.
# requires: none
source(file.path(Sys.getenv("VIZ_HELPERS", "R"), "viz.R"))
out_dir <- Sys.getenv("VIZ_OUT_DIR", tempdir())
viz_use_fonts(dpi = 300)

library(ggplot2)
library(dplyr)
library(forcats)
library(ggridges)

# One observation per city and month; one ridge per year. Time reads top to
# bottom, so the earliest year goes on the top row.
prices <- ggplot2::txhousing |>
  filter(!is.na(median), year %in% seq(2000, 2015, 3)) |>
  mutate(year = fct_rev(factor(year)))

p <- ggplot(prices, aes(median, year)) +
  geom_density_ridges(
    scale = 3, rel_min_height = 0.01, bandwidth = 8000,
    fill = viz_colours[["single"]], colour = "white", alpha = 0.9
  ) +
  scale_x_continuous(labels = label_short(), breaks = seq(0, 3e5, 1e5),
                     limits = c(0, 3.5e5)) +
  # Room above the top ridge, none below the bottom one.
  scale_y_discrete(expand = expansion(add = c(0.2, 2.2))) +
  labs(
    title = "Texas home prices rose and spread out across markets",
    subtitle = "Distribution of monthly median sale price across 46 markets, every third year",
    x = "Median sale price (USD)", y = NULL,
    caption = "Note: kernel density, bandwidth 8,000 USD. Source: ggplot2::txhousing"
  ) +
  theme_viz(grid = "v")

path <- file.path(out_dir, "ridgelines.png")
ggsave(path, p, width = 8, height = 6, dpi = 300, bg = "white")
message("wrote ", path)
