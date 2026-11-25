/** Pour comparer des textes saisis : sans majuscules, sans accents, sans espaces autour. */
export function normalize(text: string): string {
  return text
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .trim()
}

/**
 * « 1 histoire », « 3 histoires » : le nombre et son mot, accordé.
 * Le pluriel régulier ajoute un s ; sinon on le donne (« lieux », « autres histoires »).
 */
export function plural(n: number, singular: string, pluralForm = `${singular}s`): string {
  return `${n} ${n > 1 ? pluralForm : singular}`
}
