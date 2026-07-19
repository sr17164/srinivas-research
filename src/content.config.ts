import { glob } from 'astro/loaders'
import { defineCollection } from 'astro:content'

import { pageSchema, postSchema } from '~/schema'

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

export const collections = {
  pages,
  blog,
}
