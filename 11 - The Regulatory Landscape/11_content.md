# Module 11: The Regulatory Landscape

*Genomics with GoliathOmics · Goliath Research Academy* · [Course syllabus](../README.md)

**Glossary:** `glossary.md` · **Sources:** listed at the end; every regulatory statement links to
fda.gov, ecfr.gov or the Federal Register. GoliathOmics `docs/regulatory/` is an internal synthesis
and scaffold, not a filed submission.

> **Claim boundary.** GoliathOmics is not FDA-cleared, FDA-approved or "Part 11 compliant", and
> this course never says otherwise. It teaches what the rules ask for and how platform controls
> can produce evidence toward them.

> **510(k), not "501(k)".** The premarket notification program is named after section 510(k) of
> the Federal Food, Drug, and Cosmetic Act and implemented in 21 CFR Part 807 Subpart E.

## Goal

Explain, in plain terms, the premarket routes, design controls, software documentation, NGS
analytical validation and 21 CFR Part 11, and recognize which route a genomics intended use
would likely take.

## 11.1 Device, IVD, SaMD

Software that analyzes specimens to aid diagnosis can be a medical device or part of an in vitro
diagnostic (IVD). Software that is itself the device is Software as a Medical Device (SaMD).
Whether a product is a device, and which class, follows from its **intended use** and risk.

## 11.2 Three premarket routes

| Route | When | Rule | Result |
|---|---|---|---|
| **510(k)** premarket notification | a legally marketed **predicate** exists | 21 CFR 807 Subpart E: submit at least 90 days before marketing (807.81); contents in 807.87; 510(k) summary or statement (807.92/807.93); FDA decides substantial equivalence (807.100) | **cleared**; eSTAR electronic submission required since Oct 1, 2023 unless exempt |
| **De Novo** | novel, low-to-moderate risk, no predicate | 21 CFR 860 Subpart D | **granted**; creates a new classification |
| **PMA** | Class III | 21 CFR 814 | **approved** |

Substantial equivalence means the same intended use, and either the same technological
characteristics or different ones that raise no different questions of safety and effectiveness,
supported by performance data.

**Methylation precedents went through PMA.** Verified in FDA's PMA database (Nov 22, 2026):

| Device | PMA | Decision date | Applicant on the record | Product code |
|---|---|---|---|---|
| Epi proColon (SEPT9 methylation, plasma) | P130001 | Apr 12, 2016 | New Day Diagnostics, LLC | PHP |
| Cologuard (stool DNA incl. methylation markers + hemoglobin) | P130017 | Aug 11, 2014 | Exact Sciences Corporation | PHP |
| Shield (cfDNA, blood) | P230009 | Jul 26, 2024 | Guardant Health, Inc. | PHP |

The route is decided by intended use and risk. A course exercise or a product plan must not
presume 510(k).

## 11.3 Design controls and the QMSR

Since **Feb 2, 2026**, 21 CFR 820 is the Quality Management System Regulation (QMSR), which
incorporates ISO 13485:2016 by reference. Design and development controls apply to Class II and
III devices and to Class I devices automated with software (820.10(c)): planning, inputs,
outputs, reviews, verification, validation, transfer, change control, and a design history.

## 11.4 Software documentation

FDA's *Content of Premarket Submissions for Device Software Functions* (2023) sets Basic and
Enhanced documentation levels: software description, risk management, requirements, architecture,
design, development practices, verification and validation testing, version history, unresolved
anomalies. *General Principles of Software Validation* (2002) still frames validation; cyber
devices carry cybersecurity requirements under FD&C Act §524B.

## 11.5 NGS analytical validation

FDA's 2018 guidance on NGS-based tests for suspected germline diseases is scoped to germline
diagnosis, but its method is the reference pattern: predefine indications, specimen types and
performance thresholds, validate the **whole** workflow from specimen to result, and document every
decision. Map that to Modules 2–8: specimen and analyte, technique, alignment, QC thresholds,
configuration.

## 11.6 21 CFR Part 11

Part 11 applies to electronic records and signatures used to meet FDA record requirements
("predicate rules"). Key controls in 11.10:

| Clause | Control |
|---|---|
| (a) | system validation |
| (b) | accurate and complete copies |
| (c) | record protection and retention |
| (d), (g) | limited access, authority checks |
| (e) | secure, computer-generated, time-stamped **audit trails** that record who created, modified or deleted a record and when, never obscure earlier values, and are kept as long as the record |
| (f), (h) | operational and device checks |
| (i), (j) | trained people; written accountability for e-signatures |
| (k) | documentation controls |

Subpart C (11.50, 11.70, 11.100–11.300): electronic signatures that are unique, linked to their
record, and show signer, date/time and meaning. FDA's 2003 *Scope and Application* guidance
describes where FDA exercises enforcement discretion; predicate-rule record keeping still applies.

Module 12 maps each clause to GoliathApp's history features (H1–H4) and GoliathOmics' records.

## 11.7 Labs vs manufacturers

Clinical laboratories are regulated under CLIA (42 CFR 493). FDA's 2024 rule on laboratory
developed tests was vacated by a federal court on Mar 31, 2025, and FDA removed the rule's
amendments to 21 CFR 809.3 on Sep 19, 2025. A distributed software product or kit is still a
device question.

## Lab sequence (desk research)

1. Pick a hypothetical intended use, for example "aid in detecting colorectal cancer from plasma
   cfDNA methylation". Which route is likely, and why?
2. Open the three PMA records above in FDA's PMA database and the 510(k) database; note one
   product code and one decision summary section relevant to software.
3. List three questions a reviewer would ask about the software, and the module of this course
   whose controls would answer each.

## Evidence to submit

* A one-page route memo with links to the FDA sources you used.

## Sources

* FDA, Premarket Notification 510(k): https://www.fda.gov/medical-devices/premarket-submissions-selecting-and-preparing-correct-submission/premarket-notification-510k
* 21 CFR 807 Subpart E: https://www.ecfr.gov/current/title-21/chapter-I/subchapter-H/part-807/subpart-E
* FDA, eSTAR Program: https://www.fda.gov/medical-devices/how-study-and-market-your-device/estar-program
* FDA, De Novo: https://www.fda.gov/medical-devices/premarket-submissions-selecting-and-preparing-correct-submission/de-novo-classification-request
* 21 CFR 860 Subpart D: https://www.ecfr.gov/current/title-21/chapter-I/subchapter-H/part-860/subpart-D
* 21 CFR 814: https://www.ecfr.gov/current/title-21/chapter-I/subchapter-H/part-814
* FDA PMA database: https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfpma/pma.cfm (records P130001, P130017, P230009)
* 21 CFR 820 (QMSR): https://www.ecfr.gov/current/title-21/chapter-I/subchapter-H/part-820 and https://www.fda.gov/medical-devices/postmarket-requirements-devices/quality-management-system-regulation-qmsr
* 21 CFR 11: https://www.ecfr.gov/current/title-21/chapter-I/subchapter-A/part-11
* FDA, Part 11 Scope and Application (2003): https://www.fda.gov/regulatory-information/search-fda-guidance-documents/part-11-electronic-records-electronic-signatures-scope-and-application
* FDA, Content of Premarket Submissions for Device Software Functions (2023): https://www.fda.gov/regulatory-information/search-fda-guidance-documents/content-premarket-submissions-device-software-functions
* FDA, General Principles of Software Validation: https://www.fda.gov/regulatory-information/search-fda-guidance-documents/general-principles-software-validation
* FDA, NGS-based tests for germline diseases (2018): https://www.fda.gov/regulatory-information/search-fda-guidance-documents/considerations-design-development-and-analytical-validation-next-generation-sequencing-ngs-based
* FDA, Laboratory Developed Tests: https://www.fda.gov/medical-devices/in-vitro-diagnostics/laboratory-developed-tests
* CLIA, 42 CFR 493: https://www.ecfr.gov/current/title-42/chapter-IV/subchapter-G/part-493
