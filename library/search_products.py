#!/usr/bin/env python3

DOCUMENTATION = """
---
module: search_products
short_description: Search K&L Products by Search Term
description:
    - For a given search term, will search K&L Wines and return back a list of matching products
    - Optionally saves state for comparing product results to previous searches
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
products:
    [
        {
            "name": string,
            "sku": string,
            "price": float?,
        }
    ]
"""

EXAMPLES = """
- name: find matching products
  search_products:
    term: "Octomore"
    output_file: "{{ product_output }}/{{ ansible_host }}"
  register: products
"""

import asyncio
import os
from sys import intern
from typing import Optional, Set as TSet  # ansible * clash
from itertools import chain

from ansible.module_utils.basic import *
from ansible.module_utils.kl_helpers import get_products_for_term


FIELDS = {
    "term": {"required": True, "type": "str"},
    "output_file": {"required": False, "type": "str"},
}


def get_previous_skus(filename: str) -> TSet[str]:
    if not os.path.exists(filename):
        return {}
    with open(filename, "r") as skus_file:
        # Intern strings so they match on hash/identity when sets are compared
        return {intern(s.strip()) for s in skus_file.readlines()}


def check_sku_difference(
    term: str, output_file: Optional[str], skus: TSet[str]
) -> bool:
    """ Check if skus for the given search term have changed since the last play """
    if not output_file:
        # If we're not asked to keep state, products are always "changed=True"
        return True

    previous = get_previous_skus(output_file)
    is_changed = previous != skus

    # Write new products if there's a difference
    if is_changed:
        with open(output_file, "w+") as skus_file:
            skus_file.write("\n".join(sorted(skus)))

    return is_changed


def main():
    module = AnsibleModule(argument_spec=FIELDS)
    search_term = module.params["term"]

    products = asyncio.get_event_loop().run_until_complete(
        get_products_for_term(search_term)
    )

    is_changed = check_sku_difference(
        search_term, module.params["output_file"], {intern(p.sku) for p in products}
    )

    module.exit_json(changed=is_changed, products=[p.to_dict() for p in products])


if __name__ == "__main__":
    main()
