/**
 * context/AuthContext.js
 * ----------------------
 * Global authentication state via React Context API.
 * Stores user object and JWT token in sessionStorage.
 * Provides login() and logout() helpers used throughout the app.
 */

import React, { createContext, useContext, useState, useCallback } from 'react';

const AuthContext = createContext(null);

const TOKEN_KEY = 'hr_token';
const USER_KEY  = 'hr_user';

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => sessionStorage.getItem(TOKEN_KEY));
  const [user,  setUser]  = useState(() => {
    const stored = sessionStorage.getItem(USER_KEY);
    try { return stored ? JSON.parse(stored) : null; }
    catch { return null; }
  });

  /** Called after successful login API response */
  const login = useCallback((newToken, newUser) => {
    sessionStorage.setItem(TOKEN_KEY, newToken);
    sessionStorage.setItem(USER_KEY, JSON.stringify(newUser));
    setToken(newToken);
    setUser(newUser);
  }, []);

  /** Called on logout or 401 response */
  const logout = useCallback(() => {
    sessionStorage.removeItem(TOKEN_KEY);
    sessionStorage.removeItem(USER_KEY);
    setToken(null);
    setUser(null);
  }, []);

  /** Update user object in context (e.g. after profile edit) */
  const updateUser = useCallback((updatedUser) => {
    sessionStorage.setItem(USER_KEY, JSON.stringify(updatedUser));
    setUser(updatedUser);
  }, []);

  const isAuthenticated = !!token;
  const isAdmin = user?.role === 'Admin';

  return (
    <AuthContext.Provider value={{ token, user, isAuthenticated, isAdmin, login, logout, updateUser }}>
      {children}
    </AuthContext.Provider>
  );
}

/** Convenience hook for consuming auth context */
export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>');
  return ctx;
}

export default AuthContext;
