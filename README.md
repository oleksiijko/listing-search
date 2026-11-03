# Listing Search

A local full-stack property search over the 12 listings in the supplied JSON. The React UI calls the Flask API for filtering, ranking, and pagination.

## Run locally

From this folder, with Python 3.11+, [uv](https://docs.astral.sh/uv/) and Node.js 22.13+ (22.x) or 24+:

```sh
uv sync --locked
npm ci
npm run build
uv run --locked flask --app backend.app run --port 8000
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). For frontend development, leave Flask running and start `npm run dev` in another terminal. Vite proxies `/api` to Flask.

## Search and scoring

All filters are optional and combined with AND. Prices and minimum bedrooms use inclusive bounds. City is an exact case-insensitive match after trimming whitespace. The keyword is a case-insensitive substring of the description.

The relevance score ranges from 0 to 1:

- `recency = 2^(-ageInDays / 30)`. Age uses the current UTC date, with future dates treated as age zero. Recency halves every 30 days.
- `budgetFit = 1 / (1 + abs(price - targetBudget) / targetBudget)`. A listing exactly at the budget gets 1. Prices equally far above and below the budget get the same fit. Set Max price to enforce a ceiling.
- With a budget, `score = 0.7 * budgetFit + 0.3 * recency`. Without a budget, the score is just recency. The weights favor price fit while giving newer listings a chance to move up.

The API sorts by the full score, newest listing date, then source and ID. It slices the sorted results into pages and the UI rounds scores for display. The JSON is loaded once at startup. Each query scans the dataset and sorts its matches. This is simple for the supplied dataset. Source records are kept separate, including records with similar addresses.

## API and code map

`GET /api/listings` accepts `minPrice`, `maxPrice`, `minBedrooms`, `city`, `keyword`, `targetBudget`, `page` (default 1), and `pageSize` (default 5, range 1–100).

```sh
curl 'http://127.0.0.1:8000/api/listings?city=Springfield&targetBudget=450000&pageSize=2'
```

The response contains `results` (listing objects with `score`), `page`, `pageSize`, `total`, and `totalPages`. A valid search with no matches returns HTTP 200 and an empty first page. Invalid filters or a page past the last return HTTP 400 with an `error` message.

- `backend/app.py` loads data and handles HTTP. `backend/search.py` owns validation and the pure search and scoring functions.
- `src/app.tsx` coordinates request state. `src/search-form.tsx` renders the filters, `src/listing-results.tsx` renders the results table and pagination, and `src/search-api.ts` validates API responses.
- `data/sample_listings.json` contains the supplied data. `tests/test_search.py` covers the search logic and HTTP behavior.

## Checks

```sh
uv run --locked python -m unittest discover -s tests -v
uv run --locked mypy backend tests
uv run --locked ruff check backend tests
uv run --locked ruff format --check backend tests
npm run lint
npm run build
```
