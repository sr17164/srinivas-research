import { getCollection } from 'astro:content'

import { SITE } from '../config'

import type { CollectionEntry } from 'astro:content'
import type { GitHubView } from '~/types'

type BlogEntry = CollectionEntry<'blog'>
type BlogEntryList = BlogEntry[]

/**
 * Ensures that a value is a positive integer.
 */
function ensurePositiveInteger(value: number, name: string) {
  if (Number.isInteger(value) && value > 0) return value

  throw new Error(
    `'${name}' must be a positive integer. Please check 'src/config.ts' for the correct configuration.`
  )
}

/**
 * Parses a tuple containing an enabled state and numeric value.
 */
export function parseTuple(
  tuple: boolean | [boolean, number] | undefined,
  name: string
) {
  if (!tuple || !Array.isArray(tuple) || !tuple[0]) return undefined

  return ensurePositiveInteger(tuple[1], name)
}

/**
 * Resolves the displayed reading time for a research article.
 */
export function getMinutesRead(
  minutesRead: number | boolean,
  computedMinutesRead: number
) {
  if (minutesRead === false) return 0

  if (typeof minutesRead === 'number' && minutesRead > 0) {
    return minutesRead
  }

  return computedMinutesRead
}

/**
 * Retrieves research articles.
 * Draft articles remain visible during development but are excluded in
 * production.
 */
export async function getFilteredPosts(): Promise<BlogEntryList> {
  return await getCollection('blog', ({ data }) => {
    return import.meta.env.PROD ? !data.draft : true
  })
}

/**
 * Sorts research articles by publication date in descending order.
 */
export function getSortedPosts(posts: BlogEntryList): BlogEntryList {
  return [...posts].sort(
    (a, b) => b.data.pubDate.valueOf() - a.data.pubDate.valueOf()
  )
}

/**
 * Sorts research articles by title, publication date or modification date.
 */
export function sortPostsByField(
  posts: BlogEntryList,
  field: 'pubDate' | 'lastModDate' | 'title'
): BlogEntryList {
  return [...posts].sort((a, b) => {
    if (field === 'title') {
      return a.data.title.localeCompare(b.data.title, SITE.lang, {
        sensitivity: 'base',
      })
    }

    if (field === 'pubDate') {
      return b.data.pubDate.valueOf() - a.data.pubDate.valueOf()
    }

    const aDate =
      a.data.lastModDate instanceof Date ? a.data.lastModDate.valueOf() : 0

    const bDate =
      b.data.lastModDate instanceof Date ? b.data.lastModDate.valueOf() : 0

    return bDate - aDate
  })
}

/**
 * Returns a matching logo override from the supplied configuration.
 */
export function matchLogo(
  input: string,
  logos: GitHubView['mainLogoOverrides'] | GitHubView['subLogoMatches']
) {
  for (const [pattern, logo] of logos) {
    if (typeof pattern === 'string' && input === pattern) {
      return logo
    }

    if (pattern instanceof RegExp && pattern.test(input)) {
      return logo
    }
  }

  return undefined
}

/**
 * Extracts the package name before a version suffix.
 */
export function extractPackageName(tagName: string) {
  const match = tagName.match(/(^@?[^@]+?)(?:@)/)

  return match ? match[1] : tagName
}

/**
 * Extracts a semantic version number from a tag.
 */
export function extractVersionNum(tagName: string) {
  const match = tagName.match(/.+(\d+\.\d+\.\d+(?:-[\w.]+)?)(?:\s|$)/)

  return match ? match[1] : tagName
}

/**
 * Separates the highlighted portion of a semantic version number.
 */
export function processVersion(
  versionNum: string
): ['major' | 'minor' | 'patch' | 'pre', string, string] {
  const parts = versionNum.split(/(\.)/g)
  let highlightedIndex = -1
  let versionType: 'major' | 'minor' | 'patch' | 'pre'

  for (let index = parts.length - 1; index >= 0; index--) {
    if (parts[index] === '.') continue

    const value = Number(parts[index])

    if (!Number.isNaN(value) && value > 0) {
      highlightedIndex = index
      break
    }
  }

  if (highlightedIndex === 0) {
    versionType = 'major'
  } else if (highlightedIndex === 2) {
    versionType = 'minor'
  } else if (highlightedIndex === 4) {
    versionType = 'patch'
  } else {
    versionType = 'pre'
  }

  const nonHighlightedPart = parts.slice(0, highlightedIndex).join('')
  const highlightedPart = parts.slice(highlightedIndex).join('')

  return [versionType, nonHighlightedPart, highlightedPart]
}

/**
 * Builds tag relationships from article tag groups.
 */
export function buildTagRelations(
  input: string[][] | string[] | Record<string, string[]>
): {
  unique: string[]
  relations: Record<string, string[]>
} {
  const relationMap = new Map<string, Set<string>>()

  const ensure = (key: string): Set<string> => {
    const existing = relationMap.get(key)

    if (existing) return existing

    const created = new Set<string>()
    relationMap.set(key, created)

    return created
  }

  const isStringMatrix = (value: unknown[]): value is string[][] =>
    value.length > 0 && Array.isArray(value[0])

  if (Array.isArray(input)) {
    if (isStringMatrix(input)) {
      for (const group of input) {
        const cleanedTags = Array.from(
          new Set(group.map((tag) => tag.trim()).filter(Boolean))
        )

        for (const currentTag of cleanedTags) {
          const relatedTags = ensure(currentTag)

          for (const candidateTag of cleanedTags) {
            if (candidateTag !== currentTag) {
              relatedTags.add(candidateTag)
            }
          }
        }
      }
    } else {
      for (const tag of input) {
        const cleanedTag = String(tag).trim()

        if (cleanedTag) ensure(cleanedTag)
      }
    }
  } else {
    for (const [tag, related] of Object.entries(input)) {
      const relatedTags = ensure(tag)

      for (const relatedTag of related) {
        if (relatedTag && relatedTag !== tag) {
          relatedTags.add(relatedTag)
        }
      }
    }
  }

  const unique = Array.from(relationMap.keys()).sort((a, b) =>
    a.localeCompare(b)
  )

  const relations: Record<string, string[]> = {}

  for (const tag of unique) {
    relations[tag] = Array.from(relationMap.get(tag) ?? [])
  }

  return {
    unique,
    relations,
  }
}
