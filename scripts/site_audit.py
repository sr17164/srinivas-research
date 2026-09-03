#!/usr/bin/env python3
"""Static pre-publication checks for SM Research.

This complements `pnpm check`, `pnpm lint`, `pnpm format` and `pnpm build`.
It catches editorial, linking and packaging errors that are easy to miss.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLOG = ROOT / "src" / "content" / "blog"
CONTRIBUTORS = ROOT / "src" / "content" / "contributors"
AUTHORS = ROOT / "src" / "content" / "authors"
PUBLIC = ROOT / "public"
CURRENT_VIEWS = ROOT / "src" / "data" / "currentViews.ts"

REQUIRED_FRONTMATTER = {
    "title",
    "slug",
    "description",
    "pubDate",
    "reportType",
    "assetClass",
    "sector",
    "market",
    "outcome",
    "outcomeSummary",
    "draft",
}

REQUIRED_CONTRIBUTOR_FRONTMATTER = {
    "title",
    "description",
    "author",
    "pubDate",
    "reportType",
    "editorialStatus",
    "disclosure",
    "draft",
}

FORBIDDEN_PATTERNS: dict[str, str] = {
    "contentReference artefact": r"contentReference\[|oaicite",
    "unfinished placeholder": (
        r"To be completed|Planned supporting files|Publication pending"
    ),
    "removed conviction field": r"\bconviction\s*=|\bconviction\?:",
    "old commodity sample claim": r"103 monthly regression observations",
    "old commodity gold result": r"Gold sensitivity.*0\.84|β\s*=\s*0\.84",
    "overstated verification wording": r"Revised,\s+independently verified",
}

EXCLUDED_DIRECTORIES = {
    ".astro",
    ".git",
    ".pnpm-store",
    ".vercel",
    "__pycache__",
    "dist",
    "node_modules",
}


def frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}

    end = text.find("\n---", 4)
    if end == -1:
        return {}

    data: dict[str, str] = {}

    for line in text[4:end].splitlines():
        match = re.match(r"^([A-Za-z][A-Za-z0-9_]*):\s*(.*)$", line)
        if match:
            data[match.group(1)] = match.group(2).strip()

    return data


def clean_scalar(value: str) -> str:
    return value.strip().strip("'\"")


def is_excluded(path: Path) -> bool:
    return any(
        part in EXCLUDED_DIRECTORIES
        for part in path.relative_to(ROOT).parts
    )


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    slugs: dict[str, Path] = {}
    titles: dict[str, Path] = {}
    featured_public: list[Path] = []

    articles = sorted([*BLOG.glob("*.md"), *BLOG.glob("*.mdx")])

    for path in articles:
        text = path.read_text(encoding="utf-8")
        fm = frontmatter(text)
        missing = sorted(REQUIRED_FRONTMATTER - set(fm))

        if missing:
            errors.append(
                f"{path.relative_to(ROOT)}: missing frontmatter {missing}"
            )

        title = clean_scalar(fm.get("title", ""))
        slug = clean_scalar(fm.get("slug", ""))
        draft = clean_scalar(fm.get("draft", "false")).lower() == "true"
        featured = clean_scalar(fm.get("featured", "false")).lower() == "true"

        outcome = clean_scalar(fm.get("outcome", ""))
        valid_outcomes = {"Successful", "Unsuccessful", "Mixed", "Open"}
        if outcome and outcome not in valid_outcomes:
            errors.append(
                f"{path.relative_to(ROOT)}: invalid outcome {outcome!r}"
            )
        if outcome and outcome != "Open" and "## Outcome and Reflection" not in text:
            errors.append(
                f"{path.relative_to(ROOT)}: resolved view needs an outcome section"
            )

        if title:
            if title in titles:
                errors.append(
                    f"Duplicate title: {title!r} in "
                    f"{titles[title].name} and {path.name}"
                )
            titles[title] = path

        if slug:
            if slug in slugs:
                errors.append(
                    f"Duplicate slug: {slug!r} in "
                    f"{slugs[slug].name} and {path.name}"
                )
            slugs[slug] = path

        if featured and not draft:
            featured_public.append(path)

        if "## Sources" not in text:
            warnings.append(
                f"{path.relative_to(ROOT)}: no '## Sources' section"
            )

        if "## Research Methodology" not in text and "## Methodology" not in text:
            warnings.append(
                f"{path.relative_to(ROOT)}: no methodology section"
            )

        for label, pattern in FORBIDDEN_PATTERNS.items():
            if re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL):
                errors.append(f"{path.relative_to(ROOT)}: contains {label}")

    if len(featured_public) != 1:
        names = ", ".join(path.name for path in featured_public) or "none"
        errors.append(
            "Exactly one non-draft article must be featured; "
            f"found {len(featured_public)} ({names})"
        )

    contributor_articles = sorted(
        path
        for path in [*CONTRIBUTORS.glob("*.md"), *CONTRIBUTORS.glob("*.mdx")]
        if not path.name.startswith("_")
    )
    author_ids = {
        path.stem
        for path in AUTHORS.glob("*.json")
        if not path.name.startswith("_")
    }
    contributor_slugs: dict[str, Path] = {}
    valid_editorial_statuses = {"Published", "Revised"}

    for path in contributor_articles:
        text = path.read_text(encoding="utf-8")
        fm = frontmatter(text)
        missing = sorted(REQUIRED_CONTRIBUTOR_FRONTMATTER - set(fm))
        if missing:
            errors.append(
                f"{path.relative_to(ROOT)}: missing contributor frontmatter {missing}"
            )

        author_id = clean_scalar(fm.get("author", ""))
        if author_id and author_id not in author_ids:
            errors.append(
                f"{path.relative_to(ROOT)}: unknown contributor author {author_id!r}"
            )

        editorial_status = clean_scalar(fm.get("editorialStatus", ""))
        if editorial_status and editorial_status not in valid_editorial_statuses:
            errors.append(
                f"{path.relative_to(ROOT)}: invalid editorial status {editorial_status!r}"
            )

        slug = clean_scalar(fm.get("slug", path.stem))
        if slug in contributor_slugs:
            errors.append(
                f"Duplicate contributor slug: {slug!r} in "
                f"{contributor_slugs[slug].name} and {path.name}"
            )
        contributor_slugs[slug] = path

        for required_section in (
            "## Methodology",
            "## Risks and Counterarguments",
            "## Limitations",
            "## Sources",
            "## Disclosures",
        ):
            if required_section not in text:
                warnings.append(
                    f"{path.relative_to(ROOT)}: missing {required_section!r} section"
                )

    current_views_text = CURRENT_VIEWS.read_text(encoding="utf-8")
    linked_slugs = re.findall(
        r"href:\s*['\"]/research/([^/'\"]+)/['\"]",
        current_views_text,
    )

    for slug in linked_slugs:
        if slug not in slugs:
            errors.append(
                f"src/data/currentViews.ts: missing article for slug {slug!r}"
            )

    if "Research in progress" in current_views_text:
        errors.append(
            "src/data/currentViews.ts: remove remaining research placeholder"
        )

    if "/contributors/" in current_views_text:
        errors.append(
            "src/data/currentViews.ts: contributor content cannot enter Current Views"
        )

    all_text_files = [
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and path.suffix.lower()
        in {".astro", ".ts", ".md", ".mdx", ".js", ".json"}
        and not is_excluded(path)
    ]

    for path in all_text_files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        for label, pattern in FORBIDDEN_PATTERNS.items():
            if re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL):
                errors.append(f"{path.relative_to(ROOT)}: contains {label}")

    expected_assets = [
        PUBLIC / "downloads" / "commodity-regime-analysis.zip",
        PUBLIC / "downloads" / "commodity-regime-model.xlsx",
        PUBLIC / "models" / "commodity-regime-sensitivities.svg",
        PUBLIC / "models" / "commodity-regime-differences.svg",
        PUBLIC / "models" / "commodity-regime-thresholds.svg",
        PUBLIC / "models" / "commodity-regime-audit.svg",
        PUBLIC / "research-figures" / "brent-balance-and-price-outlook.svg",
        PUBLIC / "research-figures" / "copper-valuation-and-supply-gap.svg",
        PUBLIC / "research-figures" / "gold-real-yield-and-official-demand.svg",
        PUBLIC / "research-figures" / "gold-august-2026-reunderwriting.svg",
        PUBLIC / "research-figures" / "us-2s10s-steepener-framework.svg",
        ROOT / "scripts" / "generate_research_figures.py",
        ROOT / "src" / "pages" / "projects" / "commodity-regime-analysis.astro",
    ]

    for path in expected_assets:
        if not path.exists():
            errors.append(f"Missing public asset: {path.relative_to(ROOT)}")


    research_figure_pattern = re.compile(r'src=["\'](/research-figures/[^"\']+)["\']')
    for path in articles:
        text = path.read_text(encoding="utf-8")
        for asset_url in research_figure_pattern.findall(text):
            asset_path = PUBLIC / asset_url.lstrip("/")
            if not asset_path.exists():
                errors.append(
                    f"{path.relative_to(ROOT)}: missing research figure {asset_url}"
                )

    legacy_project_index = (
        PUBLIC / "projects" / "commodity-regime-analysis" / "index.html"
    )
    if legacy_project_index.exists():
        errors.append(
            "Remove legacy public project index: "
            f"{legacy_project_index.relative_to(ROOT)}"
        )

    package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    dependencies = {
        **package.get("dependencies", {}),
        **package.get("devDependencies", {}),
    }
    for unused_math_package in ("remark-math", "rehype-katex"):
        if unused_math_package in dependencies:
            errors.append(
                f"package.json: remove unused {unused_math_package} dependency"
            )

    generated_files = [
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and ("__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"})
    ]
    for path in generated_files:
        errors.append(
            f"Remove generated Python cache: {path.relative_to(ROOT)}"
        )


    head = (ROOT / "src" / "components" / "base" / "Head.astro").read_text(
        encoding="utf-8"
    )
    if "/icon-512.png" in head:
        errors.append(
            "src/components/base/Head.astro: browser favicon must use the SM favicon, not icon-512.png"
        )
    for required_icon in ("/favicon.ico?v=3", "/favicon-32.png?v=3"):
        if required_icon not in head:
            errors.append(
                f"src/components/base/Head.astro: missing favicon reference {required_icon}"
            )

    inherited_astro_svg = PUBLIC / "favicon.svg"
    if inherited_astro_svg.exists():
        svg_text = inherited_astro_svg.read_text(encoding="utf-8", errors="ignore")
        if "Astro" in svg_text or "vscodeIconsFileTypeLightAstro" in svg_text:
            errors.append(
                "public/favicon.svg: remove the inherited Astro favicon"
            )

    for icon_name in (
        "favicon.ico",
        "favicon-16.png",
        "favicon-32.png",
        "apple-touch-icon.png",
        "icon-192.png",
        "icon-512.png",
        "icon-mask.png",
    ):
        icon_path = PUBLIC / icon_name
        if not icon_path.exists():
            errors.append(f"Missing SM icon: {icon_path.relative_to(ROOT)}")

    inherited_astro_icon_hashes = {
        "2bdf29165175136c1b756461bebbd2a45cadde6ea4af74cf592c61ab859eb72d",
        "3e0dd854b9c66d3376ce1b347de7c990d9b123e13b5669013407fd90020718a1",
        "5c6c45ae48cbfae2dda4d8549199175f77f06d68738503fa36dea650fc3c404e",
    }
    for icon_name in ("apple-touch-icon.png", "icon-192.png", "icon-512.png"):
        icon_path = PUBLIC / icon_name
        if icon_path.exists():
            digest = hashlib.sha256(icon_path.read_bytes()).hexdigest()
            if digest in inherited_astro_icon_hashes:
                errors.append(
                    f"{icon_path.relative_to(ROOT)}: inherited Astro icon restored"
                )

    research_index = (ROOT / "src" / "pages" / "research" / "index.astro").read_text(
        encoding="utf-8"
    )
    if '<PageNavigation current="research" />' not in research_index:
        errors.append(
            "src/pages/research/index.astro: add the landing-page navigation row"
        )

    back_link = (
        ROOT / "src" / "components" / "widgets" / "BackLink.astro"
    ).read_text(encoding="utf-8")
    if "cd .." in back_link:
        errors.append(
            "src/components/widgets/BackLink.astro: replace inherited 'cd ..' copy"
        )

    config = (ROOT / "src" / "config.ts").read_text(encoding="utf-8")
    if "VERCEL_PROJECT_PRODUCTION_URL" not in config:
        errors.append(
            "src/config.ts: derive SITE.website from VERCEL_PROJECT_PRODUCTION_URL"
        )

    base_layout = (ROOT / "src" / "layouts" / "BaseLayout.astro").read_text(
        encoding="utf-8"
    )
    for integration in (
        "@vercel/analytics/astro",
        "@vercel/speed-insights/astro",
    ):
        if integration not in base_layout:
            errors.append(
                f"src/layouts/BaseLayout.astro: missing {integration}"
            )

    for removed_dependency in ("p5", "@types/p5"):
        if removed_dependency in dependencies:
            errors.append(
                f"package.json: remove unused {removed_dependency} dependency"
            )

    outcomes_page = ROOT / "src" / "pages" / "outcomes.astro"
    if not outcomes_page.exists():
        errors.append("Missing recruiter-facing decision log: src/pages/outcomes.astro")
    else:
        outcomes_text = outcomes_page.read_text(encoding="utf-8")
        normalized_outcomes_text = re.sub(r"\s+", " ", outcomes_text)
        if "audited portfolio returns" not in normalized_outcomes_text:
            errors.append(
                "src/pages/outcomes.astro: clarify that outcomes are not audited returns"
            )
        if "hit rate" in outcomes_text.lower():
            errors.append(
                "src/pages/outcomes.astro: do not present a student research hit rate"
            )

    if "path: '/outcomes'" not in config:
        errors.append("src/config.ts: add Outcomes to the primary navigation")

    if "path: '/contributors'" not in config:
        errors.append("src/config.ts: add Contributors to the primary navigation")

    contributor_architecture_files = (
        ROOT / "src" / "pages" / "contributors" / "index.astro",
        ROOT / "src" / "pages" / "contributors" / "submit.astro",
        ROOT / "src" / "pages" / "contributors" / "research" / "index.astro",
        ROOT
        / "src"
        / "pages"
        / "contributors"
        / "research"
        / "[...slug].astro",
        ROOT / "src" / "pages" / "contributors" / "[authorSlug].astro",
        ROOT / "src" / "pages" / "contributors" / "rss.xml.js",
        ROOT
        / "src"
        / "components"
        / "contributors"
        / "ContributorArticle.astro",
    )
    for path in contributor_architecture_files:
        if not path.exists():
            errors.append(
                f"Missing contributor-platform file: {path.relative_to(ROOT)}"
            )

    submission_form_url = (
        "https://docs.google.com/forms/d/e/"
        "1FAIpQLSeShurDNE3SwpHYr7QZXOTwFpDgcA6XuQl8vP5s0BhZEVbVfA/viewform"
    )
    submission_touchpoints = (
        ROOT / "src" / "pages" / "contributors" / "index.astro",
        ROOT / "src" / "pages" / "contributors" / "submit.astro",
        ROOT / "src" / "components" / "home" / "ContributorGateway.astro",
    )
    for path in submission_touchpoints:
        touchpoint_text = path.read_text(encoding="utf-8") if path.exists() else ""
        if path.exists() and submission_form_url not in touchpoint_text:
            errors.append(
                f"{path.relative_to(ROOT)}: missing canonical contributor form URL"
            )

    schema_text = (ROOT / "src" / "schema.ts").read_text(encoding="utf-8")
    for required_schema_rule in (
        "author: reference('authors')",
        "editorialStatus: z.enum(['Published', 'Revised'])",
        "disclosure: z.string().trim().min(1)",
        "shortBio: z.string().trim().max(420).default('')",
        "researchInterests: z.array(z.string().trim().min(1)).max(8).default([])",
    ):
        if required_schema_rule not in schema_text:
            errors.append(
                "src/schema.ts: missing contributor validation "
                f"({required_schema_rule})"
            )

    submission_guide_text = submission_touchpoints[1].read_text(encoding="utf-8")
    if "srinivas.medida05@gmail.com" not in submission_guide_text:
        errors.append(
            "src/pages/contributors/submit.astro: missing contributor email fallback"
        )
    if "srinivas.medida08@gmail.com" in submission_guide_text:
        errors.append(
            "src/pages/contributors/submit.astro: stale contributor submission email"
        )

    contributor_article_component = (
        ROOT
        / "src"
        / "components"
        / "contributors"
        / "ContributorArticle.astro"
    )
    if contributor_article_component.exists():
        contributor_article_text = contributor_article_component.read_text(
            encoding="utf-8"
        )
        for required_attribution in (
            "Contributor Research",
            "Written by",
            "This Contributor Research was written by",
            "analysis and conclusion are the author's own",
            "not a personal investment",
            "/contributors/${author.id}/",
        ):
            if required_attribution not in contributor_article_text:
                errors.append(
                    "ContributorArticle.astro: missing required attribution or "
                    f"responsibility copy ({required_attribution})"
                )

    outcomes_text = outcomes_page.read_text(encoding="utf-8")
    if "getFilteredContributorResearch" in outcomes_text:
        errors.append(
            "src/pages/outcomes.astro: contributor research cannot enter the Decision Log"
        )

    footer_text = (ROOT / "src" / "components" / "base" / "Footer.astro").read_text(
        encoding="utf-8"
    )
    if "'/outcomes/'" not in footer_text:
        errors.append("src/components/base/Footer.astro: add Outcomes link")

    investment_summary = (
        ROOT / "src" / "components" / "research" / "InvestmentSummary.astro"
    ).read_text(encoding="utf-8")
    for required_rule in (
        "list-style: none",
        ".summary-drivers li::before",
        "padding-left: 1rem",
    ):
        if required_rule not in investment_summary:
            errors.append(
                "src/components/research/InvestmentSummary.astro: "
                f"missing bullet-overlap fix ({required_rule})"
            )

    analysis_script = (
        PUBLIC
        / "projects"
        / "commodity-regime-analysis"
        / "commodity_regime_analysis.py"
    ).read_text(encoding="utf-8")
    if "contained 104 monthly rows" in analysis_script:
        errors.append(
            "commodity_regime_analysis.py: generated narrative still hardcodes raw row count"
        )
    if "write_summary(raw, model_data" not in analysis_script:
        errors.append(
            "commodity_regime_analysis.py: pass raw data into write_summary"
        )

    methodology = (
        PUBLIC
        / "projects"
        / "commodity-regime-analysis"
        / "docs"
        / "methodology.md"
    ).read_text(encoding="utf-8")
    if "median of the available lagged headline-CPI series" not in methodology:
        errors.append(
            "docs/methodology.md: explain the 2.68% robustness threshold"
        )

    results_csv = (
        PUBLIC
        / "projects"
        / "commodity-regime-analysis"
        / "outputs"
        / "primary_relationship_results.csv"
    )
    if results_csv.exists():
        header = results_csv.read_text(encoding="utf-8").splitlines()[0]
        if "Model" not in header.split(","):
            errors.append(
                "primary_relationship_results.csv: add a Model column"
            )

    global_markets_page = (
        ROOT / "src" / "pages" / "models" / "global-markets-simulation.mdx"
    )
    global_markets_data = ROOT / "src" / "data" / "globalMarketsSimulation.ts"
    selected_work_component = (
        ROOT / "src" / "components" / "models" / "SelectedWork.astro"
    )

    global_markets_components = (
        ROOT / "src" / "components" / "models" / "GlobalMarketsOverview.astro",
        ROOT / "src" / "components" / "models" / "GlobalMarketsAllocation.astro",
        ROOT / "src" / "components" / "models" / "GlobalMarketsMetrics.astro",
        ROOT / "src" / "components" / "models" / "GlobalMarketsLimitations.astro",
        ROOT / "src" / "components" / "models" / "GlobalMarketsSessionComparison.astro",
        ROOT / "src" / "components" / "models" / "GlobalMarketsSellSideComparison.astro",
        ROOT / "src" / "components" / "models" / "GlobalMarketsSessionLedger.astro",
    )

    for required_path in (
        global_markets_page,
        global_markets_data,
        *global_markets_components,
        ROOT / "src" / "components" / "models" / "ModelBreadcrumb.astro",
    ):
        if not required_path.exists():
            errors.append(
                f"Missing Global Markets project file: {required_path.relative_to(ROOT)}"
            )

    if global_markets_page.exists() and global_markets_data.exists():
        global_markets_page_text = global_markets_page.read_text(encoding="utf-8")
        global_markets_data_text = global_markets_data.read_text(encoding="utf-8")
        global_markets_component_text = "\n".join(
            component.read_text(encoding="utf-8")
            for component in global_markets_components
            if component.exists()
        )
        combined_global_markets_text = "\n".join(
            (
                global_markets_page_text,
                global_markets_data_text,
                global_markets_component_text,
            )
        )
        normalized_global_markets_text = re.sub(
            r"\s+", " ", combined_global_markets_text
        ).lower()

        required_global_markets_values = {
            "29 July participant count": "participantCount: 102",
            "29 July displayed buy-side rank": "displayedLeaderboardRank: 2",
            "29 July buy-side score": "exactSessionScore: 93.05",
            "29 July portal P&L": "portalPnl: 3_801_651",
            "29 July return": "returnOnInitialFunds: 19",
            "29 July Sharpe ratio": "sharpeRatio: 1.2",
            "29 July portfolio-value field": "portfolioValueField: 21_536_948.55",
            "29 July commission": "commissionPaid: -214_627",
            "29 July average net exposure": "averageNetExposure: 553_247",
            "29 July average contract exposure": "averageContractExposure: -2_391.55",
            "29 July chat and voice trades": "chatAndVoiceTrades: 7",
            "29 July exchange trades": "exchangeTrades: 5",
            "29 July BSRM": "value: 98.98",
            "29 July execution": "value: 96.08",
            "29 July risk appetite": "value: 70.19",
            "29 July ROI platform subscore": "value: 100",
            "29 July average equity allocation": "equities: 70.2",
            "29 July average cash allocation": "cash: 29.8",
            "29 July final equity allocation": "equities: 99.5",
            "29 July final cash allocation": "cash: 0.5",
            "22 July buy-side P&L": "portalPnl: 2_907_448",
            "22 July buy-side return": "returnOnInitialFunds: 14.5",
            "22 July buy-side Sharpe": "sharpeRatio: 0.66",
            "22 July buy-side score": "exactSessionScore: 79.18",
            "22 July buy-side composite rank": "compositeLeaderboardRank: 25",
            "22 July buy-side P&L rank": "pnlRank: 4",
            "22 July final cash allocation": "cash: 73.6",
            "27 July sell-side score": "exactSessionScore: 88.89",
            "27 July sell-side trading P&L": "tradingPnl: 842_052",
            "27 July sell-side commission": "commissionRevenue: 153_635",
            "27 July sell-side total P&L": "totalPnl: 995_687",
            "27 July sell-side rank": "overallLeaderboardRank: 8",
            "27 July participant count": "participantCount: 93",
            "27 July exchange trades": "exchangeTrades: 499",
            "27 July chat trades": "chatTrades: 13",
            "29 July sell-side participant count": "participantCount: 104",
            "29 July sell-side rank": "overallLeaderboardRank: 15",
            "29 July sell-side score": "exactSessionScore: 77.78",
            "29 July sell-side commission": "commissionRevenue: 192_145",
            "29 July sell-side trading P&L": "tradingPnl: -496_309",
            "29 July sell-side total P&L": "totalPnl: -304_164",
            "29 July sell-side exchange trades": "exchangeTrades: 389",
            "29 July sell-side chat trades": "chatTrades: 21",
            "initial-session date": "date: '2026-07-15'",
            "initial-session score": "exactSessionScore: 60.73",
            "initial-session P&L": "portalPnl: 1_836_906",
            "3 August date": "date: '2026-08-03'",
            "3 August buy-side participant count": "participantCount: 93",
            "3 August buy-side rank": "leaderboardRank: 5",
            "3 August buy-side score": "exactSessionScore: 89.68",
            "3 August buy-side P&L": "portalPnl: 3_330_183",
            "3 August buy-side commission": "commissionPaid: -268_753",
            "3 August buy-side portfolio value": "portfolioValue: 23_019_276.57",
            "3 August buy-side ROI subscore": "roi: 100",
            "3 August buy-side execution": "execution: 69.57",
            "3 August buy-side risk management": "buySideRiskManagement: 98.81",
            "3 August buy-side risk appetite": "riskAppetite: 80.01",
            "3 August sell-side participant count": "participantCount: 96",
            "3 August sell-side rank": "leaderboardRank: 9",
            "3 August sell-side score": "exactSessionScore: 89.04",
            "3 August sell-side commission": "commissionRevenue: 202_035",
            "3 August sell-side trading P&L": "tradingPnl: 893_072",
            "3 August derived sell-side total P&L": "derivedTotalPnl: 1_095_107",
            "3 August sell-side chat trades": "chatTrades: 18",
            "3 August sell-side commission metric": "commissionMetric: 76.32",
            "3 August sell-side exchange-trade metric": "exchangeTradeMetric: 100",
            "3 August sell-side risk management": "sellSideRiskManagement: 84.21",
        }

        for label, value in required_global_markets_values.items():
            if value not in combined_global_markets_text:
                errors.append(
                    f"Global Markets simulation: missing exact {label} value ({value})"
                )

        for forbidden_claim in (
            "1st/102",
            "1st of 102",
            "officially ranked first",
            "won the event",
            "top 1%",
            "100% return",
            "4th/148",
            "4th of 148",
            "4th/153",
            "4th of 153",
            "8th overall",
            "89% combined",
            "overall 89%",
        ):
            if forbidden_claim.lower() in global_markets_page_text.lower():
                errors.append(
                    "global-markets-simulation.mdx: remove unsupported or "
                    f"ambiguous claim ({forbidden_claim})"
                )

        for percentage, required_context in (
            (r"88\.89%", "sell-side"),
            (r"77\.78%", "sell-side"),
            (r"89\.04%", "sell-side"),
            (r"93\.05%", "asset-management"),
            (r"89\.68%", "asset-management"),
        ):
            for match in re.finditer(percentage, global_markets_page_text):
                window_start = max(0, match.start() - 150)
                window_end = min(len(global_markets_page_text), match.end() + 150)
                context = global_markets_page_text[window_start:window_end].lower()
                if required_context not in context:
                    errors.append(
                        "global-markets-simulation.mdx: every "
                        f"{percentage.replace('\\', '')} reference must be explicitly "
                        f"labelled {required_context}"
                    )

        for required_phrase in (
            "simulated rather than real capital",
            "without the weighting formula",
            "displayed 2nd of 102",
            "highest valid",
            "first-place result was subsequently voided",
            "portal-reported p&amp;l",
            "does not mechanically reconcile",
            "99.5% equities",
            "100% roi figure is a proprietary platform subscore",
            "77.78% figure is a sell-side score",
            "different cohorts, market paths and news sequences",
            "strongest role-specific results occurred on different dates",
            "principal sell-side result",
            "strongest same-event evidence across both mandates",
            "5th of 93",
            "9th of 96",
            "simultaneous top-decile performance across both roles",
            "sell-side total of <strong>$1,095,107 is derived</strong>",
        ):
            if required_phrase.lower() not in normalized_global_markets_text:
                errors.append(
                    "global-markets-simulation.mdx: missing limitation or "
                    f"interpretation wording ({required_phrase})"
                )

    models_page_text = (ROOT / "src" / "pages" / "models.mdx").read_text(
        encoding="utf-8"
    )
    for required_models_copy in (
        "Dual-Role Global Markets Simulation",
        "href: '/models/global-markets-simulation/'",
        "93.05% score",
        "$3.80m of portal-reported P&L",
        "highest valid finisher",
        "19.0% return",
        "1.20 Sharpe",
        "8th of 93",
        "July–August 2026",
    ):
        if required_models_copy not in models_page_text:
            errors.append(
                f"src/pages/models.mdx: missing Global Markets card copy ({required_models_copy})"
            )

    if selected_work_component.exists():
        selected_work_text = selected_work_component.read_text(encoding="utf-8")
        for required_link_support in ("href?: string", "linkLabel?: string"):
            if required_link_support not in selected_work_text:
                errors.append(
                    "src/components/models/SelectedWork.astro: missing linked-card "
                    f"support ({required_link_support})"
                )

    model_methodology_page = (
        ROOT / "src" / "pages" / "models" / "commodity-regime-analysis.mdx"
    ).read_text(encoding="utf-8")
    if "CommodityRegimeResults" not in model_methodology_page:
        errors.append(
            "commodity-regime-analysis.mdx: render results from generated outputs"
        )
    if "walk-forward testing" not in model_methodology_page:
        errors.append(
            "commodity-regime-analysis.mdx: disclose that contemporaneous sensitivity is not a trading signal"
        )
    for hardcoded_result in ("-0.030</td>", "0.493</td>", "0.016</td>"):
        if hardcoded_result in model_methodology_page:
            errors.append(
                "commodity-regime-analysis.mdx: remove hardcoded result table"
            )

    errors = list(dict.fromkeys(errors))
    warnings = list(dict.fromkeys(warnings))

    print(f"Articles checked: {len(articles)}")
    print(f"Errors: {len(errors)}")
    for item in errors:
        print(f"  ERROR: {item}")

    print(f"Warnings: {len(warnings)}")
    for item in warnings:
        print(f"  WARNING: {item}")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
