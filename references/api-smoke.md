# API smoke transcript

Run 2026-10-21T22:38:01 against `http://127.0.0.1:8000` by `scripts/api_smoke.py`. Lists are cut to three items for reading.

## Eligibility, scenario 1: 2512 filed 16 June 2026

`POST /api/v1/eligibility` → **200**

```json
{"code": "2512", "monthly_salary_sek": 40000, "fte_percent": 100, "application_type": "first_permit", "filed_on": "2026-06-16", "decided_on": "2026-07-01"}
```

```json
{
 "status": "pass",
 "rule_id": "salary_90",
 "reason": "Salary requirement for first permits decided from 1 June 2026 and for extensions not covered by the transition: at least 90 % of the median in force when the application was filed.",
 "percent": 90.0,
 "median": {
  "amount": 38300,
  "scb_reference_year": 2025,
  "effective_from": "2026-06-16",
  "effective_to": null,
  "source": {
   "key": "mv_lonekrav",
   "title": "Migrationsverket: Lönekrav för arbetstillstånd",
   "url": "https://www.migrationsverket.se/ordforklaringar/lonekrav-for-arbetstillstand",
   "checked_on": "2026-10-21"
  }
 },
 "threshold_sek": 34470,
 "margin_sek": 5530,
 "margin_percent": 16.0,
 "warnings": [],
 "sources": [
  {
   "key": "mv_lonekrav",
   "title": "Migrationsverket: Lönekrav för arbetstillstånd",
   "url": "https://www.migrationsverket.se/ordforklaringar/lonekrav-for-arbetstillstand",
   "checked_on": "2026-10-21"
  }
 ],
 "disclaimer": "The salary must also be in line with the collective agreement or what is customary in the occupation or industry, which Lönekrav does not check. This is information, not legal advice."
}
```

## Eligibility, scenario 2: filed 15 June 2026

`POST /api/v1/eligibility` → **200**

```json
{"code": "2512", "monthly_salary_sek": 40000, "fte_percent": 100, "application_type": "first_permit", "filed_on": "2026-06-15", "decided_on": "2026-07-01"}
```

```json
{
 "status": "pass",
 "rule_id": "salary_90",
 "reason": "Salary requirement for first permits decided from 1 June 2026 and for extensions not covered by the transition: at least 90 % of the median in force when the application was filed.",
 "percent": 90.0,
 "median": {
  "amount": 37100,
  "scb_reference_year": 2024,
  "effective_from": "2025-06-17",
  "effective_to": "2026-06-15",
  "source": {
   "key": "mv_lonekrav",
   "title": "Migrationsverket: Lönekrav för arbetstillstånd",
   "url": "https://www.migrationsverket.se/ordforklaringar/lonekrav-for-arbetstillstand",
   "checked_on": "2026-10-21"
  }
 },
 "threshold_sek": 33390,
 "margin_sek": 6610,
 "margin_percent": 19.8,
 "warnings": [],
 "sources": [
  {
   "key": "mv_lonekrav",
   "title": "Migrationsverket: Lönekrav för arbetstillstånd",
   "url": "https://www.migrationsverket.se/ordforklaringar/lonekrav-for-arbetstillstand",
   "checked_on": "2026-10-21"
  }
 ],
 "disclaimer": "The salary must also be in line with the collective agreement or what is customary in the occupation or industry, which Lönekrav does not check. This is information, not legal advice."
}
```

## Eligibility, scenario 3: exempt code 3511

`POST /api/v1/eligibility` → **200**

```json
{"code": "3511", "monthly_salary_sek": 40000, "fte_percent": 100, "application_type": "first_permit", "filed_on": "2026-10-21", "decided_on": "2026-10-21"}
```

```json
{
 "status": "pass",
 "rule_id": "salary_75_exempt",
 "reason": "Occupation 3511 is on the exempt list. 5 kap. 6 §: the 90 % requirement does not apply; 75 % of the median applies instead.",
 "percent": 75.0,
 "median": {
  "amount": 38300,
  "scb_reference_year": 2025,
  "effective_from": "2026-06-16",
  "effective_to": null,
  "source": {
   "key": "mv_lonekrav",
   "title": "Migrationsverket: Lönekrav för arbetstillstånd",
   "url": "https://www.migrationsverket.se/ordforklaringar/lonekrav-for-arbetstillstand",
   "checked_on": "2026-10-21"
  }
 },
 "threshold_sek": 28725,
 "margin_sek": 11275,
 "margin_percent": 39.3,
 "warnings": [],
 "sources": [
  {
   "key": "mv_lonekrav",
   "title": "Migrationsverket: Lönekrav för arbetstillstånd",
   "url": "https://www.migrationsverket.se/ordforklaringar/lonekrav-for-arbetstillstand",
   "checked_on": "2026-10-21"
  },
  {
   "key": "sfs_2026_605",
   "title": "SFS 2026:605, utlänningsförordningen 5 kap. 5–6 §§",
   "url": "https://svenskforfattningssamling.se/doc/2026605.html",
   "checked_on": "2026-10-20"
  }
 ],
 "disclaimer": "The salary must also be in line with the collective agreement or what is customary in the occupation or industry, which Lönekrav does not check. This is information, not legal advice."
}
```

## Eligibility, scenario 4: banned code 5343

`POST /api/v1/eligibility` → **200**

```json
{"code": "5343", "monthly_salary_sek": 40000, "fte_percent": 100, "application_type": "first_permit", "filed_on": "2026-06-16", "decided_on": "2026-07-01"}
```

```json
{
 "status": "not_permitted",
 "rule_id": null,
 "reason": "5 kap. 5 §: work permits may not be granted.",
 "percent": null,
 "median": null,
 "threshold_sek": null,
 "margin_sek": null,
 "margin_percent": null,
 "warnings": [],
 "sources": [
  {
   "key": "sfs_2026_605",
   "title": "SFS 2026:605, utlänningsförordningen 5 kap. 5–6 §§",
   "url": "https://svenskforfattningssamling.se/doc/2026605.html",
   "checked_on": "2026-10-20"
  }
 ],
 "disclaimer": "The salary must also be in line with the collective agreement or what is customary in the occupation or industry, which Lönekrav does not check. This is information, not legal advice."
}
```

## Eligibility, scenario 5: 9210 partial ban

`POST /api/v1/eligibility` → **200**

```json
{"code": "9210", "monthly_salary_sek": 40000, "fte_percent": 100, "application_type": "first_permit", "filed_on": "2026-06-16", "decided_on": "2026-07-01"}
```

```json
{
 "status": "pass",
 "rule_id": "salary_75_exempt",
 "reason": "Occupation 9210 is on the exempt list. 5 kap. 6 §: the 90 % requirement does not apply; 75 % of the median applies instead.",
 "percent": 75.0,
 "median": {
  "amount": 38300,
  "scb_reference_year": 2025,
  "effective_from": "2026-06-16",
  "effective_to": null,
  "source": {
   "key": "mv_lonekrav",
   "title": "Migrationsverket: Lönekrav för arbetstillstånd",
   "url": "https://www.migrationsverket.se/ordforklaringar/lonekrav-for-arbetstillstand",
   "checked_on": "2026-10-21"
  }
 },
 "threshold_sek": 28725,
 "margin_sek": 11275,
 "margin_percent": 39.3,
 "warnings": [
  {
   "kind": "partial_ban",
   "message": "Work permits cannot be granted for forest berry pickers (bärplockare i skog), even though the occupation group is otherwise on the exempt list. Other jobs in the group are covered by the 75 % level.",
   "source": {
    "key": "mv_lonekrav",
    "title": "Migrationsverket: Lönekrav för arbetstillstånd",
    "url": "https://www.migrationsverket.se/ordforklaringar/lonekrav-for-arbetstillstand",
    "checked_on": "2026-10-21"
   }
  }
 ],
 "sources": [
  {
   "key": "mv_lonekrav",
   "title": "Migrationsverket: Lönekrav för arbetstillstånd",
   "url": "https://www.migrationsverket.se/ordforklaringar/lonekrav-for-arbetstillstand",
   "checked_on": "2026-10-21"
  },
  {
   "key": "sfs_2026_605",
   "title": "SFS 2026:605, utlänningsförordningen 5 kap. 5–6 §§",
   "url": "https://svenskforfattningssamling.se/doc/2026605.html",
   "checked_on": "2026-10-20"
  }
 ],
 "disclaimer": "The salary must also be in line with the collective agreement or what is customary in the occupation or industry, which Lönekrav does not check. This is information, not legal advice."
}
```

## Eligibility, scenario 6: extension filed 30 Nov 2026, permit granted before June

`POST /api/v1/eligibility` → **200**

```json
{"code": "2512", "monthly_salary_sek": 40000, "fte_percent": 100, "application_type": "extension", "filed_on": "2026-11-30", "decided_on": "2026-12-20", "current_permit_granted_on": "2026-01-10"}
```

```json
{
 "status": "pass",
 "rule_id": "transition_maintenance_80",
 "reason": "Extensions filed 1 June–1 December 2026 for a permit granted before 1 June 2026 keep the earlier maintenance requirement: at least 80 % of the median, with no 75 % exemption.",
 "percent": 80.0,
 "median": {
  "amount": 38300,
  "scb_reference_year": 2025,
  "effective_from": "2026-06-16",
  "effective_to": null,
  "source": {
   "key": "mv_lonekrav",
   "title": "Migrationsverket: Lönekrav för arbetstillstånd",
   "url": "https://www.migrationsverket.se/ordforklaringar/lonekrav-for-arbetstillstand",
   "checked_on": "2026-10-21"
  }
 },
 "threshold_sek": 30640,
 "margin_sek": 9360,
 "margin_percent": 30.5,
 "warnings": [],
 "sources": [
  {
   "key": "mv_god_forsorjning",
   "title": "Migrationsverket: God försörjning – försörjningskrav för arbetstillstånd",
   "url": "https://www.migrationsverket.se/ordforklaringar/god-forsorjning---forsorjningskrav-for-arbetstillstand.html",
   "checked_on": "2026-10-21"
  },
  {
   "key": "mv_lonekrav",
   "title": "Migrationsverket: Lönekrav för arbetstillstånd",
   "url": "https://www.migrationsverket.se/ordforklaringar/lonekrav-for-arbetstillstand",
   "checked_on": "2026-10-21"
  }
 ],
 "disclaimer": "The salary must also be in line with the collective agreement or what is customary in the occupation or industry, which Lönekrav does not check. This is information, not legal advice."
}
```

## Eligibility, scenario 6: same extension filed 2 Dec 2026

`POST /api/v1/eligibility` → **200**

```json
{"code": "2512", "monthly_salary_sek": 40000, "fte_percent": 100, "application_type": "extension", "filed_on": "2026-12-02", "decided_on": "2027-01-10", "current_permit_granted_on": "2026-01-10"}
```

```json
{
 "status": "pass",
 "rule_id": "salary_90",
 "reason": "Salary requirement for first permits decided from 1 June 2026 and for extensions not covered by the transition: at least 90 % of the median in force when the application was filed.",
 "percent": 90.0,
 "median": {
  "amount": 38300,
  "scb_reference_year": 2025,
  "effective_from": "2026-06-16",
  "effective_to": null,
  "source": {
   "key": "mv_lonekrav",
   "title": "Migrationsverket: Lönekrav för arbetstillstånd",
   "url": "https://www.migrationsverket.se/ordforklaringar/lonekrav-for-arbetstillstand",
   "checked_on": "2026-10-21"
  }
 },
 "threshold_sek": 34470,
 "margin_sek": 5530,
 "margin_percent": 16.0,
 "warnings": [],
 "sources": [
  {
   "key": "mv_lonekrav",
   "title": "Migrationsverket: Lönekrav för arbetstillstånd",
   "url": "https://www.migrationsverket.se/ordforklaringar/lonekrav-for-arbetstillstand",
   "checked_on": "2026-10-21"
  }
 ],
 "disclaimer": "The salary must also be in line with the collective agreement or what is customary in the occupation or industry, which Lönekrav does not check. This is information, not legal advice."
}
```

## Eligibility, scenario 7: 80 % of full time

`POST /api/v1/eligibility` → **200**

```json
{"code": "2512", "monthly_salary_sek": 40000, "fte_percent": 80, "application_type": "first_permit", "filed_on": "2026-06-16", "decided_on": "2026-07-01"}
```

```json
{
 "status": "pass",
 "rule_id": "salary_90",
 "reason": "Salary requirement for first permits decided from 1 June 2026 and for extensions not covered by the transition: at least 90 % of the median in force when the application was filed.",
 "percent": 90.0,
 "median": {
  "amount": 38300,
  "scb_reference_year": 2025,
  "effective_from": "2026-06-16",
  "effective_to": null,
  "source": {
   "key": "mv_lonekrav",
   "title": "Migrationsverket: Lönekrav för arbetstillstånd",
   "url": "https://www.migrationsverket.se/ordforklaringar/lonekrav-for-arbetstillstand",
   "checked_on": "2026-10-21"
  }
 },
 "threshold_sek": 34470,
 "margin_sek": 5530,
 "margin_percent": 16.0,
 "warnings": [
  {
   "kind": "part_time",
   "message": "The requirement applies to the monthly salary actually paid. Migrationsverket states it as \"a monthly salary or wages totalling at least\" the threshold and gives no reduction for part-time work, so a part-time salary must still reach the full amount.",
   "source": {
    "key": "mv_employees",
    "title": "Migrationsverket: Employees (work permit requirements)",
    "url": "https://www.migrationsverket.se/en/you-want-to-apply/work/employee-or-self-employed/employees.html",
    "checked_on": "2026-10-21"
   }
  }
 ],
 "sources": [
  {
   "key": "mv_lonekrav",
   "title": "Migrationsverket: Lönekrav för arbetstillstånd",
   "url": "https://www.migrationsverket.se/ordforklaringar/lonekrav-for-arbetstillstand",
   "checked_on": "2026-10-21"
  },
  {
   "key": "mv_employees",
   "title": "Migrationsverket: Employees (work permit requirements)",
   "url": "https://www.migrationsverket.se/en/you-want-to-apply/work/employee-or-self-employed/employees.html",
   "checked_on": "2026-10-21"
  }
 ],
 "disclaimer": "The salary must also be in line with the collective agreement or what is customary in the occupation or industry, which Lönekrav does not check. This is information, not legal advice."
}
```

## Eligibility, scenario 8: decided after June 2027 with no 2027 median

`POST /api/v1/eligibility` → **200**

```json
{"code": "2512", "monthly_salary_sek": 40000, "fte_percent": 100, "application_type": "first_permit", "filed_on": "2027-06-20", "decided_on": "2027-06-20"}
```

```json
{
 "status": "pass",
 "rule_id": "salary_90",
 "reason": "Salary requirement for first permits decided from 1 June 2026 and for extensions not covered by the transition: at least 90 % of the median in force when the application was filed.",
 "percent": 90.0,
 "median": {
  "amount": 38300,
  "scb_reference_year": 2025,
  "effective_from": "2026-06-16",
  "effective_to": null,
  "source": {
   "key": "mv_lonekrav",
   "title": "Migrationsverket: Lönekrav för arbetstillstånd",
   "url": "https://www.migrationsverket.se/ordforklaringar/lonekrav-for-arbetstillstand",
   "checked_on": "2026-10-21"
  }
 },
 "threshold_sek": 34470,
 "margin_sek": 5530,
 "margin_percent": 16.0,
 "warnings": [
  {
   "kind": "stale_median",
   "message": "SCB publishes a new median every June and it may already apply. This answer uses 38 300 SEK (SCB 2025), the newest in Lönekrav's registry.",
   "source": {
    "key": "mv_lonekrav",
    "title": "Migrationsverket: Lönekrav för arbetstillstånd",
    "url": "https://www.migrationsverket.se/ordforklaringar/lonekrav-for-arbetstillstand",
    "checked_on": "2026-10-21"
   }
  }
 ],
 "sources": [
  {
   "key": "mv_lonekrav",
   "title": "Migrationsverket: Lönekrav för arbetstillstånd",
   "url": "https://www.migrationsverket.se/ordforklaringar/lonekrav-for-arbetstillstand",
   "checked_on": "2026-10-21"
  }
 ],
 "disclaimer": "The salary must also be in line with the collective agreement or what is customary in the occupation or industry, which Lönekrav does not check. This is information, not legal advice."
}
```

## Eligibility, scenario 9: declared young tech company

`POST /api/v1/eligibility` → **200**

```json
{"code": "2512", "monthly_salary_sek": 40000, "fte_percent": 100, "application_type": "first_permit", "filed_on": "2026-06-16", "decided_on": "2026-07-01", "exemptions": ["young_tech_company"]}
```

```json
{
 "status": "pass",
 "rule_id": "salary_75_exempt",
 "reason": "Declared exemption. Employee of a young tech or life-science company: Employed by a tech or life-science company that is being built up, is less than five years old and has fewer than 100 employees.",
 "percent": 75.0,
 "median": {
  "amount": 38300,
  "scb_reference_year": 2025,
  "effective_from": "2026-06-16",
  "effective_to": null,
  "source": {
   "key": "mv_lonekrav",
   "title": "Migrationsverket: Lönekrav för arbetstillstånd",
   "url": "https://www.migrationsverket.se/ordforklaringar/lonekrav-for-arbetstillstand",
   "checked_on": "2026-10-21"
  }
 },
 "threshold_sek": 28725,
 "margin_sek": 11275,
 "margin_percent": 39.3,
 "warnings": [],
 "sources": [
  {
   "key": "mv_lonekrav",
   "title": "Migrationsverket: Lönekrav för arbetstillstånd",
   "url": "https://www.migrationsverket.se/ordforklaringar/lonekrav-for-arbetstillstand",
   "checked_on": "2026-10-21"
  }
 ],
 "disclaimer": "The salary must also be in line with the collective agreement or what is customary in the occupation or industry, which Lönekrav does not check. This is information, not legal advice."
}
```

## Eligibility, scenario 10: 3511 on a transitional extension

`POST /api/v1/eligibility` → **200**

```json
{"code": "3511", "monthly_salary_sek": 40000, "fte_percent": 100, "application_type": "extension", "filed_on": "2026-11-30", "decided_on": "2026-12-20", "current_permit_granted_on": "2026-01-10"}
```

```json
{
 "status": "pass",
 "rule_id": "transition_maintenance_80",
 "reason": "Extensions filed 1 June–1 December 2026 for a permit granted before 1 June 2026 keep the earlier maintenance requirement: at least 80 % of the median, with no 75 % exemption.",
 "percent": 80.0,
 "median": {
  "amount": 38300,
  "scb_reference_year": 2025,
  "effective_from": "2026-06-16",
  "effective_to": null,
  "source": {
   "key": "mv_lonekrav",
   "title": "Migrationsverket: Lönekrav för arbetstillstånd",
   "url": "https://www.migrationsverket.se/ordforklaringar/lonekrav-for-arbetstillstand",
   "checked_on": "2026-10-21"
  }
 },
 "threshold_sek": 30640,
 "margin_sek": 9360,
 "margin_percent": 30.5,
 "warnings": [],
 "sources": [
  {
   "key": "mv_god_forsorjning",
   "title": "Migrationsverket: God försörjning – försörjningskrav för arbetstillstånd",
   "url": "https://www.migrationsverket.se/ordforklaringar/god-forsorjning---forsorjningskrav-for-arbetstillstand.html",
   "checked_on": "2026-10-21"
  },
  {
   "key": "mv_lonekrav",
   "title": "Migrationsverket: Lönekrav för arbetstillstånd",
   "url": "https://www.migrationsverket.se/ordforklaringar/lonekrav-for-arbetstillstand",
   "checked_on": "2026-10-21"
  }
 ],
 "disclaimer": "The salary must also be in line with the collective agreement or what is customary in the occupation or industry, which Lönekrav does not check. This is information, not legal advice."
}
```

## Eligibility, scenario 11: filed 20 May 2026, decided 20 June

`POST /api/v1/eligibility` → **200**

```json
{"code": "2512", "monthly_salary_sek": 40000, "fte_percent": 100, "application_type": "first_permit", "filed_on": "2026-05-20", "decided_on": "2026-06-20"}
```

```json
{
 "status": "pass",
 "rule_id": "salary_90",
 "reason": "Salary requirement for first permits decided from 1 June 2026 and for extensions not covered by the transition: at least 90 % of the median in force when the application was filed.",
 "percent": 90.0,
 "median": {
  "amount": 37100,
  "scb_reference_year": 2024,
  "effective_from": "2025-06-17",
  "effective_to": "2026-06-15",
  "source": {
   "key": "mv_lonekrav",
   "title": "Migrationsverket: Lönekrav för arbetstillstånd",
   "url": "https://www.migrationsverket.se/ordforklaringar/lonekrav-for-arbetstillstand",
   "checked_on": "2026-10-21"
  }
 },
 "threshold_sek": 33390,
 "margin_sek": 6610,
 "margin_percent": 19.8,
 "warnings": [],
 "sources": [
  {
   "key": "mv_lonekrav",
   "title": "Migrationsverket: Lönekrav för arbetstillstånd",
   "url": "https://www.migrationsverket.se/ordforklaringar/lonekrav-for-arbetstillstand",
   "checked_on": "2026-10-21"
  }
 ],
 "disclaimer": "The salary must also be in line with the collective agreement or what is customary in the occupation or industry, which Lönekrav does not check. This is information, not legal advice."
}
```

## Eligibility, scenario 12: extension of a permit granted 10 July 2026

`POST /api/v1/eligibility` → **200**

```json
{"code": "2512", "monthly_salary_sek": 40000, "fte_percent": 100, "application_type": "extension", "filed_on": "2026-11-30", "decided_on": "2026-12-20", "current_permit_granted_on": "2026-07-10"}
```

```json
{
 "status": "pass",
 "rule_id": "salary_90",
 "reason": "Salary requirement for first permits decided from 1 June 2026 and for extensions not covered by the transition: at least 90 % of the median in force when the application was filed.",
 "percent": 90.0,
 "median": {
  "amount": 38300,
  "scb_reference_year": 2025,
  "effective_from": "2026-06-16",
  "effective_to": null,
  "source": {
   "key": "mv_lonekrav",
   "title": "Migrationsverket: Lönekrav för arbetstillstånd",
   "url": "https://www.migrationsverket.se/ordforklaringar/lonekrav-for-arbetstillstand",
   "checked_on": "2026-10-21"
  }
 },
 "threshold_sek": 34470,
 "margin_sek": 5530,
 "margin_percent": 16.0,
 "warnings": [],
 "sources": [
  {
   "key": "mv_lonekrav",
   "title": "Migrationsverket: Lönekrav för arbetstillstånd",
   "url": "https://www.migrationsverket.se/ordforklaringar/lonekrav-for-arbetstillstand",
   "checked_on": "2026-10-21"
  }
 ],
 "disclaimer": "The salary must also be in line with the collective agreement or what is customary in the occupation or industry, which Lönekrav does not check. This is information, not legal advice."
}
```

## Eligibility, out of scope: first permit decided 31 May 2026

`POST /api/v1/eligibility` → **200**

```json
{"code": "2512", "monthly_salary_sek": 40000, "fte_percent": 100, "application_type": "first_permit", "filed_on": "2026-05-01", "decided_on": "2026-05-31"}
```

```json
{
 "status": "out_of_scope",
 "rule_id": null,
 "reason": "Lönekrav covers ordinary work permits decided under the rules in force from 1 June 2026. Earlier decisions, extensions filed before that date, EU Blue Cards, ICT permits, seasonal work and other permit types follow other rules.",
 "percent": null,
 "median": null,
 "threshold_sek": null,
 "margin_sek": null,
 "margin_percent": null,
 "warnings": [],
 "sources": [
  {
   "key": "mv_lonekrav",
   "title": "Migrationsverket: Lönekrav för arbetstillstånd",
   "url": "https://www.migrationsverket.se/ordforklaringar/lonekrav-for-arbetstillstand",
   "checked_on": "2026-10-21"
  }
 ],
 "disclaimer": "The salary must also be in line with the collective agreement or what is customary in the occupation or industry, which Lönekrav does not check. This is information, not legal advice."
}
```

## Eligibility, invalid: extension without a permit date

`POST /api/v1/eligibility` → **422**

```json
{"code": "2512", "monthly_salary_sek": 40000, "fte_percent": 100, "application_type": "extension", "filed_on": "2026-06-16", "decided_on": "2026-07-01"}
```

```json
{
 "detail": [
  {
   "type": "value_error",
   "loc": [
    "body"
   ],
   "msg": "Value error, current_permit_granted_on is required for an extension and only allowed for one",
   "input": {
    "code": "2512",
    "monthly_salary_sek": 40000,
    "fte_percent": 100,
    "application_type": "extension",
    "filed_on": "2026-06-16",
    "decided_on": "2026-07-01"
   },
   "ctx": {
    "error": {}
   }
  }
 ]
}
```

## Eligibility, unknown code

`POST /api/v1/eligibility` → **404**

```json
{"code": "1234", "monthly_salary_sek": 40000, "fte_percent": 100, "application_type": "first_permit", "filed_on": "2026-06-16", "decided_on": "2026-07-01"}
```

```json
{
 "detail": "unknown SSYK code '1234'"
}
```

## Search, fast: backend developer

`POST /api/v1/search` → **200**

```json
{"text": "backend developer"}
```

```json
{
 "mode_used": "fast",
 "fallback_reason": null,
 "searched_text": "backend developer",
 "title_list": null,
 "passages": null,
 "low_confidence": false,
 "hits": [
  {
   "code": "2512",
   "title_sv": "Mjukvaru- och systemutvecklare m.fl.",
   "title_en": "Software- and system developers",
   "scores": {
    "kblab": 0.6936643123626709,
    "bm25": 7.139098644256592
   },
   "ranks": {
    "kblab": 2,
    "bm25": 1
   },
   "fused_score": 0.021047065044949763,
   "fused_rank": 1,
   "matched_chunk": {
    "kind": "synonyms_sv",
    "text": "Produktägare, IT; Programmerare, data; Programutvecklare; Programvarukonstruktör; Programvaruutvecklare; Projektledare, IT applikationsprogrammerare; Projektledare, IT, databasutveckling; Projektledare, IT, programvaruutveckling; Projektledare, IT, systemutveckling; Projektledare, IT, webb- och multimedia; Projektledare, systemutveckling; Softwaredesigner; Systemdesigner; Systemerare; Systemkonstruktör; Systemprogrammerare; Systemtekniker, systemerare; Systemutvecklare; Systemvetare; Webbprogrammerare; Webbutvecklare; GIS-utvecklare; Backend-utvecklare; Frontend-utvecklare; gränssnittsutvecklare; utvecklare av klientdel; UI-utvecklare; designer av klientdel; gränssnittsdesigner; UI-designer; IKT-programutvecklare; programvaruprogrammerare; programmerare; programvaruingenjör; applikationsingenjör; lösningsutvecklare; programmeringsanalytiker; Projektledare, IT; IT-projektledare; projektledare inom IKT"
   },
   "legal_flags": []
  },
  {
   "code": "2513",
   "title_sv": "Utvecklare inom spel och digitala media",
   "title_en": "Games and digital media developers",
   "scores": {
    "kblab": 0.6162564754486084,
    "bm25": 5.592464447021484
   },
   "ranks": {
    "kblab": 3,
    "bm25": 2
   },
   "fused_score": 0.020711725550435225,
   "fused_rank": 2,
   "matched_chunk": {
    "kind": "synonyms_en",
    "text": "digital games developer; computer games developer; virtual games developer; video games developer; games programmer; digital games developers"
   },
   "legal_flags": []
  },
  {
   "code": "2143",
   "title_sv": "Civilingenjörsyrken inom elektroteknik",
   "title_en": "Engineering professionals in electrical, electronics and telecommunications",
   "scores": {
    "kblab": 0.7121975421905518,
    "bm25": 4.236775875091553
   },
   "ranks": {
    "kblab": 1,
    "bm25": 26
   },
   "fused_score": 0.019881814715974076,
   "fused_rank": 3,
   "matched_chunk": {
    "kind": "synonyms_sv",
    "text": "maskinvarukonstruktör"
   },
   "legal_flags": []
  },
  "… 2 more"
 ],
 "honest_fit": "The SSYK code on a work-permit offer must match the duties actually performed. These are the occupations whose official descriptions best match the text, not advice on which code to choose."
}
```

## Search, full: backend developer

`POST /api/v1/search` → **200**

```json
{"text": "backend developer", "mode": "full"}
```

```json
{
 "mode_used": "full",
 "fallback_reason": null,
 "searched_text": "backend developer",
 "title_list": null,
 "passages": null,
 "low_confidence": false,
 "hits": [
  {
   "code": "2512",
   "title_sv": "Mjukvaru- och systemutvecklare m.fl.",
   "title_en": "Software- and system developers",
   "scores": {
    "kblab": 0.6936643123626709,
    "harrier": 0.5514954328536987,
    "bm25": 7.139098644256592
   },
   "ranks": {
    "kblab": 2,
    "harrier": 2,
    "bm25": 1
   },
   "fused_score": 0.03717609730301428,
   "fused_rank": 1,
   "matched_chunk": {
    "kind": "synonyms_sv",
    "text": "Produktägare, IT; Programmerare, data; Programutvecklare; Programvarukonstruktör; Programvaruutvecklare; Projektledare, IT applikationsprogrammerare; Projektledare, IT, databasutveckling; Projektledare, IT, programvaruutveckling; Projektledare, IT, systemutveckling; Projektledare, IT, webb- och multimedia; Projektledare, systemutveckling; Softwaredesigner; Systemdesigner; Systemerare; Systemkonstruktör; Systemprogrammerare; Systemtekniker, systemerare; Systemutvecklare; Systemvetare; Webbprogrammerare; Webbutvecklare; GIS-utvecklare; Backend-utvecklare; Frontend-utvecklare; gränssnittsutvecklare; utvecklare av klientdel; UI-utvecklare; designer av klientdel; gränssnittsdesigner; UI-designer; IKT-programutvecklare; programvaruprogrammerare; programmerare; programvaruingenjör; applikationsingenjör; lösningsutvecklare; programmeringsanalytiker; Projektledare, IT; IT-projektledare; projektledare inom IKT"
   },
   "legal_flags": []
  },
  {
   "code": "2513",
   "title_sv": "Utvecklare inom spel och digitala media",
   "title_en": "Games and digital media developers",
   "scores": {
    "kblab": 0.6162564754486084,
    "harrier": 0.5051956176757812,
    "bm25": 5.592464447021484
   },
   "ranks": {
    "kblab": 3,
    "harrier": 5,
    "bm25": 2
   },
   "fused_score": 0.03609634093505061,
   "fused_rank": 2,
   "matched_chunk": {
    "kind": "synonyms_en",
    "text": "digital games developer; computer games developer; virtual games developer; video games developer; games programmer; digital games developers"
   },
   "legal_flags": []
  },
  {
   "code": "2519",
   "title_sv": "Övriga IT-specialister",
   "title_en": "ICT-specialist professionals not elsewhere classified",
   "scores": {
    "kblab": 0.5773189067840576,
    "harrier": 0.47812601923942566,
    "bm25": 4.0282392501831055
   },
   "ranks": {
    "kblab": 6,
    "harrier": 9,
    "bm25": 37
   },
   "fused_score": 0.032737052279858195,
   "fused_rank": 3,
   "matched_chunk": {
    "kind": "synonyms_sv",
    "text": "Agil coach, IT; Agile coach, IT; Datalingvist; Datastrateg; Interaktionsdesigner; IT-brottsutredare; IT-strateg; Processansvarig, ITIL; Release manager, IT; Scrum master, IT; Servicedesigner, IT; Systemexpert, IT; Systemingenjör, data; Systemman; Tjänstedesigner, IT; UX-designer; Servicedesigner/Tjänstedesigner; Servicedesigner; Tjänstedesigner; analytiker för användargränssnitt; analytiker för användarens upplevelse; användningsutvärderare; utvärderare av användarens upplevelse; användningsanalytiker; designer av användargränssnitt; ingenjör för användarförmågan; gränssnittsdesigner; hjälpmedelsdesigner; UI-designer; formgivare av intelligenta system; designer av maskininlärningssystem; AI-systemdesigner; designer av intelligenta IT-system; designer av artificiell intelligens; IKT-hjälpmedelstestare; hjälpmedelsprovare; testare av hjälpmedel; provare av hjälpmedel; IKT-användbarhetstestare; användbarhetsingenjör"
   },
   "legal_flags": []
  },
  "… 2 more"
 ],
 "honest_fit": "The SSYK code on a work-permit offer must match the duties actually performed. These are the occupations whose official descriptions best match the text, not advice on which code to choose."
}
```

## Search, fast: sjuksköterska

`POST /api/v1/search` → **200**

```json
{"text": "sjuksköterska"}
```

```json
{
 "mode_used": "fast",
 "fallback_reason": null,
 "searched_text": "sjuksköterska",
 "title_list": null,
 "passages": null,
 "low_confidence": false,
 "hits": [
  {
   "code": "2232",
   "title_sv": "Barnsjuksköterskor",
   "title_en": "Nurses - children",
   "scores": {
    "kblab": 0.8438960909843445,
    "bm25": 20.99001693725586
   },
   "ranks": {
    "kblab": 1,
    "bm25": 9
   },
   "fused_score": 0.02074126870990734,
   "fused_rank": 1,
   "matched_chunk": {
    "kind": "synonyms_sv",
    "text": "Sjuksköterska, barnavårdscentral"
   },
   "legal_flags": []
  },
  {
   "code": "2225",
   "title_sv": "Psykiatrisjuksköterskor",
   "title_en": "Psychiatry nurses",
   "scores": {
    "kblab": 0.8149264454841614,
    "bm25": 20.99001693725586
   },
   "ranks": {
    "kblab": 3,
    "bm25": 8
   },
   "fused_score": 0.020284780578898223,
   "fused_rank": 2,
   "matched_chunk": {
    "kind": "synonyms_sv",
    "text": "Sjuksköterska, psykiatrisk vård"
   },
   "legal_flags": []
  },
  {
   "code": "5324",
   "title_sv": "Undersköterskor, mottagning",
   "title_en": "Assistant nurses, clinic",
   "scores": {
    "kblab": 0.8202250003814697,
    "bm25": 6.951716423034668
   },
   "ranks": {
    "kblab": 2,
    "bm25": 19
   },
   "fused_score": 0.019926500612494895,
   "fused_rank": 3,
   "matched_chunk": {
    "kind": "synonyms_sv",
    "text": "Undersköterska/Omvårdnadsassistent, mottagning"
   },
   "legal_flags": [
    {
     "kind": "exempt_75",
     "note": "5 kap. 6 §: the 90 % requirement does not apply; 75 % of the median applies instead.",
     "effective_from": "2026-06-01",
     "source": {
      "source": "sfs",
      "ref": "SFS 2026:605, 5 kap. 6 §",
      "url": "https://svenskforfattningssamling.se/doc/2026605.html"
     },
     "checked_on": "2026-10-20"
    }
   ]
  },
  "… 2 more"
 ],
 "honest_fit": "The SSYK code on a work-permit offer must match the duties actually performed. These are the occupations whose official descriptions best match the text, not advice on which code to choose."
}
```

## Search, title list

`POST /api/v1/search` → **200**

```json
{"text": "Aktuarie/Försäkringsaktuarie/Försäkringsmatematiker", "mode": "full"}
```

```json
{
 "mode_used": "full",
 "fallback_reason": null,
 "searched_text": "Aktuarie/Försäkringsaktuarie/Försäkringsmatematiker",
 "title_list": [
  "Aktuarie",
  "Försäkringsaktuarie",
  "Försäkringsmatematiker"
 ],
 "passages": null,
 "low_confidence": false,
 "hits": [
  {
   "code": "2121",
   "title_sv": "Matematiker och aktuarier",
   "title_en": "Mathematicians and actuaries",
   "scores": {
    "kblab": 0.7170548439025879,
    "harrier": 0.7064918279647827,
    "bm25": 13.456313133239746
   },
   "ranks": {
    "kblab": 3,
    "harrier": 1,
    "bm25": 1
   },
   "fused_score": 0.037184491282851936,
   "fused_rank": 1,
   "matched_chunk": {
    "kind": "synonyms_sv",
    "text": "Aktuarie, försäkringsbolag; Kryptolog, matematiker; Livförsäkringsaktuarie; Matematiker; aktuariekonsult"
   },
   "legal_flags": []
  },
  {
   "code": "3321",
   "title_sv": "Försäkringssäljare och försäkringsrådgivare",
   "title_en": "Insurance sellers and insurance advisers",
   "scores": {
    "kblab": 0.8324375152587891,
    "harrier": 0.6795710921287537,
    "bm25": null
   },
   "ranks": {
    "kblab": 1,
    "harrier": 2,
    "bm25": null
   },
   "fused_score": 0.03252247488101534,
   "fused_rank": 2,
   "matched_chunk": {
    "kind": "title",
    "text": "Försäkringssäljare och försäkringsrådgivare / Insurance sellers and insurance advisers"
   },
   "legal_flags": []
  },
  {
   "code": "3314",
   "title_sv": "Skadereglerare och värderare",
   "title_en": "Claims assessor and valuers",
   "scores": {
    "kblab": 0.785554051399231,
    "harrier": 0.6555026769638062,
    "bm25": null
   },
   "ranks": {
    "kblab": 2,
    "harrier": 3,
    "bm25": null
   },
   "fused_score": 0.03200204813108039,
   "fused_rank": 3,
   "matched_chunk": {
    "kind": "synonyms_en",
    "text": "insurance fraud investigator; insurance policy processing worker; insurance examiners; insurance inspectors; insurance auditors; insurance fraud auditor; insurance policy processing workers; insurance fraud examiner; insurance claims handler; insurance claims assessor; claims processor; claims inspector; insurance claims processor; claims adjuster; property and casualty insurance claims examiner; claims examiner; insurance claims analyst; insurance claims examiner; insurance claims inspector; claims analyst; claims consultant; travelling insurance assessor; claims service supervisor; insurance claims officer; insurance claims consultant; claims handler; casualty insurance adjuster; claims representative; civil damages inspector; contract claims examiner; loss adjuster; vehicle damage appraiser; insurance loss adjuster; claims adjusters supervisor; damage appraiser; field appraiser; material damage appraiser; automobile claims technical adjuster; chartered loss adjuster; fire claims adjuster"
   },
   "legal_flags": []
  },
  "… 2 more"
 ],
 "honest_fit": "The SSYK code on a work-permit offer must match the duties actually performed. These are the occupations whose official descriptions best match the text, not advice on which code to choose."
}
```

## Search, nonsense

`POST /api/v1/search` → **200**

```json
{"text": "asdf"}
```

```json
{
 "mode_used": "fast",
 "fallback_reason": null,
 "searched_text": "asdf",
 "title_list": null,
 "passages": null,
 "low_confidence": true,
 "hits": [
  {
   "code": "8113",
   "title_sv": "Brunnsborrare m.fl.",
   "title_en": "Well drillers and borers and related workers",
   "scores": {
    "kblab": 0.5079922676086426,
    "bm25": null
   },
   "ranks": {
    "kblab": 1,
    "bm25": null
   },
   "fused_score": 0.01639344262295082,
   "fused_rank": 1,
   "matched_chunk": {
    "kind": "synonyms_en",
    "text": "Tourpusher"
   },
   "legal_flags": []
  },
  {
   "code": "2282",
   "title_sv": "Dietister",
   "title_en": "Dieticians",
   "scores": {
    "kblab": 0.4486052989959717,
    "bm25": null
   },
   "ranks": {
    "kblab": 2,
    "bm25": null
   },
   "fused_score": 0.016129032258064516,
   "fused_rank": 2,
   "matched_chunk": {
    "kind": "synonyms_sv",
    "text": "Dietist"
   },
   "legal_flags": []
  },
  {
   "code": "9320",
   "title_sv": "Handpaketerare och andra fabriksarbetare",
   "title_en": "Manufacturing labourers",
   "scores": {
    "kblab": 0.43584197759628296,
    "bm25": null
   },
   "ranks": {
    "kblab": 3,
    "bm25": null
   },
   "fused_score": 0.015873015873015872,
   "fused_rank": 3,
   "matched_chunk": {
    "kind": "synonyms_sv",
    "text": "Packare; orderplockare"
   },
   "legal_flags": []
  },
  "… 2 more"
 ],
 "honest_fit": "The SSYK code on a work-permit offer must match the duties actually performed. These are the occupations whose official descriptions best match the text, not advice on which code to choose."
}
```

## Search, pasted ad with parse_ad

`POST /api/v1/search` → **200**

```json
{"text": "Backend Developer (Python)\n\nAbout us\nNorthwind Ledger is a fast-growing fintech company in Stockholm. We help 4 000 small businesses get paid on time. Our team of 60 people comes from 20 countries.\n\nResponsibilities\n- Design, build and maintain the REST APIs behind our invoicing platform\n- Write well-tested Python services and review your colleagues' code\n- Improve the performance and reliability of our PostgreSQL databases\n- Take part in the on-call rotation and fix production incidents\n\nRequirements\n- At least three years of experience developing backend systems in Python\n- Good knowledge of SQL and relational databases\n- Experience with Docker and cloud platforms such as AWS\n- Fluent English; Swedish is a plus\n\nWhat we offer\n- Hybrid work with three office days a week\n- Six weeks of vacation and a wellness allowance of 5 000 SEK\n- Occupational pension and private health insurance\n", "mode": "full", "parse_ad": true}
```

```json
{
 "mode_used": "full",
 "fallback_reason": null,
 "searched_text": "Backend Developer (Python)\nDesign, build and maintain the REST APIs behind our invoicing platform\nWrite well-tested Python services and review your colleagues' code\nImprove the performance and reliability of our PostgreSQL databases\nTake part in the on-call rotation and fix production incidents\nAt least three years of experience developing backend systems in Python\nGood knowledge of SQL and relational databases\nExperience with Docker and cloud platforms such as AWS\nFluent English; Swedish is a plus",
 "title_list": null,
 "passages": [
  {
   "index": 0,
   "text": "Backend Developer (Python)",
   "label": "title",
   "keep": true,
   "by": "position"
  },
  {
   "index": 1,
   "text": "Northwind Ledger is a fast-growing fintech company in Stockholm.",
   "label": "company",
   "keep": false,
   "by": "heading"
  },
  {
   "index": 2,
   "text": "We help 4 000 small businesses get paid on time.",
   "label": "company",
   "keep": false,
   "by": "heading"
  },
  "… 12 more"
 ],
 "low_confidence": false,
 "hits": [
  {
   "code": "2512",
   "title_sv": "Mjukvaru- och systemutvecklare m.fl.",
   "title_en": "Software- and system developers",
   "scores": {
    "kblab": 0.5985780954360962,
    "harrier": 0.5412302017211914,
    "bm25": 78.03857421875
   },
   "ranks": {
    "kblab": 1,
    "harrier": 1,
    "bm25": 2
   },
   "fused_score": 0.037625594923320994,
   "fused_rank": 1,
   "matched_chunk": {
    "kind": "synonyms_en",
    "text": "database designers; data base designers; database architect; data base designer; database design engineer; data model designer; software developer; application programmer; solutions developer; programmer; software specialist; application software developer; software developers; software engineer; applications engineer; soft developer; developer of software; database integrator; data base integrators; data base integrator; database integrators; data integrator; database development specialist; data warehouse designer; data warehouse architect; data warehouse developer; ICT system architect; ICT systems architect; solution architect; IT systems architect; IT system architect; systems architect; ICT system architects; ICT systems architects; information systems architect; mobile application developer; app developer; mobile app specialist; mobile app developer; mobile application developers"
   },
   "legal_flags": []
  },
  {
   "code": "3513",
   "title_sv": "Systemadministratörer",
   "title_en": "System administrators",
   "scores": {
    "kblab": 0.5628695487976074,
    "harrier": 0.5401063561439514,
    "bm25": 63.028892517089844
   },
   "ranks": {
    "kblab": 3,
    "harrier": 2,
    "bm25": 3
   },
   "fused_score": 0.03676395289298515,
   "fused_rank": 2,
   "matched_chunk": {
    "kind": "desc_en",
    "text": "(a)  designing and developing database architecture, data structures, tables, dictionaries and naming conventions for information systems projects; (b)  designing, constructing, modifying, integrating, implementing and testing database management systems; (c)  conducting research and providing advice on the selection, application and implementation of database management tools; (d)  developing and implementing data administration policy, documentation, standards and models; (e)  developing policies and procedures for database access and usage and for the backup and recovery of data; (f)  performing the operational establishment and preventive maintenance of backups, recovery procedures, and enforcing security and integrity controls."
   },
   "legal_flags": [
    {
     "kind": "exempt_75",
     "note": "5 kap. 6 §: the 90 % requirement does not apply; 75 % of the median applies instead.",
     "effective_from": "2026-06-01",
     "source": {
      "source": "sfs",
      "ref": "SFS 2026:605, 5 kap. 6 §",
      "url": "https://svenskforfattningssamling.se/doc/2026605.html"
     },
     "checked_on": "2026-10-20"
    }
   ]
  },
  {
   "code": "2519",
   "title_sv": "Övriga IT-specialister",
   "title_en": "ICT-specialist professionals not elsewhere classified",
   "scores": {
    "kblab": 0.5564047694206238,
    "harrier": 0.4986022710800171,
    "bm25": 79.67957305908203
   },
   "ranks": {
    "kblab": 4,
    "harrier": 8,
    "bm25": 1
   },
   "fused_score": 0.03524891513982642,
   "fused_rank": 3,
   "matched_chunk": {
    "kind": "desc_en",
    "text": "User experience analysts assess client interaction and experience and analyse users' behaviours, attitudes, and emotions about the usage of a particular product, system or service. They make proposals for the improvement of the interface and usability of products, systems or services. In doing so, they take into consideration the practical, experiential, affective, meaningful and valuable aspects of human–computer interaction and product ownership, as well as the person's perceptions of system aspects such as utility, ease of use and efficiency, and user experience dynamics."
   },
   "legal_flags": []
  },
  "… 2 more"
 ],
 "honest_fit": "The SSYK code on a work-permit offer must match the duties actually performed. These are the occupations whose official descriptions best match the text, not advice on which code to choose."
}
```

## Parse a job ad

`POST /api/v1/parse-job-ad` → **200**

```json
{"text": "Backend Developer (Python)\n\nAbout us\nNorthwind Ledger is a fast-growing fintech company in Stockholm. We help 4 000 small businesses get paid on time. Our team of 60 people comes from 20 countries.\n\nResponsibilities\n- Design, build and maintain the REST APIs behind our invoicing platform\n- Write well-tested Python services and review your colleagues' code\n- Improve the performance and reliability of our PostgreSQL databases\n- Take part in the on-call rotation and fix production incidents\n\nRequirements\n- At least three years of experience developing backend systems in Python\n- Good knowledge of SQL and relational databases\n- Experience with Docker and cloud platforms such as AWS\n- Fluent English; Swedish is a plus\n\nWhat we offer\n- Hybrid work with three office days a week\n- Six weeks of vacation and a wellness allowance of 5 000 SEK\n- Occupational pension and private health insurance\n"}
```

```json
{
 "passages": [
  {
   "index": 0,
   "text": "Backend Developer (Python)",
   "label": "title",
   "keep": true,
   "by": "position"
  },
  {
   "index": 1,
   "text": "Northwind Ledger is a fast-growing fintech company in Stockholm.",
   "label": "company",
   "keep": false,
   "by": "heading"
  },
  {
   "index": 2,
   "text": "We help 4 000 small businesses get paid on time.",
   "label": "company",
   "keep": false,
   "by": "heading"
  },
  "… 12 more"
 ],
 "kept_text": "Backend Developer (Python)\nDesign, build and maintain the REST APIs behind our invoicing platform\nWrite well-tested Python services and review your colleagues' code\nImprove the performance and reliability of our PostgreSQL databases\nTake part in the on-call rotation and fix production incidents\nAt least three years of experience developing backend systems in Python\nGood knowledge of SQL and relational databases\nExperience with Docker and cloud platforms such as AWS\nFluent English; Swedish is a plus",
 "fallback_to_whole": false
}
```

## Occupation 3511

`GET /api/v1/occupations/3511` → **200**

```json
{
 "code": "3511",
 "title_sv": "Drifttekniker, IT",
 "title_en": "ICT operations technicians",
 "isco_codes": [
  "3511",
  "3513"
 ],
 "jobtech_concept_id": "13md_uyV_BNG",
 "jobtech_shared": false,
 "descriptions": [
  {
   "lang": "sv",
   "kind": "definition",
   "text": "Sköter daglig drift av informations- och kommunikationssystem, kringutrustning, maskinvara, programvara och annan datorutrustning för att identifiera och förebygga fel och driftstörningar.",
   "source": {
    "source": "jobtech",
    "ref": "taxonomy ssyk-level-4",
    "url": "https://taxonomy.api.jobtechdev.se/v1/taxonomy/graphql"
   },
   "isco_code": null,
   "shared_with": []
  },
  {
   "lang": "en",
   "kind": "definition",
   "text": "ICT technicians install, maintain, repair and operate information systems and any ICT related equipment (laptops, desktops, servers, tablets, smart phones, communications equipment, printers and any piece of computer related peripheral networks), and any type of software (drivers, operating systems, applications).",
   "source": {
    "source": "esco",
    "ref": "http://data.europa.eu/esco/occupation/3e7bf729-4442-4b9f-ad5e-83111963795c",
    "url": "http://data.europa.eu/esco/occupation/3e7bf729-4442-4b9f-ad5e-83111963795c"
   },
   "isco_code": null,
   "shared_with": []
  },
  {
   "lang": "sv",
   "kind": "definition",
   "text": "IT-tekniker installerar, utför underhåll på, reparerar och hanterar informationssystem och all IKT-relaterad utrustning (bärbara datorer, stationära datorer, servrar, surfplattor, smarttelefoner, kommunikationsutrustning, skrivare och alla typer av datorrelaterade perifera nätverk) samt alla typer av programvara (drivrutiner, operativsystem, applikationer).",
   "source": {
    "source": "esco",
    "ref": "http://data.europa.eu/esco/occupation/3e7bf729-4442-4b9f-ad5e-83111963795c",
    "url": "http://data.europa.eu/esco/occupation/3e7bf729-4442-4b9f-ad5e-83111963795c"
   },
   "isco_code": null,
   "shared_with": []
  },
  "… 4 more"
 ],
 "synonyms": [
  {
   "lang": "sv",
   "label": "Dataansvarig, datatekniker",
   "source": {
    "source": "scb_title_index",
    "ref": "ssyk_index_webb_2026.xlsx",
    "url": "https://www.scb.se/contentassets/0c0089cc085a45d49c1dc83923ad933a/ssyk_index_webb_2026.xlsx"
   },
   "jobtech_id": null,
   "esco_uri": null,
   "match_type": null
  },
  {
   "lang": "sv",
   "label": "Datasamordnare, datatekniker",
   "source": {
    "source": "scb_title_index",
    "ref": "ssyk_index_webb_2026.xlsx",
    "url": "https://www.scb.se/contentassets/0c0089cc085a45d49c1dc83923ad933a/ssyk_index_webb_2026.xlsx"
   },
   "jobtech_id": null,
   "esco_uri": null,
   "match_type": null
  },
  {
   "lang": "sv",
   "label": "Datatekniker, drift",
   "source": {
    "source": "scb_title_index",
    "ref": "ssyk_index_webb_2026.xlsx",
    "url": "https://www.scb.se/contentassets/0c0089cc085a45d49c1dc83923ad933a/ssyk_index_webb_2026.xlsx"
   },
   "jobtech_id": null,
   "esco_uri": null,
   "match_type": null
  },
  "… 38 more"
 ],
 "legal_flags": [
  {
   "kind": "exempt_75",
   "note": "5 kap. 6 §: the 90 % requirement does not apply; 75 % of the median applies instead.",
   "effective_from": "2026-06-01",
   "source": {
    "source": "sfs",
    "ref": "SFS 2026:605, 5 kap. 6 §",
    "url": "https://svenskforfattningssamling.se/doc/2026605.html"
   },
   "checked_on": "2026-10-20"
  }
 ],
 "sources": [
  {
   "source": "scb_structure",
   "ref": "ssyk-2012-koder.xlsx",
   "url": "https://www.scb.se/contentassets/0c0089cc085a45d49c1dc83923ad933a/ssyk-2012-koder.xlsx"
  },
  {
   "source": "scb_english",
   "ref": "structur_english_ssyk2012_1_4.xlsx",
   "url": "https://www.scb.se/contentassets/0c0089cc085a45d49c1dc83923ad933a/structur_english_ssyk2012_1_4.xlsx"
  },
  {
   "source": "jobtech",
   "ref": "taxonomy ssyk-level-4",
   "url": "https://taxonomy.api.jobtechdev.se/v1/taxonomy/graphql"
  },
  "… 5 more"
 ]
}
```

## Salary for 2512 with the 25–34 age band

`GET /api/v1/occupations/2512/salary?age_band=25-34&on=2026-10-21` → **200**

```json
{
 "code": "2512",
 "title_sv": "Mjukvaru- och systemutvecklare m.fl.",
 "title_en": "Software- and system developers",
 "distributions": [
  {
   "code": "2512",
   "year": 2014,
   "mean": 41200,
   "median": 40000,
   "p10": 28100,
   "p25": 33300,
   "p75": 47000,
   "p90": 55000,
   "mean_ci95": null,
   "median_ci95": null,
   "p10_ci95": null,
   "p25_ci95": null,
   "p75_ci95": null,
   "p90_ci95": null,
   "source_table": "TAB4265",
   "reference_year": 2014,
   "fetched_at": "2026-10-20T20:54:47.713753Z",
   "suppressed": []
  },
  {
   "code": "2512",
   "year": 2015,
   "mean": 41800,
   "median": 40100,
   "p10": 29100,
   "p25": 34400,
   "p75": 46900,
   "p90": 55000,
   "mean_ci95": null,
   "median_ci95": null,
   "p10_ci95": null,
   "p25_ci95": null,
   "p75_ci95": null,
   "p90_ci95": null,
   "source_table": "TAB4265",
   "reference_year": 2015,
   "fetched_at": "2026-10-20T20:54:47.713753Z",
   "suppressed": []
  },
  {
   "code": "2512",
   "year": 2016,
   "mean": 43200,
   "median": 41900,
   "p10": 29700,
   "p25": 35000,
   "p75": 49800,
   "p90": 57900,
   "mean_ci95": null,
   "median_ci95": null,
   "p10_ci95": null,
   "p25_ci95": null,
   "p75_ci95": null,
   "p90_ci95": null,
   "source_table": "TAB4265",
   "reference_year": 2016,
   "fetched_at": "2026-10-20T20:54:47.713753Z",
   "suppressed": []
  },
  "… 9 more"
 ],
 "age_bands": [
  {
   "code": "2512",
   "year": 2025,
   "age_band": "18-24",
   "mean_monthly": 36100,
   "headcount": null,
   "mean_ci95": 1800,
   "source_table": "TAB5844",
   "reference_year": 2025,
   "fetched_at": "2026-10-20T20:55:37.497460Z",
   "suppressed": [
    "headcount"
   ]
  },
  {
   "code": "2512",
   "year": 2025,
   "age_band": "25-34",
   "mean_monthly": 49300,
   "headcount": 35500,
   "mean_ci95": 1030,
   "source_table": "TAB5844",
   "reference_year": 2025,
   "fetched_at": "2026-10-20T20:55:37.497460Z",
   "suppressed": []
  },
  {
   "code": "2512",
   "year": 2025,
   "age_band": "35-44",
   "mean_monthly": 56600,
   "headcount": 36000,
   "mean_ci95": 1140,
   "source_table": "TAB5844",
   "reference_year": 2025,
   "fetched_at": "2026-10-20T20:55:37.497460Z",
   "suppressed": []
  },
  "… 4 more"
 ],
 "thresholds": [
  {
   "rule_id": "salary_90",
   "percent": 90.0,
   "amount_sek": 34470,
   "median_sek": 38300,
   "median_reference_year": 2025,
   "on": "2026-10-21"
  },
  {
   "rule_id": "salary_75_exempt",
   "percent": 75.0,
   "amount_sek": 28725,
   "median_sek": 38300,
   "median_reference_year": 2025,
   "on": "2026-10-21"
  }
 ],
 "applicable_rule_id": "salary_90",
 "simulated": {
  "age_band": "25-34",
  "year": 2025,
  "p10": 35176,
  "p25": 41039,
  "median": 47523,
  "p75": 55607,
  "p90": 64490,
  "is_simulated": true,
  "formula": "percentile × age_band_mean ÷ all_ages_mean",
  "inputs": [
   {
    "table": "TAB5932",
    "reference_year": 2025
   },
   {
    "table": "TAB5844",
    "reference_year": 2025
   }
  ]
 },
 "no_occupation_data": false
}
```

## Compare 2512, 2511 and 3512 with an offer

`POST /api/v1/compare` → **200**

```json
{"codes": ["2512", "2511", "3512"], "offer": {"monthly_salary_sek": 40000, "fte_percent": 100, "application_type": "first_permit", "filed_on": "2026-06-16", "decided_on": "2026-07-01"}}
```

```json
{
 "columns": [
  {
   "code": "2512",
   "title_sv": "Mjukvaru- och systemutvecklare m.fl.",
   "title_en": "Software- and system developers",
   "tasks_sv": [
    {
     "lang": "sv",
     "kind": "definition",
     "text": "Analyserar, designar och utvecklar IT-system eller delar av system. Utformar och utvecklar lösningar för programvara, applikationer, system och databaser.",
     "source": {
      "source": "jobtech",
      "ref": "taxonomy ssyk-level-4",
      "url": "https://taxonomy.api.jobtechdev.se/v1/taxonomy/graphql"
     },
     "isco_code": null,
     "shared_with": []
    }
   ],
   "tasks_en": [
    {
     "lang": "en",
     "kind": "definition",
     "text": "User interface developers implement, code, document and maintain the interface of a software system by using front-end development technologies.",
     "source": {
      "source": "esco",
      "ref": "http://data.europa.eu/esco/occupation/866c7813-2c03-47d7-9bdc-192cfbace57c",
      "url": "http://data.europa.eu/esco/occupation/866c7813-2c03-47d7-9bdc-192cfbace57c"
     },
     "isco_code": null,
     "shared_with": []
    },
    {
     "lang": "en",
     "kind": "definition",
     "text": "ICT application developers implement the ICT (software) applications based on the designs provided using application domain specific languages, tools, platforms and experience.",
     "source": {
      "source": "esco",
      "ref": "http://data.europa.eu/esco/occupation/bd272aee-adc9-4a06-a15c-a73b4b4a46a7",
      "url": "http://data.europa.eu/esco/occupation/bd272aee-adc9-4a06-a15c-a73b4b4a46a7"
     },
     "isco_code": null,
     "shared_with": []
    },
    {
     "lang": "en",
     "kind": "definition",
     "text": "ICT project managers schedule, control and direct the resources, people, funding and facilities to achieve the objectives of ICT projects. They establish budgets and timelines, perform risk analysis and quality management, and complete project closure reports.",
     "source": {
      "source": "esco",
      "ref": "http://data.europa.eu/esco/occupation/8b6388a4-4904-471b-9331-d3b1211f5525",
      "url": "http://data.europa.eu/esco/occupation/8b6388a4-4904-471b-9331-d3b1211f5525"
     },
     "isco_code": null,
     "shared_with": []
    },
    "… 8 more"
   ],
   "latest": {
    "code": "2512",
    "year": 2025,
    "mean": 55500,
    "median": 53500,
    "p10": 39600,
    "p25": 46200,
    "p75": 62600,
    "p90": 72600,
    "mean_ci95": 940,
    "median_ci95": 880,
    "p10_ci95": 1080,
    "p25_ci95": 970,
    "p75_ci95": 1160,
    "p90_ci95": 1340,
    "source_table": "TAB5932",
    "reference_year": 2025,
    "fetched_at": "2026-10-20T20:54:49.024907Z",
    "suppressed": []
   },
   "legal_flags": [],
   "threshold": {
    "rule_id": "salary_90",
    "percent": 90.0,
    "amount_sek": 34470,
    "median_sek": 38300,
    "median_reference_year": 2025,
    "on": "2026-06-16"
   },
   "eligibility": {
    "status": "pass",
    "rule_id": "salary_90",
    "reason": "Salary requirement for first permits decided from 1 June 2026 and for extensions not covered by the transition: at least 90 % of the median in force when the application was filed.",
    "percent": 90.0,
    "median": {
     "amount": 38300,
     "scb_reference_year": 2025,
     "effective_from": "2026-06-16",
     "effective_to": null,
     "source": {
      "key": "mv_lonekrav",
      "title": "Migrationsverket: Lönekrav för arbetstillstånd",
      "url": "https://www.migrationsverket.se/ordforklaringar/lonekrav-for-arbetstillstand",
      "checked_on": "2026-10-21"
     }
    },
    "threshold_sek": 34470,
    "margin_sek": 5530,
    "margin_percent": 16.0,
    "warnings": [],
    "sources": [
     {
      "key": "mv_lonekrav",
      "title": "Migrationsverket: Lönekrav för arbetstillstånd",
      "url": "https://www.migrationsverket.se/ordforklaringar/lonekrav-for-arbetstillstand",
      "checked_on": "2026-10-21"
     }
    ],
    "disclaimer": "The salary must also be in line with the collective agreement or what is customary in the occupation or industry, which Lönekrav does not check. This is information, not legal advice."
   }
  },
  {
   "code": "2511",
   "title_sv": "Systemanalytiker och IT-arkitekter m.fl.",
   "title_en": "System analysts and ICT-architects",
   "tasks_sv": [
    {
     "lang": "sv",
     "kind": "definition",
     "text": "Tar fram strategier för utveckling av IT-system. Ansvarar för företags och organisationers IT-struktur och ser till att IT används på ett effektivt sätt. Ansvarar för att den tekniska arkitekturen understödjer verksamhetens behov och krav.",
     "source": {
      "source": "jobtech",
      "ref": "taxonomy ssyk-level-4",
      "url": "https://taxonomy.api.jobtechdev.se/v1/taxonomy/graphql"
     },
     "isco_code": null,
     "shared_with": []
    }
   ],
   "tasks_en": [
    {
     "lang": "en",
     "kind": "definition",
     "text": "ICT system analysts specify the system needs to meet the end user requirements. They analyse system functions in order to define their goals or purposes and to discover operations and procedures for accomplishing them most efficiently. They also design new IT solutions to improve business efficiency and productivity, produce outline designs and estimate costs of new systems, specify the operations the system will perform, and the way data will be viewed by the end user. They present the design to the users and work closely with the users to implement the solution.",
     "source": {
      "source": "esco",
      "ref": "http://data.europa.eu/esco/occupation/a6a0b60f-08da-4faa-bf54-942987efb471",
      "url": "http://data.europa.eu/esco/occupation/a6a0b60f-08da-4faa-bf54-942987efb471"
     },
     "isco_code": null,
     "shared_with": []
    },
    {
     "lang": "en",
     "kind": "definition",
     "text": "ICT business analysts are in charge of analysing and designing an organisation's processes and systems, assessing the business model and its integration with technology. They also identify change needs, assess the impact of the change, capture and document requirements and then ensure that these requirements are delivered whilst supporting the business through the implementation process.",
     "source": {
      "source": "esco",
      "ref": "http://data.europa.eu/esco/occupation/fe0fa514-b48d-4a53-9757-a283c0baacf0",
      "url": "http://data.europa.eu/esco/occupation/fe0fa514-b48d-4a53-9757-a283c0baacf0"
     },
     "isco_code": null,
     "shared_with": []
    },
    {
     "lang": "en",
     "kind": "definition",
     "text": "IT auditors perform audits of information systems, platforms, and operating procedures in accordance with established corporate standards for efficiency, accuracy and security. They evaluate ICT infrastructure in terms of risk to the organisation and establish controls to mitigate loss. They determine and recommend improvements in the current risk management controls and in the implementation of system changes or upgrades.",
     "source": {
      "source": "esco",
      "ref": "http://data.europa.eu/esco/occupation/cdd3d773-75a4-4f35-bd1d-1ac720afcf9d",
      "url": "http://data.europa.eu/esco/occupation/cdd3d773-75a4-4f35-bd1d-1ac720afcf9d"
     },
     "isco_code": null,
     "shared_with": []
    },
    "… 17 more"
   ],
   "latest": {
    "code": "2511",
    "year": 2025,
    "mean": 58500,
    "median": 56200,
    "p10": 41000,
    "p25": 47700,
    "p75": 66700,
    "p90": 77800,
    "mean_ci95": 590,
    "median_ci95": 790,
    "p10_ci95": 490,
    "p25_ci95": 1020,
    "p75_ci95": 1240,
    "p90_ci95": 1480,
    "source_table": "TAB5932",
    "reference_year": 2025,
    "fetched_at": "2026-10-20T20:54:49.024907Z",
    "suppressed": []
   },
   "legal_flags": [],
   "threshold": {
    "rule_id": "salary_90",
    "percent": 90.0,
    "amount_sek": 34470,
    "median_sek": 38300,
    "median_reference_year": 2025,
    "on": "2026-06-16"
   },
   "eligibility": {
    "status": "pass",
    "rule_id": "salary_90",
    "reason": "Salary requirement for first permits decided from 1 June 2026 and for extensions not covered by the transition: at least 90 % of the median in force when the application was filed.",
    "percent": 90.0,
    "median": {
     "amount": 38300,
     "scb_reference_year": 2025,
     "effective_from": "2026-06-16",
     "effective_to": null,
     "source": {
      "key": "mv_lonekrav",
      "title": "Migrationsverket: Lönekrav för arbetstillstånd",
      "url": "https://www.migrationsverket.se/ordforklaringar/lonekrav-for-arbetstillstand",
      "checked_on": "2026-10-21"
     }
    },
    "threshold_sek": 34470,
    "margin_sek": 5530,
    "margin_percent": 16.0,
    "warnings": [],
    "sources": [
     {
      "key": "mv_lonekrav",
      "title": "Migrationsverket: Lönekrav för arbetstillstånd",
      "url": "https://www.migrationsverket.se/ordforklaringar/lonekrav-for-arbetstillstand",
      "checked_on": "2026-10-21"
     }
    ],
    "disclaimer": "The salary must also be in line with the collective agreement or what is customary in the occupation or industry, which Lönekrav does not check. This is information, not legal advice."
   }
  },
  {
   "code": "3512",
   "title_sv": "Supporttekniker, IT",
   "title_en": "ICT support technicians",
   "tasks_sv": [
    {
     "lang": "sv",
     "kind": "definition",
     "text": "Ger teknisk support. Genomför felsökningar, analyserar och åtgärdar uppkomna fel. Ger service och support i samband med installation och underhåll av system. Löser problem som uppstår t.ex. med användares lösenord.",
     "source": {
      "source": "jobtech",
      "ref": "taxonomy ssyk-level-4",
      "url": "https://taxonomy.api.jobtechdev.se/v1/taxonomy/graphql"
     },
     "isco_code": null,
     "shared_with": []
    }
   ],
   "tasks_en": [
    {
     "lang": "en",
     "kind": "definition",
     "text": "ICT help desk agents provide technical assistance to computer users, answer questions or solve computer problems for clients via telephone or electronically. They provide assistance concerning the use of computer hardware and software.",
     "source": {
      "source": "esco",
      "ref": "http://data.europa.eu/esco/occupation/aaeec9a7-dc57-4485-890c-86b3eef735f9",
      "url": "http://data.europa.eu/esco/occupation/aaeec9a7-dc57-4485-890c-86b3eef735f9"
     },
     "isco_code": null,
     "shared_with": []
    }
   ],
   "latest": {
    "code": "3512",
    "year": 2025,
    "mean": 40600,
    "median": 38500,
    "p10": 28300,
    "p25": 32900,
    "p75": 46200,
    "p90": 55000,
    "mean_ci95": 1000,
    "median_ci95": 1100,
    "p10_ci95": 820,
    "p25_ci95": 1080,
    "p75_ci95": 1300,
    "p90_ci95": 1490,
    "source_table": "TAB5932",
    "reference_year": 2025,
    "fetched_at": "2026-10-20T20:54:49.024907Z",
    "suppressed": []
   },
   "legal_flags": [
    {
     "kind": "exempt_75",
     "note": "5 kap. 6 §: the 90 % requirement does not apply; 75 % of the median applies instead.",
     "effective_from": "2026-06-01",
     "source": {
      "source": "sfs",
      "ref": "SFS 2026:605, 5 kap. 6 §",
      "url": "https://svenskforfattningssamling.se/doc/2026605.html"
     },
     "checked_on": "2026-10-20"
    }
   ],
   "threshold": {
    "rule_id": "salary_75_exempt",
    "percent": 75.0,
    "amount_sek": 28725,
    "median_sek": 38300,
    "median_reference_year": 2025,
    "on": "2026-06-16"
   },
   "eligibility": {
    "status": "pass",
    "rule_id": "salary_75_exempt",
    "reason": "Occupation 3512 is on the exempt list. 5 kap. 6 §: the 90 % requirement does not apply; 75 % of the median applies instead.",
    "percent": 75.0,
    "median": {
     "amount": 38300,
     "scb_reference_year": 2025,
     "effective_from": "2026-06-16",
     "effective_to": null,
     "source": {
      "key": "mv_lonekrav",
      "title": "Migrationsverket: Lönekrav för arbetstillstånd",
      "url": "https://www.migrationsverket.se/ordforklaringar/lonekrav-for-arbetstillstand",
      "checked_on": "2026-10-21"
     }
    },
    "threshold_sek": 28725,
    "margin_sek": 11275,
    "margin_percent": 39.3,
    "warnings": [],
    "sources": [
     {
      "key": "mv_lonekrav",
      "title": "Migrationsverket: Lönekrav för arbetstillstånd",
      "url": "https://www.migrationsverket.se/ordforklaringar/lonekrav-for-arbetstillstand",
      "checked_on": "2026-10-21"
     },
     {
      "key": "sfs_2026_605",
      "title": "SFS 2026:605, utlänningsförordningen 5 kap. 5–6 §§",
      "url": "https://svenskforfattningssamling.se/doc/2026605.html",
      "checked_on": "2026-10-20"
     }
    ],
    "disclaimer": "The salary must also be in line with the collective agreement or what is customary in the occupation or industry, which Lönekrav does not check. This is information, not legal advice."
   }
  }
 ],
 "honest_fit": "The SSYK code on a work-permit offer must match the duties actually performed. These are the occupations whose official descriptions best match the text, not advice on which code to choose."
}
```

## Compare, one code only

`POST /api/v1/compare` → **422**

```json
{"codes": ["2512"]}
```

```json
{
 "detail": [
  {
   "type": "value_error",
   "loc": [
    "body",
    "codes"
   ],
   "msg": "Value error, codes: give 2–5 distinct codes, got 1",
   "input": [
    "2512"
   ],
   "ctx": {
    "error": {}
   }
  }
 ]
}
```

## Legal timeline

`GET /api/v1/legal/timeline` → **200**

```json
[
 {
  "date": "2021-06-22",
  "kind": "median",
  "summary": "Median 32 400 SEK (SCB 2020) applies to applications filed from this day",
  "source": {
   "key": "mv_lonekrav",
   "title": "Migrationsverket: Lönekrav för arbetstillstånd",
   "url": "https://www.migrationsverket.se/ordforklaringar/lonekrav-for-arbetstillstand",
   "checked_on": "2026-10-21"
  }
 },
 {
  "date": "2022-06-21",
  "kind": "median",
  "summary": "Median 33 200 SEK (SCB 2021) applies to applications filed from this day",
  "source": {
   "key": "mv_lonekrav",
   "title": "Migrationsverket: Lönekrav för arbetstillstånd",
   "url": "https://www.migrationsverket.se/ordforklaringar/lonekrav-for-arbetstillstand",
   "checked_on": "2026-10-21"
  }
 },
 {
  "date": "2023-06-20",
  "kind": "median",
  "summary": "Median 34 200 SEK (SCB 2022) applies to applications filed from this day",
  "source": {
   "key": "mv_lonekrav",
   "title": "Migrationsverket: Lönekrav för arbetstillstånd",
   "url": "https://www.migrationsverket.se/ordforklaringar/lonekrav-for-arbetstillstand",
   "checked_on": "2026-10-21"
  }
 },
 "… 13 more"
]
```

## Benchmark results

`GET /api/v1/benchmark` → **200**

```json
{
 "run_at": "2026-10-21T20:19:09+00:00",
 "models": {
  "kblab": "KBLab/sentence-bert-swedish-cased@6b5e83cd29c0",
  "harrier": "microsoft/harrier-oss-v1-0.6b@f9b9dc8d367d"
 },
 "n_queries": {
  "handwritten": 32,
  "generated": 333,
  "generated_with_english": 152
 },
 "metrics": {
  "kblab": {
   "en": {
    "handwritten": {
     "recall_at_1": 0.53125,
     "recall_at_5": 0.96875,
     "mrr": 0.7274305555555556,
     "n": 32
    },
    "all_paired": {
     "recall_at_1": 0.5380434782608695,
     "recall_at_5": 0.8695652173913043,
     "mrr": 0.68261516563147,
     "n": 184
    },
    "generated": {
     "recall_at_1": 0.5394736842105263,
     "recall_at_5": 0.8486842105263158,
     "mrr": 0.6731803467000835,
     "n": 152
    }
   },
   "sv": {
    "handwritten": {
     "recall_at_1": 0.65625,
     "recall_at_5": 0.96875,
     "mrr": 0.7864583333333334,
     "n": 32
    },
    "all_paired": {
     "recall_at_1": 0.5760869565217391,
     "recall_at_5": 0.8260869565217391,
     "mrr": 0.6754528985507247,
     "n": 184
    },
    "generated_sv_only": {
     "recall_at_1": 0.2983425414364641,
     "recall_at_5": 0.6298342541436464,
     "mrr": 0.43820485837060424,
     "n": 181
    },
    "generated": {
     "recall_at_1": 0.5592105263157895,
     "recall_at_5": 0.7960526315789473,
     "mrr": 0.6520833333333332,
     "n": 152
    }
   }
  },
  "harrier": {
   "en": {
    "handwritten": {
     "recall_at_1": 0.625,
     "recall_at_5": 0.96875,
     "mrr": 0.7533854166666667,
     "n": 32
    },
    "all_paired": {
     "recall_at_1": 0.7065217391304348,
     "recall_at_5": 0.9239130434782609,
     "mrr": 0.7980719461697723,
     "n": 184
    },
    "generated": {
     "recall_at_1": 0.7236842105263158,
     "recall_at_5": 0.9144736842105263,
     "mrr": 0.8074796365914787,
     "n": 152
    }
   },
   "sv": {
    "handwritten": {
     "recall_at_1": 0.625,
     "recall_at_5": 0.96875,
     "mrr": 0.7471354166666667,
     "n": 32
    },
    "all_paired": {
     "recall_at_1": 0.6793478260869565,
     "recall_at_5": 0.9130434782608695,
     "mrr": 0.7777691511387164,
     "n": 184
    },
    "generated_sv_only": {
     "recall_at_1": 0.4198895027624309,
     "recall_at_5": 0.7292817679558011,
     "mrr": 0.5479829869332632,
     "n": 181
    },
    "generated": {
     "recall_at_1": 0.6907894736842105,
     "recall_at_5": 0.9013157894736842,
     "mrr": 0.78421835839599,
     "n": 152
    }
   }
  },
  "bm25": {
   "en": {
    "handwritten": {
     "recall_at_1": 0.46875,
     "recall_at_5": 0.875,
     "mrr": 0.6033854166666667,
     "n": 32
    },
    "all_paired": {
     "recall_at_1": 0.6413043478260869,
     "recall_at_5": 0.8478260869565217,
     "mrr": 0.7257009144237405,
     "n": 184
    },
    "generated": {
     "recall_at_1": 0.6776315789473685,
     "recall_at_5": 0.8421052631578947,
     "mrr": 0.7514515455304929,
     "n": 152
    }
   },
   "sv": {
    "handwritten": {
     "recall_at_1": 0.34375,
     "recall_at_5": 0.625,
     "mrr": 0.47369791666666666,
     "n": 32
    },
    "all_paired": {
     "recall_at_1": 0.40217391304347827,
     "recall_at_5": 0.5597826086956522,
     "mrr": 0.47613871635610766,
     "n": 184
    },
    "generated_sv_only": {
     "recall_at_1": 0.292817679558011,
     "recall_at_5": 0.4088397790055249,
     "mrr": 0.34308515302990444,
     "n": 181
    },
    "generated": {
     "recall_at_1": 0.4144736842105263,
     "recall_at_5": 0.5460526315789473,
     "mrr": 0.4766525689223058,
     "n": 152
    }
   }
  },
  "fused": {
   "en": {
    "handwritten": {
     "recall_at_1": 0.75,
     "recall_at_5": 1.0,
     "mrr": 0.8645833333333334,
     "n": 32
    },
    "all_paired": {
     "recall_at_1": 0.7391304347826086,
     "recall_at_5": 0.9402173913043478,
     "mrr": 0.822403381642512,
     "n": 184
    },
    "generated": {
     "recall_at_1": 0.7368421052631579,
     "recall_at_5": 0.9276315789473685,
     "mrr": 0.8135233918128655,
     "n": 152
    }
   },
   "sv": {
    "handwritten": {
     "recall_at_1": 0.75,
     "recall_at_5": 1.0,
     "mrr": 0.8447916666666667,
     "n": 32
    },
    "all_paired": {
     "recall_at_1": 0.7010869565217391,
     "recall_at_5": 0.9347826086956522,
     "mrr": 0.7955314009661835,
     "n": 184
    },
    "generated_sv_only": {
     "recall_at_1": 0.40331491712707185,
     "recall_at_5": 0.7292817679558011,
     "mrr": 0.5506818381127774,
     "n": 181
    },
    "generated": {
     "recall_at_1": 0.6907894736842105,
     "recall_at_5": 0.9210526315789473,
     "mrr": 0.7851608187134503,
     "n": 152
    }
   }
  },
  "fused_fast": {
   "en": {
    "handwritten": {
     "recall_at_1": 0.625,
     "recall_at_5": 0.96875,
     "mrr": 0.7747395833333334,
     "n": 32
    },
    "all_paired": {
     "recall_at_1": 0.6358695652173914,
     "recall_at_5": 0.8967391304347826,
     "mrr": 0.746268978605935,
     "n": 184
    },
    "generated": {
     "recall_at_1": 0.6381578947368421,
     "recall_at_5": 0.881578947368421,
     "mrr": 0.7402751670843776,
     "n": 152
    }
   },
   "sv": {
    "handwritten": {
     "recall_at_1": 0.71875,
     "recall_at_5": 0.90625,
     "mrr": 0.8026041666666667,
     "n": 32
    },
    "all_paired": {
     "recall_at_1": 0.6521739130434783,
     "recall_at_5": 0.842391304347826,
     "mrr": 0.7323887163561077,
     "n": 184
    },
    "generated_sv_only": {
     "recall_at_1": 0.34806629834254144,
     "recall_at_5": 0.6574585635359116,
     "mrr": 0.4790669122160835,
     "n": 181
    },
    "generated": {
     "recall_at_1": 0.6381578947368421,
     "recall_at_5": 0.8289473684210527,
     "mrr": 0.7176065162907268,
     "n": 152
    }
   }
  }
 },
 "gap_recall_at_5": {
  "kblab": {
   "handwritten": 0.0,
   "all_paired": 0.04347826086956519,
   "generated": 0.052631578947368474
  },
  "harrier": {
   "handwritten": 0.0,
   "all_paired": 0.010869565217391353,
   "generated": 0.013157894736842146
  },
  "bm25": {
   "handwritten": 0.25,
   "all_paired": 0.2880434782608695,
   "generated": 0.29605263157894735
  },
  "fused": {
   "handwritten": 0.0,
   "all_paired": 0.005434782608695565,
   "generated": 0.006578947368421129
  },
  "fused_fast": {
   "handwritten": 0.0625,
   "all_paired": 0.05434782608695654,
   "generated": 0.05263157894736836
  }
 },
 "handwritten_top5_overlap_ge3": 0.875,
 "diagnosis": {
  "method": "fused",
  "n_paired": 184,
  "gap": 0.005434782608695652,
  "groups": [
   {
    "origin": "generated",
    "form": "single",
    "n": 129,
    "recall_at_5": {
     "en": 0.9147286821705426,
     "sv": 0.9224806201550387
    },
    "gap_points": -0.005434782608695652,
    "share_of_gap": -1.0
   },
   {
    "origin": "generated",
    "form": "slash",
    "n": 23,
    "recall_at_5": {
     "en": 1.0,
     "sv": 0.9130434782608695
    },
    "gap_points": 0.010869565217391304,
    "share_of_gap": 2.0
   },
   {
    "origin": "handwritten",
    "form": "single",
    "n": 32,
    "recall_at_5": {
     "en": 1.0,
     "sv": 1.0
    },
    "gap_points": 0.0,
    "share_of_gap": 0.0
   }
  ]
 },
 "low_confidence": {
  "share_above": 0.9508196721311475,
  "nonsense_max": 0.49406251311302185,
  "n": 549,
  "n_nonsense": 15,
  "ok": true,
  "cutoff": 0.5454738736152649,
  "note": "top fused hit's KBLab similarity, full mode, both languages"
 },
 "previous": {
  "source": "benchmark_results_001.json",
  "run_at": "2026-10-21T12:37:50+00:00",
  "fused_recall_at_5": {
   "en": 0.993006993006993,
   "sv": 0.8951048951048951
  },
  "n_paired": 143,
  "gap": 0.09790209790209792,
  "handwritten_top5_overlap_ge3": 0.6875
 }
}
```

## Health

`GET /api/v1/health` → **200**

```json
{
 "status": "ok",
 "models_loaded": [
  "harrier",
  "kblab"
 ],
 "index_chunks": 9551
}
```

