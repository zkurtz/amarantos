#!/usr/bin/env python3
"""
Dietary Nutrient Health Impact Estimation Tool

This script provides tools to:
1. Search PubMed for meta-analyses on dietary compounds
2. Extract and parse effect sizes from literature
3. Visualize the current estimates
4. Update estimates based on new evidence

Usage:
    python derive_nutrient_estimates.py --search "coffee mortality"
    python derive_nutrient_estimates.py --visualize
    python derive_nutrient_estimates.py --validate
"""

import argparse
import csv
import json
import re
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from xml.etree import ElementTree

# Optional imports for visualization
try:
    import matplotlib.pyplot as plt
    import numpy as np

    HAS_PLOTTING = True
except ImportError:
    HAS_PLOTTING = False


@dataclass
class NutrientEstimate:
    """Represents a health impact estimate for a dietary compound."""

    supplement: str
    main_effect: str
    lower_bound: float
    upper_bound: float

    @property
    def point_estimate(self) -> float:
        """Geometric mean of bounds (appropriate for ratios)."""
        return (self.lower_bound * self.upper_bound) ** 0.5

    @property
    def uncertainty_width(self) -> float:
        """Width of confidence interval."""
        return self.upper_bound - self.lower_bound

    @property
    def is_beneficial(self) -> bool:
        """True if upper bound is below 1.0 (clearly beneficial)."""
        return self.upper_bound < 1.0

    @property
    def is_uncertain(self) -> bool:
        """True if bounds cross 1.0 (uncertain effect)."""
        return self.lower_bound < 1.0 < self.upper_bound

    @property
    def is_harmful(self) -> bool:
        """True if lower bound is above 1.0 (clearly harmful)."""
        return self.lower_bound > 1.0


def load_estimates(csv_path: str = "dietary_nutrients.csv") -> list[NutrientEstimate]:
    """Load nutrient estimates from CSV file."""
    estimates = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            estimates.append(
                NutrientEstimate(
                    supplement=row["supplement"],
                    main_effect=row["main_effect"],
                    lower_bound=float(row["5%_lower_bound"]),
                    upper_bound=float(row["95%_upper_bound"]),
                )
            )
    return estimates


def save_estimates(
    estimates: list[NutrientEstimate], csv_path: str = "dietary_nutrients.csv"
) -> None:
    """Save nutrient estimates to CSV file."""
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["supplement", "main_effect", "5%_lower_bound", "95%_upper_bound"]
        )
        for e in estimates:
            writer.writerow([e.supplement, e.main_effect, e.lower_bound, e.upper_bound])


class PubMedSearcher:
    """Search PubMed for meta-analyses and systematic reviews."""

    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    def __init__(self, email: str = "researcher@example.com"):
        self.email = email

    def search(
        self, query: str, max_results: int = 10
    ) -> list[dict[str, Optional[str]]]:
        """
        Search PubMed for articles matching the query.

        Args:
            query: Search terms (e.g., "coffee mortality meta-analysis")
            max_results: Maximum number of results to return

        Returns:
            List of article metadata dictionaries
        """
        # Add meta-analysis filter for higher quality results
        enhanced_query = f"({query}) AND (meta-analysis[pt] OR systematic review[pt])"

        # Search for PMIDs
        search_url = (
            f"{self.BASE_URL}/esearch.fcgi?"
            f"db=pubmed&term={urllib.parse.quote(enhanced_query)}"
            f"&retmax={max_results}&retmode=json&email={self.email}"
        )

        try:
            with urllib.request.urlopen(search_url, timeout=30) as response:
                data = json.loads(response.read().decode())
                pmids = data.get("esearchresult", {}).get("idlist", [])
        except (urllib.error.URLError, json.JSONDecodeError) as e:
            print(f"Search error: {e}")
            return []

        if not pmids:
            return []

        # Fetch article details
        return self._fetch_details(pmids)

    def _fetch_details(self, pmids: list[str]) -> list[dict[str, Optional[str]]]:
        """Fetch detailed information for a list of PMIDs."""
        fetch_url = (
            f"{self.BASE_URL}/efetch.fcgi?"
            f"db=pubmed&id={','.join(pmids)}&retmode=xml&email={self.email}"
        )

        try:
            with urllib.request.urlopen(fetch_url, timeout=30) as response:
                xml_data = response.read().decode()
        except urllib.error.URLError as e:
            print(f"Fetch error: {e}")
            return []

        return self._parse_xml(xml_data)

    def _parse_xml(self, xml_data: str) -> list[dict[str, Optional[str]]]:
        """Parse PubMed XML response into article dictionaries."""
        articles = []
        try:
            root = ElementTree.fromstring(xml_data)
            for article in root.findall(".//PubmedArticle"):
                title_elem = article.find(".//ArticleTitle")
                abstract_elem = article.find(".//AbstractText")
                pmid_elem = article.find(".//PMID")
                year_elem = article.find(".//PubDate/Year")
                journal_elem = article.find(".//Journal/Title")

                articles.append(
                    {
                        "pmid": pmid_elem.text if pmid_elem is not None else None,
                        "title": title_elem.text if title_elem is not None else None,
                        "abstract": (
                            abstract_elem.text if abstract_elem is not None else None
                        ),
                        "year": year_elem.text if year_elem is not None else None,
                        "journal": (
                            journal_elem.text if journal_elem is not None else None
                        ),
                    }
                )
        except ElementTree.ParseError as e:
            print(f"XML parse error: {e}")

        return articles


class EffectSizeExtractor:
    """Extract effect sizes (hazard ratios, relative risks) from text."""

    # Patterns for common effect size reporting formats
    PATTERNS = [
        # HR = 0.85 (95% CI: 0.78-0.92)
        r"(?:HR|RR|OR)\s*[=:]\s*(\d+\.?\d*)\s*\(95%\s*CI[:\s]+(\d+\.?\d*)\s*[-–]\s*(\d+\.?\d*)\)",
        # hazard ratio 0.85 (0.78, 0.92)
        r"(?:hazard|relative|odds)\s+ratio[:\s]+(\d+\.?\d*)\s*\((\d+\.?\d*)[,\s]+(\d+\.?\d*)\)",
        # RR 0.85; 95% CI, 0.78-0.92
        r"(?:HR|RR|OR)\s+(\d+\.?\d*)[;,]\s*95%\s*CI[,:\s]+(\d+\.?\d*)\s*[-–]\s*(\d+\.?\d*)",
        # pooled RR of 0.85
        r"pooled\s+(?:HR|RR|OR)\s+(?:of\s+)?(\d+\.?\d*)",
    ]

    def extract(self, text: str) -> list[dict[str, float]]:
        """
        Extract effect sizes from text.

        Returns list of dicts with keys: 'estimate', 'lower', 'upper'
        """
        if not text:
            return []

        results = []
        text_lower = text.lower()

        for pattern in self.PATTERNS:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                if len(match) == 3:
                    try:
                        results.append(
                            {
                                "estimate": float(match[0]),
                                "lower": float(match[1]),
                                "upper": float(match[2]),
                            }
                        )
                    except ValueError:
                        continue
                elif len(match) == 1:
                    try:
                        results.append(
                            {
                                "estimate": float(match[0]),
                                "lower": None,
                                "upper": None,
                            }
                        )
                    except ValueError:
                        continue

        return results


def visualize_estimates(estimates: list[NutrientEstimate]) -> None:
    """Create a forest plot visualization of the estimates."""
    if not HAS_PLOTTING:
        print("Visualization requires matplotlib and numpy.")
        print("Install with: pip install matplotlib numpy")
        return

    # Sort by point estimate
    sorted_estimates = sorted(estimates, key=lambda x: x.point_estimate)

    fig, ax = plt.subplots(figsize=(12, max(8, len(sorted_estimates) * 0.25)))

    y_positions = np.arange(len(sorted_estimates))

    # Plot confidence intervals
    for i, est in enumerate(sorted_estimates):
        color = "green" if est.is_beneficial else ("red" if est.is_harmful else "gray")
        ax.hlines(y=i, xmin=est.lower_bound, xmax=est.upper_bound, color=color, alpha=0.6)
        ax.scatter(est.point_estimate, i, color=color, s=50, zorder=5)

    # Reference line at 1.0
    ax.axvline(x=1.0, color="black", linestyle="--", alpha=0.5, label="No effect")

    # Labels
    ax.set_yticks(y_positions)
    ax.set_yticklabels([e.supplement for e in sorted_estimates], fontsize=8)
    ax.set_xlabel("Relative Risk / Hazard Ratio")
    ax.set_title("Dietary Compounds: Estimated Health Impact\n(90% Confidence Intervals)")

    # Add legend
    ax.scatter([], [], color="green", label="Beneficial (95% CI < 1.0)")
    ax.scatter([], [], color="gray", label="Uncertain (CI crosses 1.0)")
    ax.scatter([], [], color="red", label="Harmful (5% CI > 1.0)")
    ax.legend(loc="upper right")

    plt.tight_layout()
    plt.savefig("dietary_nutrients_forest_plot.png", dpi=150, bbox_inches="tight")
    print("Saved visualization to: dietary_nutrients_forest_plot.png")
    plt.show()


def validate_estimates(estimates: list[NutrientEstimate]) -> None:
    """Validate estimates and report statistics."""
    print("\n" + "=" * 60)
    print("DIETARY NUTRIENTS ESTIMATE VALIDATION")
    print("=" * 60)

    print(f"\nTotal compounds: {len(estimates)}")

    beneficial = [e for e in estimates if e.is_beneficial]
    uncertain = [e for e in estimates if e.is_uncertain]
    harmful = [e for e in estimates if e.is_harmful]

    print(f"\nClassification:")
    print(f"  Clearly beneficial (95% CI < 1.0): {len(beneficial)}")
    print(f"  Uncertain (CI crosses 1.0):        {len(uncertain)}")
    print(f"  Potentially harmful (5% CI > 1.0): {len(harmful)}")

    print("\n" + "-" * 60)
    print("TOP 10 MOST BENEFICIAL (by point estimate)")
    print("-" * 60)
    sorted_by_benefit = sorted(estimates, key=lambda x: x.point_estimate)
    for i, e in enumerate(sorted_by_benefit[:10], 1):
        print(f"{i:2}. {e.supplement[:35]:<35} {e.point_estimate:.3f} ({e.lower_bound:.2f}-{e.upper_bound:.2f})")

    print("\n" + "-" * 60)
    print("COMPOUNDS WITH UNCERTAIN EVIDENCE")
    print("-" * 60)
    for e in uncertain:
        print(f"  - {e.supplement[:40]:<40} ({e.lower_bound:.2f}-{e.upper_bound:.2f})")

    print("\n" + "-" * 60)
    print("WIDEST CONFIDENCE INTERVALS (most uncertain)")
    print("-" * 60)
    sorted_by_width = sorted(estimates, key=lambda x: x.uncertainty_width, reverse=True)
    for e in sorted_by_width[:10]:
        print(f"  - {e.supplement[:35]:<35} width: {e.uncertainty_width:.3f}")

    # Check for logical issues
    print("\n" + "-" * 60)
    print("DATA QUALITY CHECKS")
    print("-" * 60)

    issues = []
    for e in estimates:
        if e.lower_bound >= e.upper_bound:
            issues.append(f"{e.supplement}: lower bound >= upper bound")
        if e.lower_bound < 0.5:
            issues.append(f"{e.supplement}: unusually low lower bound ({e.lower_bound})")
        if e.upper_bound > 1.5:
            issues.append(f"{e.supplement}: unusually high upper bound ({e.upper_bound})")

    if issues:
        print("Issues found:")
        for issue in issues:
            print(f"  WARNING: {issue}")
    else:
        print("No data quality issues found.")


def search_literature(query: str, verbose: bool = True) -> None:
    """Search PubMed for meta-analyses related to a query."""
    print(f"\nSearching PubMed for: {query}")
    print("-" * 50)

    searcher = PubMedSearcher()
    extractor = EffectSizeExtractor()

    articles = searcher.search(query, max_results=5)

    if not articles:
        print("No results found.")
        return

    for article in articles:
        print(f"\nPMID: {article['pmid']}")
        print(f"Year: {article['year']}")
        print(f"Journal: {article['journal']}")
        print(f"Title: {article['title']}")

        if article["abstract"]:
            # Try to extract effect sizes
            effects = extractor.extract(article["abstract"])
            if effects:
                print("Extracted effect sizes:")
                for effect in effects:
                    if effect["lower"] and effect["upper"]:
                        print(
                            f"  RR/HR: {effect['estimate']:.2f} "
                            f"(95% CI: {effect['lower']:.2f}-{effect['upper']:.2f})"
                        )
                    else:
                        print(f"  RR/HR: {effect['estimate']:.2f}")

            if verbose:
                print(f"Abstract: {article['abstract'][:500]}...")

        print("-" * 50)


def main():
    parser = argparse.ArgumentParser(
        description="Dietary Nutrient Health Impact Estimation Tool"
    )
    parser.add_argument(
        "--search", type=str, help="Search PubMed for meta-analyses on a compound"
    )
    parser.add_argument(
        "--visualize", action="store_true", help="Generate forest plot visualization"
    )
    parser.add_argument(
        "--validate", action="store_true", help="Validate and summarize estimates"
    )
    parser.add_argument(
        "--csv", type=str, default="dietary_nutrients.csv", help="Path to CSV file"
    )

    args = parser.parse_args()

    # Resolve path relative to script location
    script_dir = Path(__file__).parent
    csv_path = script_dir / args.csv

    if args.search:
        search_literature(args.search)
    elif args.visualize:
        estimates = load_estimates(csv_path)
        visualize_estimates(estimates)
    elif args.validate:
        estimates = load_estimates(csv_path)
        validate_estimates(estimates)
    else:
        # Default: run validation
        print("Dietary Nutrient Estimation Tool")
        print("=" * 40)
        print("\nUsage:")
        print("  --search QUERY   Search PubMed for meta-analyses")
        print("  --visualize      Generate forest plot")
        print("  --validate       Validate and summarize data")
        print("\nExample:")
        print('  python derive_nutrient_estimates.py --search "omega-3 mortality"')
        print("  python derive_nutrient_estimates.py --visualize")

        if csv_path.exists():
            print(f"\nLoaded {len(load_estimates(csv_path))} compounds from {csv_path}")


if __name__ == "__main__":
    main()
