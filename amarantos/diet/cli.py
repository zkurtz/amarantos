#!/usr/bin/env python3
"""Dietary Nutrient Health Impact Estimation Tool.

This module provides tools to:
1. Search PubMed for meta-analyses on dietary compounds
2. Extract and parse effect sizes from literature
3. Visualize the current estimates
4. Validate estimates

Usage:
    uv run python -m amarantos.diet.cli search "coffee mortality"
    uv run python -m amarantos.diet.cli visualize
    uv run python -m amarantos.diet.cli validate
"""

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from xml.etree import ElementTree

import click
import matplotlib.pyplot as plt
import numpy as np

from amarantos.core.loaders import load_all_interventions
from amarantos.core.schemas import Intervention


class PubMedSearcher:
    """Search PubMed for meta-analyses and systematic reviews."""

    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    def __init__(self, email: str = "researcher@example.com"):
        """Initialize the searcher with an email for NCBI API."""
        self.email = email

    def search(self, query: str, max_results: int = 10) -> list[dict[str, str | None]]:
        """Search PubMed for articles matching the query.

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
            click.echo(f"Search error: {e}", err=True)
            return []

        if not pmids:
            return []

        # Fetch article details
        return self._fetch_details(pmids)

    def _fetch_details(self, pmids: list[str]) -> list[dict[str, str | None]]:
        """Fetch detailed information for a list of PMIDs."""
        fetch_url = f"{self.BASE_URL}/efetch.fcgi?" f"db=pubmed&id={','.join(pmids)}&retmode=xml&email={self.email}"

        try:
            with urllib.request.urlopen(fetch_url, timeout=30) as response:
                xml_data = response.read().decode()
        except urllib.error.URLError as e:
            click.echo(f"Fetch error: {e}", err=True)
            return []

        return self._parse_xml(xml_data)

    def _parse_xml(self, xml_data: str) -> list[dict[str, str | None]]:
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
                        "abstract": abstract_elem.text if abstract_elem is not None else None,
                        "year": year_elem.text if year_elem is not None else None,
                        "journal": journal_elem.text if journal_elem is not None else None,
                    }
                )
        except ElementTree.ParseError as e:
            click.echo(f"XML parse error: {e}", err=True)

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

    def extract(self, text: str) -> list[dict[str, float | None]]:
        """Extract effect sizes from text.

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


def visualize_estimates(interventions: list[Intervention], output_path: Path | None = None) -> None:
    """Create a forest plot visualization of the estimates."""
    # Sort by point estimate (using first effect)
    sorted_interventions = sorted(interventions, key=lambda x: x.effects[0].estimate)

    fig, ax = plt.subplots(figsize=(12, max(8, len(sorted_interventions) * 0.25)))

    y_positions = np.arange(len(sorted_interventions))

    # Plot confidence intervals
    for i, intervention in enumerate(sorted_interventions):
        effect = intervention.effects[0]
        color = "green" if effect.is_beneficial else ("red" if effect.is_harmful else "gray")
        ax.hlines(y=i, xmin=effect.ci_lower, xmax=effect.ci_upper, color=color, alpha=0.6)
        ax.scatter(effect.estimate, i, color=color, s=50, zorder=5)

    # Reference line at 1.0
    ax.axvline(x=1.0, color="black", linestyle="--", alpha=0.5, label="No effect")

    # Labels
    ax.set_yticks(y_positions)
    ax.set_yticklabels([i.name for i in sorted_interventions], fontsize=8)
    ax.set_xlabel("Relative Risk / Hazard Ratio")
    ax.set_title("Dietary Compounds: Estimated Health Impact\n(90% Confidence Intervals)")

    # Add legend
    ax.scatter([], [], color="green", label="Beneficial (95% CI < 1.0)")
    ax.scatter([], [], color="gray", label="Uncertain (CI crosses 1.0)")
    ax.scatter([], [], color="red", label="Harmful (5% CI > 1.0)")
    ax.legend(loc="upper right")

    plt.tight_layout()

    if output_path is None:
        output_path = Path.cwd() / "dietary_nutrients_forest_plot.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    click.echo(f"Saved visualization to: {output_path}")
    plt.show()


def validate_estimates(interventions: list[Intervention]) -> None:
    """Validate estimates and report statistics."""
    click.echo("\n" + "=" * 60)
    click.echo("DIETARY NUTRIENTS ESTIMATE VALIDATION")
    click.echo("=" * 60)

    click.echo(f"\nTotal compounds: {len(interventions)}")

    beneficial = [i for i in interventions if i.effects[0].is_beneficial]
    uncertain = [i for i in interventions if i.effects[0].is_uncertain]
    harmful = [i for i in interventions if i.effects[0].is_harmful]

    click.echo("\nClassification:")
    click.echo(f"  Clearly beneficial (95% CI < 1.0): {len(beneficial)}")
    click.echo(f"  Uncertain (CI crosses 1.0):        {len(uncertain)}")
    click.echo(f"  Potentially harmful (5% CI > 1.0): {len(harmful)}")

    click.echo("\n" + "-" * 60)
    click.echo("TOP 10 MOST BENEFICIAL (by point estimate)")
    click.echo("-" * 60)
    sorted_by_benefit = sorted(interventions, key=lambda x: x.effects[0].estimate)
    for idx, intervention in enumerate(sorted_by_benefit[:10], 1):
        effect = intervention.effects[0]
        name = intervention.name[:35]
        click.echo(f"{idx:2}. {name:<35} {effect.estimate:.3f} ({effect.ci_lower:.2f}-{effect.ci_upper:.2f})")

    click.echo("\n" + "-" * 60)
    click.echo("COMPOUNDS WITH UNCERTAIN EVIDENCE")
    click.echo("-" * 60)
    for intervention in uncertain:
        effect = intervention.effects[0]
        click.echo(f"  - {intervention.name[:40]:<40} ({effect.ci_lower:.2f}-{effect.ci_upper:.2f})")

    click.echo("\n" + "-" * 60)
    click.echo("WIDEST CONFIDENCE INTERVALS (most uncertain)")
    click.echo("-" * 60)
    sorted_by_width = sorted(interventions, key=lambda x: x.effects[0].uncertainty_width, reverse=True)
    for intervention in sorted_by_width[:10]:
        effect = intervention.effects[0]
        click.echo(f"  - {intervention.name[:35]:<35} width: {effect.uncertainty_width:.3f}")

    # Check for logical issues
    click.echo("\n" + "-" * 60)
    click.echo("DATA QUALITY CHECKS")
    click.echo("-" * 60)

    issues = []
    for intervention in interventions:
        effect = intervention.effects[0]
        if effect.ci_lower >= effect.ci_upper:
            issues.append(f"{intervention.name}: lower bound >= upper bound")
        if effect.ci_lower < 0.5:
            issues.append(f"{intervention.name}: unusually low lower bound ({effect.ci_lower})")
        if effect.ci_upper > 1.5:
            issues.append(f"{intervention.name}: unusually high upper bound ({effect.ci_upper})")

    if issues:
        click.echo("Issues found:")
        for issue in issues:
            click.echo(f"  WARNING: {issue}")
    else:
        click.echo("No data quality issues found.")


def search_literature(query: str, verbose: bool = True) -> None:
    """Search PubMed for meta-analyses related to a query."""
    click.echo(f"\nSearching PubMed for: {query}")
    click.echo("-" * 50)

    searcher = PubMedSearcher()
    extractor = EffectSizeExtractor()

    articles = searcher.search(query, max_results=5)

    if not articles:
        click.echo("No results found.")
        return

    for article in articles:
        click.echo(f"\nPMID: {article['pmid']}")
        click.echo(f"Year: {article['year']}")
        click.echo(f"Journal: {article['journal']}")
        click.echo(f"Title: {article['title']}")

        if article["abstract"]:
            # Try to extract effect sizes
            effects = extractor.extract(article["abstract"])
            if effects:
                click.echo("Extracted effect sizes:")
                for effect in effects:
                    if effect["lower"] and effect["upper"]:
                        click.echo(
                            f"  RR/HR: {effect['estimate']:.2f} "
                            f"(95% CI: {effect['lower']:.2f}-{effect['upper']:.2f})"
                        )
                    else:
                        click.echo(f"  RR/HR: {effect['estimate']:.2f}")

            if verbose:
                abstract_text = article["abstract"]
                if abstract_text and len(abstract_text) > 500:
                    abstract_text = abstract_text[:500] + "..."
                click.echo(f"Abstract: {abstract_text}")

        click.echo("-" * 50)


@click.group()
def cli() -> None:
    """Dietary Nutrient Health Impact Estimation Tool."""
    pass


@cli.command()
@click.argument("query")
@click.option("--verbose/--no-verbose", default=True, help="Show full abstracts")
def search(query: str, verbose: bool) -> None:
    """Search PubMed for meta-analyses on a compound.

    Example: uv run python -m amarantos.diet.cli search "omega-3 mortality"
    """
    search_literature(query, verbose=verbose)


@cli.command()
@click.option("--output", "-o", type=click.Path(), help="Output file path for the plot")
def visualize(output: str | None) -> None:
    """Generate a forest plot visualization of all estimates."""
    interventions = load_all_interventions("diet")
    output_path = Path(output) if output else None
    visualize_estimates(interventions, output_path)


@cli.command()
def validate() -> None:
    """Validate and summarize the nutrient estimates."""
    interventions = load_all_interventions("diet")
    validate_estimates(interventions)


@cli.command()
def list_compounds() -> None:
    """List all compounds in the database."""
    interventions = load_all_interventions("diet")
    click.echo(f"\nDietary compounds in database ({len(interventions)} total):\n")
    for intervention in sorted(interventions, key=lambda x: x.name.lower()):
        effect = intervention.effects[0]
        status = "+" if effect.is_beneficial else ("?" if effect.is_uncertain else "-")
        click.echo(f"  {status} {intervention.name}")


if __name__ == "__main__":
    cli()
