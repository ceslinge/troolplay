/** Un nombre stable tiré d'un texte : le même texte donne toujours le même nombre. */
export function hashString(text: string): number {
  let hash = 0
  for (const letter of text) {
    hash = (hash * 31 + letter.charCodeAt(0)) >>> 0
  }
  return hash
}
