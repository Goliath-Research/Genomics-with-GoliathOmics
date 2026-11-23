# Part 11 Gap Matrix (template with the course lab's current state)

*Genomics with GoliathOmics · Goliath Research Academy* · [Module 12](12_content.md)

Status: **Available** (in the pinned lab), **Pending** (an open or planned GoliathApp PR),
**Gap** (no change planned yet), **Organizational** (a procedure, not software).
Update the status column when a feature merges. This is a working matrix, not a compliance claim.

| Clause | Requirement (summary) | Platform evidence | Status |
|---|---|---|---|
| 11.10(a) | validated system | GoliathApp and GoliathOmics CI (PG18/PG19), course tests, validation evidence index | Available, partial: validation is a process you document |
| 11.10(b) | accurate, complete copies | `fn_ledger_checkpoint()` heads (H1); no portal export of a run's evidence yet | Pending (H1, GoliathApp #109) / Gap (export format) |
| 11.10(c) | protect records, retention | append-only ledgers, authorized purge with tombstones (H1); retention policy `platform/RetentionPolicy` (H3) | Pending (GoliathApp #109, #111) |
| 11.10(d) | limit access | RBAC roles, scopes, semantic `required_permission`; omics permissions registered by GoliathOmics PR #115 | Available with #115 |
| 11.10(e) | audit trail: who, what, when, never obscure prior values | portal audits + `wf.event` ledgers (H1); Meta values (H2); runs (H3); relational clinical tables (GoliathOmics #116); `cfg.study_start_request` and `/work` logs not covered; UTC default caveat (12.4) | Pending (GoliathApp #109–#111, GoliathOmics #116) / Gap |
| 11.10(f) | operational sequencing checks | DomainProgram lifecycle programs, QC gates (Module 7), claim gate (Module 10) | Available |
| 11.10(g) | authority checks | God Architect only for `platform/*`; session active role; permission checks per request | Available |
| 11.10(h) | device / source checks | worker enrollment and tokens | Available, partial |
| 11.10(i) | trained personnel | this course's assessments are evidence | Organizational |
| 11.10(j) | written signature accountability policy | | Organizational |
| 11.10(k) | documentation controls | docs in git, config `content_hash`, change-management plan | Available, partial |
| 11.50 / 11.70 | signature manifestation, record linking | H4 `platform/ElectronicSignature`, content SHA-256 | Pending (GoliathApp #112) |
| 11.100–11.300 | signature uniqueness, components, identity controls | Entra sign-in + H4 re-authentication window | Pending (GoliathApp #112) |
