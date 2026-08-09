function normalizeUrl(value: string): string {
  const withProtocol = /^https?:\/\//i.test(value) ? value : `https://${value}`;
  return withProtocol.replace(/\/+$/, "");
}

const configuredUrl = process.env.NEXT_PUBLIC_SITE_URL?.trim();
const vercelUrl =
  process.env.VERCEL_PROJECT_PRODUCTION_URL?.trim() ?? process.env.VERCEL_URL?.trim();

export const SITE_URL = configuredUrl
  ? normalizeUrl(configuredUrl)
  : vercelUrl
    ? normalizeUrl(vercelUrl)
    : "http://localhost:3000";
