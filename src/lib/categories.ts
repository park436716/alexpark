export type CategoryKey =
  | 'constitutional-law'
  | 'civil-law'
  | 'criminal-law'
  | 'commercial-law'
  | 'civil-procedure'
  | 'criminal-procedure'
  | 'administrative-law'
  | 'concepts'
  | 'overviews'
  | 'other';

export interface CategoryMeta {
  slug: CategoryKey;
  ko: string;
  en: string;
  blurb: string;
}

export const categories: CategoryMeta[] = [
  { slug: 'constitutional-law', ko: '헌법', en: 'Constitutional Law', blurb: '기본권, 권력분립, 헌법재판' },
  { slug: 'civil-law', ko: '민법', en: 'Civil Law', blurb: '계약, 불법행위, 물권, 가족, 상속' },
  { slug: 'criminal-law', ko: '형법', en: 'Criminal Law', blurb: '총론, 각론' },
  { slug: 'commercial-law', ko: '상법', en: 'Commercial Law', blurb: '회사, 증권, 보험, 해상' },
  { slug: 'civil-procedure', ko: '민사소송법', en: 'Civil Procedure', blurb: '증거, 강제집행' },
  { slug: 'criminal-procedure', ko: '형사소송법', en: 'Criminal Procedure', blurb: '수사, 공판, 증거' },
  { slug: 'administrative-law', ko: '행정법', en: 'Administrative Law', blurb: '행정소송, 규제' },
  { slug: 'concepts', ko: '개념·방법론', en: 'Concepts', blurb: '주요 도그마틱, 해석 방법론' },
  { slug: 'overviews', ko: '종합', en: 'Overviews', blurb: '여러 문헌을 아우르는 종합 정리' },
  { slug: 'other', ko: '기타', en: 'Other', blurb: '국제법, 법철학, 기타' },
];

const map = new Map(categories.map((c) => [c.slug, c] as const));

export function getCategory(slug: string): CategoryMeta | undefined {
  return map.get(slug as CategoryKey);
}
