# [K&L Wines](klwines.com) Price Tracker (w/ Ansible)
---

Using Ansible to do some homework for me and checking for price changes on whiskey (or other imbibments) I'm on the watch for (using my favorite whiskey store!).

## Modules
A Library is included with two modules:

- `search_products`: Given a search term (E.g. Octomore), search K&L Wines for matching products
  - If provided an `output_file`, will keep state and compare results to the previous run
- `compare_prices`: Given a list of SKUS (E.g. results for a search term), get the product prices
  - If provided an `output_file`, will keep state and compare results to the previous run



## Example Output
Notice that the `check search term` and `compare product prices` tasks will only show changes if:
- The products returned for a search term are different from the previous run
- The prices for an included product is changed from previous run

```sh
$ ansible-playbook play.yaml --limit localhost,ardbeg

PLAY [Prep KL Module State Directories] *****************

TASK [create products output dir] ***********************
ok: [localhost]

TASK [create prices output dir] *************************
ok: [localhost]

PLAY [Check K&L Prices] *********************************

TASK [create products output file] **********************
ok: [ardbeg]

TASK [check search term] ********************************
ok: [ardbeg]

TASK [create build output file] *************************
changed: [ardbeg]

TASK [compare product prices] ***************************
changed: [ardbeg]

TASK [save prices] **************************************
changed: [ardbeg]

PLAY [Combine Price Output] *****************************

TASK [create new output build directory] ****************
ok: [localhost]

TASK [write CSV headers] ********************************
changed: [localhost]

TASK [combine price CSVs] *******************************
changed: [localhost]

TASK [cleanup build dir] ********************************
changed: [localhost]

PLAY RECAP **********************************************
ardbeg                     : ok=5    changed=3    unreachable=0    failed=0    skipped=2    rescued=0    ignored=0
localhost                  : ok=6    changed=3    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

## Example Report (csv)
```csv
Search Term,SKU,Name,Previous Price,Current Price,Difference
ardbeg,1011309,Ardbeg "Uigeadail" Islay Single Malt Scotch Whisky (750ml) (Previously $73),72.99,56.99,16.00
ardbeg,1323099,Ardbeg "An Oa" Islay Single Malt Scotch Whisky (750ml),59.99,59.99,$0.00
ardbeg,992236,Ardbeg 10 Year Old Islay Single Malt Scotch Whisky (750ml) (Previously $50),44.99,44.99,$0.00
ardbeg,1051653,Ardbeg "Corryvreckan" Islay Single Malt Scotch Whisky (750ml) (Elsewhere $82),69.99,69.99,$0.00
ardbeg,1439409,Ardbeg 19 Year "Traigh Bhan" Islay Single Malt Scotch Whisky (750ml),299.99,299.99,$0.00
ardbeg,1417130,Ardbeg 12 Year Old "That Boutique-y Whisky Company" Batch #15 Islay Single Malt Scotch Whisky 375ml,119.99,119.99,$0.00
```


## Example Inventory

```ini
[scotch]
ardbeg
laphroaig
octomore

[wine]
caymus
justin

[all:vars]
ansible_python_interpreter=/path/to/virtualenvs/ansible/bin/python
user_data_path = "."
```

# Example Ansible.cfg
```ini
[defaults]
inventory = hosts
retry_files_enabled = True
```