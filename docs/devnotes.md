# Development Notes

## Current State Assessment

Amarantos is a solid **information system** - clean data model, good test coverage, working CLI. But it's not yet the **decision-support system** the vision describes.

Key gaps between vision and reality:
- "Evolves with user" → User schema exists but is never used
- "Adapting to circumstances" → Same output for everyone regardless of age, constraints, goals

## Completed Work

- [x] Priority 1 (Evidence Integration): refs linked to choices via `[@ref_id]` citations
- [x] `--show-sources` flag on describe command
- [x] HardClaim → Claim refactor with effects list (#32)
- [x] 207 references with structured hard_claims
- [x] `amos` CLI alias (#35)
- [x] Test coverage for evidence linkage (85%+ citation coverage)
- [x] `ref_ids` computed property on Effect extracts citations from evidence text

## Recommended Priorities

### Priority 1: Personalization Foundation

**Why first**: The User schema already exists. Small effort to activate it.

**Concrete steps**:
1. Add `amarantos profile` command to create/edit `~/.amarantos/profile.yaml`
2. Start simple: age-based effect adjustment (many interventions have age-stratified data)
3. Add `--profile` flag to rank command that loads and applies user context
4. Display "For your profile: +X.X years" alongside generic estimate

**Success metric**: Two people with different ages see different rankings.

### Priority 2: Constraint Filtering

**Why second**: High practical value, relatively easy to implement.

**Concrete steps**:
1. Add `--max-cost` and `--max-hours` flags to rank command
2. Add `--sort cost-efficiency` option (P30 / annual_cost_usd)
3. Add `amarantos budget --hours 300 --usd 1000` for constrained recommendations

**Success metric**: Users can get recommendations that fit their actual lifestyle constraints.

### Priority 3: Data Model Hardening

**Why third**: Important but less urgent. Current data mostly works.

**Concrete steps**:
1. Add validators: `std >= 0`, `mean > 0` for mortality ratios, reasonable bounds
2. Validate `duration_h * weekly_freq * 52 ≈ annual_cost_h` consistency
3. Consider separating `RatioEffect` vs `LinearEffect` types (mortality vs years)
4. Add structured `Interaction` schema for contraindications

**Success metric**: Invalid data fails loudly at load time.

### Priority 4: Ref Aggregation

**Why fourth**: The 207-reference bibliography contains structured `hard_claims` that are currently unused. These could be aggregated to compute or validate choice effects.

**Concrete steps**:
1. Add `amarantos refs` command to list references with claim counts
2. Create mapping from ref claims to choice effects for validation
3. Consider making refs the source of truth, with choice effects computed from claims

**Success metric**: Every choice effect can be traced back to specific ref claims.

### Deferred: CLI Polish

Lower priority. Do incrementally as other work proceeds:
- JSON/CSV export
- Comparison mode
- Better uncertainty visualization

## Architecture Notes

**Key insight from exploration**: The 207-reference bibliography is a treasure trove that's completely unused by the ranking system. The `Claim` objects in refs have structured effect data that could be automatically aggregated instead of manually copied to choice effects.

**Future consideration**: Could refs become the source of truth, with choice effects computed from claims? This would be a larger refactor but would make the system self-auditing.

## Quick Wins (< 1 hour each)

1. ~~Add `amarantos stats` command showing domain counts, coverage metrics~~ ✓ Done
2. Add `amarantos domains` listing all domains with choice counts
3. Add `--json` flag for machine-readable output
4. Add bounds validation to Effect fields
5. Populate a few `soft_claims` in refs (currently all empty)

## Open Questions

- Should effects be computed from refs (source of truth) or remain manually curated?
- How to handle conflicting studies? (Currently implicit in large std)
- What's the minimum useful personalization? (Age alone? Age + fitness?)
- Should interactions be hard constraints or just warnings?
