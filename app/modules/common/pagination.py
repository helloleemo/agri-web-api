
from dataclasses import dataclass
from fastapi import Query

@dataclass
class Pagination:
    skip: int
    limit:int


def pagination_dep(
    skip: int = Query(0, ge = 0),
    limit:int = Query(10, ge=1, le=100)
) -> Pagination:
    return Pagination(skip=skip, limit=limit)

