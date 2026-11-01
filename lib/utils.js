import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Merge class names safely with Tailwind
 * @param  {...any} inputs
 * @returns {string}
 */
export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

/**
 * Format date string to readable format
 * @param {string|Date} date
 * @returns {string}
 */
export function formatDate(date) {
  if (!date) return '—';
  const d = new Date(date);
  return d.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * Capitalize first letter of string
 * @param {string} str
 * @returns {string}
 */
export function capitalize(str) {
  if (!str) return '';
  return str.charAt(0).toUpperCase() + str.slice(1);
}
