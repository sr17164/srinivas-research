export type MarketStance =
  'Bullish' | 'Mildly Bullish' | 'Neutral' | 'Mildly Bearish' | 'Bearish'

export interface CurrentView {
  market: string
  stance: MarketStance
  timeHorizon: string
  rationale: string
  href?: string
  researchStatus?: string
}

export const CURRENT_VIEWS_LAST_REVIEWED = '2026-07-19'

export const currentViews: CurrentView[] = [
  {
    market: 'Gold',
    stance: 'Mildly Bullish',
    timeHorizon: '3–6 months',
    rationale:
      'Structural central-bank demand and policy uncertainty provide support, while the near-term baseline remains more balanced unless growth or rate expectations weaken.',
    href: '/research/why-i-remained-bullish-gold/',
  },
  {
    market: 'Brent Crude',
    stance: 'Bearish',
    timeHorizon: '3–6 months',
    rationale:
      'Recovering Gulf supply and weak full-year demand should move the market towards surplus later in the year, although renewed regional disruption remains the principal upside risk.',
    researchStatus: 'Research in progress',
  },
  {
    market: 'Copper',
    stance: 'Neutral',
    timeHorizon: '3–6 months',
    rationale:
      'A small projected refined surplus and slower demand growth argue against chasing elevated prices, while constrained mine supply and long-term grid, electrification and data-centre demand support the structural case.',
    researchStatus: 'Research in progress',
  },
]
