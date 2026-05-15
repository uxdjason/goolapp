import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const apps = defineCollection({
  loader: glob({ pattern: "**/*.{md,mdx}", base: "./src/content/apps" }),
  schema: z.object({
    title: z.string(),
    slug: z.string(),
    description: z.string().max(160),
    shortDescription: z.string().max(80),
    category: z.enum(['calculator', 'quiz', 'converter', 'tool', 'misc']),
    primaryKeyword: z.string(),
    secondaryKeywords: z.array(z.string()).default([]),
    publishedAt: z.date(),
    updatedAt: z.date().optional(),
    legacyUrl: z.string().url().optional(),
    relatedSlugs: z.array(z.string()).default([]),
    draft: z.boolean().default(false),
    seo: z.object({
      title: z.string().min(20).max(60),
      description: z.string().min(80).max(160),
      canonicalPath: z.string().regex(/^\/.+\/$/),
      ogTitle: z.string().min(20).max(70),
      ogDescription: z.string().min(80).max(200),
      ogImage: z.string().default('/og/default.png'),
      ogType: z.literal('website').default('website'),
      twitterCard: z.enum(['summary', 'summary_large_image']).default('summary_large_image'),
      searchTitle: z.string().min(20).max(60).optional(),
      searchDescription: z.string().min(80).max(160).optional(),
      intent: z.enum(['informational', 'transactional', 'navigational']),
      primaryKeyword: z.string(),
      secondaryKeywords: z.array(z.string()).max(10),
      lsiKeywords: z.array(z.string()).default([]),
      robots: z.enum(['index,follow', 'noindex,follow', 'noindex,nofollow']).default('index,follow'),
    }),
  }),
});

const blogDrafts = defineCollection({
  loader: glob({ pattern: "**/*.{md,mdx}", base: "./src/content/blog-drafts" }),
  schema: z.object({
    title: z.string(),
    targetAppSlug: z.string(),
    targetAppUrl: z.string(),
    keywords: z.array(z.string()),
    createdAt: z.date(),
    uploadedToNaver: z.boolean().default(false),
  }),
});

export const collections = { apps, 'blog-drafts': blogDrafts };
