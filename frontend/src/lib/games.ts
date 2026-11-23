import type { Server } from '../api/servers'

export const GAME_LABELS: Record<Server['game'], string> = {
  dofus: 'Dofus',
  retro: 'Dofus Retro',
  touch: 'Dofus Touch',
}

/** Les serveurs pour un menu, sous le titre de leur jeu (l'API les donne déjà triés par jeu). */
export function serverOptions<T>(servers: Server[], value: (server: Server) => T) {
  return servers.map((s) => ({ value: value(s), label: s.name, group: GAME_LABELS[s.game] }))
}
