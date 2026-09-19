export type AssetType = 'gold' | 'bitcoin' | 'nvidia';

export interface AssetInfo {
  id: AssetType;
  name: string;
  ticker: string;
  color: string;
  category: string;
}

export interface NavigationItem {
  id: string;
  name: string;
  path: string;
  iconName: string;
}
