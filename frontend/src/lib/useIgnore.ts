import { useMutation, useQueryClient } from '@tanstack/react-query'
import { ignoreCharacter, unignoreCharacter } from '../api/characters'
import { useToast } from './toast'

/** Ignorer ou ne plus ignorer : ensuite, toutes les listes se rechargent sans lui, ou avec. */
export function useIgnore(id: number, name: string) {
  const queryClient = useQueryClient()
  const toast = useToast()
  const refresh = () => queryClient.invalidateQueries({ predicate: (q) => q.queryKey[0] !== 'me' })
  const ignore = useMutation({
    mutationFn: () => ignoreCharacter(id),
    onSuccess: async () => {
      await refresh()
      toast.show(`${name} n'apparaît plus dans tes listes.`, 'success')
    },
    onError: (e) => toast.show(`Pas ignoré : ${e.message}`, 'error'),
  })
  const unignore = useMutation({
    mutationFn: () => unignoreCharacter(id),
    onSuccess: async () => {
      await refresh()
      toast.show(`${name} revient dans tes listes.`, 'success')
    },
    onError: (e) => toast.show(`Pas fait : ${e.message}`, 'error'),
  })
  return { ignore, unignore }
}
