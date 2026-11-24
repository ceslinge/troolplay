/** Une erreur renvoyée par le serveur, prête à afficher. */
export class ApiError extends Error {
  status: number
  /** Les erreurs champ par champ, déjà traduites, pour les afficher sous chaque champ. */
  fields: Record<string, string>

  constructor(status: number, message: string, fields: Record<string, string> = {}) {
    super(message)
    this.status = status
    this.fields = fields
  }
}

type ValidationIssue = {
  loc: (string | number)[]
  type: string
  msg: string
  ctx?: { min_length?: number; max_length?: number }
}

/** Traduit une erreur de validation de FastAPI en phrase française. */
function explain(issue: ValidationIssue): string {
  switch (issue.type) {
    case 'missing':
      return 'Obligatoire'
    case 'string_too_short':
      return `Au moins ${issue.ctx?.min_length} caractères`
    case 'string_too_long':
      return `Pas plus de ${issue.ctx?.max_length} caractères`
    case 'literal_error':
      return 'Il faut cocher cette case'
    case 'value_error':
      // Nos propres messages sont déjà en français. Seul celui des adresses vient de Pydantic, en anglais.
      return issue.loc.at(-1) === 'email' ? 'Adresse email invalide' : issue.msg.replace(/^Value error, /, '')
    default:
      return 'Valeur invalide'
  }
}

/**
 * Appelle l'API. Le cookie de session part tout seul : le site et l'API sont sur la même adresse.
 * Lève une ApiError si la réponse n'est pas bonne.
 */
export async function apiFetch<T = void>(
  path: string,
  options: { method?: string; body?: unknown } = {},
): Promise<T> {
  let response: Response
  try {
    response = await fetch(`/api${path}`, {
      method: options.method ?? 'GET',
      headers: options.body === undefined ? undefined : { 'Content-Type': 'application/json' },
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
    })
  } catch {
    // Pas de réponse du tout (serveur éteint, connexion coupée) : une erreur comme les autres, pour que les formulaires l'affichent.
    throw new ApiError(0, "Le panneau ne répond pas. Vérifie ta connexion, ou réessaie dans un moment.")
  }

  if (response.ok) {
    return response.status === 204 ? (undefined as T) : response.json()
  }

  const payload = await response.json().catch(() => null)
  const detail = payload?.detail
  if (response.status === 422 && Array.isArray(detail)) {
    const fields: Record<string, string> = {}
    for (const issue of detail as ValidationIssue[]) {
      const field = String(issue.loc.at(-1))
      fields[field] ??= explain(issue)
    }
    // Une règle qui porte sur plusieurs champs à la fois arrive sans champ précis (« body »).
    throw new ApiError(422, fields.body ?? 'Certains champs sont à corriger.', fields)
  }
  if (response.status >= 500 || typeof detail !== 'string') {
    throw new ApiError(response.status, "Le panneau ne répond pas comme prévu. Réessaie dans un moment.")
  }
  throw new ApiError(response.status, detail)
}
