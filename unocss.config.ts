import {
  defineConfig,
  presetWind3,
  presetAttributify,
  presetIcons,
  transformerVariantGroup,
} from 'unocss'

import { UI } from './src/config'

import type { PresetWind3Theme } from 'unocss'
import type {
  IconNavItem,
  ResponsiveNavItem,
  IconSocialItem,
  ResponsiveSocialItem,
} from './src/types'

const { internalNavs, socialLinks, githubView } = UI

const navIcons = internalNavs
  .filter(
    (item) =>
      item.displayMode !== 'alwaysText' &&
      item.displayMode !== 'textHiddenOnMobile'
  )
  .map((item) => (item as IconNavItem | ResponsiveNavItem).icon)

const socialIcons = socialLinks
  .filter(
    (item) =>
      item.displayMode !== 'alwaysText' &&
      item.displayMode !== 'textHiddenOnMobile'
  )
  .map((item) => (item as IconSocialItem | ResponsiveSocialItem).icon)

const githubVersionColor: Record<string, string> = {
  major: 'bg-rose/15 text-rose-700 dark:text-rose-300',
  minor: 'bg-purple/15 text-purple-700 dark:text-purple-300',
  patch: 'bg-green/15 text-green-700 dark:text-green-300',
  pre: 'bg-teal/15 text-teal-700 dark:text-teal-300',
}

const githubVersionClass = Object.keys(githubVersionColor).map(
  (key) => `github-${key}`
)

const githubSubLogos = githubView.subLogoMatches.map((item) => item[1])

export default defineConfig<PresetWind3Theme>({
  content: {
    filesystem: [
      './src/content/**/*.{md,mdx}',
      './src/pages/**/*.{astro,md,mdx}',
      './src/{layouts,components}/**/*.astro',
    ],
  },

  extendTheme: (theme) => {
    return {
      ...theme,
      breakpoints: {
        ...theme.breakpoints,
        lgp: '1128px',
      },
      fontFamily: {
        ...theme.fontFamily,
        sans: 'var(--font-sans)',
        mono: 'var(--font-mono)',
        condensed: 'var(--font-condensed)',
      },
    }
  },

  rules: [],

  shortcuts: [
    [
      /^(\w+)-transition(?:-(\d+))?$/,
      (match) =>
        `transition-${
          match[1] === 'op' ? 'opacity' : match[1]
        } duration-${match[2] ? match[2] : '300'} ease-in-out`,
    ],

    [
      /^shadow-custom_(-?\d+)_(-?\d+)_(-?\d+)_(-?\d+)$/,
      ([_, x, y, blur, spread]) =>
        `shadow-[${x}px_${y}px_${blur}px_${spread}px_rgba(0,0,0,0.2)] dark:shadow-[${x}px_${y}px_${blur}px_${spread}px_rgba(255,255,255,0.25)]`,
    ],

    [
      /^btn-(\w+)$/,
      ([_, color]) =>
        [
          'inline-flex',
          'items-center',
          'justify-center',
          'whitespace-nowrap',
          'px-3',
          'py-1.5',
          'border',
          'border-[#8885]!',
          'rounded',
          'bg-transparent',
          'op-70',
          'no-underline!',
          'decoration-none!',
          'transition-all',
          'duration-200',
          'ease-out',

          `hover:op-100`,
          `hover:text-${color}`,
          `hover:border-${color}/45!`,
          `hover:bg-${color}/10`,
          'hover:no-underline!',
          'hover:decoration-none!',

          `focus:op-100`,
          `focus:text-${color}`,
          `focus:border-${color}/45!`,
          `focus:bg-${color}/10`,
          'focus:outline-none',
          'focus:no-underline!',
          'focus:decoration-none!',

          `focus-visible:op-100`,
          `focus-visible:text-${color}`,
          `focus-visible:border-${color}/55!`,
          `focus-visible:bg-${color}/10`,
          `focus-visible:ring-2`,
          `focus-visible:ring-${color}/20`,
          'focus-visible:outline-none',
          'focus-visible:no-underline!',
          'focus-visible:decoration-none!',

          'active:no-underline!',
          'active:decoration-none!',
        ].join(' '),
    ],

    [
      /^github-(major|minor|patch|pre)$/,
      ([, version]) => `rounded ${githubVersionColor[version]}`,
    ],
  ],

  presets: [
    presetWind3(),

    presetAttributify({
      strict: true,
      prefix: 'u-',
      prefixedOnly: false,
    }),

    presetIcons({
      extraProperties: {
        'display': 'inline-block',
        'height': '1.2em',
        'width': '1.2em',
        'vertical-align': 'text-bottom',
      },
    }),
  ],

  transformers: [transformerVariantGroup()],

  safelist: [
    ...navIcons,
    ...socialIcons,
    ...githubVersionClass,
    ...githubSubLogos,

    'btn-slate',
    'btn-blue',
    'btn-emerald',
    'btn-amber',
    'btn-rose',
    'btn-violet',
    'btn-cyan',
  ],
})
