import type { Gender } from '../api/characters'

type Forms = Record<Gender, string>

/** Choisit la forme qui s'accorde au genre grammatical du personnage. */
export function agree(gender: Gender, forms: Forms): string {
  return forms[gender]
}
