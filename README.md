# SM Research

Independent investment research by Srinivas Medida, covering commodity markets, macroeconomic forces, valuation, capital allocation and quantitative analysis.

## Technology

- [Astro](https://astro.build/)
- TypeScript
- MDX content collections
- UnoCSS
- Pagefind search
- Vercel deployment

## Local development

This project uses pnpm and requires Node.js 22.12 or later.

```bash
pnpm install
pnpm dev
```

The development server will print the local URL in the terminal.

## Quality checks

```bash
pnpm run check
pnpm run lint
python3 scripts/site_audit.py
pnpm run build
```

## Production deployment

The site is configured for Vercel. Generated folders such as `node_modules`, `.astro` and `dist` are intentionally excluded from version control and should not be uploaded manually. Vercel installs dependencies from `package.json` and `pnpm-lock.yaml`, then runs the production build.

Before connecting the final custom domain, update `SITE.website` in `src/config.ts`:

```ts
website: 'https://example.com/',
```

Keep the trailing slash.

## Content

Research articles are stored in `src/content/blog`. Downloadable models and related files are stored under `public/models` and `public/downloads`.

## Attribution

The site is based on the MIT-licensed Astro AntfuStyle Theme. See `LICENSE` for the original licence terms.
