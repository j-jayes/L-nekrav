"""The occupation map over REST and MCP (007 contracts/http.md): neighbours, closeness, the map."""

from lonekrav.core.occupation_map import HONEST_SIMILAR, load_map, load_similarity


def test_neighbours_carry_titles_medians_and_the_duties_rule(api_client):
    r = api_client.get("/api/v1/occupations/2512/neighbours", params={"k": 3})
    assert r.status_code == 200
    body = r.json()
    stored = next(p for p in load_map().points if p.code == "2512").neighbours[:3]
    assert [n["code"] for n in body["neighbours"]] == [n.code for n in stored]  # by similarity, never pay
    assert [n["cosine"] for n in body["neighbours"]] == [n.cosine for n in stored]
    assert body["honest_fit"] == HONEST_SIMILAR
    first = body["neighbours"][0]
    assert set(first) >= {"title_sv", "title_en", "median_sek", "median_year"}
    closer = api_client.get("/api/v1/closeness", params={"a": "2512", "b": first["code"]}).json() \
        if first["code"] in api_client.app.state.service.profiles else None
    if closer:  # the same answer as /closeness for that pair
        assert (first["percentile"], first["same_description"]) == (closer["percentile"], closer["same_description"])
    assert all(0 <= n["percentile"] <= 100 or n["same_description"] for n in body["neighbours"])


def test_neighbours_errors(api_client):
    assert api_client.get("/api/v1/occupations/1234/neighbours").status_code == 404
    assert api_client.get("/api/v1/occupations/2512/neighbours", params={"k": 11}).status_code == 422


def test_closeness_of_two_codes(api_client):
    r = api_client.get("/api/v1/closeness", params={"a": "2512", "b": "2421"})
    assert r.status_code == 200
    body = r.json()
    assert body["cosine"] == round(load_similarity()[("2421", "2512")], 3)
    assert 0 <= body["percentile"] <= 100 and body["same_description"] is False
    assert body["honest_fit"] == HONEST_SIMILAR


def test_codes_that_share_a_description(api_client):
    body = api_client.get("/api/v1/closeness", params={"a": "1211", "b": "1212"}).json()
    assert body["same_description"] is (load_similarity()[("1211", "1212")] >= 0.99)


def test_closeness_errors(api_client):
    assert api_client.get("/api/v1/closeness", params={"a": "2512", "b": "1234"}).status_code == 404
    assert api_client.get("/api/v1/closeness", params={"a": "2512", "b": "2512"}).status_code == 422


def test_the_map_has_every_known_point_with_its_titles_and_median(api_client):
    r = api_client.get("/api/v1/map")
    assert r.status_code == 200
    body = r.json()
    profiles = api_client.app.state.service.profiles
    assert [p["code"] for p in body["points"]] == sorted(c for c in profiles if c in {p.code for p in load_map().points})
    p = next(p for p in body["points"] if p["code"] == "2512")
    assert p["title_en"] == profiles["2512"].title_en and p["median_sek"] and p["median_year"]
    assert len(p["neighbours"]) == 10 and body["major_groups"]["2"]["en"]
    assert body["stale"] is False and len(body["pair_quantiles"]) == 101
