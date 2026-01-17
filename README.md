# Amarantos

Tips and tools for personal wellness and longevity. *Amarantos* (ἀμάραντος) is Greek for "unfading" or "immortal" and is the root of *amaranth*—a flower known for retaining its color even dried.

> **Warning: AI-Generated Content**
>
> This repository was generated with AI assistance and has not been thoroughly vetted by a human. References, claims, and code may contain errors or inaccuracies. Please double-check all information against primary sources and exercise critical judgment. Treat this as a starting point for careful research, not a definitive resource.

## CLI Commands

```bash
# Rank all choices by 30th percentile lifespan impact
amarantos

# Filter by domain
amarantos --domain exercise

# Show only top/bottom 5
amarantos -n 5

# Show top 3 from each domain
amarantos --maxd 3

# Describe a specific choice
amarantos describe cycling
```

### Example

```
$ amarantos --maxd 1

Choice                                    P30 (years)       $/year   hours/year
------------------------------------------------------------------------------
Moderate Cardio                                 +1.63          200          120
Caloric Restriction                             +1.08         -500            0
Strong Social Connections                       +1.08          500          350
Finnish Sauna                                   +1.08         1200          150
Almonds                                         +0.98          100          100
Rapamycin                                       +0.87          500            2
Optimal Sleep Duration                          +0.69            0            0
Cognitive Training                              +0.19          200          100
Nature Exposure                                 +0.14          100          100
Alcohol Abstinence or Minimal Intake            +0.04         -500            0

P30: conservative (30th percentile) estimate of the *average* years of life extension
$/year, hours/year: annual cost of the intervention
```

See also: [External Resources](resources/README.md)

## Installation

```bash
uv add amarantos
```
