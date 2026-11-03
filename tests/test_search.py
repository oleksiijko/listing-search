import unittest
from datetime import date, timedelta

from backend.app import create_app
from backend.search import Listing, SearchQuery, search

TODAY = date(2026, 9, 5)


def listing(listing_id: str, *, source: str = "MLS_A", **changes: object) -> Listing:
    data: dict[str, object] = {
        "id": listing_id,
        "source": source,
        "address": "100 Oak Avenue",
        "city": "Springfield",
        "state": "VA",
        "zip": "22150",
        "price": 450_000,
        "bedrooms": 3,
        "bathrooms": 2,
        "sqft": 1500,
        "latitude": 38.8,
        "longitude": -77.2,
        "listedDate": TODAY,
        "status": "active",
        "description": "Sunny home with a fenced garden.",
    }
    return Listing.model_validate(data | changes)


class SearchTests(unittest.TestCase):
    def test_all_filters_apply_with_inclusive_bounds(self) -> None:
        match = listing("yes", city=" Springfield ")
        options = [
            listing("cheap", price=449_999),
            listing("expensive", price=450_001),
            listing("small", bedrooms=2),
            listing("far", city="Fairfax"),
            listing("different", description="Private balcony"),
            match,
        ]
        query = SearchQuery.model_validate(
            {
                "minPrice": 450_000,
                "maxPrice": 450_000,
                "minBedrooms": 3,
                "city": " SPRINGFIELD ",
                "keyword": " GARDEN ",
            }
        )

        page = search(options, query, TODAY)

        self.assertEqual([result.listing for result in page.results], [match])

    def test_budget_can_rank_an_older_listing_higher(self) -> None:
        old = listing("old", listedDate=TODAY - timedelta(days=30))
        recent = listing("recent", price=900_000)

        by_budget = search(
            [recent, old], SearchQuery.model_validate({"targetBudget": 450_000}), TODAY
        )
        by_date = search([recent, old], SearchQuery(), TODAY)

        self.assertEqual(by_budget.results[0].listing, old)
        self.assertAlmostEqual(by_budget.results[0].score, 0.85)
        self.assertEqual(by_date.results[0].listing, recent)

    def test_future_dates_cannot_exceed_perfect_relevance(self) -> None:
        future = listing("future", listedDate=TODAY + timedelta(days=1))
        page = search(
            [future], SearchQuery.model_validate({"targetBudget": 450_000}), TODAY
        )
        self.assertEqual(page.results[0].score, 1.0)

    def test_ties_have_stable_source_and_id_order_across_pages(self) -> None:
        third = listing("1", source="MLS_B")
        second = listing("2")
        first = listing("1")
        options = [third, second, first]

        page_one = search(options, SearchQuery.model_validate({"pageSize": 2}), TODAY)
        page_two = search(
            reversed(options),
            SearchQuery.model_validate({"page": 2, "pageSize": 2}),
            TODAY,
        )

        self.assertEqual([row.listing for row in page_one.results], [first, second])
        self.assertEqual([row.listing for row in page_two.results], [third])
        self.assertEqual((page_two.total, page_two.total_pages), (3, 2))


class ListingsApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = create_app().test_client()

    def test_query_validation_returns_readable_errors(self) -> None:
        invalid = {
            "minPrice=700000&maxPrice=200000": "Minimum price",
            "minPrice=-1": "minPrice",
            "maxPrice=NaN": "maxPrice",
            "maxPrice=Infinity": "maxPrice",
            "minBedrooms=2.5": "minBedrooms",
            "targetBudget=0": "targetBudget",
            "page=0": "page",
            "pageSize=0": "pageSize",
            "pageSize=-1": "pageSize",
            "pageSize=101": "pageSize",
            "pageSize=2&pageSize=3": "only once",
            "pageSize=": "pageSize",
            "minprice=20": "minprice",
        }
        for query, error_text in invalid.items():
            with self.subTest(query=query):
                response = self.client.get(f"/api/listings?{query}")
                self.assertEqual(response.status_code, 400)
                self.assertIn(error_text, response.get_json()["error"])

    def test_city_with_no_matches_returns_an_empty_first_page(self) -> None:
        response = self.client.get("/api/listings?city=Atlantis")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json,
            {"results": [], "page": 1, "pageSize": 5, "total": 0, "totalPages": 0},
        )

    def test_last_partial_page_and_first_invalid_page(self) -> None:
        response = self.client.get("/api/listings?pageSize=5&page=3")
        beyond = self.client.get("/api/listings?pageSize=5&page=4")
        empty_beyond = self.client.get("/api/listings?city=Atlantis&page=2")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            (response.get_json()["total"], response.get_json()["totalPages"]), (12, 3)
        )
        self.assertEqual(len(response.get_json()["results"]), 2)
        self.assertEqual(beyond.status_code, 400)
        self.assertEqual(empty_beyond.status_code, 400)


if __name__ == "__main__":
    unittest.main()
