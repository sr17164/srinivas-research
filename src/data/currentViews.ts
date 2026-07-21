export type MarketStance =
  'Bullish' | 'Mildly Bullish' | 'Neutral' | 'Mildly Bearish' | 'Bearish'

export interface CurrentView {
  market: string
  stance: MarketStance
  timeHorizon: string
  rationale: string
  href?: string
  linkLabel?: string
  researchStatus?: string
}

export const CURRENT_VIEWS_LAST_REVIEWED = '2026-07-20'

export const currentViews: CurrentView[] = [
  {
    market: 'Gold',
    stance: 'Mildly Bullish',
    timeHorizon: '3–6 months',
    rationale:
      'Structural central-bank demand and policy uncertainty remain supportive, but this is a new, lower-conviction stance rather than a continuation of the failed early-2026 trade.',
    href: '/research/why-i-remained-bullish-gold/',
    linkLabel: 'Review prior thesis',
  },
  {
    market: 'Brent Crude',
    stance: 'Bearish',
    timeHorizon: '3–6 months',
    rationale:
      'Recovering Gulf flows and an expected return to inventory builds in 4Q26 support a bearish medium-term view, although renewed regional disruption remains the principal upside risk.',
    href: '/research/why-i-am-bearish-brent-crude-into-late-2026/',
  },
  {
    market: 'Copper',
    stance: 'Neutral',
    timeHorizon: '3–6 months',
    rationale:
      'Record prices and elevated visible stocks argue against chasing the rally, while regional inventory distortion, tight concentrate supply and long-term grid and data-centre demand prevent a clean bearish view.',
    href: '/research/why-i-am-neutral-copper-after-the-2026-rally/',
  },
]
