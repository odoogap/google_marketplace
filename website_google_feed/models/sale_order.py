from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _google_merchant_survey(self):
        prod_list = [
            {"gtin": line.product_id.barcode or str(line.product_id.id)}
            for line in self.order_line
            if not getattr(line, 'is_delivery', False)
        ]
        merchant_id = self.env['ir.config_parameter'].sudo().get_str('website.google_merchant_id', '102186315')
        return {
            "merchant_id": merchant_id,
            "order_id": self.id,
            "email": self.partner_id.email,
            "delivery_country": self.partner_shipping_id.country_id.code,
            "estimated_delivery_date": self.expected_date and self.expected_date.strftime('%Y-%m-%d') or False,
            "products": prod_list
        }
