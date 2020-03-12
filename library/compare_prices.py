#!/usr/bin/env python3

DOCUMENTATION = """
---
module: compare_prices
short_description: Query K&L Product SKUs for prices
description:
    - With a list of product_skus, will query current K&L price
    - Optionally saves state for comparing product prices to previous queries
version_added: '2.9'

options:
    term:
        description:
            - Search term to use (E.g. Laphroaig)
        required: true
        default: null
        aliases: []
    output_file:
        description:
            - File to save search result product SKUS (for change comparison)
        required: false
        default: null
        aliases: []

requirements:
    - python >= 3.8
    - requests_html >= 0.10
"""


RETURN = """
changed: bool
prices:
    [
        {
            "current_price": float?,
            "difference": float?,
            "name": string,
            "previous_price": float?,
            "sku": string,
        }
    ]
"""

EXAMPLES = """
- name: find product prices
  check_prices:
    product_skus: '[{
        "name": "Octomore \"10.3 - Islay Barley\" Heavily Peated Islay Single Malt Whisky (750ml)",
        "sku": "1441557"
        "price": 249.99,
    }]'
    output_file: "{{ prices_file }}"
  register: products

"""
import asyncio
import csv
import os
import re
from typing import Dict, List, Optional

from ansible.module_utils.basic import *
from ansible.module_utils.kl_helpers import (
    Product,
    PriceChange,
    coalesce_float,
    get_product_by_sku,
)


Prices = Dict[str, Optional[float]]

FIELDS = {
    "product_skus": {"required": True, "type": "list"},
    "output_file": {"required": False, "type": "str"},
}

CSV_HEADERS = ["sku", "price"]


def get_previous_prices(filename: str) -> Prices:
    if not os.path.exists(filename):
        return {}

    with open(filename, "w+") as prices_file:
        reader = csv.reader(prices_file)
        try:
            next(reader)  # Skip headers
        except StopIteration:
            # There's no data, return an empty dict
            return {}
        return {row[0]: coalesce_float(row[1]) for row in reader}


def write_new_prices(output_file: str, prices: Prices) -> None:
    with open(output_file, "w") as output_file:
        writer = csv.writer(output_file)
        writer.writerow(CSV_HEADERS)
        for sku, price in prices.items():
            writer.writerow([sku, f"{price:.02f}" if price is not None else ""])


def has_price_changes(previous: Prices, new: Prices) -> bool:
    """ Compare previous & new prices
        
            Worst perf case is when prices all match,
            Best case is an early return due to prise/sku mismatch
    """
    if new and not previous:
        return True
    for sku, new_price in new.items():
        # Try to early return for any of the following mismatches
        if sku not in previous:
            return True
        if new_price != previous[sku]:
            return True
    return False


def get_price_changes(
    products: List[Product], output_file: Optional[str],
) -> List[PriceChange]:
    """ Check if skus for the given search term have changed since the last play """
    if not output_file:
        # If we're not asked to keep state, products are always "changed=True"
        return [PriceChange(p.name, p.sku, None, p.price, p.price) for p in products]

    new_prices = {p.sku: p.price for p in products}
    previous = get_previous_prices(output_file)
    is_changed = has_price_changes(previous, new_prices)

    # Write new products if there's a difference
    if is_changed:
        write_new_prices(output_file, new_prices)

    return [
        PriceChange(
            p.name,
            p.sku,
            previous.get(p.sku),
            p.price,
            previous.get(p.sku, p.price) - p.price,
        )
        for p in products
    ]


def main():
    module = AnsibleModule(argument_spec=FIELDS)

    products = asyncio.get_event_loop().run_until_complete(
        asyncio.gather(
            *[get_product_by_sku(sku) for sku in module.params["product_skus"]]
        )
    )
    changes = get_price_changes(
        [p for p in products if p is not None], module.params["output_file"],
    )
    is_changed = any(map(lambda c: c.difference, changes))
    module.exit_json(changed=is_changed, prices=[c.to_dict() for c in changes])


if __name__ == "__main__":
    main()
