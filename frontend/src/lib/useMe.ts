import { useQuery } from '@tanstack/react-query'
import { fetchMe } from '../api/accounts'

/** Qui est connecté : data vaut null pour un visiteur. */
export function useMe() {
  return useQuery({ queryKey: ['me'], queryFn: fetchMe, retry: false, staleTime: 60_000 })
}
