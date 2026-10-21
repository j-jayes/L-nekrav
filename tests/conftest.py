from pathlib import Path

import pytest

from lonekrav.core.profiles import Inputs
from lonekrav.etl import esco, ilo, jobtech, mis2012, scb_files, scb_pxweb

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures() -> Path:
    return FIXTURES


@pytest.fixture
def inputs(fixtures) -> Inputs:
    f = fixtures
    labels = scb_pxweb.occupation_labels(f / "pxweb/TAB5932.json")
    groups = jobtech.parse(f / "jobtech/ssyk_level_4.json")
    return Inputs(
        salary_labels=labels,
        structure=scb_files.parse_structure(f / "scb/ssyk-2012-koder.xlsx"),
        english=scb_files.parse_english(f / "scb/structur_english_ssyk2012_1_4.xlsx"),
        title_index=scb_files.parse_title_index(f / "scb/ssyk_index_webb_2026.xlsx"),
        isco_key=scb_files.parse_isco_key(f / "scb/webb_nyckel_ssyk2012_isco-08_20160905.xlsx"),
        jobtech=groups,
        jobtech_by_scb=jobtech.expand_merged(groups, set(labels)),
        ilo=ilo.parse(f / "ilo/isco08_en.xlsx"),
        esco={o.uri: o for o in map(esco.parse, sorted((f / "esco").glob("*.json")))},
        mis=mis2012.parse(mis2012.load_pages(f / "mis2012/pages.json")),
    )
