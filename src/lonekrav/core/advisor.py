"""What the advisor agent takes in and the guarantees its memo carries (Feature 003, research R10).

The model writes the memo; this module makes sure it never leaves without the honest-fit notice,
the not-legal-advice statement and the third-party disclosure, whatever the model wrote.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from lonekrav.core.adparse import AdText
from lonekrav.core.eligibility import DISCLAIMER, Offer
from lonekrav.core.search import HONEST_FIT

THIRD_PARTY_NOTICE = ("Written with a third-party language model (via OpenRouter), which received "
                      "the ad, background and offer you sent.")
NO_RESULTS = ("This memo is not based on any Lönekrav result: the model called no Lönekrav "
              "operation, so treat its codes and figures as unchecked.")


class AdvisorRequest(BaseModel):
    ad: str = AdText.model_fields["text"]
    background: str | None = Field(default=None, max_length=5_000,
                                   description="The applicant's education and experience")
    offer: Offer | None = Field(default=None, description="The offer, without a code")


def finalise_memo(memo: str, tools_called: list[str]) -> str:
    memo = memo.strip().removesuffix(THIRD_PARTY_NOTICE).rstrip()  # re-added last, below
    parts = [memo]
    if HONEST_FIT not in memo:
        parts.append(HONEST_FIT)
    if not tools_called and NO_RESULTS not in memo:
        parts.append(NO_RESULTS)
    if "not legal advice" not in memo.casefold():
        parts.append(DISCLAIMER)
    parts.append(THIRD_PARTY_NOTICE)
    return "\n\n".join(parts)
