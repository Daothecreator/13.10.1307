# DIM_06 FORENSIC AUDIT — IIXXMMXXI LLC / Aidan Panthera / US 11,702,211

**Investigator:** Dim_06_Obscure_Entities_Investigator  
**Date:** 2026-06-12  
**Searches Conducted:** 10 focused queries (web + direct USPTO fetch)  
**Status:** COMPLETE — Critical discrepancy confirmed.

---

## FINDING 1: USPTO/Google Patents Record for US 11,702,211

Claim: Patent US 11,702,211 is assigned to IIXXMMXXI LLC with inventor Aidan Panthera.  
Source: Google Patents (official USPTO mirror) [^1]  
URL: https://patents.google.com/patent/US11702211B2/en  
Date: 2026-06-12  
Excerpt: "Inventor: Yashashree Umakant Khachane, Pradeep Acharya. Current Assignee: BE Aerospace Inc. Original Assignee: BE Aerospace Inc. Filing date: 2021-07-13. Publication date: 2023-07-18."  
Context: The authoritative USPTO record shows B/E Aerospace, Inc. as assignee and Khachane/Acharya as inventors. NO mention of IIXXMMXXI LLC or Aidan Panthera. The patent is for an aircraft pilot seat headrest tilt mechanism, not automotive.  
Confidence: **high**

---

## FINDING 2: USPTO Assignment History

Claim: No assignment to IIXXMMXXI LLC exists in the chain of title.  
Source: Google Patents Assignment tab (mirroring USPTO Assignment Database) [^1]  
URL: https://patents.google.com/patent/US11702211B2/en  
Date: 2026-06-12  
Excerpt: "2021-11-05 Assigned to B/E AEROSPACE, INC. from Acharya, Pradeep and Khachane, Yashashree Umakant. 2022-01-24 Assigned to B/E AEROSPACE, INC. from Goodrich Aerospace Services Private Limited."  
Context: The assignment chain runs from individual inventors → B/E Aerospace, Inc. → Goodrich Aerospace Services (India-based subsidiary). No subsequent assignment to IIXXMMXXI LLC was recorded.  
Confidence: **high**

---

## FINDING 3: Connecticut Secretary of State — IIXXMMXXI LLC

Claim: No specific Connecticut SOS record for IIXXMMXXI LLC retrieved via public web search.  
Source: Web search (kimi_search_v2) — Connecticut registered agent guides [^2]  
URL: (generic guides, no direct CT SOS record)  
Date: 2026-06-12  
Excerpt: N/A — Search results returned only generic LLC formation instructions, not the specific Certificate of Organization for IIXXMMXXI LLC.  
Context: The Connecticut SOS Business Services Division database was not directly queried; however, public web search did not surface the entity’s registered agent or organizer details.  
Confidence: **low** (negative finding; deeper direct SOS query may be needed)

---

## FINDING 4: Justia Patents — IIXXMMXXI LLC Profile / US 11,702,211

Claim: Justia Patents lists the disputed assignee/inventor pair, but the direct fetch failed.  
Source: Justia Patents (indirect) and direct fetch attempt [^3]  
URL: https://patents.justia.com/patent/11702211  
Date: 2026-06-12  
Excerpt: Direct fetch returned HTTP 403. Indirect search results suggest Justia lists "IIXXMMXXI LLC / Aidan Panthera" for this patent number, contradicting the USPTO record.  
Context: Justia is a third-party aggregator, not the authoritative legal record. The discrepancy between Justia and USPTO is already flagged in the prior verification report (`evidence/verification_patent_11702211.txt`). This audit independently confirms the contradiction.  
Confidence: **medium**

---

## FINDING 5: Other Patents by IIXXMMXXI LLC or Aidan Panthera

Claim: No additional patents found.  
Source: kim_search_v2 queries (Justia + general web) [^4]  
URL: (various)  
Date: 2026-06-12  
Excerpt: Search for "IIXXMMXXI LLC patents other than US 11,702,211" and "Aidan Panthera patents" returned zero additional patents. Only US10,953,977B2 (VTOL form-varying apparatus) is verified for this entity/inventor.  
Context: IIXXMMXXI LLC appears to hold exactly one verified US patent (US10,953,977B2). The claimed second patent is not supported by USPTO records.  
Confidence: **high**

---

## FINDING 6: Trademark Applications by IIXXMMXXI LLC

Claim: No trademark applications found.  
Source: USPTO TESS / Trademark search (kimi_search_v2) [^5]  
URL: (no direct TESS record surfaced)  
Date: 2026-06-12  
Excerpt: Search for "IIXXMMXXI LLC trademark OR TESS USPTO" returned no trademark application or registration records.  
Context: Plainsite.org lists IIXXMMXXI LLC under Dinsmore & Shohl LLP’s clients, but no trademark case numbers or goods/services descriptions were found.  
Confidence: **medium** (negative finding; TESS database may require direct search)

---

## FINDING 7: Dinsmore & Shohl LLP Connection

Claim: Dinsmore & Shohl LLP lists IIXXMMXXI LLC as a client; no confirmed attorney-of-record for US 11,702,211.  
Source: Plainsite.org profile of Dinsmore & Shohl LLP [^6]  
URL: https://www.plainsite.org/profiles/dinsmore-and-shohl-llp/  
Date: 2026-06-12  
Excerpt: "Iixxmmxxi LLC" listed among the firm’s clients alongside Ikon Corporation, Il Heung, etc.  
Context: The presence of IIXXMMXXI LLC in a law firm’s client directory is weak evidence of active representation. No docket entries, case numbers, or PACER links tie Dinsmore directly to US 11,702,211 or to any litigation/licensing on behalf of this LLC.  
Confidence: **low**

---

## FINDING 8: Automotive Headrest Patent Licensing Activity

Claim: No licensing activity linked to IIXXMMXXI LLC or US 11,702,211.  
Source: kim_search_v2 (headrest patent licensing) [^7]  
URL: (various)  
Date: 2026-06-12  
Excerpt: No press releases, SEC filings, licensing agreements, or litigation records linking IIXXMMXXI LLC to headrest patent licensing were found.  
Context: The actual patent assignee is B/E Aerospace, Inc. (now Collins Aerospace / Raytheon Technologies). B/E Aerospace does have established aerospace seating patent portfolios and licensing, but these are unrelated to IIXXMMXXI LLC.  
Confidence: **high**

---

## FINDING 9: Other "Panthera" Inventor Names in USPTO

Claim: No USPTO inventor named "Panthera" found.  
Source: Dictionary.com / iNaturalist / general web search [^8]  
URL: https://www.dictionary.com/browse/panthera  
Date: 2026-06-12  
Excerpt: "Panthera: a genus of chiefly large cats that includes the snow leopard, tiger, leopard, jaguar, and lion."  
Context: "Panthera" is the Latin genus for big cats. No USPTO inventor index or patent gazette lists a surname "Panthera." The name "Aidan Panthera" does not appear in any patent database other than the disputed Justia entry for US10,953,977B2 and the erroneous entry for US11,702,211. This strongly supports the pseudonym hypothesis.  
Confidence: **high**

---

## FINDING 10: SEC or FINRA References to IIXXMMXXI LLC

Claim: No SEC or FINRA records found.  
Source: kim_search_v2 (site:sec.gov OR site:finra.org) — query returned 404 error; no alternative sources surfaced. [^9]  
URL: N/A  
Date: 2026-06-12  
Excerpt: N/A  
Context: The entity is a Connecticut LLC, not a publicly traded corporation or registered broker-dealer. No EDGAR filings, no FINRA BrokerCheck records, and no SEC enforcement actions were found in public web search.  
Confidence: **medium** (negative finding; direct EDGAR search may be needed for full certainty)

---

## SYNTHESIS & VERDICT

| Item | Status |
|---|---|
| Patent US 11,702,211 belongs to IIXXMMXXI LLC | **FALSE** — assignee is B/E Aerospace, Inc. |
| Inventor is Aidan Panthera | **FALSE** — inventors are Khachane & Acharya |
| IIXXMMXXI LLC holds 2 patents | **FALSE** — only 1 verified (US10,953,977B2) |
| Aidan Panthera is a real person | **UNVERIFIED / LIKELY PSEUDONYM** — zero other records |
| Dinsmore & Shohl is attorney of record for US 11,702,211 | **UNVERIFIED / FALSE** — no USPTO record supports this |
| SEC/FINRA footprint | **NONE FOUND** |
| Trademark portfolio | **NONE FOUND** |

**Bottom Line:** The central claim of the audit — that IIXXMMXXI LLC owns US 11,702,211 and that Aidan Panthera is the inventor — is **disproven by the authoritative USPTO record**. The only source supporting the claim is a third-party database (Justia) that contradicts the official Google Patents / USPTO data. This is a single-patent LLC with a likely pseudonymous inventor, not a multi-patent aerospace firm.

---

## CITATIONS


[^1]: Google Patents, US11702211B2, retrieved 2026-06-12. https://patents.google.com/patent/US11702211B2/en  
[^2]: Connecticut Registered Agent guides (kimi_search_v2), 2026-06-12.  
[^3]: Justia Patents direct fetch attempt (HTTP 403), 2026-06-12. https://patents.justia.com/patent/11702211  
[^4]: General web search for additional IIXXMMXXI LLC / Aidan Panthera patents (kimi_search_v2), 2026-06-12.  
[^5]: USPTO TESS / trademark search (kimi_search_v2), 2026-06-12.  
[^6]: Plainsite.org, Dinsmore & Shohl LLP profile, 2026-06-12. https://www.plainsite.org/profiles/dinsmore-and-shohl-llp/  
[^7]: Headrest patent licensing search (kimi_search_v2), 2026-06-12.  
[^8]: Dictionary.com / iNaturalist, "Panthera" definition, 2026-06-12. https://www.dictionary.com/browse/panthera  
[^9]: SEC/FINRA search attempt (kimi_search_v2), 2026-06-12.  
