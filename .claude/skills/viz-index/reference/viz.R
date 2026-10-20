# House chart helpers for ggplot2: theme, palette, fonts and number formats.
#
# Copy this file to R/viz.R in your project and source it from the setup chunk:
#
#   source("R/viz.R")
#   viz_use_fonts(dpi = 300)   # the dpi you will ggsave() at; 96 inside Quarto
#
# The conventions it encodes are the viz-index skill's: Inter, a horizontal
# grid, no ticks, a markdown title flush left so coloured words can replace a
# legend, and numbers written 1,000 / 25,000 / 5m / 1.2bn.
#
# Needs ggplot2, ggtext and scales; showtext and sysfonts for the font.

viz_colours <- c(
  single    = "midnightblue",  # the one series when there is only one
  highlight = "#D95F02",       # the one thing to look at (Dark2's orange)
  muted     = "grey80",        # everything that is not the point
  ink       = "#1A1A1A",       # title
  text      = "#4A4A4A",       # axis text and axis titles
  grey_text = "#6B6B6B",       # subtitle, caption
  grid      = "#E6E6E6",
  reference = "grey50"         # dashed reference lines
)

# Brewer Dark2, for two to six categories. Same values as
# RColorBrewer::brewer.pal(8, "Dark2"), spelled out so this file has no
# dependency on it. For a colour-vision-safe alternative use base R's
# palette.colors(palette = "Okabe-Ito").
viz_palette <- c("#1B9E77", "#D95F02", "#7570B3", "#E7298A",
                 "#66A61E", "#E6AB02", "#A6761D", "#666666")

# Set by viz_use_fonts(). Until then the theme uses the device default, because
# naming a font the machine does not have produces one "font family not found"
# warning per text grob.
.viz_fonts <- new.env(parent = emptyenv())
.viz_fonts$family <- ""

#' Register Inter with R's graphics devices.
#'
#' Inter is a Google font and is not installed on most machines, so R cannot
#' draw with it until showtext has fetched and registered it. Returns TRUE on
#' success; on failure (offline, packages missing) it leaves the theme on the
#' device default rather than emitting a warning for every label drawn.
#'
#' @param dpi Must equal the dpi you render at -- ggsave(dpi = 300) or the
#'   chunk's fig-dpi (Quarto's HTML default is 96) -- or showtext draws every
#'   piece of text at the wrong size, silently.
viz_use_fonts <- function(dpi = 96) {
  have <- requireNamespace("sysfonts", quietly = TRUE) &&
    requireNamespace("showtext", quietly = TRUE)
  if (!have) {
    return(invisible(FALSE))
  }

  ok <- tryCatch({
    if (!"Inter" %in% sysfonts::font_families()) {
      sysfonts::font_add_google("Inter", "Inter")
    }
    showtext::showtext_auto()
    showtext::showtext_opts(dpi = dpi)
    TRUE
  }, error = function(e) FALSE)

  if (ok) .viz_fonts$family <- "Inter"
  invisible(ok)
}

#' The font family currently registered, or "" for the device default.
#'
#' Use this in geom_text(family = viz_font()) instead of hardcoding "Inter",
#' so charts stay warning-free when viz_use_fonts() could not fetch the font.
viz_font <- function() .viz_fonts$family

#' The house ggplot2 theme.
#'
#' theme_minimal with the chart junk gone: no minor grid, no ticks, and a grid
#' in one direction only -- perpendicular to the variable of interest, which is
#' horizontal for most charts and vertical for horizontal bars. Title, subtitle
#' and caption are markdown, so viz_span() can colour words in them, and the
#' title sits flush with the panel's left edge. Axis titles stay: units go
#' there. No legend by default; with more than four colours add
#' theme(legend.position = "bottom").
#'
#' @param base_size 14 for a blog or report figure at 8 x 5 in, 20 for a slide.
#' @param grid "h" horizontal lines (the default), "v" vertical lines (for
#'   horizontal bars), "both" (scatterplots), "none".
theme_viz <- function(base_size = 14, grid = c("h", "v", "both", "none"),
                      base_family = NULL) {
  grid <- match.arg(grid)
  family <- base_family %||% .viz_fonts$family
  grid_line <- ggplot2::element_line(colour = viz_colours[["grid"]], linewidth = 0.4)

  ggplot2::theme_minimal(base_size = base_size, base_family = family) +
    ggplot2::theme(
      plot.title = ggtext::element_markdown(
        face = "bold", size = base_size * 1.15, colour = viz_colours[["ink"]],
        lineheight = 1.15, margin = ggplot2::margin(b = 6)
      ),
      plot.subtitle = ggtext::element_markdown(
        size = base_size * 0.9, colour = viz_colours[["grey_text"]],
        lineheight = 1.15, margin = ggplot2::margin(b = 10)
      ),
      plot.caption = ggtext::element_markdown(
        size = base_size * 0.65, colour = viz_colours[["grey_text"]], hjust = 0,
        margin = ggplot2::margin(t = 10)
      ),
      plot.title.position = "plot",
      plot.caption.position = "plot",
      plot.background = ggplot2::element_rect(fill = "white", colour = NA),
      legend.position = "none",
      panel.grid.minor = ggplot2::element_blank(),
      panel.grid.major.x = if (grid %in% c("v", "both")) grid_line else ggplot2::element_blank(),
      panel.grid.major.y = if (grid %in% c("h", "both")) grid_line else ggplot2::element_blank(),
      axis.ticks = ggplot2::element_blank(),
      axis.title = ggplot2::element_text(colour = viz_colours[["text"]], size = base_size * 0.85),
      axis.title.x = ggplot2::element_text(margin = ggplot2::margin(t = 8)),
      axis.title.y = ggplot2::element_text(margin = ggplot2::margin(r = 8)),
      axis.text = ggplot2::element_text(colour = viz_colours[["text"]], size = base_size * 0.8),
      strip.text = ggplot2::element_text(
        hjust = 0, face = "bold", size = base_size * 0.85, colour = viz_colours[["ink"]]
      )
    )
}

#' Wrap a label in a colour span, for use in ggtext titles and subtitles.
#'
#' Lets the title act as the legend, so the reader decodes the colour and
#' reads the point in one pass.
viz_span <- function(text, colour) {
  sprintf("<span style='color:%s;'>**%s**</span>", colour, text)
}

#' Axis and value labels for large numbers: 1,000  25,000  5m  1.2bn  3tn.
#'
#' Below a million, comma thousands and `accuracy` decimals; from a million,
#' one decimal and a lowercase m, bn or tn with a trailing .0 dropped. Negative
#' numbers keep their sign; NA stays NA. Pass it as `labels =` to a scale or
#' call it on a vector for geom_text().
#'
#' @param accuracy Rounding for values under a million: 1, 0.1, 0.01.
label_short <- function(accuracy = 1) {
  decimals <- max(0, -floor(log10(accuracy) + 1e-9))
  function(x) {
    a <- abs(x)
    small <- formatC(round(a / accuracy) * accuracy, format = "f",
                     digits = decimals, big.mark = ",")
    unit <- ifelse(a >= 1e12, 1e12, ifelse(a >= 1e9, 1e9, 1e6))
    suffix <- ifelse(a >= 1e12, "tn", ifelse(a >= 1e9, "bn", "m"))
    big <- paste0(sub("\\.0$", "", formatC(a / unit, format = "f", digits = 1)), suffix)
    out <- paste0(ifelse(x < 0, "-", ""), ifelse(a >= 1e6, big, small))
    out[is.na(x)] <- NA
    out
  }
}

#' Percent labels: 12%, or 12.5% with accuracy = 0.1.
#'
#' @param scale 100 when the data are proportions (0.12), 1 when they are
#'   already percentage points (12).
label_pct <- function(accuracy = 1, scale = 100) {
  scales::label_percent(accuracy = accuracy, scale = scale)
}

`%||%` <- function(a, b) if (is.null(a)) b else a
