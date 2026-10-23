// The one API client. Its types are generated from the server's own schema (research R6):
// regenerate with `uv run python scripts/export_openapi.py && npm run gen`.
import createClient from "openapi-fetch";
import type { components, paths } from "./schema";

// `fetch` is looked up per call, so tests can stub globalThis.fetch after this module loads.
export const api = createClient<paths>({ baseUrl: location.origin, fetch: (r) => globalThis.fetch(r) });

type S = components["schemas"];
export type SearchAnswer = S["SearchAnswer"];
export type SearchHit = S["SearchHit"];
export type AdPassage = S["AdPassage"];
export type SalaryPayload = S["SalaryPayload"];
export type ThresholdLine = S["ThresholdLine"];
export type Comparison = S["Comparison"];
export type CompareColumn = S["CompareColumn"];
export type EligibilityAnswer = S["EligibilityAnswer"];
export type EligibilityRequest = S["EligibilityRequest"];
export type Offer = S["Offer"];
export type TimelineEvent = S["TimelineEvent"];
export type Registry = S["Registry"];
export type Source = S["Source"];
export type LegalFlag = S["LegalFlag"];
export type OccupationProfile = S["OccupationProfile"];
export type MarketAnswer = S["MarketAnswer"];
export type YearlyAds = S["YearlyAds"];
