# Blog Block

Blog and CMS — markdown articles, categories, RSS feed generation, SEO metadata, and comments.

**Triggers**: blog, cms, article, post, news, rss, content, writing, editorial

**Env vars**:
| Variable | Default | Description |
|----------|---------|-------------|
| `BLOG_TITLE` | `My Blog` | Site title |
| `BLOG_DESCRIPTION` | — | Site description |
| `SITE_URL` | `http://localhost:3000` | Canonical site URL |

**API endpoints**: `/api/blog/articles`, `/api/blog/articles/{id}`, `/api/blog/rss`, `/api/blog/categories`

**Dependencies**: `pip: markdown>=3.5.0, feedgen>=1.0.0`
