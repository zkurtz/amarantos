# Development Notes

## Current State Assessment

Amarantos is a solid **information system** - clean data model, good test coverage, working CLI. But it's not yet the **decision-support system** the vision describes.

Key gaps between vision and reality:
- "Evolves with user" → User schema exists but is never used
- "Evidence-first" → Bibliography disconnected from ranking; evidence quality not surfaced
- "Adapting to circumstances" → Same output for everyone regardless of age, constraints, goals

## Recommended Priorities

### Priority 1: Evidence Integration

**Why first**: This is foundational. Without trustworthy evidence linkage, personalization and filtering are built on sand.

**Concrete steps**:
1. Add `ref_ids: list[str]` field to `Effect` class linking to Reference IDs
2. Create validation script ensuring every choice effect cites ≥1 reference
3. Add `--show-sources` flag to `describe` command
4. Surface evidence type distribution in rank output (e.g., "3 RCTs, 2 cohorts")

**Success metric**: Every effect traceable to specific references; users can see evidence quality.

### Priority 2: Personalization Foundation

**Why second**: The User schema already exists. Small effort to activate it.

**Concrete steps**:
1. Add `amarantos profile` command to create/edit `~/.amarantos/profile.yaml`
2. Start simple: age-based effect adjustment (many interventions have age-stratified data)
3. Add `--profile` flag to rank command that loads and applies user context
4. Display "For your profile: +X.X years" alongside generic estimate

**Success metric**: Two people with different ages see different rankings.

### Priority 3: Constraint Filtering

**Why third**: High practical value, relatively easy to implement.

**Concrete steps**:
1. Add `--max-cost` and `--max-hours` flags to rank command
2. Add `--sort cost-efficiency` option (P30 / annual_cost_usd)
3. Add `amarantos budget --hours 300 --usd 1000` for constrained recommendations

**Success metric**: Users can get recommendations that fit their actual lifestyle constraints.

### Priority 4: Data Model Hardening

**Why fourth**: Important but less urgent. Current data mostly works.

**Concrete steps**:
1. Add validators: `std >= 0`, `mean > 0` for mortality ratios, reasonable bounds
2. Validate `duration_h * weekly_freq * 52 ≈ annual_cost_h` consistency
3. Consider separating `RatioEffect` vs `LinearEffect` types (mortality vs years)
4. Add structured `Interaction` schema for contraindications

**Success metric**: Invalid data fails loudly at load time.

### Deferred: CLI Polish

Lower priority. Do incrementally as other work proceeds:
- JSON/CSV export
- Comparison mode
- Better uncertainty visualization

## Architecture Notes

**Key insight from exploration**: The 207-reference bibliography is a treasure trove that's completely unused by the ranking system. The `Claim` objects in refs have structured effect data that could be automatically aggregated instead of manually copied to choice effects.

**Future consideration**: Could refs become the source of truth, with choice effects computed from claims? This would be a larger refactor but would make the system self-auditing.

## Quick Wins (< 1 hour each)

1. Add `amarantos stats` command showing domain counts, coverage metrics
2. Add `amarantos domains` listing all domains with choice counts
3. Add `--json` flag for machine-readable output
4. Add bounds validation to Effect fields
5. Populate a few `soft_claims` in refs (currently all empty)

## Open Questions

- Should effects be computed from refs (source of truth) or remain manually curated?
- How to handle conflicting studies? (Currently implicit in large std)
- What's the minimum useful personalization? (Age alone? Age + fitness?)
- Should interactions be hard constraints or just warnings?
