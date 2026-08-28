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

export const CURRENT_VIEWS_LAST_REVIEWED = '2026-08-27'

export const currentViews: CurrentView[] = [
  {
    market: 'Gold',
    stance: 'Neutral',
    timeHorizon: '3–6 months',
    rationale:
      'Q2 central-bank demand and renewed ETF inflows support the structural case, but a 2.34% US 10-year real yield and a tactical August rebound leave limited near-term asymmetry.',
    href: '/research/gold-after-the-august-2026-rebound/',
  },
  {
    market: 'Brent Crude',
    stance: 'Mildly Bearish',
    timeHorizon: '6–12 months',
    rationale:
      'A projected late-year return to surplus still points lower over time, but renewed Hormuz disruption, a 1.8 mb/d 3Q deficit and July stock draws weaken the near-term short case.',
    href: '/research/why-i-am-bearish-brent-crude-into-late-2026/',
  },
  {
    market: 'Copper',
    stance: 'Neutral',
    timeHorizon: '3–6 months',
    rationale:
      'A day-delayed LME price near $14,350/t and official forecasts for small refined surpluses argue against chasing the rally, while concentrate tightness and long-run power demand prevent a clean bearish view.',
    href: '/research/why-i-am-neutral-copper-after-the-2026-rally/',
  },
]
