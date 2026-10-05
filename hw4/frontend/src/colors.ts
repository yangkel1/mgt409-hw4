// Turn catalogue color names ("heather gray", "navy blue") into swatch colors.
const SWATCHES: [string, string][] = [
  ['multicolor', 'conic-gradient(#00356b, #b5121b, #f2c94c, #2e6b3f, #00356b)'],
  ['light blue', '#9cc3ea'],
  ['heather', '#b9bcbf'],
  ['charcoal', '#4a4d52'],
  ['navy', '#14254a'],
  ['blue', '#286dc0'],
  ['white', '#ffffff'],
  ['ivory', '#f6f0e1'],
  ['cream', '#f6f0e1'],
  ['gray', '#9ea3a8'],
  ['grey', '#9ea3a8'],
  ['black', '#151515'],
  ['red', '#b5121b'],
  ['crimson', '#9e1b32'],
  ['maroon', '#6d1f2b'],
  ['green', '#2e6b3f'],
  ['yellow', '#f2c94c'],
  ['gold', '#d4a72c'],
  ['orange', '#e8772e'],
  ['pink', '#f4a7b9'],
  ['purple', '#5b3a8c'],
  ['brown', '#7a5230'],
  ['tan', '#c9a46a'],
]

export function swatchFor(name: string): string {
  const n = name.toLowerCase()
  return SWATCHES.find(([key]) => n.includes(key))?.[1] ?? '#d9d4ca'
}
