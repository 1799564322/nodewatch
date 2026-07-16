export type UserRole = 'admin' | 'viewer'

export interface User {
  id: string
  username: string
  role: UserRole
}

export interface AuthResponse {
  user: User
}

