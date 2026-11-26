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

const VOWEL = /^[aeiouàâäéèêëîïôöùûüœæ]/i

/**
 * « de Gorrik », « d’Ombre », « d’Ysolde » : la préposition devant un nom, élidée devant
 * une voyelle. Le Y s’élide quand il sonne comme une voyelle (Ysolde, Yves), pas devant
 * une autre voyelle (Yugo). Le H reste tel quel : muet ou non, on ne peut pas le savoir.
 * Même règle côté backend : backend/text.py.
 */
export function ofName(name: string): string {
  const elided = VOWEL.test(name) || (/^y/i.test(name) && !VOWEL.test(name.slice(1)))
  return elided ? `d’${name}` : `de ${name}`
}
