from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from math import ceil, exp2
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel

DEFAULT_PAGE_SIZE = 5
MAX_PAGE_SIZE = 100
RECENCY_HALF_LIFE_DAYS = 30
BUDGET_WEIGHT = 0.7


class Listing(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel, frozen=True, allow_inf_nan=False
    )

    id: str
    source: str
    address: str
    city: str
    state: str
    zip: str
    price: float = Field(ge=0)
    bedrooms: int = Field(ge=0)
    bathrooms: float = Field(ge=0)
    sqft: int = Field(ge=0)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    listed_date: date
    status: Literal["active", "pending", "sold"]
    description: str


class SearchQuery(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        extra="forbid",
        str_strip_whitespace=True,
        allow_inf_nan=False,
        frozen=True,
    )

    min_price: float | None = Field(default=None, ge=0)
    max_price: float | None = Field(default=None, ge=0)
    min_bedrooms: int | None = Field(default=None, ge=0)
    city: str = Field(default="", max_length=120)
    keyword: str = Field(default="", max_length=250)
    target_budget: float | None = Field(default=None, gt=0)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE)

    @model_validator(mode="after")
    def validate_price_range(self) -> Self:
        if (
            self.min_price is not None
            and self.max_price is not None
            and self.min_price > self.max_price
        ):
            raise ValueError(
                "Minimum price must be less than or equal to maximum price."
            )
        return self


@dataclass(frozen=True)
class RankedListing:
    listing: Listing
    score: float


@dataclass(frozen=True)
class SearchPage:
    results: list[RankedListing]
    total: int
    total_pages: int


def relevance(listing: Listing, target_budget: float | None, today: date) -> float:
    age_days = max(0, (today - listing.listed_date).days)
    recency = exp2(-age_days / RECENCY_HALF_LIFE_DAYS)
    if target_budget is None:
        return recency

    relative_gap = abs(listing.price - target_budget) / target_budget
    budget_fit = 1 / (1 + relative_gap)
    return BUDGET_WEIGHT * budget_fit + (1 - BUDGET_WEIGHT) * recency


def search(listings: Iterable[Listing], query: SearchQuery, today: date) -> SearchPage:
    city = query.city.casefold()
    keyword = query.keyword.casefold()
    ranked = [
        RankedListing(listing, relevance(listing, query.target_budget, today))
        for listing in listings
        if (query.min_price is None or listing.price >= query.min_price)
        and (query.max_price is None or listing.price <= query.max_price)
        and (query.min_bedrooms is None or listing.bedrooms >= query.min_bedrooms)
        and (not city or listing.city.strip().casefold() == city)
        and (not keyword or keyword in listing.description.casefold())
    ]
    ranked.sort(
        key=lambda result: (
            -result.score,
            -result.listing.listed_date.toordinal(),
            result.listing.source,
            result.listing.id,
        ),
    )

    total = len(ranked)
    total_pages = ceil(total / query.page_size)
    start = (query.page - 1) * query.page_size
    return SearchPage(ranked[start : start + query.page_size], total, total_pages)
