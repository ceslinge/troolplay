/** Pour comparer des textes saisis : sans majuscules, sans accents, sans espaces autour. */
export function normalize(text: string): string {
  return text
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .trim()
}
