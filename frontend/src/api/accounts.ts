import { ApiError, apiFetch } from './client'

export type Me = {
  email: string
  role: 'user' | 'moderator' | 'admin'
  created_at: string
  /** Pour montrer les bons boutons. Le serveur revérifie toujours : ce n'est pas une protection. */
  capabilities: Capability[]
  /** Suspendu : le site ne montre que la décision et de quoi la contester (#141). */
  suspended: boolean
  /** null : définitivement, ou pas suspendu. */
  suspended_until: string | null
}

/** Les capacités de backend/accounts/roles.py. */
export type Capability =
  | 'see_hidden'
  | 'see_owner'
  | 'moderate'
  | 'ban'
  | 'delete_any'
  | 'manage_npcs'
  | 'manage_servers'
  | 'manage_roles'

type Message = { detail: string }

/** La personne connectée, ou null. */
export async function fetchMe(): Promise<Me | null> {
  try {
    return await apiFetch<Me>('/me')
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) {
      return null
    }
    throw error
  }
}

export const signUp = (body: { email: string; password: string; accept_rules: boolean; age_confirmed: boolean }) =>
  apiFetch<Message>('/accounts', { method: 'POST', body })

export const verifyEmail = (token: string) => apiFetch('/accounts/verify', { method: 'POST', body: { token } })

export const resendVerification = (email: string) =>
  apiFetch<Message>('/accounts/verify/resend', { method: 'POST', body: { email } })

export const logIn = (body: { email: string; password: string }) => apiFetch('/session', { method: 'POST', body })

export const logOut = () => apiFetch('/session', { method: 'DELETE' })

export const forgotPassword = (email: string) =>
  apiFetch<Message>('/password/forgot', { method: 'POST', body: { email } })

export const resetPassword = (body: { token: string; password: string }) =>
  apiFetch('/password/reset', { method: 'POST', body })

export const changePassword = (body: { current_password: string; new_password: string }) =>
  apiFetch('/me/password', { method: 'PATCH', body })

export const deleteAccount = (password: string) => apiFetch('/me', { method: 'DELETE', body: { password } })
