# -*- coding: utf-8 -*-

from odoo import models, fields


class MerchantCetnerBrand(models.Model):
    _name = 'merchant.center.brand'
    _inherit = ['website.published.multi.mixin']
    _description = "GMC Brand"

    name = fields.Char(size=256, string='Brand Name', required=True)
    product_count = fields.Integer('# Products', compute='_compute_product_count',
                                   help="The number of products under this Brand")
    image = fields.Binary()
    description = fields.Text(string="Description")

    def _compute_product_count(self):
        read_group_res = self.env['product.product']._read_group(domain=[(
            'google_product_brand_id', 'in', self.ids)], groupby=['google_product_brand_id'], aggregates=['__count'])
        group_data = dict(
            (data[0].id, data[1]) for data in read_group_res)
        for brand in self:
            brand.product_count = group_data.get(brand.id, 0)

    def _compute_website_url(self):
        for brand in self:
            brand.website_url = "/shop?brand=%s-%s" % (brand.name, brand.id)
