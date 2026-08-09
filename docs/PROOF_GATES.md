# Proof Gates

## Stage Progression

| Gate | Status | Evidence |
|------|--------|----------|
| IDENTITY_RESOLVED | ✅ PASS | mermicorn.repo.yaml |
| PROBLEM_VERIFIED | ✅ PASS | docs/PROBLEM.md |
| NOVELTY_AND_LINEAGE_RESOLVED | ✅ PASS | docs/DONOR_MAP.md |
| TARGET_CONTRACT_FROZEN | ✅ PASS | machine/target-contract.json |
| DONOR_PLAN_RESOLVED | ✅ PASS | docs/DONOR_MAP.md |
| VERTICAL_SLICE_ALIVE | ✅ PASS | Engine implementation |
| DETERMINISTIC_PROOF_GREEN | ✅ PASS | tests/unit/ |
| ADVERSARIAL_SURVIVAL | ✅ PASS | tests/adversarial/ |
| OPERABLE_AND_OBSERVABLE | ✅ PASS | machine/capability-manifest.json |
| AUTHORITY_BOUND | ✅ PASS | SECURITY.md |
| PROOF_RECEIPT_BOUND | ✅ PASS | machine/proof-receipt.json |
| CANONICAL_POSITION_RESOLVED | ✅ PASS | CANONICAL.md |

## Test Coverage

| Test Type | Status |
|-----------|--------|
| Unit | ✅ Passing |
| Integration | ✅ Passing |
| Adversarial | ✅ Passing |

## Invariants Tested

| Invariant | Positive Test | Negative Test |
|-----------|---------------|---------------|
| Core mechanism works | Valid input → result | Invalid input → error |
| State transitions | Valid transition → success | Invalid transition → rejection |
| Export functionality | Data → file | Empty data → graceful |
