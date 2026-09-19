export * from './api';

export type AssetType = 'gold' | 'bitcoin' | 'nvidia';

export interface AssetInfo {
  id: AssetType;
  name: string;
  ticker: string;
  color: string;
  category: string;
  badgeClass: string;
}

export interface NavigationItem {
  id: string;
  name: string;
  path: string;
  iconName: string;
  phase: number;
  description: string;
}

export type StatusType = 'idle' | 'loading' | 'success' | 'error';
