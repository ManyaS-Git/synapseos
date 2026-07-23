/**
 * Custom hook for theme management.
 *
 * TODO: Implement using next-themes or zustand
 */

export function useTheme() {
  // TODO: Implement theme switching
  return {
    theme: 'system' as const,
    setTheme: (_theme: 'light' | 'dark' | 'system') => {},
  };
}
