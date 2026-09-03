import { getEntry } from 'astro:content'
import rss from '@astrojs/rss'

import { SITE } from '~/config'
import {
  getFilteredContributorResearch,
  getSortedContributorResearch,
} from '~/utils/data'
import { withBasePath } from '~/utils/path'

export async function GET() {
  const items = getSortedContributorResearch(
    await getFilteredContributorResearch()
  )
  const siteUrl = SITE.website.endsWith('/') ? SITE.website : `${SITE.website}/`

  const feedItems = await Promise.all(
    items.map(async (item) => {
      const author = await getEntry(item.data.author)

      if (!author) {
        throw new Error(`Contributor article ${item.id} has no valid author.`)
      }

      return {
        title: item.data.title,
        link: withBasePath(`/contributors/research/${item.id}/`),
        pubDate: item.data.pubDate,
        description: item.data.description,
        author: author.data.fullName,
        categories: [
          'Contributor Research',
          item.data.reportType,
          ...item.data.tags,
        ],
      }
    })
  )

  return rss({
    title: `${SITE.title} — Contributor Research`,
    description:
      'Independently authored student research published through the SM Research contributor channel.',
    site: siteUrl,
    items: feedItems,
    stylesheet: withBasePath('/rss-styles.xsl'),
  })
}
