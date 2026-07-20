import { html } from 'satori-html'
import backgroundBase64 from './base64'

import type { BgType } from '~/types'

export const ogImageMarkup = (
  authorOrBrand: string,
  title: string,
  bgType: BgType
) => {
  if (!['plum', 'dot'].includes(bgType))
    throw new Error(
      "The value of 'bgType' must be one of the following: 'plum', 'dot'."
    )

  return html`<div
    tw="relative flex w-full h-full bg-[#111111]"
    style="font-family: 'Inter'"
  >
    <img
      tw="absolute inset-0 w-full h-full"
      src="${backgroundBase64[bgType]}"
      alt=""
    />

    <div tw="absolute inset-0 flex flex-col justify-between px-18 py-16">
      <div tw="flex flex-col">
        <div tw="text-[#f0f0f0] text-5xl">${authorOrBrand}</div>

        <div tw="mt-3 text-[#888888] text-xl" style="letter-spacing: 0.14em">
          INDEPENDENT INVESTMENT RESEARCH
        </div>
      </div>

      <div tw="flex max-w-[1020px] text-white text-6xl leading-tight">
        ${title}
      </div>
    </div>
  </div>`
}
