import { z } from "zod";

const listingSchema = z.object({
  id: z.string(),
  source: z.string(),
  address: z.string(),
  city: z.string(),
  state: z.string(),
  zip: z.string(),
  price: z.number().nonnegative(),
  bedrooms: z.int().nonnegative(),
  status: z.enum(["active", "pending", "sold"]),
  score: z.number().min(0).max(1),
});

const searchPageSchema = z.object({
  results: z.array(listingSchema),
  total: z.int().nonnegative(),
  totalPages: z.int().nonnegative(),
  page: z.int().positive(),
  pageSize: z.int().positive(),
});

export type SearchPage = z.infer<typeof searchPageSchema>;

export type SearchResult =
  | { kind: "success"; data: SearchPage }
  | { kind: "invalid"; message: string }
  | { kind: "unavailable" };

const errorSchema = z.object({ error: z.string() });

export async function fetchListings(
  params: URLSearchParams,
  signal: AbortSignal,
): Promise<SearchResult> {
  const response = await fetch("/api/listings?" + params.toString(), {
    signal,
    headers: { Accept: "application/json" },
  });

  if (response.status === 400) {
    const body: unknown = await response.json();
    return { kind: "invalid", message: errorSchema.parse(body).error };
  }
  if (!response.ok) {
    return { kind: "unavailable" };
  }

  const body: unknown = await response.json();
  return { kind: "success", data: searchPageSchema.parse(body) };
}
