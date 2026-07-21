import { getCollection, type CollectionEntry } from 'astro:content';

export type Post = CollectionEntry<'wiki'>;

export function categoryOf(post: Post): string {
  if (post.data.category) return post.data.category;
  const first = post.id.split('/')[0];
  return first ?? 'other';
}

export function slugOf(post: Post): string {
  const parts = post.id.split('/');
  return parts[parts.length - 1] ?? post.id;
}

export function sortKey(post: Post): number {
  const y = post.data.year;
  if (typeof y === 'number') return y;
  if (typeof y === 'string') {
    const n = parseInt(y, 10);
    if (!Number.isNaN(n)) return n;
  }
  return 0;
}

export async function getAllPosts(): Promise<Post[]> {
  const posts = await getCollection('wiki', ({ data }) => !data.draft);
  return posts.sort((a, b) => {
    const diff = sortKey(b) - sortKey(a);
    if (diff !== 0) return diff;
    return a.data.title.localeCompare(b.data.title);
  });
}

export async function getPostsByCategory(category: string): Promise<Post[]> {
  const all = await getAllPosts();
  return all.filter((p) => categoryOf(p) === category);
}
