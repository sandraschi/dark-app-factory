# SEO Block

SEO manager — sitemap.xml, robots.txt, JSON-LD structured data, Open Graph / Twitter cards, meta tags, and URL redirects.

**Triggers**: seo, meta, sitemap, robots, structured.data, opengraph, jsonld, redirect, canonical

**Env vars**:
| Variable | Default | Description |
|----------|---------|-------------|
| `SITE_URL` | `http://localhost:3000` | Canonical site URL |
| `SEO_TITLE` | — | Default page title |
| `SEO_DESCRIPTION` | — | Default meta description |
| `SEO_IMAGE` | — | Default OG image URL |

**API endpoints**: `/api/seo/sitemap.xml`, `/api/seo/robots.txt`, `/api/seo/settings`, `/api/seo/redirects`

**Dependencies**: (none)
