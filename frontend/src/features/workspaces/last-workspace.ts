export const LAST_WORKSPACE_KEY = 'atm.lastWorkspace'

export function readLastWorkspace(): string | null {
  try {
    return localStorage.getItem(LAST_WORKSPACE_KEY)
  } catch {
    return null
  }
}
