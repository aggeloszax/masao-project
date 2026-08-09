const MIN_TABLE_NUMBER = 1;
const MAX_TABLE_NUMBER = 999;

export function parseTableNumber(value: string | null | undefined): number | null {
  const normalized = value?.trim();
  if (!normalized || !/^\d{1,3}$/.test(normalized)) return null;
  const parsed = Number(normalized);
  return parsed >= MIN_TABLE_NUMBER && parsed <= MAX_TABLE_NUMBER ? parsed : null;
}
