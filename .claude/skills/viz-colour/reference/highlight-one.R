# Highlight one series: everything grey, the one thing in colour, named in
# the title. Wilke: for maximum effect, remove colour from everything except
# what you want looked at.
# requires: none
source(file.path(Sys.getenv("VIZ_HELPERS", "R"), "viz.R"))
out_dir <- Sys.getenv("VIZ_OUT_DIR", tempdir())
viz_use_fonts(dpi = 300)

library(ggplot2)
library(dplyr)

focus <- "Austin"

prices <- ggplot2::txhousing |>
  group_by(city, year) |>
  summarise(median = median(median, na.rm = TRUE), .groups = "drop") |>
  filter(!is.na(median)) |>
  mutate(colour = if_else(city == focus, viz_colours[["highlight"]], viz_colours[["muted"]]))

# Draw the grey lines first and the highlighted one last, so it sits on top.
context <- filter(prices, city != focus)
star <- filter(prices, city == focus)
rank_2015 <- prices |>
  filter(year == 2015) |>
  mutate(rank = rank(-median)) |>
  filter(city == focus) |>
  pull(rank)

p <- ggplot(mapping = aes(year, median, group = city)) +
  geom_line(data = context, colour = viz_colours[["muted"]], linewidth = 0.5) +
  geom_line(data = star, colour = viz_colours[["highlight"]], linewidth = 1.4) +
  geom_text(data = filter(star, year == max(year)), aes(label = city),
            hjust = 0, nudge_x = 0.3, family = viz_font(), size = 11 / .pt,
            fontface = "bold", colour = viz_colours[["highlight"]]) +
  scale_x_continuous(breaks = seq(2000, 2015, 5)) +
  scale_y_continuous(labels = label_short()) +
  coord_cartesian(clip = "off") +
  labs(
    title = paste0(viz_span(focus, viz_colours[["highlight"]]), " is the ",
                   scales::ordinal(rank_2015), " dearest of 46 Texas markets"),
    subtitle = "Median sale price by year, every market in the data",
    x = NULL, y = "Median price (USD)",
    caption = "Source: ggplot2::txhousing (Texas A&M Real Estate Center)"
  ) +
  theme_viz() +
  theme(plot.margin = margin(5.5, 50, 5.5, 5.5))

path <- file.path(out_dir, "highlight-one.png")
ggsave(path, p, width = 8, height = 5, dpi = 300, bg = "white")
message("wrote ", path)
