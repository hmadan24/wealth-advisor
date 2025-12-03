/**
 * App configuration - handles different environments
 */

// API base URL - uses environment variable in production, proxy in development
export const API_BASE_URL = import.meta.env.VITE_API_URL || '';

// Build the full API URL for a path
export function apiUrl(path) {
  // In development, Vite proxy handles /api/* routes
  // In production, use the full API URL
  if (API_BASE_URL) {
    return `${API_BASE_URL}${path}`;
  }
  return path;
}

// Environment checks
export const isDev = import.meta.env.DEV;
export const isProd = import.meta.env.PROD;

// App info
export const APP_NAME = 'Wealth Advisor';
export const APP_VERSION = '2.0.0';

