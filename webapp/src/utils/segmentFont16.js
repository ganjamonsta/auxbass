/**
 * 16-Segment Alphanumeric Starburst Font Definitions & Helpers
 * Authentic Vacuum Fluorescent Display (VFD) Character Encoding
 * 
 * Segment Layout:
 *       -- A1 --  -- A2 --
 *      |\       |       /|
 *      | \   H  |  K   / |
 *      F  \     J     /  B
 *      |   \    |    /   |
 *      |    \   |   /    |
 *       -- G1 -   - G2 --
 *      |    /   |   \    |
 *      |   /    |    \   |
 *      E  /     M     \  C
 *      | /   L  |  N   \ |
 *      |/       |       \|
 *       -- D1 --  -- D2 --   (DP)
 * 
 * Supports:
 * - Full English uppercase (A-Z) & numbers (0-9)
 * - Complete Cyrillic alphabet (А-Я, Ё)
 * - Punctuation & audio symbols
 * - Animation frames: spinning CD wheel, cassette reels, Larson wave, VU meters
 */

export const SEGMENTS = {
  A1: 1 << 0,  // 0x0001 - Top Left Horizontal
  A2: 1 << 1,  // 0x0002 - Top Right Horizontal
  B:  1 << 2,  // 0x0004 - Upper Right Vertical
  C:  1 << 3,  // 0x0008 - Lower Right Vertical
  D2: 1 << 4,  // 0x0010 - Bottom Right Horizontal
  D1: 1 << 5,  // 0x0020 - Bottom Left Horizontal
  E:  1 << 6,  // 0x0040 - Lower Left Vertical
  F:  1 << 7,  // 0x0080 - Upper Left Vertical
  G1: 1 << 8,  // 0x0100 - Middle Left Horizontal
  G2: 1 << 9,  // 0x0200 - Middle Right Horizontal
  H:  1 << 10, // 0x0400 - Upper Left Diagonal
  J:  1 << 11, // 0x0800 - Upper Center Vertical
  K:  1 << 12, // 0x1000 - Upper Right Diagonal
  L:  1 << 13, // 0x2000 - Lower Left Diagonal
  M:  1 << 14, // 0x4000 - Lower Center Vertical
  N:  1 << 15, // 0x8000 - Lower Right Diagonal
  DP: 1 << 16  // 0x10000 - Decimal Point
}

const { A1, A2, B, C, D2, D1, E, F, G1, G2, H, J, K, L, M, N, DP } = SEGMENTS

export const FONT16 = {
  // Space & empty
  ' ': 0,
  '\u00A0': 0,

  // Numbers 0-9
  '0': A1 | A2 | B | C | D2 | D1 | E | F | K | L,
  '1': B | C | K,
  '2': A1 | A2 | B | G2 | G1 | E | D1 | D2,
  '3': A1 | A2 | B | G2 | C | D2 | D1,
  '4': F | G1 | G2 | B | C,
  '5': A1 | A2 | F | G1 | G2 | C | D2 | D1,
  '6': A1 | A2 | F | E | D1 | D2 | C | G2 | G1,
  '7': A1 | A2 | B | C,
  '8': A1 | A2 | B | C | D2 | D1 | E | F | G1 | G2,
  '9': A1 | A2 | B | C | D2 | D1 | F | G1 | G2,

  // Latin Letters (A-Z)
  'A': A1 | A2 | B | C | E | F | G1 | G2,
  'B': A1 | A2 | J | M | D1 | D2 | B | C | G2,
  'C': A1 | A2 | F | E | D1 | D2,
  'D': A1 | A2 | J | M | D1 | D2 | B | C,
  'E': A1 | A2 | F | E | D1 | D2 | G1,
  'F': A1 | A2 | F | E | G1,
  'G': A1 | A2 | F | E | D1 | D2 | C | G2,
  'H': F | E | B | C | G1 | G2,
  'I': A1 | A2 | J | M | D1 | D2,
  'J': B | C | D2 | D1 | E,
  'K': F | E | G1 | K | N,
  'L': F | E | D1 | D2,
  'M': F | E | H | K | B | C,
  'N': F | E | H | N | B | C,
  'O': A1 | A2 | B | C | D2 | D1 | E | F,
  'P': A1 | A2 | B | G2 | G1 | F | E,
  'Q': A1 | A2 | B | C | D2 | D1 | E | F | N,
  'R': A1 | A2 | B | G2 | G1 | F | E | N,
  'S': A1 | A2 | F | G1 | G2 | C | D2 | D1,
  'T': A1 | A2 | J | M,
  'U': F | E | D1 | D2 | C | B,
  'V': F | E | L | K,
  'W': F | E | L | N | C | B,
  'X': H | K | L | N,
  'Y': H | K | M,
  'Z': A1 | A2 | K | L | D1 | D2,

  // Cyrillic Alphabet (А-Я, Ё) - Hand-tuned for authentic 16-seg Starburst aesthetic
  'А': A1 | A2 | B | C | E | F | G1 | G2,
  'Б': A1 | A2 | F | E | D1 | D2 | C | G2 | G1,
  'В': A1 | A2 | J | M | D1 | D2 | B | C | G2,
  'Г': A1 | A2 | F | E,
  'Д': A1 | A2 | B | C | E | F | D1 | D2 | L | N,
  'Е': A1 | A2 | F | E | D1 | D2 | G1,
  'Ё': A1 | A2 | F | E | D1 | D2 | G1 | H | K,
  'Ж': J | M | H | K | L | N | G1 | G2, // Iconic Starburst snowflake
  'З': A1 | A2 | B | G2 | C | D2 | D1,
  'И': F | E | B | C | L | K,
  'Й': F | E | B | C | L | K | H,
  'К': F | E | G1 | K | N,
  'Л': A1 | A2 | B | C | E | F,
  'М': F | E | H | K | B | C,
  'Н': F | E | B | C | G1 | G2,
  'О': A1 | A2 | B | C | D2 | D1 | E | F,
  'П': A1 | A2 | F | E | B | C,
  'Р': A1 | A2 | B | G2 | G1 | F | E,
  'С': A1 | A2 | F | E | D1 | D2,
  'Т': A1 | A2 | J | M,
  'У': F | G1 | G2 | B | C | D2 | D1,
  'Ф': A1 | A2 | B | F | G1 | G2 | J | M,
  'Х': H | K | L | N,
  'Ц': F | E | D1 | D2 | B | C | N,
  'Ч': F | G1 | G2 | B | C,
  'Ш': F | E | J | M | B | C | D1 | D2,
  'Щ': F | E | J | M | B | C | D1 | D2 | N,
  'Ъ': A1 | J | F | E | D1 | D2 | C | G2 | G1,
  'Ы': F | E | D1 | G1 | J | M | B | C,
  'Ь': F | E | D1 | D2 | C | G2 | G1,
  'Э': A1 | A2 | B | C | D2 | D1 | G2,
  'Ю': F | E | G1 | A2 | B | C | D2 | G2 | M,
  'Я': A1 | A2 | B | G2 | G1 | F | L | N,

  // Punctuation, Symbols, Math, Brackets
  '-': G1 | G2,
  '_': D1 | D2,
  '=': G1 | G2 | D1 | D2,
  '+': J | M | G1 | G2,
  '*': H | K | L | N | J | M | G1 | G2,
  '/': L | K,
  '\\': H | N,
  '|': J | M,
  ':': J | M,
  ';': J | L,
  '.': DP,
  ',': L,
  '\'': J,
  '`': H,
  '"': F | B,
  '!': J | DP,
  '?': A1 | A2 | B | G2 | M | DP,
  '>': H | L,
  '<': K | N,
  '(': K | N,
  ')': H | L,
  '[': A1 | F | E | D1,
  ']': A2 | B | C | D2,
  '{': A1 | H | L | D1,
  '}': A2 | K | N | D2,
  '^': L | N,
  '~': A1 | G2,
  '%': H | L | G1 | G2 | K | N,
  '&': A1 | H | G1 | E | D1 | D2 | C | N,
  '#': F | E | B | C | G1 | G2 | D1 | D2,
  '@': A1 | A2 | B | C | D2 | D1 | E | F | G1 | G2 | J,
  '$': A1 | A2 | F | G1 | G2 | C | D2 | D1 | J | M
}

/**
 * Returns 16-segment bitmask for a given character.
 * Unknown characters gracefully fallback to space or a subtle center dash.
 */
export function getCharMask(char) {
  if (!char) return 0
  const upper = char.toUpperCase()
  if (FONT16[upper] !== undefined) {
    return FONT16[upper]
  }
  return G1 | G2 // Fallback dash
}

/**
 * Encodes string to array of segment masks.
 */
export function encodeString(str, length = 0) {
  if (!str) str = ''
  const masks = []
  for (let i = 0; i < str.length; i++) {
    masks.push(getCharMask(str[i]))
  }
  if (length > 0) {
    while (masks.length < length) {
      masks.push(0)
    }
    return masks.slice(0, length)
  }
  return masks
}

/**
 * Spinning Disc animation frames (VFD CD icon)
 */
export const DISC_FRAMES = [
  A1 | A2,
  K | B,
  G2 | C,
  D2 | D1,
  E | L,
  G1 | F,
  H | A1
]

/**
 * Equalizer bar patterns (levels 0 to 5) for a single cell
 */
export const VU_LEVEL_MASKS = [
  0,
  D1 | D2,
  D1 | D2 | G1 | G2,
  D1 | D2 | G1 | G2 | A1 | A2,
  D1 | D2 | G1 | G2 | A1 | A2 | E | C,
  D1 | D2 | G1 | G2 | A1 | A2 | E | C | F | B
]

/**
 * Larson Scanner (Knight Rider) wave generator
 * Returns an array of segment masks for a given beam position (0 to cellCount - 1)
 */
export function getLarsonMasks(cellCount, headPos) {
  const result = new Array(cellCount).fill(0)
  for (let i = 0; i < cellCount; i++) {
    const dist = Math.abs(i - headPos)
    if (dist === 0) {
      result[i] = A1 | A2 | G1 | G2 | D1 | D2 | J | M // Core pulse
    } else if (dist === 1) {
      result[i] = G1 | G2 | H | N // Inner trail
    } else if (dist === 2) {
      result[i] = G1 | G2 // Soft trail
    }
  }
  return result
}

/**
 * Random glitch segment mask generator for Matrix/Decode effect
 */
export function getRandomGlitchMask() {
  const allBits = [A1, A2, B, C, D2, D1, E, F, G1, G2, H, J, K, L, M, N]
  let mask = 0
  const count = 2 + Math.floor(Math.random() * 6)
  for (let i = 0; i < count; i++) {
    const bit = allBits[Math.floor(Math.random() * allBits.length)]
    mask |= bit
  }
  return mask
}
