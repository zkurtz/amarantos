# New Entry Rubric

How to add a new intervention to `data/choices/`.

## Prerequisites

1. Read `README.md` in this directory for methodology
2. Understand the three `Outcome` types in `amarantos/core/schemas.py`

## Template

```yaml
domain: diet  # or "exercise", etc.
name: Intervention Name (dosage/frequency)
summary: |
  High-level description of the intervention and its potential benefits/harms.
  Include key caveats. Keep to 3-5 lines.
effects:
  - outcome: Relative mortality risk
    evidence: |
      [Source type]: [Study description]. [Sample size]. [Causal/Associative].
      [Key limitations]. Author Year (https://full-url-to-source).
    mean: 0.85
    std: 0.03

  - outcome: Years of delayed aging
    evidence: |
      [How estimated - direct or extrapolated]. [Uncertainty acknowledgment].
      Author Year (https://url) if applicable.
    mean: 0.5
    std: 0.5

  - outcome: Subjective wellbeing - number of just-noticeable differences
    evidence: |
      [Source or reasoning]. Author Year (https://url).
    mean: 0.2
    std: 0.3
```

**Note:** All references must include full URLs in parentheses.

## Step-by-Step Process

### 1. Define the Intervention

Be specific about:
- **Dosage**: "500mg/day", "3-4 cups/day", "2 sessions/week"
- **Comparison**: vs. placebo, vs. non-users, vs. sedentary
- **Population**: general adults, specific conditions, age groups

### 2. Search for Evidence

**For mortality/morbidity:**
```
PubMed: "[intervention] meta-analysis mortality OR cardiovascular"
```

**For wellbeing/mood:**
```
PubMed: "[intervention] meta-analysis depression OR wellbeing OR mood"
```

**For aging biomarkers:**
```
PubMed: "[intervention] biological age OR telomere OR epigenetic clock"
```

### 3. Evaluate Each Outcome

#### Relative Mortality Risk

- Best evidence: Meta-analyses of cohort studies or RCTs
- Look for: Hazard ratios, relative risks with 95% CIs
- Convert CI to std: `std = (upper - lower) / 3.92`

#### Years of Delayed Aging

- Direct evidence: Epigenetic clock studies, biological age markers
- Indirect: Extrapolate from mortality (rough heuristic: 10% mortality reduction ≈ 1 year)
- Often speculative: Use large std (0.5-2.0 years)

#### Subjective Wellbeing

- Look for: Depression/anxiety meta-analyses, quality of life studies
- Effect sizes often in SMD (standardized mean difference)
- Convert SMD to "just-noticeable differences": rough 1:1 mapping
- If no evidence: mean=0, std=0.5

### 4. Document Evidence Quality

Use these phrases in evidence fields:

| Phrase | Meaning |
|--------|---------|
| "Meta-analysis of N RCTs" | Strong causal evidence |
| "Meta-analysis of N cohort studies" | Strong associative evidence |
| "Associative; confounding possible" | Acknowledge observational limitation |
| "Extrapolated from..." | Indirect estimate |
| "Intuition-based; no direct evidence" | Highly uncertain |
| "Conflicting evidence" | Inflate std accordingly |

### 5. Sanity Check

Before committing:
- [ ] All three outcomes present
- [ ] Evidence field explains reasoning
- [ ] Std is larger when evidence is weaker
- [ ] Extraordinary effects have extraordinary evidence (or huge std)
- [ ] YAML loads without error: `uv run python -c "from amarantos.core.loaders import load_all_choices; load_all_choices()"`

## Examples

### Good Entry (strong evidence)

```yaml
- outcome: Relative mortality risk
  evidence: |
    Meta-analysis of 40 cohort studies, n=3.8M. HR 0.83 (95% CI: 0.79-0.88)
    for 3-4 cups/day vs non-drinkers. Associative evidence; healthy user
    bias possible. Poole 2017 (https://pubmed.ncbi.nlm.nih.gov/29167102/).
  mean: 0.83
  std: 0.023
```

### Good Entry (weak evidence)

```yaml
- outcome: Years of delayed aging
  evidence: |
    No direct epigenetic clock studies found. Extrapolated from mortality
    reduction assuming Gompertz curve. Highly speculative estimate.
  mean: 0.3
  std: 1.0
```

### Poor Entry (avoid)

```yaml
- outcome: Relative mortality risk
  evidence: "Reduces mortality"  # Too vague! No URL!
  mean: 0.7
  std: 0.01  # Overconfident!
```
