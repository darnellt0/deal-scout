/**
 * Authentication utilities for Deal Scout
 */

export interface User {
  id: number;
  username: string;
  email: string;
  role: string;
  first_name?: string;
  last_name?: string;
}

/**
 * Get the authentication token from localStorage
 */
export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("token");
}

/**
 * Get the current user from localStorage
 */
export function getUser(): User | null {
  if (typeof window === "undefined") return null;
  const userStr = localStorage.getItem("user");
  if (!userStr) return null;
  try {
    return JSON.parse(userStr);
  } catch {
    return null;
  }
}

/**
 * Check if user is authenticated
 */
export function isAuthenticated(): boolean {
  return !!getToken();
}

/**
 * Save authentication data to localStorage
 */
export function saveAuth(token: string, user: User): void {
  localStorage.setItem("token", token);
  localStorage.setItem("user", JSON.stringify(user));
}

/**
 * Clear authentication data from localStorage
 */
export function clearAuth(): void {
  localStorage.removeItem("token");
  localStorage.removeItem("user");
}

/**
 * Get authorization headers for API requests
 */
export function getAuthHeaders(): HeadersInit {
  const token = getToken();
  if (!token) return {};

  return {
    Authorization: `Bearer ${token}`,
  };
}

/**
 * Check if user is a seller
 */
export function isSeller(): boolean {
  const user = getUser();
  return user?.role === "seller";
}

/**
 * Check if user is a buyer
 */
export function isBuyer(): boolean {
  const user = getUser();
  return user?.role === "buyer";
}
