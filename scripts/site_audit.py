#!/usr/bin/env python3
"""Static pre-publication checks for SM Research.

This does not replace `pnpm check`, `pnpm lint` or `pnpm build`. It catches
content and packaging errors that are easy to miss during editorial work.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLOG = ROOT / "src" / "content" / "blog"
PUBLIC = ROOT / "public"

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
        match = re.match(
            r"^([A-Za-z][A-Za-z0-9_]*):\s*(.*)$",
            line,
        )

        if match:
            data[match.group(1)] = match.group(2).strip()

    return data


def is_excluded(path: Path) -> bool:
    relative_parts = path.relative_to(ROOT).parts

    return any(
        part in EXCLUDED_DIRECTORIES
        for part in relative_parts
    )


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    slugs: dict[str, Path] = {}
    titles: dict[str, Path] = {}

    articles = sorted(
        [
            *BLOG.glob("*.md"),
            *BLOG.glob("*.mdx"),
        ]
    )

    for path in articles:
        text = path.read_text(encoding="utf-8")
        fm = frontmatter(text)

        missing = sorted(REQUIRED_FRONTMATTER - set(fm))

        if missing:
            errors.append(
                f"{path.relative_to(ROOT)}: "
                f"missing frontmatter {missing}"
            )

        title = fm.get("title", "").strip("'\"")
        slug = fm.get("slug", "").strip("'\"")

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

        if "## Sources" not in text:
            warnings.append(
                f"{path.relative_to(ROOT)}: "
                "no '## Sources' section"
            )

        if (
            "## Research Methodology" not in text
            and "## Methodology" not in text
        ):
            warnings.append(
                f"{path.relative_to(ROOT)}: "
                "no methodology section"
            )

        for label, pattern in FORBIDDEN_PATTERNS.items():
            if re.search(
                pattern,
                text,
                flags=re.IGNORECASE | re.DOTALL,
            ):
                errors.append(
                    f"{path.relative_to(ROOT)}: contains {label}"
                )

    all_text_files = [
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and path.suffix.lower()
        in {
            ".astro",
            ".ts",
            ".md",
            ".mdx",
            ".js",
            ".json",
        }
        and not is_excluded(path)
    ]

    for path in all_text_files:
        text = path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

        for label, pattern in FORBIDDEN_PATTERNS.items():
            if re.search(
                pattern,
                text,
                flags=re.IGNORECASE | re.DOTALL,
            ):
                errors.append(
                    f"{path.relative_to(ROOT)}: contains {label}"
                )

    expected_assets = [
        PUBLIC / "downloads" / "commodity-regime-analysis.zip",
        PUBLIC / "downloads" / "commodity-regime-model.xlsx",
        PUBLIC / "models" / "commodity-equity-sensitivity.png",
        PUBLIC / "models" / "brent-threshold-robustness.png",
        ROOT
        / "src"
        / "pages"
        / "projects"
        / "commodity-regime-analysis.astro",
    ]

    for path in expected_assets:
        if not path.exists():
            errors.append(
                f"Missing public asset: {path.relative_to(ROOT)}"
            )

    legacy_project_index = (
        PUBLIC / "projects" / "commodity-regime-analysis" / "index.html"
    )
    if legacy_project_index.exists():
        errors.append(
            "Remove legacy public project index: "
            f"{legacy_project_index.relative_to(ROOT)}"
        )

    config_path = ROOT / "src" / "config.ts"
    config = config_path.read_text(encoding="utf-8")

    if "https://your-final-domain.com/" in config:
        warnings.append(
            "src/config.ts: SITE.website still uses the "
            "production-domain placeholder"
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
