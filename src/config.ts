import type { Site, Ui, Features } from './types'

const productionHost =
  process.env.VERCEL_PROJECT_PRODUCTION_URL ?? process.env.VERCEL_URL
const website = (
  productionHost ? `https://${productionHost}/` : 'http://localhost:4321/'
) as Site['website']

export const SITE: Site = {
  website,
  base: '/',
  title: 'SM Research',
  description:
    'Independent research on commodity markets, macroeconomic forces, valuation and capital allocation, supported by financial modelling and quantitative analysis.',
  author: 'Srinivas Medida',
  lang: 'en',
  ogLocale: 'en_GB',
  imageDomains: ['images.unsplash.com'],
}

export const UI: Ui = {
  internalNavs: [
    {
      path: '/research',
      title: 'Research',
      displayMode: 'alwaysText',
      text: 'Research',
    },
    {
      path: '/models',
      title: 'Models',
      displayMode: 'alwaysText',
      text: 'Models',
    },
    {
      path: '/about',
      title: 'About',
      displayMode: 'alwaysText',
      text: 'About',
    },
  ],

  socialLinks: [],

  navBarLayout: {
    left: [],
    right: ['internalNavs', 'hr', 'searchButton', 'themeButton'],
    mergeOnMobile: true,
  },

  tabbedLayoutTabs: [
    {
      title: 'Research',
      path: '/research',
    },
    {
      title: 'Models',
      path: '/models',
    },
  ],

  postView: {
    postMetaStyle: 'minimal',
    useCoverAltAsCaption: true,
  },

  groupView: {
    maxGroupColumns: 3,
    showGroupItemColorOnHover: true,
  },

  githubView: {
    monorepos: [],
    mainLogoOverrides: [],
    subLogoMatches: [],
  },

  externalLink: {
    newTab: true,
    cursorType: '',
    showNewTabIcon: false,
  },
}

/**
 * Globally controls optional site features.
 */
export const FEATURES: Features = {
  slideEnterAnim: [
    true,
    {
      enterStep: 80,
    },
  ],

  ogImage: [
    true,
    {
      authorOrBrand: SITE.title,
      fallbackTitle: 'Research on markets, valuation and capital allocation.',
      fallbackBgType: 'plum',
      collections: [
        {
          collection: 'blog',
          pathnamePrefix: '/research',
        },
      ],
    },
  ],

  toc: [
    true,
    {
      minHeadingLevel: 2,
      maxHeadingLevel: 4,
      displayPosition: 'right',
      displayMode: 'content',
    },
  ],

  share: false,

  giscus: false,

  search: [
    true,
    {
      includes: ['blog'],
      filter: true,
      navHighlight: true,
      batchLoadSize: [true, 5],
      maxItemsPerPage: [true, 3],
    },
  ],

  tag: [
    true,
    {
      displayPosition: 'right',
      displayMode: 'content',
      filterMode: 'AND',
    },
  ],
}
