from odoo import api, fields, models
from odoo.http import request
from odoo.tools import urls


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
        """Prepare the Google Merchant Center items of the feed.

        Follows Google's product data specification
        (https://support.google.com/merchants/answer/7052112) and the conventions of
        Odoo's own feed (``website_sale.product_feed``).

        :return: one dict per product; empty optional attributes are omitted
        :rtype: list[dict]
        """
        lang = website.default_lang_id.code or self.env.lang
        products = self.with_context(lang=lang, display_default_code=False)
        base_url = website.get_base_url()
        IrHttp = self.env["ir.http"]

        # Pricelist of this website in the requested currency. Without it, fall back
        # to the sales price, which is expressed in the company currency.
        pricelist = self.env["product.pricelist"].search(
            [
                ("website_id", "=", website.id),
                ("currency_id.name", "=", currency_code.upper()),
            ],
            limit=1,
        )

        def absolute_url(path, localized=True):
            # Language prefix (e.g. /fr/shop/...) needs the request's routing context.
            if localized and request:
                path = IrHttp._url_lang(path, lang_code=lang)
            return urls.urljoin(base_url, path)

        feed_items = []
        for product in products:
            if not product._is_variant_possible():
                continue

            currency = pricelist.currency_id or product.currency_id
            price = (
                pricelist and self._get_price_from_pricelist(product, pricelist)
            ) or product.lst_price
            # Google rejects items with a zero price.
            if currency.compare_amounts(price, 0) <= 0:
                continue

            brand = product.google_product_brand_id.name
            mpn = product.google_mpn or product.default_code
            item = {
                # Kept as the variant id so existing GMC listings stay matched.
                "id": product.id,
                "title": product.display_name[:150],
                "description": (
                    product.website_meta_description
                    or product.description_sale
                    or product.display_name
                )[:5000],
                "link": absolute_url(product.website_url),
                "image_link": (
                    # Google does not allow placeholder images.
                    absolute_url(product._get_image_1920_url(), localized=False)
                    if product.image_128
                    else ""
                ),
                "additional_image_link": [
                    absolute_url(url, localized=False)
                    for url in product._get_extra_image_1920_urls()[:10]
                ],
                "availability": "out_of_stock" if product._is_sold_out() else "in_stock",
                "price": f"{price:.{currency.decimal_places}f} {currency.name}",
                "condition": "new",
                "brand": brand or "",
                "gtin": product.barcode or "",
                "mpn": mpn or "",
                # "no" only when the product has neither a GTIN nor a brand + MPN pair.
                "identifier_exists": "yes" if product.barcode or (brand and mpn) else "no",
                "adult": "yes" if product.google_adult else "no",
                "product_type": [
                    category.replace("/", ">")
                    for category in product.public_categ_ids.sorted("sequence").mapped(
                        "display_name"
                    )[:5]
                ],
            }
            # Required for variants in most countries, groups them under one product.
            if len(product.product_tmpl_id.product_variant_ids) > 1:
                item["item_group_id"] = product.product_tmpl_id.id
            feed_items.append(item)

        return feed_items

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

    def _get_related_fields_variant_template(self):
        return super()._get_related_fields_variant_template() + [
            "sync_with_mc",
            "google_product_brand_id",
            "google_mpn",
            "google_adult",
        ]

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
