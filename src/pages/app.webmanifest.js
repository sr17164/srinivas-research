import { withBasePath } from '~/utils/path'

export async function GET() {
  const manifest = {
    id: withBasePath('/'),
    name: 'SM Research',
    short_name: 'SM Research',
    description:
      'Independent research on commodity markets, macroeconomic forces, valuation and capital allocation, supported by financial modelling and quantitative analysis by Srinivas Medida.',
    icons: [
      {
        src: withBasePath('/icon-192.png'),
        type: 'image/png',
        sizes: '192x192',
      },
      {
        src: withBasePath('/icon-512.png'),
        type: 'image/png',
        sizes: '512x512',
      },
      {
        src: withBasePath('/icon-mask.png'),
        type: 'image/png',
        sizes: '512x512',
        purpose: 'maskable',
      },
    ],
    scope: withBasePath('/'),
    start_url: withBasePath('/'),
    display: 'standalone',
    orientation: 'portrait-primary',
    categories: ['finance', 'education', 'business'],
    theme_color: '#ffffff',
    background_color: '#ffffff',
  }

  return new Response(JSON.stringify(manifest), {
    headers: {
      'Content-Type': 'application/manifest+json; charset=utf-8',
    },
  })
}
