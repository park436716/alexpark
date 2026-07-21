import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const wiki = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './wiki' }),
  schema: z.object({
    title: z.string(),
    authors: z.string().optional(),
    year: z.union([z.string(), z.number()]).optional(),
    doi: z.string().optional(),
    source: z.string().optional(),
    category: z.string().optional(),
    pdf_path: z.string().optional(),
    pdf_filename: z.string().optional(),
    source_collection: z.string().optional(),
    tags: z.array(z.string()).optional(),
    date: z.union([z.string(), z.date()]).optional(),
    summary: z.string().optional(),
    draft: z.boolean().optional(),
  }),
});

export const collections = { wiki };
