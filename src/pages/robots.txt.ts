import type { APIRoute } from 'astro';

const SITE = 'https://goolapp.com';

export const GET: APIRoute = () => {
  const isLive = import.meta.env.PUBLIC_ADSENSE_ENABLED === 'true';

  // 도메인 이전 전 (preview / *.pages.dev / 로컬): 색인 차단
  // 도메인 이전 후 (production goolapp.com): 정상 색인 허용
  const body = isLive ? PROD_ROBOTS : PREVIEW_ROBOTS;

  return new Response(body, {
    headers: { 'Content-Type': 'text/plain; charset=utf-8' },
  });
};

const PROD_ROBOTS = `User-agent: *
Allow: /

Disallow: /_design-system/

Sitemap: ${SITE}/sitemap-index.xml
`;

const PREVIEW_ROBOTS = `User-agent: *
Disallow: /
`;
