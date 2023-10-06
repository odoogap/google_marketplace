# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.addons.http_routing.models.ir_http import slug


class ProductProduct(models.Model):
    _inherit = 'product.product'

    sync_with_mc = fields.Boolean(string='Sync with Google MC')

    google_tax_rate = fields.Integer(string='Google Tax Rate', default="20")
    google_merchant_price = fields.Float(string='Google Price', compute="_compute_merchant_price", store=False,
                                         readonly=False)
    google_product_brand_id = fields.Many2one('merchant.center.brand', string='Brand')
    google_mpn = fields.Char(string='Google MPN')
    age_restricted = fields.Boolean(string='Apply age restrictions')

    @api.depends('lst_price', 'google_tax_rate')
    def _compute_merchant_price(self):
        for product in self:
            percentage_rate = float(product.google_tax_rate) / 100 + 1
            product.google_merchant_price = product.lst_price * percentage_rate

    def get_google_feed_xml(self, website):
        domain = website.domain or ''
        if domain and domain[-1] == '/':
            domain = domain[:-1]

        feed_info_array = []

        website_language = self.env['res.lang'].browse(website._default_language()).code

        for product in self:
            product_template = product.product_tmpl_id[0]
            feed_info_array.append({
                'title': product.with_context(lang=website_language).display_name,
                'link': "{}/shop/{}".format(domain, slug(product_template)),
                'description': product.with_context(lang=website_language).description_sale or '',
                'image_link': '{}/web/image/product.product/{}/image_1024'.format(domain, product.id),
                'price': '{} {}'.format(product.google_merchant_price, product.currency_id.display_name),
                'product_type': ', '.join(product.public_categ_ids.mapped('display_name')),
                'gtin': product.barcode or '',
                'condition': 'new',
                'id': product.id,
                'availability': 'in stock',
                'brand': product.google_product_brand_id.name or '',
                'mpn': product.google_mpn or product.default_code,
                'adult': product.age_restricted,
            })

        return feed_info_array
