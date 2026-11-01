export type Category = { id: number; slug: string; name: string };
export type Product = { id: number; sku: string; name: string; brand: string; description: string; price: number;
  specifications: Record<string, string | number | boolean>; attributes: string[]; image_url: string | null; source: string; category: Category };
export type Scored = { product: Product; score: number; reasons: string[]; rec_id: number | null };
export type Parsed = { category: string | null; budget_min: number | null; budget_max: number | null; brands: string[]; keywords: string[];
  required_specs: Record<string, unknown>; intent: string; method: string };
export type AssistantOut = { reply: string; reply_method: string; parsed: Parsed; results: Scored[] };
export type Comparison = { id: number; products: Product[]; spec_keys: string[]; summary: string; summary_method: string; created_at: string };
export type Prefs = { budget_max: number | null; favorite_categories: string[]; favorite_brands: string[]; interests: string[] };
