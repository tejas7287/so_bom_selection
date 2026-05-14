# Bill Of Material from Sale Order Line

**Version:** 1.0  
**Category:** Manufacturing  
**License:** AGPL-3  
**Author:** Cybrosys Techno Solutions
**Website:** https://www.cybrosys.com

## Description

Select the BOM in sale order line and generate the manufacturing order of components

Select the Bill of Material of each product in Sale Order Line. After confirmation of Sale Order, Manufacturing Order of the components in the Bill of Material will be created automatically.

## Features

- Odoo 19.0 compatible
- Addon module
- Select the BOM in sale order line and generate the manufacturing order of components

## Dependencies

This module depends on the following Odoo modules:

- `sale_management`
- `mrp`
- `stock`
- `stock_barcode`

## Installation

1. Clone this repository into your Odoo addons directory:
   ```bash
   git clone https://github.com/tejas7287/so_bom_selection.git
   ```

2. Add the module path to your Odoo configuration file (`odoo.conf`):
   ```
   addons_path = /path/to/odoo/addons,/path/to/so_bom_selection
   ```

3. Restart the Odoo server:
   ```bash
   sudo systemctl restart odoo
   ```

4. Go to **Apps** → **Update Apps List** → Search for **"Bill Of Material from Sale Order Line"** → Click **Install**

## Module Structure

```
so_bom_selection/
├── README.rst
├── __init__.py
├── __manifest__.py
├── controllers/
├── doc/
├── hooks.py
├── models/
├── reports/
├── static/
├── views/
```

## Configuration

After installation, configure the module through Odoo's Settings menu or the module's specific configuration options.

## License

This project is licensed under the AGPL-3 License.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
