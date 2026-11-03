from datetime import UTC, datetime
from pathlib import Path

from flask import Flask, Response, jsonify, request, send_from_directory
from pydantic import TypeAdapter, ValidationError

from backend.search import Listing, SearchQuery, search

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BUILD_DIR = PROJECT_ROOT / "dist"
DATA_PATH = PROJECT_ROOT / "data" / "sample_listings.json"


def create_app() -> Flask:
    listings = TypeAdapter(list[Listing]).validate_json(DATA_PATH.read_bytes())
    app = Flask(
        __name__, static_folder=str(BUILD_DIR / "assets"), static_url_path="/assets"
    )

    @app.get("/")
    def index() -> Response | tuple[str, int]:
        if not (BUILD_DIR / "index.html").is_file():
            return (
                "Build the frontend with npm ci and npm run build, or use npm run dev.",
                503,
            )
        return send_from_directory(BUILD_DIR, "index.html")

    @app.get("/api/listings")
    def list_properties() -> Response | tuple[Response, int]:
        duplicate = next(
            (name for name, values in request.args.lists() if len(values) > 1), None
        )
        if duplicate is not None:
            return jsonify(error=f"Provide {duplicate} only once."), 400

        try:
            query = SearchQuery.model_validate(request.args.to_dict())
        except ValidationError as error:
            messages = []
            for issue in error.errors(
                include_url=False, include_context=False, include_input=False
            ):
                field = ".".join(map(str, issue["loc"]))
                message = issue["msg"].removeprefix("Value error, ")
                messages.append(f"{field}: {message}" if field else message)
            return jsonify(error="; ".join(messages)), 400

        page = search(listings, query, datetime.now(UTC).date())
        if query.page > max(1, page.total_pages):
            return jsonify(error="That page does not exist. Start on page 1."), 400

        return jsonify(
            results=[
                result.listing.model_dump(mode="json", by_alias=True)
                | {"score": result.score}
                for result in page.results
            ],
            page=query.page,
            pageSize=query.page_size,
            total=page.total,
            totalPages=page.total_pages,
        )

    return app
