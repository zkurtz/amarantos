# Methodology: Dietary Nutrients Health Impact Assessment

## Overview

This document describes the methodology used to derive the health impact estimates in `dietary_nutrients.csv`. The confidence bounds represent estimated **relative risk (RR) or hazard ratio (HR)** for all-cause mortality or major health outcomes associated with regular consumption/supplementation.

## Interpretation of Values

- **Values < 1.0**: Reduced risk (beneficial effect)
- **Value = 1.0**: No effect (neutral)
- **Values > 1.0**: Increased risk (potentially harmful)

For example, a range of `0.85-0.96` for coffee indicates an estimated 4-15% reduction in all-cause mortality risk with moderate consumption.

## Data Sources and Evidence Hierarchy

### Primary Sources (weighted highest)
1. **Meta-analyses** of randomized controlled trials (RCTs)
2. **Large-scale prospective cohort studies** (e.g., Nurses' Health Study, EPIC, UK Biobank)
3. **Systematic reviews** in peer-reviewed journals
4. **Cochrane Reviews**

### Secondary Sources
5. Individual RCTs with adequate sample sizes
6. Mendelian randomization studies
7. Mechanistic studies with strong biological plausibility

### Tertiary Sources (context only)
8. Animal studies (especially for emerging compounds like NMN, fisetin)
9. In vitro studies
10. Expert consensus statements

## Confidence Bound Derivation

### Step 1: Literature Review
For each nutrient/supplement, we surveyed:
- PubMed for meta-analyses (search: "[compound] mortality meta-analysis")
- Cochrane Library for systematic reviews
- Major longevity research databases (AgingPortfolio, GeroScience)

### Step 2: Effect Size Extraction
- When available, we used pooled effect estimates from meta-analyses
- For compounds without mortality data, we used surrogate endpoints (cardiovascular events, cancer incidence, biomarker improvements)

### Step 3: Uncertainty Adjustment

The bounds were widened based on:

| Factor | Adjustment |
|--------|------------|
| Limited human RCT data | Widen by ±0.03-0.05 |
| Primarily observational data | Widen by ±0.02-0.04 |
| Dose-dependent effects unclear | Widen by ±0.02 |
| Publication bias suspected | Shift toward null by 0.01-0.02 |
| Strong mechanistic support | Narrow by 0.01-0.02 |

### Step 4: Conservative Adjustment
- All estimates were adjusted conservatively toward the null (1.0)
- Emerging compounds (NMN, fisetin) have wider bounds reflecting uncertainty
- Compounds with mixed evidence (vitamin E, calcium) have bounds crossing 1.0

## Specific Methodology Notes

### Well-Established Compounds
**Coffee, Green Tea, Olive Oil, Fiber, Fatty Fish, Nuts**
- Multiple large meta-analyses available
- Consistent dose-response relationships
- Narrower confidence bounds justified

### Moderate Evidence Compounds
**Creatine, CoQ10, Curcumin, Probiotics**
- Good mechanistic data
- Limited mortality studies
- Surrogate endpoints used
- Wider bounds applied

### Emerging/Speculative Compounds
**NMN/NR, Fisetin, Quercetin (senolytic use), Spermidine**
- Strong preclinical data
- Limited human long-term studies
- Bounds cross 1.0 or approach it
- High uncertainty acknowledged

### Context-Dependent Compounds
**Iron, Calcium, Vitamin E**
- U-shaped or J-shaped dose-response curves
- Deficiency harmful, excess harmful
- Bounds reflect "adequate" intake
- Wider ranges due to individual variation

## Key Literature References

### Meta-Analyses Consulted

1. **Coffee**: Poole et al. (2017) BMJ - umbrella review of 201 meta-analyses
2. **Omega-3**: Hu et al. (2019) JACC - meta-analysis of 13 RCTs
3. **Fiber**: Reynolds et al. (2019) Lancet - systematic review
4. **Nuts**: Aune et al. (2016) BMC Medicine - dose-response meta-analysis
5. **Vitamin D**: Autier et al. (2014) Lancet Diabetes Endocrinol
6. **Green Tea**: Tang et al. (2015) Heart - meta-analysis
7. **Olive Oil**: Guasch-Ferré et al. (2022) JACC
8. **Spermidine**: Madeo et al. (2018) Science - review of mechanisms
9. **Berberine**: Lan et al. (2015) Atherosclerosis - meta-analysis

### Longevity-Specific Resources

- Kaeberlein Lab publications (interventions testing program)
- NIA Interventions Testing Program results
- GeroScience journal reviews
- Longevity research consortium publications

## Limitations and Caveats

### Important Limitations

1. **Individual variation**: Genetic polymorphisms affect response (e.g., equol producers vs non-producers, caffeine metabolism)

2. **Dose matters**: Estimates assume "moderate/adequate" intake; extreme doses may have different effects

3. **Synergies and interactions**: Compounds may interact; estimates are for single-compound effects

4. **Confounding**: Observational data may be confounded by healthy user bias

5. **Publication bias**: Positive results more likely published

6. **Temporal changes**: Evidence evolves; estimates should be updated periodically

### What This Is NOT

- **Not medical advice**: Consult healthcare providers before supplementation
- **Not precise**: Bounds are estimates reflecting uncertainty
- **Not comprehensive**: Individual compounds may have effects beyond those captured

## Updating This Dataset

Estimates should be reviewed when:
- New large-scale RCTs are published
- New meta-analyses become available
- NIA Interventions Testing Program releases results
- Major cohort studies publish findings

## Suggested Use

This dataset is intended for:
1. **Research prioritization**: Identifying well-supported vs speculative interventions
2. **Educational purposes**: Understanding relative evidence strength
3. **Personal decision-making framework**: Not as definitive guidance

## Version History

- **v1.0** (2025-01): Initial release with 62 compounds
