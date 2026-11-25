import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router'
import { logOut } from '../api/accounts'
import { clearLocalDrafts } from './storage'
import { useToast } from './toast'

/** Quitter le compte (déconnexion, suppression) : rien de ce qui était à soi ne reste derrière. */
export function useLeave() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  return async function leave() {
    clearLocalDrafts()
    queryClient.setQueryData(['me'], null)
    // Ce qui a été chargé connecté ne doit pas resservir au visiteur qui suit.
    await queryClient.invalidateQueries({ predicate: (query) => query.queryKey[0] !== 'me' })
    navigate('/')
  }
}

export function useLogOut() {
  const leave = useLeave()
  const toast = useToast()
  return useMutation({
    mutationFn: logOut,
    onSuccess: leave,
    onError: (failure) => toast.show(`Pas déconnecté : ${failure.message}`, 'error'),
  })
}
