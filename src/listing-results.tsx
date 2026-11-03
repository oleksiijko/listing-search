import type { FC } from "react";
import type { SearchPage } from "./search-api";

interface ListingResultsProps {
  data: SearchPage;
  onPageChange: (page: number) => void;
}

const currency = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 2,
  minimumFractionDigits: 0,
});

const percent = new Intl.NumberFormat("en-US", {
  style: "percent",
  maximumFractionDigits: 1,
});

export const ListingResults: FC<ListingResultsProps> = ({ data, onPageChange }) => {
  const { results, page, pageSize, total, totalPages } = data;
  if (total === 0) {
    return <p className="text-sm text-muted-foreground">No matching listings</p>;
  }

  const first = (page - 1) * pageSize + 1;
  const last = first + results.length - 1;

  return (
    <>
      <p className="mb-3 text-sm text-muted-foreground">
        Showing {first}–{last} of {total} {total === 1 ? "listing" : "listings"}
      </p>
      <table aria-label="Ranked listings" className="listings-table w-full table-fixed text-sm">
        <colgroup>
          <col />
          <col className="w-20 sm:w-32" />
          <col className="w-12 sm:w-20" />
          <col className="w-14 sm:w-24" />
        </colgroup>
        <thead className="bg-muted text-xs text-muted-foreground">
          <tr>
            <th scope="col">Address</th>
            <th scope="col">Price</th>
            <th scope="col">Beds</th>
            <th scope="col"><span className="sr-only">Relevance </span>Score</th>
          </tr>
        </thead>
        <tbody className="tabular-nums">
          {results.map((listing) => (
            <tr key={JSON.stringify([listing.source, listing.id])}>
              <th scope="row">
                {listing.address}
                <span className="block text-xs font-normal text-muted-foreground">
                  {listing.city}, {listing.state} {listing.zip}
                  <span className="capitalize"> · {listing.status}</span>
                </span>
              </th>
              <td>{currency.format(listing.price)}</td>
              <td>{listing.bedrooms}</td>
              <td>{percent.format(listing.score)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <nav
        aria-label="Results pages"
        className="mt-4 flex flex-wrap items-center justify-between gap-2 text-sm"
      >
        <button
          type="button"
          className="button-secondary"
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
        >
          Previous
        </button>
        <span className="tabular-nums">Page {page} of {totalPages}</span>
        <button
          type="button"
          className="button-secondary"
          onClick={() => onPageChange(page + 1)}
          disabled={page >= totalPages}
        >
          Next
        </button>
      </nav>
    </>
  );
};
