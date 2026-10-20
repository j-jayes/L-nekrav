# Annotation on a line chart: a dashed reference line for a date, a dashed
# grey line for the long-run average, a label with a white backing so the
# line does not strike through it, and an arrow to the point being named.
# requires: none
source(file.path(Sys.getenv("VIZ_HELPERS", "R"), "viz.R"))
out_dir <- Sys.getenv("VIZ_OUT_DIR", tempdir())
viz_use_fonts(dpi = 300)

library(ggplot2)
library(dplyr)

jobless <- ggplot2::economics |>
  mutate(unemploy = unemploy * 1000)   # the source is in thousands

peak <- jobless |> slice_max(unemploy, n = 1)
average <- mean(jobless$unemploy)
crisis <- as.Date("2008-09-15")

p <- ggplot(jobless, aes(date, unemploy)) +
  # Reference lines first, so the data draws over them.
  geom_hline(yintercept = average, linetype = "dashed", colour = viz_colours[["reference"]]) +
  geom_vline(xintercept = crisis, linetype = "dashed", colour = viz_colours[["reference"]]) +
  geom_line(colour = viz_colours[["single"]], linewidth = 1) +
  # A label, not text: the white fill hides the line behind it. linewidth = 0
  # removes the border (label.size is deprecated in ggplot2 4.0).
  annotate("label", x = crisis, y = 4e6, label = "Lehman Brothers fails",
           hjust = 1.05, family = viz_font(), size = 10 / .pt,
           colour = viz_colours[["text"]], fill = "white", linewidth = 0,
           label.padding = unit(0.25, "lines")) +
  annotate("label", x = as.Date("1968-01-01"), y = average, vjust = -0.3, hjust = 0,
           label = paste("1967-2015 average", label_short(accuracy = 0.1)(average)),
           family = viz_font(), size = 10 / .pt, colour = viz_colours[["grey_text"]],
           fill = "white", linewidth = 0, label.padding = unit(0.15, "lines")) +
  # An arrow from a comment to the point it is about.
  annotate("curve", x = as.Date("2001-06-01"), y = peak$unemploy,
           xend = peak$date - 120, yend = peak$unemploy, curvature = 0.25,
           colour = viz_colours[["text"]], linewidth = 0.4,
           arrow = arrow(length = unit(0.18, "cm"), type = "closed")) +
  annotate("text", x = as.Date("2000-12-01"), y = peak$unemploy, hjust = 1,
           label = paste0(format(peak$date, "%B %Y"), "\n", label_short(accuracy = 0.1)(peak$unemploy), " out of work"),
           family = viz_font(), size = 10 / .pt, colour = viz_colours[["text"]], lineheight = 1) +
  scale_x_date(date_breaks = "10 years", date_labels = "%Y") +
  scale_y_continuous(labels = label_short(), limits = c(0, NA),
                     expand = expansion(mult = c(0, 0.05))) +
  labs(
    title = paste0("US unemployment peaked at ", label_short(accuracy = 0.1)(peak$unemploy),
                   " a year after the crash"),
    subtitle = "Unemployed persons, monthly",
    x = NULL, y = "Unemployed persons",
    caption = "Source: ggplot2::economics (US FRED)"
  ) +
  theme_viz()

path <- file.path(out_dir, "annotate-reference-lines.png")
ggsave(path, p, width = 8, height = 5, dpi = 300, bg = "white")
message("wrote ", path)
