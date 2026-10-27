# Feature Specification: Occupation map

**Feature Branch**: `007-occupation-map`

**Created**: 2026-10-27

**Status**: Draft

**Input**: User description: "Project the descriptions and titles of the occupations into the
vector space, use UMAP to reduce the dimensions, and plot the occupations in a nice interactive
chart, so a user can see how close two specific occupations are. Use this concept in the
occupation search part of the UI too." Decisions from the review on 2026-10-27:
- Build each occupation from the multilingual model's vectors for its title and description
  chunks. Leave out the synonym lists and every chunk that contains ILO text.
- Measure "how close" in the full embedding space; the 2-D map is only a picture.
- Colour points by SSYK major group, and show pay only in tooltips and neighbour lists.
- In search, highlight the hits and selected codes, with lines to each selected code's five
  nearest neighbours. Do not project the query itself.

## User Scenarios & Testing *(mandatory)*

Lönekrav's search ranks codes for a text, and Feature 006 shows what each selected code pays. What
neither shows is the *shape* of the classification. A candidate who finds 2511 System analysts
does not see that 2512 Software developers and 2519 Other ICT specialists describe almost the same
work, while a code from another major group that ranked fourth sits far away. The map makes that
visible.

The users are the same as in 006. The map helps them check that the codes they are considering
really are the plausible ones for their duties, and see which other codes describe similar work.
It never suggests a code for its pay: points are coloured by kind of work, pay appears only when
the user points at a code, and neighbours are listed by similarity.

Facts checked on 2026-10-27, which this spec relies on:
- The cached vectors of the multilingual model cover every title and description chunk (0
  missing). After leaving out the synonym and ILO chunks, each of the 429 codes keeps between 2
  and 177 chunks (median 10).
- Averaging those vectors per code gives sensible neighbours:
  - 2511 → 2512 (0.939), 2519 (0.935), 1312, 1311, 2514;
  - 2221 Professional nurses → 2239, 5323, 5330, 2224;
  - 5120 Cooks → 3452, 9412, 3451.
- The similarity between codes is compressed: across all pairs, the 5th, 50th and 95th
  percentiles are 0.645, 0.736 and 0.843. A raw similarity of 0.85 therefore already means "closer
  than about 95 % of pairs", and the page must explain closeness in those terms.
- 22 pairs of codes are near-identical (similarity above 0.99), almost all manager codes split
  only by level, for example 1311/1312 "ICT service managers, level 1/level 2". They share their
  descriptions, so their points coincide.

### User Story 1 - How close are two occupations? (Priority: P1)

A candidate picks two codes (for example the two plausible codes from their search) and sees how
similar their official descriptions are: a plain sentence ("2511 and 2512 are closer than 99 % of
pairs of occupations") and the similarity value. Each selected code lists its most similar
occupations, nearest first.

**Why this priority**: this is the question the user asked, and it can be answered exactly from
the full-dimension vectors, without the map picture.

**Independent Test**: request the neighbours of 2511 and the closeness of 2511 and 2512; check
both against similarities recomputed from the cached vectors, and the percentile against the
distribution of all pairs.

**Acceptance Scenarios**:

1. **Given** codes 2511 and 2512, **When** their closeness is shown, **Then** it gives the
   similarity and the share of all code pairs that are less similar, rounded to a whole per cent.
2. **Given** code 2511, **When** its neighbours are shown, **Then** it lists the ten most similar
   codes, nearest first, each with its titles, similarity and median salary, and with the
   statement that the code must match the duties.
3. **Given** a near-identical pair (for example 1311/1312), **When** their closeness is shown,
   **Then** it says their official descriptions are the same, so the text cannot tell them apart,
   and names what distinguishes them in the classification (for example the level in the title).

---

### User Story 2 - See the map (Priority: P2)

A candidate opens the map of all 429 occupations. Each point is one code, placed so that codes
with similar descriptions sit near each other and coloured by its major group, with group names
written on the map. Pointing at a point (or tabbing to it) shows its code, titles and median
salary. Clicking a point selects it, and lines run to its five nearest neighbours. The user can
zoom and pan, and a table view lists the same codes with their neighbours.

**Why this priority**: the picture gives the overview the user asked for, but it is an
approximation of the closeness, which Story 1 gives exactly.

**Independent Test**: render the map from the committed map data; check there are 429 points,
the colours follow the first digit, the tooltip shows the right titles and median, and selecting
a point draws five lines to the codes the neighbour list names.

**Acceptance Scenarios**:

1. **Given** the map, **When** it renders, **Then** each code is one point, the colour follows its
   major group, and each group's name appears once near its points.
2. **Given** a point, **When** the user hovers, taps or focuses it, **Then** its code, English and
   Swedish titles and SCB median (with year) are shown; with a code already selected, also its
   closeness to that code.
3. **Given** stacked points (a near-identical pair), **When** the user points at them, **Then** the
   tooltip lists every code at that spot.
4. **Given** a phone-width screen, **When** the map renders, **Then** it fits without sideways
   scrolling and can be zoomed with buttons as well as gestures.
5. **Given** the map, **When** the user cannot use a pointer, **Then** a keyboard path reaches
   every highlighted point, and a table view lists all codes with their nearest neighbours.

---

### User Story 3 - The map in search (Priority: P2)

On step 1 (Find your code), after a search, the map highlights the result codes and fills in the
codes the candidate has selected, with lines from each selected code to its five nearest
neighbours. On desktop the map sits beside the results; on a phone it is a collapsible panel
under them. Each result card says which selected code it is closest to, if any are selected.

**Why this priority**: it puts the closeness where the code is chosen, which the user asked for.

**Independent Test**: search for "data scientist", select 2511; check that the five hits are
outlined on the map, 2511 is filled, and five lines run to the codes listed as its neighbours.

**Acceptance Scenarios**:

1. **Given** search results, **When** the map is shown, **Then** every hit is outlined and every
   other point is muted.
2. **Given** a selected code, **When** the map is shown, **Then** that code is filled and five lines
   run to its nearest neighbours by full-dimension similarity.
3. **Given** a new search, **When** results change, **Then** the outlines follow without the map
   changing its layout or zoom.
4. **Given** "Your number" (Feature 006), **When** a code card is shown, **Then** a "Similar work"
   section lists its five nearest neighbours by similarity, never by pay.

---

### Edge Cases

- Two codes with identical descriptions: their points coincide. The tooltip lists both, and their
  closeness reads "the same official description" instead of a percentile.
- A code whose only chunks are its title (the minimum is 2 chunks): it is mapped like any other.
  The map data records how many chunks it was built from, so a thin description can be seen.
- A code with no published median: the tooltip says SCB publishes no median for it.
- A code banned from permits: shown like any other, with its flag in the tooltip.
- A rebuilt index whose chunk texts changed: the map must be rebuilt. The serving side refuses map
  data that names a different model or chunk set than the index it runs with.
- No code selected: no lines are drawn; the map shows only the search hits.

## Requirements *(mandatory)*

### Functional Requirements

**The map data**

- **FR-001**: The system MUST build one vector per code by averaging the multilingual model's
  vectors for that code's title and description chunks, excluding synonym chunks and every chunk
  flagged as containing ILO text. Each vector is then normalised.
- **FR-002**: Closeness between two codes MUST be the cosine similarity of their vectors. Each
  code's ten nearest neighbours MUST be stored with their similarity.
- **FR-003**: The system MUST store the percentile of every pair's similarity, or enough of the
  distribution of all pairs' similarities to give a pair's percentile to a whole per cent.
- **FR-004**: The 2-D positions MUST come from UMAP over the code vectors with cosine distance and
  a fixed seed. The parameters, the model identity and the date MUST be stored with the positions.
- **FR-005**: The map data MUST be a committed artefact built ahead of time. It MUST be documented
  in the data dictionary and contain no description or ILO text, only codes, positions,
  neighbours, counts and parameters.
- **FR-006**: Building the map MUST NOT require the serving image to hold the dimension-reduction
  library. Serving reads only the committed data.

**The surfaces**

- **FR-007**: The system MUST serve the map (all points with their group and neighbours) and, per
  code, its neighbours with titles and latest median. The closeness of any two codes MUST be
  available over REST and as an MCP tool.
- **FR-008**: Every neighbour and closeness answer MUST carry the honest-fit statement. Neighbours
  MUST be ordered by similarity and never by pay.
- **FR-009**: Near-identical pairs (similarity ≥ 0.99) MUST be labelled as sharing their
  description, not given a percentile.

**The page**

- **FR-010**: The map MUST show every code as a point coloured by major group, with direct group
  labels, a tooltip (code, titles, median and year, flags, and closeness to the selected code),
  zoom and pan by pointer and buttons, a keyboard path through the highlighted points, and a
  table view.
- **FR-011**: On step 1, the map MUST outline the search hits, fill the selected codes and draw
  lines to each selected code's five nearest neighbours. It sits beside the results on wide
  screens and in a collapsible panel on phones.
- **FR-012**: Selecting two codes MUST show their closeness sentence (FR-009 wording for
  near-identical pairs).
- **FR-013**: Each code card on "Your number" MUST have a "Similar work" section with its five
  nearest neighbours.
- **FR-014**: Colour MUST NOT encode pay anywhere on the map.
- **FR-015** (added in implementation): points MUST NOT be coloured by major group either. Ten
  hues fail the dataviz all-pairs check, and the groups are skill levels that the map's domain
  clusters cut across. Colour marks only the codes in play, and a code's group is read per point.
  This supersedes the "coloured by its major group" wording in Story 2 and FR-010.

### Key Entities

- **Map point**: a code, its x and y, its major group (first digit), the number of chunks it was
  built from, and its ten neighbours (code and similarity).
- **Map build**: the model identity, the chunk kinds used, ILO excluded, the UMAP parameters and
  seed, the build date, and the similarity distribution of all pairs.
- **Closeness**: two codes, their similarity, the share of pairs less similar, and whether they
  share a description.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For every code, the stored neighbours equal the ten most similar codes recomputed
  from the cached vectors.
- **SC-002**: For 2511, the neighbours include 2512 and 2519 in the top three. For 2221
  Professional nurses, they include 2239 and 2224 in the top five (measured 2026-10-27).
- **SC-003**: Codes that sit near each other on the map are mostly close in full dimension. Of
  each code's ten nearest on the map, at least 50 % on average are among its 20 nearest in full
  dimension. On 2026-10-27, UMAP with 15 neighbours, min_dist 0.1 and seed 0 gave 65 %, and a
  rerun on the same machine gave identical positions.
- **SC-004**: The map renders 429 points and responds to pointer movement without visible lag on
  a phone-class device (each frame under 16 ms in a 4× CPU-throttled browser).
- **SC-005**: Zero serious accessibility violations, and no sideways scrolling at 390 px.
- **SC-006**: The serving image grows by less than 1 MB, and its memory does not change
  measurably.

## Assumptions

- Feature 006 is merged first; this feature builds on its step layout and "Your number" cards.
- The cached multilingual vectors are the ones the index uses. Building the map needs the local
  raw cache; the container only serves the committed result.
- A new dimension-reduction library is added only to the build tooling. Its output is not
  byte-stable across machines, so the positions are rebuilt only on purpose and tests check
  structure and neighbours, not exact coordinates.
- The query text is not placed on the map (that would need the model and UMAP at request time).
- ILO-derived content is excluded entirely, so no ruling on derived vectors is needed.
