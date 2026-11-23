# Module 12: Audit History, Evidence Package & Capstone

*Genomics with GoliathOmics · Goliath Research Academy* · [Course syllabus](../README.md)

**Files:** `12_ledger_drill.sql` · `part11_gap_matrix.md` · `evidence_package_template.md`

> **Status.** This module teaches GoliathApp's history features as they land. **H1**, the
> append-only hash-chained ledger, is GoliathApp PR #109 (open, not merged). **H2**
> (ObjValuesHistory), **H3** (workflow run history and retention) and **H4** (electronic
> signatures) are follow-up GoliathApp PRs not yet open. Each lab step checks for the feature
> first and says SKIP when the pinned GoliathApp does not have it.

> **Claim boundary.** You are assembling evidence *toward* 21 CFR Part 11 and a premarket
> submission. Nothing here makes GoliathOmics "Part 11 compliant" or cleared.

## Goal

Use the platform's own history to answer a reviewer's questions: who did what, when, under which
configuration, and can you prove the record was not changed? Then package that evidence for one
real run.

## 12.1 "History must exist, no gaps"

A record is only as good as its history. Part 11.10(e) asks for secure, computer-generated,
time-stamped audit trails that never obscure earlier values and are kept as long as the record.
Module 9 listed what the lab records today; this module checks each item against that bar.

## 12.2 H1: the append-only ledger

GoliathApp H1 registers audit tables as **ledgers** (`portal.sp_ledger_register`):

* each row gets `ledger_seq`, `txid`, `prev_hash` and `row_hash`, chaining it to the row before;
* `UPDATE`, `DELETE` and `TRUNCATE` are rejected; rows leave only through an authorized retention
  purge (`portal.ledger_purge_authorization`), and each removed row leaves a tombstone so the chain
  still verifies;
* `portal.fn_ledger_verify(name)` and `portal.fn_ledger_verify_all()` recompute the chain and
  report `missing_seq`, `prev_mismatch`, `hash_mismatch` or `head_mismatch`;
* `portal.fn_ledger_checkpoint()` returns every ledger head, which is what you export and keep
  outside the database.

Registered in H1: the `portal.*_audit` tables (God Architect, security admin, model authoring,
record editor, session active role, external identity link), onboarding `AuditLog`, `wf.event`
and `wf.event_delivery`.

## 12.3 Lab: the ledger drill

```bash
python course_lab.py sql "12 - Audit History, Evidence Package & Capstone/12_ledger_drill.sql"
```

The drill runs in one transaction and rolls back. It lists ledger heads, verifies, appends one
row through `portal.fn_session_audit_active_role`, shows that UPDATE and DELETE are refused, then
has the database owner disable the guard trigger and edit the row. `fn_ledger_verify_all()`
reports `hash_mismatch`.

**Lesson:** the ledger is *tamper-evident*, not tamper-proof. Someone who owns the database can
still change bytes; the chain makes it visible. That is why checkpoints are exported and kept
(and, with H4, signed) outside the database.

To try it before H1 merges, rebuild the disposable lab on the PR head (this replaces your lab):

```bash
python course_lab.py down
GOLIATH_APP_REF_OVERRIDE=<GoliathApp PR #109 head commit> python course_lab.py up
```

The course was checked this way against PR #109 head `ec9f0da`: the official apply and seed
scripts ran unchanged, `fn_ledger_verify_all()` returned no problems, and the drill detected the
owner's edit as `hash_mismatch`.

## 12.4 Time-stamps must be unambiguous

Run in the lab:

```sql
SET TimeZone = 'America/New_York';
SELECT now(), (now() AT TIME ZONE 'utc')::timestamptz AS default_expression;
```

Many platform tables default `created_at_utc` to `now() AT TIME ZONE 'utc'` on a `timestamptz`
column. That stores the correct instant only when the session time zone is UTC (Neon's default,
and the course's Docker database). On a server set to another zone the value shifts by the
offset. Write it down as a finding: 11.10(e) needs a time-stamp you can trust without knowing the
server's settings. The course compose file pins the database to UTC.

## 12.5 What is not in a ledger yet

Use the lab to confirm each item, then place it in `part11_gap_matrix.md`:

| Record | Today | Closes with |
|---|---|---|
| Meta object values (Samples, Patients through Meta) | current value only | H2 ObjValuesHistory |
| `omics_clinical` writes through semantic requests | no audit row; Meta dual-write flags all false | GoliathOmics change after H2 |
| `cfg.study_start_request.status` | updated in place (queued → failed) | H3 or a GoliathOmics status-event table |
| workflow runs, node executions, run history on definition delete | cascade delete | H3 |
| JSONL action logs on `/work` | files, not tamper-evident | H3 export + hash |
| seed scripts | write without `god_architect_audit` rows | GoliathApp seed audit |
| sign-off of validation evidence | none | H4 e-signatures |

## 12.6 The evidence package

Fill in `evidence_package_template.md` for the canary study `academy_ena_srr28293403`
(HG00621, run SRR28293403). Every row cites where the evidence lives: a table and key, a file
and hash, a commit, a CI run. Rows you cannot fill are gaps, and you list them; you do not invent
values.

## 12.7 Capstone

1. Choose one documented GoliathOmics scenario other than the worked example (for example
   RNA-seq with kallisto on tissue, DIA proteomics, or the plant abiotic stress pack).
2. Write its intended use and the likely regulatory route (Module 11), with sources.
3. Resolve its configuration with provenance (Module 8) and list the QC guardrails that gate it
   (Module 7).
4. Describe its study design, partitions and the claim gate state (Module 10).
5. Produce the evidence package and the Part 11 gap matrix for it, citing real lab records.
6. Present the open gaps and which platform change closes each.

## Evidence to submit

* The drill output (or the SKIP line and the pin you used).
* The completed evidence package and gap matrix.
* The capstone write-up.
