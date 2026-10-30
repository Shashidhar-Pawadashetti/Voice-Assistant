# 07 — Scheme Eligibility Engine and Governance

## 1. Non-negotiable rule

**The LLM never decides eligibility.** Scheme eligibility is evaluated only by a deterministic Python engine using an approved, versioned scheme definition and typed farmer facts.

The assistant may say “potentially suitable based on the information shared” but must never say “you are approved”, “you will receive this amount” or “your application will be accepted”.

## 2. Three-valued condition logic

Every condition evaluates to one of:

- `TRUE`: input evidence satisfies the condition;
- `FALSE`: input evidence contradicts the condition;
- `UNKNOWN`: required fact or authoritative evidence is missing, stale or unverifiable.

Do not coerce UNKNOWN to FALSE or TRUE.

### AND / OR semantics

| Expression | Evaluation |
|---|---|
| TRUE AND TRUE | TRUE |
| TRUE AND UNKNOWN | UNKNOWN |
| FALSE AND UNKNOWN | FALSE |
| TRUE OR UNKNOWN | TRUE |
| FALSE OR UNKNOWN | UNKNOWN |
| FALSE OR FALSE | FALSE |

A hard exclusion condition that evaluates TRUE should fail the candidate. If an exclusion condition is UNKNOWN, the result cannot be a confident potential match.

## 3. Recommendation outcome contract

Use these outcome values:

- `POTENTIALLY_MATCHED`: all configured required conditions in the current approved rule version evaluate TRUE, but the system still does not confer entitlement or verify official acceptance;
- `NEEDS_MORE_INFORMATION`: one or more required conditions evaluate UNKNOWN and there is no decisive failure;
- `NOT_MATCHED`: at least one decisive disqualifying condition evaluates FALSE or a hard exclusion evaluates TRUE;
- `RULES_NOT_VERIFIED`: scheme metadata/rules are draft, incomplete, expired or lack adequate official evidence; do not show as a factual real-scheme recommendation.

`POTENTIALLY_MATCHED` must include a persistent `official_verification_required: true` flag for real schemes unless a lawful, authoritative real-time integration proves otherwise. No such integration is assumed.

Synthetic schemes must be labelled `DEMO_ONLY` in every API and UI result. Their output is a test case, not a real benefit recommendation.

## 4. Rule schema

Use JSON/YAML data (choose one canonical format; JSON is easiest for Pydantic validation) with:

- immutable `scheme_id`;
- `classification`: `REAL_GOVERNMENT` or `SYNTHETIC_DEMO`;
- name/localized display names;
- authority/government level;
- assistance category;
- geography applicability;
- effective dates;
- `rule_version`;
- `verification_status`: `VERIFIED`, `DRAFT`, `INCOMPLETE`, `EXPIRED`;
- source references with title, URL, publisher, date checked and relevant section/page;
- required slot declarations;
- rule tree / conditions;
- exclusions;
- documents and application steps only when officially sourced;
- `last_verified_at` and `review_due_at`.

Do not store code snippets or arbitrary Python expressions in scheme JSON. Use a controlled operator set.

## 5. Allowed rule operators

Initial safe set:

- `eq`, `ne`;
- `in`, `not_in`;
- `gte`, `gt`, `lte`, `lt` for validated numeric values;
- `exists` / `is_known`;
- `all` and `any` group operators.

Do not support `eval`, Python expressions, dynamic imports, SQL fragments or executable rules.

Numeric comparisons must declare units. Compare only normalized values of the same canonical unit.

## 6. Input evidence model

Facts must have:

- value and canonical unit/code;
- source/provenance;
- status (self-reported, confirmed, officially verified, unknown);
- source turn or official source ID;
- timestamp;
- normalizer version.

User-stated information is not equivalent to a government-verified record. Rules must declare evidence strength needed for each condition.

## 7. Evaluation algorithm

```python
def evaluate_scheme(scheme, farmer_facts, evaluation_time):
    if scheme.verification_status != "VERIFIED":
        return RULES_NOT_VERIFIED

    condition_results = evaluate_rule_tree(
        scheme.rule_tree,
        farmer_facts,
        evaluation_time,
    )

    if condition_results.has_decisive_failure:
        outcome = NOT_MATCHED
    elif condition_results.has_unknown_required_condition:
        outcome = NEEDS_MORE_INFORMATION
    else:
        outcome = POTENTIALLY_MATCHED

    return immutable_explanation_trace(
        outcome=outcome,
        rule_version=scheme.rule_version,
        matched=condition_results.matched,
        failed=condition_results.failed,
        unknown=condition_results.unknown,
        sources=scheme.sources,
        official_verification_required=True,
    )
```

The code is illustrative; the actual implementation must define hard-exclusion semantics, rule-tree validation and effective-date behavior in tests.

## 8. Reproducibility

Persist the following for every recommendation run:

- immutable farmer fact snapshot or referenced slot version;
- scheme ID and exact rule version/hash;
- evaluator version;
- evaluation timestamp;
- condition-by-condition output;
- source references and verification date;
- final cautious outcome.

If a fact changes, create a new evaluation run. Do not silently rewrite prior traces.

## 9. Source governance

For every real scheme:

1. obtain current official source(s), not an unsourced blog;
2. identify exact eligibility clauses, exclusions, notified area/crop/season rules and application steps relevant to this product;
3. record source URL, publication/effective date, access date and page/section;
4. encode as draft;
5. write positive, negative, boundary and unknown tests;
6. have a human reviewer compare encoded logic with the official source;
7. change status to `VERIFIED` only after review;
8. version and release; do not mutate historical rule versions.

No admin UI is required. Updates are code-reviewed data releases.

## 10. Freshness policy

- Store `effective_from`, `effective_to` when available.
- Store `last_verified_at` and `review_due_at`.
- For a scheme dependent on annual/seasonal state notifications, require the matching notification and time period. Never reuse a past season as current.
- If a source cannot be refreshed, mark the definition stale and return `RULES_NOT_VERIFIED`.

## 11. LLM boundary

The LLM may:

- identify a farmer's intent;
- extract a farmer-stated fact;
- propose a canonical term for validation;
- phrase a question/answer in Kannada using the supplied facts;
- explain rule trace facts supplied by the engine.

The LLM may not:

- add or change rule conditions;
- infer government verification;
- choose an eligibility outcome;
- invent benefit amounts/deadlines/documents/application URLs;
- override a failed rule;
- hide unknown conditions.
