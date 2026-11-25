import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { fetchNamesakes, type Namesakes } from '../api/characters'

const PAUSE = 400

/** Pendant la saisie, une fois la frappe posée : les noms déjà portés sur ce serveur (#122). */
export function useNamesakes(serverId: string, name: string, ingameName: string, but?: number): Namesakes | undefined {
  const [typed, setTyped] = useState({ name, ingameName })
  useEffect(() => {
    const pending = setTimeout(() => setTyped({ name, ingameName }), PAUSE)
    return () => clearTimeout(pending)
  }, [name, ingameName])

  const asked = Boolean(serverId) && Boolean(typed.name.trim() || typed.ingameName.trim())
  const found = useQuery({
    queryKey: ['namesakes', serverId, typed.name.trim(), typed.ingameName.trim(), but],
    queryFn: () => fetchNamesakes(Number(serverId), typed.name, typed.ingameName, but),
    enabled: asked,
    placeholderData: keepPreviousData,
    staleTime: 30_000,
  })
  return asked ? found.data : undefined
}
