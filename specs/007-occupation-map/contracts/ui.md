# UI contract: Occupation map

## `OccupationMap` component

- **Points**:
  - 429 circles of radius 2.5 in `--color-axis` grey.
  - No colour by major group, and no group labels on the map (see `references/occupation-map.md`,
    "Design changes made while building"). A code's group is shown in the readout and the table.
- **Focus set**: the search hits (outlined) and the selected codes (filled, radius 6). Each
  selected code has lines to its 5 nearest neighbours, in `--color-muted`.
- **Tooltip**:
  - code, English and Swedish titles, "Median {m} SEK (SCB {year})" or "SCB publishes no median";
  - the legal flags;
  - with a selected code, "Closer to {sel} than {p} % of pairs", or "Same official description as
    {sel}".
  - Stacked points list every code at that spot.
- **Controls**: + / − / Selected (zoom to the selected codes and their neighbours) / Reset buttons, wheel zoom, and drag to pan. Tab moves through the
  focus set; Enter selects (adds to the selection, at most 4, as today).
- **Table view**: `<details>` "Show as a table": Code | Title | Group | Nearest five.
- **Caption**: "Each point is an occupation, placed by how similar its official description is
  (multilingual model, UMAP). Distances on the map are approximate; the closeness figures are
  exact. Similar descriptions never decide which code fits: the duties do."

## Placement

- **Step 1**: on screens ≥ 1024 px, a two-column grid (results | map, the map sticky). On
  narrower screens, `<details>` "Map of similar occupations" under the results.
- **Step 2**: each card gets `<details>` "Similar work", which lists the 5 neighbours with their
  closeness sentences. When exactly two codes are selected, the closeness sentence for the pair
  appears above the cards.

It must fit 390 px with no sideways scroll, and axe must report no serious or critical violations.
