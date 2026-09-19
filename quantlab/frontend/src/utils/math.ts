export function mean(numbers: number[]): number {
  if (numbers.length === 0) return 0;
  return numbers.reduce((acc, val) => acc + val, 0) / numbers.length;
}

export function standardDeviation(numbers: number[]): number {
  if (numbers.length < 2) return 0;
  const avg = mean(numbers);
  const variance = numbers.reduce((acc, val) => acc + Math.pow(val - avg, 2), 0) / (numbers.length - 1);
  return Math.sqrt(variance);
}

export function calculateReturns(prices: number[]): number[] {
  if (prices.length < 2) return [];
  const rets: number[] = [0];
  for (let i = 1; i < prices.length; i++) {
    const p0 = prices[i - 1];
    const p1 = prices[i];
    rets.push(p0 > 0 ? (p1 - p0) / p0 : 0);
  }
  return rets;
}
