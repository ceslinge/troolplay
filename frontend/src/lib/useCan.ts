import type { Capability } from '../api/accounts'
import { useMe } from './useMe'

/** Ce que la personne connectée peut faire, pour montrer les bons boutons. Le serveur revérifie toujours. */
export function useCan(capability: Capability): boolean {
  const me = useMe()
  return me.data?.capabilities.includes(capability) ?? false
}
