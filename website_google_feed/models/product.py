# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.http import request


class ProductProduct(models.Model):
    _inherit = "product.product"

    sync_with_mc = fields.Boolean(string="Sync with Google MC")
    google_product_brand_id = fields.Many2one("merchant.center.brand", string="Brand")
    google_mpn = fields.Char(string="Google MPN")
    google_adult = fields.Boolean(string="Google MC Adult Rating?", default=False)

    def _get_price_from_pricelist(self, product, pricelist):
        rule_id = pricelist._get_product_rule(
            product,
            quantity=1.0,
            uom=product.uom_id,
            date=fields.Datetime.now(),
        )

        rule = (
            self.env["product.pricelist.item"].browse(rule_id)
            if rule_id
            else self.env["product.pricelist.item"]
        )

        return rule._compute_price(
            product,
            quantity=1.0,
            currency=pricelist.currency_id,
            uom=product.uom_id,
            date=fields.Datetime.now(),
        )

    def get_google_feed_xml(self, website, currency_code):
        domain = (website.domain or "").rstrip("/")
        feed_info_array = []

        # Find pricelist for this website + currency
        pricelist = self.env["product.pricelist"].search(
            [
                ("website_id", "=", website.id),
                ("currency_id.name", "=", currency_code.upper()),
            ],
            limit=1,
        )

        slug = request.env["ir.http"]._slug
        currency_name = (
            pricelist.currency_id.display_name if pricelist else currency_code.upper()
        )

        for product in self:
            tmpl = product.product_tmpl_id

            price_unit = (
                pricelist
                and self._get_price_from_pricelist(product, pricelist)
                or product.lst_price
            )

            feed_info_array.append(
                {
                    "id": product.id,
                    "title": product.display_name,
                    "link": f"{domain}/shop/{slug(tmpl)}",
                    "description": product.with_context(lang="fr_FR").description_sale
                    or "",
                    "image_link": f"{domain}/web/image/product.product/{product.id}/image_1024",
                    "price": f"{price_unit} {currency_name}",
                    "product_type": ", ".join(
                        product.public_categ_ids.mapped("display_name")
                    ),
                    "gtin": product.barcode or "",
                    "condition": "new",
                    "availability": "in stock",
                    "brand": product.google_product_brand_id.name or "",
                    "mpn": product.google_mpn or product.default_code or "",
                    "adult": "yes" if product.google_adult else "no",
                }
            )

        return feed_info_array


class ProductTemplate(models.Model):
    _inherit = "product.template"

    sync_with_mc = fields.Boolean(
        string="Sync with Google MC",
        compute="_compute_sync_with_mc",
        inverse="_set_sync_with_mc",
        store=True,
    )
    google_product_brand_id = fields.Many2one(
        "merchant.center.brand",
        string="Brand",
        compute="_compute_google_product_brand_id",
        inverse="_set_google_product_brand_id",
        store=True,
    )
    google_mpn = fields.Char(
        string="Google MPN",
        compute="_compute_google_mpn",
        inverse="_set_google_mpn",
        store=True,
    )
    google_adult = fields.Boolean(
        string="Google MC Adult Rating?",
        default=False,
        compute="_compute_google_adult",
        inverse="_set_google_adult",
        store=True,
    )

    @api.depends("product_variant_ids.sync_with_mc")
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

    @api.depends("product_variant_ids.google_product_brand_id")
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

    @api.depends("product_variant_ids.google_mpn")
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

    @api.depends("product_variant_ids.google_adult")
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
