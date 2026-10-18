import { api } from '@/lib/api-client'
import type { AuthResponse, User } from '@/types/api'

export interface LoginInput {
  email: string
  password: string
}
export interface RegisterInput extends LoginInput {
  full_name: string
}
export interface ProfilePatch {
  full_name?: string
  avatar_color?: string
}
export interface PasswordInput {
  current_password: string
  new_password: string
}

export const authApi = {
  login: (body: LoginInput) => api.post<AuthResponse>('/auth/login', body),
  register: (body: RegisterInput) => api.post<AuthResponse>('/auth/register', body),
  me: () => api.get<User>('/users/me'),
  updateMe: (body: ProfilePatch) => api.patch<User>('/users/me', body),
  changePassword: (body: PasswordInput) => api.post<void>('/users/me/password', body),
}
