import { glob } from 'astro/loaders'
import { defineCollection } from 'astro:content'

import {
  authorSchema,
  contributorResearchSchema,
  pageSchema,
  postSchema,
} from '~/schema'

const pages = defineCollection({
  loader: glob({
    base: './src/pages',
    pattern: '**/*.mdx',
  }),
  schema: pageSchema,
})

const blog = defineCollection({
  loader: glob({
    base: './src/content/blog',
    pattern: '**/[^_]*.{md,mdx}',
  }),
  schema: postSchema,
})

const authors = defineCollection({
  loader: glob({
    base: './src/content/authors',
    pattern: '**/[^_]*.json',
  }),
  schema: authorSchema,
})

const contributorResearch = defineCollection({
  loader: glob({
    base: './src/content/contributors',
    pattern: '**/[^_]*.{md,mdx}',
  }),
  schema: contributorResearchSchema,
})

export const collections = {
  pages,
  blog,
  authors,
  contributorResearch,
}
