# Skill: Content Management & Blog Platform (2026 SOTA)

## 1. Domain Context
A headless or full-stack CMS with public blog/article front-end and a rich content authoring back-office.
Use cases: corporate blog, news site, knowledge base, documentation portal, personal portfolio.

## 2. Mandatory Pages & Routes

### Public front-end
- `/` — Featured post hero, category strip, recent posts grid, newsletter signup
- `/blog` — Paginated post list with search + category filter
- `/blog/:slug` — Full article: cover image, author bio, reading time, ToC, share buttons, related posts
- `/category/:slug` — Category archive
- `/author/:slug` — Author profile with their posts
- `/search` — Full-text search results

### Authoring back-office (`/admin`)
- `/admin` — Stats: posts published, draft queue, recent comments
- `/admin/posts` — Post list (status badges: Draft / Published / Scheduled), quick actions
- `/admin/posts/new` — Rich editor (Markdown or block-based)
- `/admin/posts/:id/edit` — Edit with revision history sidebar
- `/admin/media` — Image/file library with upload, crop, alt-text
- `/admin/categories` — Tag & category CRUD
- `/admin/authors` — Author management, invite by email

## 3. Data Model (PostgreSQL preferred)
```sql
posts (id, slug, title, excerpt, body_md TEXT, cover_image_url,
       author_id FK, category_id FK, status ENUM('draft','published','scheduled'),
       published_at TIMESTAMPTZ, scheduled_for TIMESTAMPTZ,
       reading_time_minutes INT, meta_title, meta_description, created_at, updated_at)
categories (id, slug, name, description, colour)
authors (id, slug, name, bio, avatar_url, email, role ENUM('editor','author','admin'))
revisions (id, post_id FK, body_md TEXT, changed_by FK, created_at)
media (id, filename, url, alt_text, mime_type, size_bytes, uploaded_by FK, created_at)
```

## 4. Backend Specifics
- Full-text search: PostgreSQL `tsvector` on `posts.title || ' ' || posts.body_md`; expose `GET /api/search?q=`
- Slug generation: auto-generated from title, unique-enforced, editable before publish
- Scheduled publishing: background task checks `scheduled_for` every minute, flips status to `published`
- RSS/Atom feed: `GET /feed.xml` — required for discoverability
- Sitemap: `GET /sitemap.xml` — all published post slugs with `lastmod`
- Image optimisation: resize uploaded images to max 1920px, generate WebP variant, store both URLs
- Draft preview: signed URL token (`GET /preview/:token`) that renders draft without publishing

## 5. Frontend Specifics
- Article body: render Markdown with syntax highlighting (highlight.js or Prism)
- Table of Contents: auto-generated from H2/H3 headings, sticky on desktop
- Reading progress: thin progress bar at top of article (CSS only)
- Dark/light mode toggle: persisted to localStorage
- Newsletter signup: POST to `EMAIL_API_URL`; show inline success state
- Social share: native Web Share API with clipboard fallback

## 6. SEO Requirements (non-negotiable)
- `<title>` and `<meta name="description">` populated from `post.meta_title` / `post.meta_description`
- OpenGraph tags: `og:title`, `og:description`, `og:image`, `og:type=article`
- Twitter Card: `twitter:card=summary_large_image`
- Canonical URL on every post page
- Structured data: `Article` schema (JSON-LD) in every post

## 7. Key Third-Party Integrations (all via env vars)
- `STORAGE_API_URL` — media uploads
- `EMAIL_API_URL` — newsletter subscriptions, author invites
- `WEBHOOK_URL` — optional: notify external services on publish
