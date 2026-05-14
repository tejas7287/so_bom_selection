# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import io
import base64


class BarcodeController(http.Controller):

    # ------------------------------------------------------------------
    # /wo-barcode/<wo_id>
    # Primary route — one barcode per work order.
    # Serial encoded = <WORKCENTER>-<MO>  e.g. WELDING-WH-MO-00042
    # ------------------------------------------------------------------
    @http.route('/wo-barcode/<int:wo_id>', type='http', auth='user', website=True)
    def wo_barcode_page(self, wo_id, **kwargs):
        """Render a full barcode label page for a specific work order."""
        wo = request.env['mrp.workorder'].sudo().browse(wo_id)
        if not wo.exists():
            return request.not_found()

        serial = wo.wo_barcode_serial
        barcode_image = self._generate_barcode_b64(serial)

        return request.render('so_bom_selection.barcode_page_template', {
            'serial': serial,
            'barcode_image': barcode_image,
            # rich context for the template
            'wo': wo,
            'workcenter_name': wo.workcenter_id.name or '',
            'mo_name': wo.production_id.name or '',
            'product_name': wo.product_id.name or '',
            'lot': wo.semi_finished_lot_id or None,
        })

    # ------------------------------------------------------------------
    # /barcode/<serial>
    # Generic fallback route — used by StockLot.action_print_barcode()
    # and for backward-compatibility with old links.
    # ------------------------------------------------------------------
    @http.route('/barcode/<string:serial>', type='http', auth='user', website=True)
    def barcode_page(self, serial=None, **kwargs):
        """Render a barcode page from a raw serial string (lot name)."""
        barcode_image = self._generate_barcode_b64(serial)
        lot = request.env['stock.lot'].sudo().search(
            [('name', '=', serial)], limit=1
        )
        # Try to enrich with work order context if one is linked
        wo = request.env['mrp.workorder'].sudo().search(
            [('wo_barcode_serial', '=', serial)], limit=1
        )
        return request.render('so_bom_selection.barcode_page_template', {
            'serial': serial,
            'barcode_image': barcode_image,
            'wo': wo or None,
            'workcenter_name': wo.workcenter_id.name if wo else '',
            'mo_name': wo.production_id.name if wo else '',
            'product_name': wo.product_id.name if wo else (lot.product_id.name if lot else ''),
            'lot': lot or None,
        })

    # ------------------------------------------------------------------
    # /barcode/image/<serial>   — raw PNG download
    # ------------------------------------------------------------------
    @http.route('/barcode/image/<string:serial>', type='http', auth='user')
    def barcode_image(self, serial=None, **kwargs):
        """Return a raw Code128 PNG for download."""
        import barcode
        from barcode.writer import ImageWriter

        buf = io.BytesIO()
        code = barcode.get('code128', serial, writer=ImageWriter())
        code.write(buf, options={
            'write_text': True,
            'quiet_zone': 6.5,
            'module_height': 15.0,
            'font_size': 10,
        })
        buf.seek(0)
        return request.make_response(buf.read(), headers=[
            ('Content-Type', 'image/png'),
            ('Content-Disposition', f'attachment; filename=Barcode_{serial}.png'),
        ])

    # ------------------------------------------------------------------
    # Internal helper
    # ------------------------------------------------------------------
    def _generate_barcode_b64(self, serial):
        """Generate a Code128 barcode and return it as a base64 PNG string."""
        try:
            import barcode
            from barcode.writer import ImageWriter

            buf = io.BytesIO()
            code = barcode.get('code128', serial, writer=ImageWriter())
            code.write(buf, options={
                'write_text': True,
                'quiet_zone': 6.5,
                'module_height': 15.0,
                'font_size': 10,
            })
            buf.seek(0)
            return base64.b64encode(buf.read()).decode('utf-8')
        except Exception:
            return None
