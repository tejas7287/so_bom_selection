# Bill Of Material from Sale Order Line

![Version](https://img.shields.io/badge/version-1.0-blue)
![Category](https://img.shields.io/badge/category-Manufacturing-green)
![License](https://img.shields.io/badge/license-AGPL-3-orange)

| | |
|---|---|
| **Name** | Bill Of Material from Sale Order Line |
| **Version** | 1.0 |
| **Category** | Manufacturing |
| **Author** | Cybrosys Techno Solutions |
| **License** | AGPL-3 |
| **Application** | No (Addon) |
| **Website** | https://www.cybrosys.com |

## Description

Select the BOM in sale order line and generate the manufacturing order of components

Select the Bill of Material of each product in Sale Order Line. After confirmation of Sale Order, Manufacturing Order of the components in the Bill of Material will be created automatically.

## Functionality

### Models & Fields

#### Extends `mrp.bom`

**File:** `models/bom.py`

**Inherits:** `mrp.bom`

**Fields:**

| Field | Type |
|-------|------|
| `source_bom_id` | `Many2one` |

**Key Methods:**

- `_onchange_source_bom_id()` — Onchange handler
- `write()` — Overridden ORM method

#### Extends `mrp.production, mrp.workorder, mrp.workcenter, stock.move`

**File:** `models/mrp_production.py`

**Inherits:** `mrp.production`, `mrp.workorder`, `mrp.workcenter`, `stock.move`

**Fields:**

| Field | Type |
|-------|------|
| `source` | `Char` |
| `sale_line_id` | `Many2one` |
| `qty_to_produce` | `Float` |
| `customer_ref` | `Char` |
| `location_id` | `Many2one` |

**Key Methods:**

- `action_confirm()` — Action/workflow method
- `action_open_barcode_controller()` — Action/workflow method
- `action_print_semi_barcode()` — Action/workflow method
- `button_start()` — Button handler
- `create()` — Overridden ORM method

#### Extends `mrp.workorder, mrp.workcenter, product.template, stock.lot`

**File:** `models/mrp_workorder.py`

**Inherits:** `mrp.workorder`, `mrp.workcenter`, `product.template`, `stock.lot`

**Fields:**

| Field | Type |
|-------|------|
| `currency_id` | `Many2one` |
| `wc_cost_hour` | `Float` |
| `employee_cost_hour` | `Monetary` |
| `semi_finished_product_ids` | `Many2many` |
| `customer_ref` | `Char` |
| `semi_finished_lot_id` | `Many2one` |
| `wo_barcode_serial` | `Char` |
| `location_id` | `Many2one` |
| `is_semi_finished` | `Boolean` |

**Key Methods:**

- `_compute_wo_barcode_serial()` — Computed field
- `button_start()` — Button handler
- `button_finish()` — Button handler
- `action_open_semi_barcode()` — Action/workflow method
- `action_open_barcode_controller()` — Action/workflow method
- `action_print_semi_barcode()` — Action/workflow method
- `button_start()` — Button handler
- `action_print_barcode()` — Action/workflow method

#### Extends `sale.order`

**File:** `models/sale_order.py`

**Inherits:** `sale.order`

**Fields:**

| Field | Type |
|-------|------|
| `reference_template_id` | `Many2one` |

**Key Methods:**

- `action_open_bom_overview()` — Action/workflow method
- `action_confirm()` — Action/workflow method

#### Extends `sale.order.line`

**File:** `models/sale_order_line.py`

**Inherits:** `sale.order.line`

**Fields:**

| Field | Type |
|-------|------|
| `bom_id` | `Many2one` |
| `product_template_id` | `Many2one` |

#### Extends `res.partner, sale.order, mrp.production`

**File:** `models/semiproduct.py`

**Inherits:** `res.partner`, `sale.order`, `mrp.production`

**Fields:**

| Field | Type |
|-------|------|
| `customer_ref` | `Char` |

**Key Methods:**

- `create()` — Overridden ORM method
- `_compute_customer_ref()` — Computed field

#### Extends `stock.rule`

**File:** `models/stock_rule.py`

**Inherits:** `stock.rule`

### Views & UI

**Website/Portal Templates:**

- `barcode_page_template` (`barcode_page_template.xml`)

### Web Controllers & Routes

| Route | Controller |
|-------|------------|
| `/wo-barcode/<int:wo_id>` | `barcode_controller.py` |
| `/barcode/<string:serial>` | `barcode_controller.py` |
| `/barcode/image/<string:serial>` | `barcode_controller.py` |

### Reports

- `lot_barcode_report.xml`

### Frontend Assets

**JavaScript:**

- `static/src/js/print_barcode.js`

**XML Templates (Frontend):**

- `static/src/xml/mrp_barcode_template.xml`

## Dependencies

| Module | Type |
|--------|------|
| `sale_management` | Odoo Core |
| `mrp` | Odoo Core |
| `stock` | Odoo Core |
| `stock_barcode` | Odoo Core |

## File Structure

```
so_bom_selection/
├── LICENSE
├── README.md
├── README.rst
├── __init__.py
├── __manifest__.py
├── controllers/
│   ├── __init__.py
│   └── barcode_controller.py
├── doc/
│   └── RELEASE_NOTES.md
├── hooks.py
├── models/
│   ├── __init__.py
│   ├── bom.py
│   ├── mrp_production.py
│   ├── mrp_workorder.py
│   ├── sale_order.py
│   ├── sale_order_line.py
│   ├── semiproduct.py
│   └── stock_rule.py
├── reports/
│   └── lot_barcode_report.xml
├── static/
│   ├── description/
│   │   ├── assets/
│   │   ├── banner.png
│   │   ├── icon.png
│   │   └── index.html
│   └── src/
│       ├── js/
│       └── xml/
└── views/
    ├── barcode_page_template.xml
    ├── mrp_production_views.xml
    ├── mrp_workorder_views.xml
    ├── sale_order_views.xml
    └── semiproduct.xml
```

## Installation

This module is part of the **[odoo-manufacturing-inventory-suite](https://github.com/tejas7287/odoo-manufacturing-inventory-suite)** suite.

1. Place this module in your Odoo addons directory
2. Update the apps list: **Settings** → **Apps** → **Update Apps List**
3. Search for **"Bill Of Material from Sale Order Line"** and click **Install**

## License

AGPL-3
