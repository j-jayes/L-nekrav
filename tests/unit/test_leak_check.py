"""FR-018a: a benchmark query leaks when it appears in its answer's indexed text, inflected or not.

Found in planning (research R1): 104 of 111 English generated queries appeared in their answer's
ESCO description in the plural ("business managers are…"), which the exact-match check missed.
"""

import pytest

from lonekrav.etl.benchmark import phrase_in


@pytest.mark.parametrize("phrase,text,found", [
    ("business manager", "Business managers are responsible for the objectives", True),  # +1
    ("sjuksköterska", "sjuksköterskan ansvarar för omvårdnaden", True),  # +1
    ("sjuksköterska", "sjuksköterskorna", False),  # stem change, not a suffix: not caught
    ("lärare", "lärarna undervisar", False),
    ("manage", "management consultancy", False),  # +4
    ("chef", "kökschef på restaurang", False),  # starts mid-word
    ("data analyst", "Data analysts import, inspect and clean data", True),
    ("Speldesigner", "speldesignern", True),
])
def test_phrase_in(phrase, text, found):
    assert phrase_in(phrase, text) is found
