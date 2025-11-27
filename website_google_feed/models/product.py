# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.addons.http_routing.models.ir_http import slug


class ProductProduct(models.Model):
    _inherit = 'product.product'

    sync_with_mc = fields.Boolean(string='Sync with Google MC')
    google_product_brand_id = fields.Many2one('merchant.center.brand', string='Brand')
    google_mpn = fields.Char(string='Google MPN')
    google_adult = fields.Boolean(string='Google MC Adult Rating?', default=False)

    def _get_price_from_pricelist(self, product, pricelist):
        pricelist_rule = pricelist._get_product_rule(
            product,
            1.0,
            uom=product.uom_id,
            date=fields.Datetime.now(),
        )
        if not pricelist_rule:
            pricelist_rule = self.env['product.pricelist.item']
        else:
            pricelist_rule = self.env['product.pricelist.item'].browse(pricelist_rule)

        return pricelist_rule._compute_price(
            product, 1.0,
            currency=pricelist.currency_id,
            uom=product.uom_id,
            date=fields.Datetime.now()
        )

    def get_google_feed_xml(self, website, currency_code):
        domain = website.domain or ''
        if domain and domain[-1] == '/':
            domain = domain[:-1]
        feed_info_array = []
        pricelist = self.env['product.pricelist'].search([('website_id', '=', website.id), ('currency_id.name', '=', currency_code.upper())],
                                                         limit=1)
        for product in self:
            product_template = product.product_tmpl_id[0]

            price_unit = self._get_price_from_pricelist(product, pricelist)

            feed_info_array.append({
                'title': product.display_name,
                'link': "{}/shop/{}".format(domain, slug(product_template)),
                'description': product.with_context(lang='fr_FR').description_sale or '',
                'image_link': '{}/web/image/product.product/{}/image_1024'.format(domain, product.id),
                'price': '{} {}'.format(price_unit, pricelist.currency_id.display_name),
                'product_type': ', '.join(product.public_categ_ids.mapped('display_name')),
                'gtin': product.barcode or '',
                'condition': 'new',
                'id': product.id,
                'availability': 'in stock',
                'brand': product.google_product_brand_id.name or '',
                'mpn': product.google_mpn or product.default_code,
                'adult': product.google_adult and 'yes' or 'no',
            })

        return feed_info_array


class ProductTemplate(models.Model):
    _inherit = "product.template"

    sync_with_mc = fields.Boolean(string='Sync with Google MC', compute='_compute_sync_with_mc',
                                  inverse='_set_sync_with_mc', store=False)
    google_product_brand_id = fields.Many2one('merchant.center.brand', string='Brand',
                                              compute='_compute_google_product_brand_id',
                                              inverse='_set_google_product_brand_id', store=True)
    google_mpn = fields.Char(string='Google MPN', compute='_compute_google_mpn', inverse='_set_google_mpn', store=True)
    google_adult = fields.Boolean(string='Google MC Adult Rating?', default=False, compute='_compute_google_adult',
                                  inverse='_set_google_adult', store=True)

    @api.depends('product_variant_ids', 'product_variant_ids.sync_with_mc')
    def _compute_sync_with_mc(self):
        unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.sync_with_mc = template.product_variant_ids.sync_with_mc
        for template in (self - unique_variants):
            template.sync_with_mc = False

    def _set_sync_with_mc(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.product_variant_ids.sync_with_mc = template.sync_with_mc

    @api.depends('product_variant_ids', 'product_variant_ids.google_product_brand_id')
    def _compute_google_product_brand_id(self):
        unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.google_product_brand_id = template.product_variant_ids.google_product_brand_id
        for template in (self - unique_variants):
            template.google_product_brand_id = False

    def _set_google_product_brand_id(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.product_variant_ids.google_product_brand_id = template.google_product_brand_id

    @api.depends('product_variant_ids', 'product_variant_ids.google_mpn')
    def _compute_google_mpn(self):
        unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.google_mpn = template.product_variant_ids.google_mpn
        for template in (self - unique_variants):
            template.google_mpn = False

    def _set_google_mpn(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.product_variant_ids.google_mpn = template.google_mpn

    @api.depends('product_variant_ids', 'product_variant_ids.google_adult')
    def _compute_google_adult(self):
        unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.google_adult = template.product_variant_ids.google_adult
        for template in (self - unique_variants):
            template.google_adult = False

    def _set_google_adult(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.product_variant_ids.google_adult = template.google_adult
