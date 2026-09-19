export const THEME_COLORS = {
  bgMain: '#080c14',
  bgSurface: '#0e1626',
  bgCard: 'rgba(16, 26, 46, 0.75)',
  accentGreen: '#00f5a0',
  accentCyan: '#00d8ff',
  accentPurple: '#9d4edd',
  accentRed: '#ff3366',
  accentAmber: '#ffbe0b',
  textPrimary: '#f8fafc',
  textSecondary: '#94a3b8',
  textMuted: '#64748b',
};

export function getCorrelationColor(value: number): string {
  // Value between -1.0 and 1.0
  if (value >= 0.8) return 'rgba(0, 245, 160, 0.85)'; // strong positive green
  if (value >= 0.4) return 'rgba(0, 216, 255, 0.65)'; // moderate positive cyan
  if (value >= 0.1) return 'rgba(56, 189, 248, 0.35)'; // weak positive
  if (value > -0.1) return 'rgba(148, 163, 184, 0.2)'; // uncorrelated gray
  if (value > -0.4) return 'rgba(251, 191, 36, 0.4)'; // weak negative amber
  return 'rgba(255, 51, 102, 0.75)'; // strong negative rose
}

export function getRegimeBadgeColor(regime: string): { bg: string; text: string; border: string } {
  switch (regime) {
    case 'Bull Trend':
      return { bg: 'bg-emerald-500/10', text: 'text-emerald-400', border: 'border-emerald-500/30' };
    case 'Bear Trend':
      return { bg: 'bg-rose-500/10', text: 'text-rose-400', border: 'border-rose-500/30' };
    case 'Volatile Choppy':
      return { bg: 'bg-amber-500/10', text: 'text-amber-400', border: 'border-amber-500/30' };
    case 'Consolidation':
    default:
      return { bg: 'bg-cyan-500/10', text: 'text-cyan-400', border: 'border-cyan-500/30' };
  }
}
