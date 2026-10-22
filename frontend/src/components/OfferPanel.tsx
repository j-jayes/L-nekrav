import { useState } from "react";
import { api, type EligibilityAnswer, type Offer, type Registry } from "../api/client";
import { type Draft, fieldErrors, toOffer } from "../lib/offer";
import { OfferForm } from "./OfferForm";

type Props = {
  code: string; // the API validates an offer against a code
  draft: Draft;
  exemptions: Registry["exemptions"][string][];
  onApplied: (draft: Draft, offer: Offer, answer: EligibilityAnswer) => void;
  submitLabel?: string;
};

/** The offer form, checked by the API: a valid offer is applied, an invalid one shows why. */
export function OfferPanel({ code, draft, exemptions, onApplied, submitLabel }: Props) {
  const [errors, setErrors] = useState<Partial<Record<keyof Draft | "form", string>>>({});
  async function submit(d: Draft) {
    const offer = toOffer(d);
    const { data, error, response } = await api.POST("/api/v1/eligibility", { body: { ...offer, code } });
    if (data) {
      setErrors({});
      onApplied(d, offer, data);
    } else if (response.status === 422 && error && "detail" in error && Array.isArray(error.detail)) {
      setErrors(fieldErrors(error.detail as never));
    } else {
      setErrors({ form: "The offer could not be checked. Try again." });
    }
  }
  return <OfferForm key={JSON.stringify(draft)} initial={draft} exemptions={exemptions} errors={errors}
    onSubmit={submit} submitLabel={submitLabel} />;
}
