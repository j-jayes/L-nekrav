# API smoke transcript

Run 2026-10-21T22:19:52 against `http://127.0.0.1:8000` by `scripts/api_smoke.py`. Lists are cut to three items for reading.

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
     "note": "75 % of the median applies instead of 90 %",
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

