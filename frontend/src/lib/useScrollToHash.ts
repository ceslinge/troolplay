import { useEffect } from 'react'
import { useLocation } from 'react-router'

/**
 * Un lien vers une ancre (#decisions, #historique…) : on y descend une fois le contenu
 * arrivé. Le navigateur ne le fait pas seul, la page se remplissant après coup.
 */
export function useScrollToHash(id: string | undefined, ready: boolean) {
  const { hash } = useLocation()
  useEffect(() => {
    if (id && ready && hash === `#${id}`) document.getElementById(id)?.scrollIntoView({ block: 'start' })
  }, [id, ready, hash])
}
