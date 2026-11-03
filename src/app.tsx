import { useEffect, useRef, useState } from "react";
import { ListingResults } from "./listing-results";
import { fetchListings } from "./search-api";
import type { SearchResult } from "./search-api";
import { SearchForm } from "./search-form";

interface CompletedSearch {
  params: URLSearchParams;
  result: SearchResult;
}

export function App() {
  const [params, setParams] = useState(() => new URLSearchParams());
  const [completed, setCompleted] = useState<CompletedSearch>();
  const resultsHeading = useRef<HTMLHeadingElement>(null);
  const result = completed?.params === params ? completed.result : undefined;

  useEffect(() => {
    const controller = new AbortController();

    async function load() {
      try {
        const response = await fetchListings(params, controller.signal);
        if (!controller.signal.aborted) {
          setCompleted({ params, result: response });
        }
      } catch (error) {
        if (!controller.signal.aborted) {
          console.error("Listing search failed", error);
          setCompleted({ params, result: { kind: "unavailable" } });
        }
      }
    }

    void load();
    return () => controller.abort();
  }, [params]);

  function runSearch(params: URLSearchParams) {
    setParams(params);
    resultsHeading.current?.focus();
  }

  function changePage(page: number) {
    const nextParams = new URLSearchParams(params);
    nextParams.set("page", String(page));
    runSearch(nextParams);
  }

  return (
    <main className="mx-auto max-w-5xl px-4 py-5 sm:px-6 sm:py-7">
      <h1 className="mb-4 text-2xl font-semibold tracking-tight">Listing search</h1>
      <SearchForm onSearch={runSearch} />
      <section aria-labelledby="results-heading" className="mt-5 border-t border-border pt-4">
        <h2 id="results-heading" ref={resultsHeading} tabIndex={-1} className="sr-only">
          Search results
        </h2>
        <p className="sr-only" role="status">
          {result === undefined && "Loading listings."}
          {result?.kind === "success" && (
            result.data.total === 0
              ? "No matching listings."
              : result.data.total + " matches. Page " + result.data.page + "."
          )}
        </p>
        {result === undefined && (
          <p className="text-sm text-muted-foreground">
            Loading listings…
          </p>
        )}
        {result?.kind === "success" && (
          <ListingResults data={result.data} onPageChange={changePage} />
        )}
        {result?.kind === "invalid" && (
          <p role="alert" className="text-sm text-destructive">{result.message}</p>
        )}
        {result?.kind === "unavailable" && (
          <div role="alert" className="text-sm">
            <p className="text-destructive">Could not load listings</p>
            <button
              type="button"
              className="button-secondary mt-3"
              onClick={() => runSearch(new URLSearchParams(params))}
            >
              Try again
            </button>
          </div>
        )}
      </section>
    </main>
  );
}
