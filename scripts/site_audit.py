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
        PUBLIC / "models" / "commodity-equity-sensitivity.png",
        PUBLIC / "models" / "brent-threshold-robustness.png",
        ROOT / "src" / "pages" / "projects" / "commodity-regime-analysis.astro",
    ]

    for path in expected_assets:
        if not path.exists():
            errors.append(f"Missing public asset: {path.relative_to(ROOT)}")

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
