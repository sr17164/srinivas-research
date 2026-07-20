# SM Research

Independent investment research by Srinivas Medida, covering commodity markets, macroeconomic forces, valuation, capital allocation and quantitative analysis.

## Technology

- Astro and TypeScript
- MDX content collections
- UnoCSS
- Pagefind search
- Static deployment on Vercel

## Local development

This project uses pnpm and requires Node.js 22.12 or later.

```bash
pnpm install
pnpm dev
```

The development server prints the local URL in the terminal.

## Pre-publication checks

Run the complete quality gate before every production push:

```bash
pnpm validate
```

The command runs Astro diagnostics, ESLint, Prettier, the custom content audit and a full production build.

The custom audit validates frontmatter, duplicate slugs and titles, methodology and source sections, current-view article links, featured-article consistency, navigation, favicon configuration and required downloadable assets.

## Publishing research

Research articles are stored in `src/content/blog` as MDX files. Each public article should include:

- complete frontmatter and a unique slug
- a clear stance and time horizon where relevant
- scenario analysis and explicit invalidation conditions
- a research-methodology section
- a dated source list and informational-use disclaimer

Homepage market views are maintained in `src/data/currentViews.ts`. When a view has a completed article, set its `href` to the article slug and remove any `researchStatus` placeholder.

## Branding and icons

The standalone SM favicon is generated from `public/favicon.png`. The browser uses the versioned 16px, 32px and ICO variants declared in `src/components/base/Head.astro`; the PWA manifest uses the 192px and 512px SM variants. Do not restore the inherited Astro icon files.

## Models and downloads

- Public model summaries: `src/pages/models/`
- Public project page: `src/pages/projects/`
- Downloadable files: `public/downloads/`
- Reproducibility package: `public/projects/commodity-regime-analysis/`

Do not commit generated folders such as `node_modules`, `.astro` or `dist`. Vercel installs dependencies from `package.json` and `pnpm-lock.yaml` and creates the production build automatically.

## Production deployment

The repository is intended to be connected to Vercel through GitHub. Each push to `main` triggers a production build; other branches can receive preview deployments.

After Vercel assigns the final production address, update `SITE.website` in `src/config.ts`:

```ts
website: 'https://your-project.vercel.app/',
```

Keep the trailing slash. This value supplies canonical URLs, the sitemap, RSS metadata, Open Graph metadata and structured data.

## Project maintenance

The site intentionally omits the inherited theme demo content, sponsorship configuration, sample workflows, unused visual assets and unused math-rendering dependencies. Dollar-denominated market ranges are rendered as normal prose rather than being interpreted as LaTeX.

The project retains its upstream MIT licence and attribution in `LICENSE`.
