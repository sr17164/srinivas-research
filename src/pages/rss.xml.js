import { getCollection } from 'astro:content'
import rss from '@astrojs/rss'

import { SITE } from '~/config'
import { withBasePath } from '~/utils/path'

export async function GET() {
  const researchItems = await getCollection('blog')

  const publishedItems = researchItems
    .filter((item) => !item.data.draft)
    .sort(
      (a, b) =>
        new Date(b.data.pubDate).getTime() - new Date(a.data.pubDate).getTime()
    )

  const siteUrl = SITE.website.endsWith('/') ? SITE.website : `${SITE.website}/`

  const feedImageUrl = new URL('icon-512.png', siteUrl).toString()

  return rss({
    title: SITE.title,
    description: SITE.description,
    site: siteUrl,

    customData: `
      <language>${SITE.lang}</language>
      <lastBuildDate>${new Date().toUTCString()}</lastBuildDate>
      <image>
        <title>${SITE.title}</title>
        <url>${feedImageUrl}</url>
        <link>${siteUrl}</link>
      </image>
    `,

    items: publishedItems.map((item) => ({
      title: item.data.title,
      link: withBasePath(`/research/${item.id}/`),
      pubDate: item.data.pubDate,
      description: item.data.description,
      author: SITE.author,
    })),

    stylesheet: withBasePath('/rss-styles.xsl'),
  })
}
