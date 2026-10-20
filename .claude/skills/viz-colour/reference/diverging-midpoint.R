# A diverging scale around a midpoint that means something: here each
# market's monthly sales against its own average, so the colour says "above
# or below normal" and the midpoint is zero by construction.
# requires: none
source(file.path(Sys.getenv("VIZ_HELPERS", "R"), "viz.R"))
out_dir <- Sys.getenv("VIZ_OUT_DIR", tempdir())
viz_use_fonts(dpi = 300)

library(ggplot2)
library(dplyr)
library(forcats)

seasonal <- ggplot2::txhousing |>
  filter(year %in% 2010:2015, !is.na(sales)) |>
  group_by(city) |>
  filter(sum(sales) > 20000) |>            # the twelve or so largest markets
  mutate(dev = sales / mean(sales) - 1) |> # deviation from the market's own mean
  group_by(city, month) |>
  summarise(dev = mean(dev), .groups = "drop") |>
  mutate(city = fct_reorder(city, dev, .fun = max),
         month = factor(month.abb[month], levels = month.abb))

# Symmetric limits, so the same colour depth means the same size of deviation
# in both directions.
lim <- max(abs(seasonal$dev))

# The title's figure is the average June deviation, computed.
june <- label_pct()(mean(seasonal$dev[seasonal$month == "Jun"]))

p <- ggplot(seasonal, aes(month, city, fill = dev)) +
  geom_tile(width = 0.95, height = 0.95) +
  scale_fill_distiller(palette = "RdBu", direction = 1, limits = c(-lim, lim),
                       labels = label_pct(), breaks = c(-0.4, -0.2, 0, 0.2, 0.4)) +
  scale_x_discrete(expand = c(0, 0)) +
  labs(
    title = paste("Texas markets sell about", june, "more homes in June<br>than in an average month"),
    subtitle = "Monthly home sales against each market's own 2010–2015 average",
    x = NULL, y = NULL, fill = "Sales vs market average",
    caption = "Source: ggplot2::txhousing (Texas A&M Real Estate Center)"
  ) +
  theme_viz(grid = "none") +
  theme(
    legend.position = "bottom",
    legend.title.position = "top",
    legend.key.width = unit(2.4, "cm"),
    legend.key.height = unit(0.35, "cm")
  )

path <- file.path(out_dir, "diverging-midpoint.png")
ggsave(path, p, width = 8, height = 6, dpi = 300, bg = "white")
message("wrote ", path)
