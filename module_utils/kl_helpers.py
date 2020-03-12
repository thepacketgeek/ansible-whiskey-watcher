#!/usr/bin/env python3
from __future__ import annotations

import re
from typing import Any, Dict, List, NamedTuple, Optional

from requests_html import AsyncHTMLSession, Element, HTMLResponse


ROOT_URL = "http://www.klwines.com"
SKU_RE = re.compile(r"sku=(\d+)")
PRICE_RE = re.compile(r"Price: \$([\d\.]+)\n")


class Product(NamedTuple):
    """ Data for a K&L Product """

    sku: str
    name: str
    price: Optional[float]

    @classmethod
    def from_html(cls, block: Element) -> Optional[Product]:
        for link in block.find("a"):
            try:
                sku = link.attrs["data-app-insights-track-search-doc-id"]
                break
            except KeyError:
                return
        else:
            return
        price = PRICE_RE.findall(block.text)
        name = [line for line in block.text.split("\n") if "!" not in line][0]

        return cls(sku, name, float(price[0]) if price else None)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "sku": self.sku,
            "price": self.price,
        }


class PriceChange(NamedTuple):
    name: str
    sku: str
    previous_price: Optional[float]
    current_price: Optional[float]
    difference: Optional[float]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "sku": self.sku,
            "previous_price": self.previous_price,
            "current_price": self.current_price,
            "difference": self.difference,
        }


def coalesce_float(val: str) -> Optional[float]:
    """ Try to parse a str -> float, otherwise it's None """
    try:
        return float(val)
    except:
        return None


async def get_search(term: str) -> HTMLResponse:
    url = f"{ROOT_URL}/Products?searchText={term}"
    sess = AsyncHTMLSession()
    return await sess.get(url)


async def get_products_for_term(term: str) -> List[Product]:
    results = await get_search(term)
    result_containers = results.html.find("div.tf-product")
    products = [Product.from_html(block) for block in result_containers]
    return list(filter(None, products))


async def get_product_by_sku(sku: str) -> Optional[Product]:
    products = await get_products_for_term(sku)
    for product in products:
        if product.sku == sku:
            return product

