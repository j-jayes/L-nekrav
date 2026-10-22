import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, it, vi } from "vitest";
import { emptyDraft } from "../lib/offer";
import { OfferPanel } from "./OfferPanel";

it("explains a network failure instead of failing silently", async () => {  // Copilot on PR #4
  vi.stubGlobal("fetch", vi.fn(async () => { throw new TypeError("Failed to fetch"); }));
  const onApplied = vi.fn();
  render(<OfferPanel code="2512" draft={emptyDraft()} exemptions={[]} onApplied={onApplied} />);
  await userEvent.type(screen.getByLabelText(/monthly salary/i), "52000");
  await userEvent.click(screen.getByRole("button", { name: /use this offer/i }));
  expect(await screen.findByRole("alert")).toHaveTextContent(/could not be checked/i);
  expect(onApplied).not.toHaveBeenCalled();
});
