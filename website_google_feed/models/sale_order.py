from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _google_merchant_survey(self):
        prod_list = []
        for line in self.order_line:
            if not line.is_delivery:
                prod_list.append({"gtin": "%s" % line.product_id.id})

        merchant_id = self.env['ir.config_parameter'].sudo().get_param('website.google_merchant_id', '102186315')

        return {
            "merchant_id": merchant_id,
            "order_id": self.id,
            "email": self.partner_id.email,
            "delivery_country": self.partner_shipping_id.country_id.code,
            "estimated_delivery_date": self.expected_date.strftime('%Y-%m-%d'),
            "products": prod_list
        }
