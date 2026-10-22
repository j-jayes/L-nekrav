import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import type { Registry } from "../api/client";
import { emptyDraft, fieldErrors, toOffer } from "../lib/offer";
import { fixture } from "../test/fakeApi";
import { OfferForm } from "./OfferForm";

const exemptions = Object.values((fixture("registry").body as Registry).exemptions);

describe("offer helpers", () => {
  it("turns the draft into the API's Offer, with numbers as numbers", () => {
    const offer = toOffer({ ...emptyDraft(), monthly_salary_sek: "52000", fte_percent: "80", filed_on: "2026-10-01",
      decided_on: "2026-10-22" });
    expect(offer).toMatchObject({ monthly_salary_sek: 52000, fte_percent: 80, application_type: "first_permit" });
    expect(offer).not.toHaveProperty("current_permit_granted_on");
  });

  it("maps a 422 to the field it names, in plain words", () => {
    const detail = (fixture("eligibility-invalid").body as { detail: never }).detail;
    expect(fieldErrors(detail)).toEqual({ decided_on: "Expected decision date cannot be before Date filed." });
    expect(fieldErrors([{ loc: ["body", "offer", "fte_percent"], msg: "Input should be less than or equal to 100" }]))
      .toEqual({ fte_percent: "Input should be less than or equal to 100." });
  });
});

describe("OfferForm", () => {
  it("asks for the current permit's date only for an extension", async () => {
    render(<OfferForm exemptions={exemptions} onSubmit={() => {}} errors={{}} />);
    expect(screen.queryByLabelText(/current permit granted/i)).toBeNull();
    await userEvent.click(screen.getByRole("radio", { name: /extension/i }));
    expect(screen.getByLabelText(/current permit granted/i)).toBeInTheDocument();
  });

  it("shows an error beside the field it belongs to", () => {
    render(<OfferForm exemptions={exemptions} onSubmit={() => {}} errors={{ decided_on: "Too early." }} />);
    expect(screen.getByLabelText(/expected decision date/i)).toHaveAccessibleDescription("Too early.");
  });

  it("submits the draft and never stores it or puts it in the address", async () => {
    const onSubmit = vi.fn();
    const setItem = vi.spyOn(Storage.prototype, "setItem");
    const before = location.href;
    render(<OfferForm exemptions={exemptions} onSubmit={onSubmit} errors={{}} />);
    await userEvent.type(screen.getByLabelText(/monthly salary/i), "52000");
    await userEvent.click(screen.getByRole("checkbox", { name: new RegExp(`^${exemptions[0].label}`) }));
    await userEvent.click(screen.getByRole("button", { name: /use this offer/i }));
    expect(onSubmit).toHaveBeenCalledWith(expect.objectContaining({ monthly_salary_sek: "52000",
      exemptions: [exemptions[0].id] }));
    expect(setItem).not.toHaveBeenCalled();
    expect(location.href).toBe(before);
  });
});
