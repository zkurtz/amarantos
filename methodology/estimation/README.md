# Estimation Methodology

This document describes how we estimate the effects of wellness interventions on health outcomes.

## Philosophy

We model each effect as a **Gaussian distribution** with mean and standard deviation. This allows us to:
- Quantify uncertainty explicitly
- Compute confidence intervals (95% CI = mean ± 1.96 × std)
- Propagate uncertainty through downstream calculations

When evidence is weak or absent, we use **large standard deviations** rather than omitting the estimate.

## Outcomes

Each intervention is evaluated on three outcomes (see `Outcome` enum in `schemas.py`):

| Outcome | Description | Interpretation |
|---------|-------------|----------------|
| `Relative mortality risk` | Hazard/risk ratio vs. control | <1.0 is beneficial |
| `Years of delayed aging` | Biological age reduction | >0 is beneficial |
| `Subjective wellbeing` | Just-noticeable differences in life satisfaction | >0 is beneficial |

## Evidence Hierarchy

We weight evidence by study quality:

1. **Meta-analyses of RCTs** - Strongest causal evidence
2. **Individual RCTs** - Strong causal evidence
3. **Meta-analyses of cohort studies** - Strong associative evidence
4. **Individual cohort studies** - Moderate associative evidence
5. **Mechanistic reasoning** - Weak, speculative
6. **Intuition** - Very weak, requires large uncertainty

### Causal vs. Associative Evidence

- **Causal**: Randomized controlled trials establish causation. Effect sizes from RCTs can be interpreted as "if you do X, expect Y."
- **Associative**: Observational studies show correlation. Confounding is always possible (e.g., healthy user bias). Note this explicitly in evidence summaries.

## Converting Published Statistics to Mean/Std

### From 95% Confidence Interval

Given a published CI [lower, upper]:

```
mean = (lower + upper) / 2
std = (upper - lower) / (2 × 1.96)
```

### From Hazard Ratio with CI

Example: HR 0.79 (95% CI: 0.72-0.86)

```
mean = 0.79
std = (0.86 - 0.72) / (2 × 1.96) ≈ 0.036
```

### When No Uncertainty is Reported

If a study reports only a point estimate, estimate std based on:
- Similar studies with reported CIs
- Sample size (larger → smaller std)
- Effect plausibility (extraordinary claims → larger std)

## Handling Missing or Weak Evidence

When evidence for an outcome is:
- **Absent**: Use a neutral mean (1.0 for ratios, 0 for differences) with large std
- **Indirect**: Extrapolate with explicit reasoning and inflate std
- **Conflicting**: Use weighted average and inflate std to reflect disagreement

Example for an outcome with no direct evidence:
```yaml
- outcome: Years of delayed aging
  evidence: |
    No direct evidence. Extrapolated from mortality reduction using
    Gompertz model assumption. Highly speculative.
  mean: 0.0
  std: 1.0
```

## Reference Format

All references in `summary` and `evidence` fields should follow this format:

```
Terse description. Author Year (https://full-url-to-source).
```

Examples:
- `Meta-analysis of 40 cohorts. Poole 2017 (https://pubmed.ncbi.nlm.nih.gov/29167102/).`
- `RCT, n=1,877. Gordon 2018 (https://pubmed.ncbi.nlm.nih.gov/29800984/).`

**Always include the full URL** - this enables verification and follow-up reading.

## Tools for Evidence Gathering

- **PubMed**: Search for meta-analyses with `[intervention] meta-analysis mortality`
- **Cochrane Library**: High-quality systematic reviews
- **Web search**: Recent studies, especially for emerging interventions
- **Claude/LLMs**: Summarizing evidence (acknowledge as "AI-assisted synthesis")

## Quality Checklist

Before finalizing an effect estimate:
- [ ] Is the outcome clearly specified?
- [ ] Is the comparison group stated (vs. placebo, vs. no intervention)?
- [ ] Is the evidence type noted (RCT, cohort, meta-analysis)?
- [ ] Is causal vs. associative distinguished?
- [ ] Is uncertainty appropriately sized?
- [ ] Are limitations acknowledged?
- [ ] Do all references include full URLs?
