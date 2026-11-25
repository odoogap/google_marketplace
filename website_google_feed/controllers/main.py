import datetime

from odoo import http, fields
from odoo.addons.website.controllers.main import Website
from odoo.http import request


class WebsiteGoogleFeed(Website):

    @http.route(
        "/google-feed/<string:currency_code>/<int:wid>",
        type="http",
        auth="public",
        website=True,
        multilang=False,
    )
    def google_feed(self, currency_code, wid, **kwargs):
        """Generate XML Google Product Feed for given website + currency."""
        Attachment = request.env["ir.attachment"].sudo()
        Product = request.env["product.product"].sudo()
        View = request.env["ir.ui.view"].sudo()
        Website = request.env["website"].sudo()

        mimetype = "application/xml;charset=utf-8"

        website = Website.browse(wid).exists()
        if not website:
            raise request.not_found()

        feed_url = f"/google-feed/{currency_code}/{website.id}.xml"

        # ---------------------------------------------------------------------
        # HELPER
        # ---------------------------------------------------------------------
        def create_feed_attachment(url, content):
            return Attachment.create(
                {
                    "raw": content.encode("utf-8"),
                    "mimetype": mimetype,
                    "type": "binary",
                    "name": url,
                    "url": url,
                }
            )

        # ---------------------------------------------------------------------
        # Check cached attachment
        # ---------------------------------------------------------------------
        feed = Attachment.search(
            [
                ("type", "=", "binary"),
                ("url", "=", feed_url),
            ],
            limit=1,
        )

        if feed:
            created_at = fields.Datetime.from_string(feed.create_date)
            expiry_hours = website.google_feed_expire_time or 48
            expired = (datetime.datetime.now() - created_at) > datetime.timedelta(
                hours=expiry_hours
            )

            if not expired and feed.raw:
                return request.make_response(feed.raw.content, [("Content-Type", mimetype)])
            else:
                feed.unlink()

        # ---------------------------------------------------------------------
        # Build product list (filtered)
        # ---------------------------------------------------------------------
        domain = [
            ("sale_ok", "=", True),
            ("active", "=", True),
            ("website_published", "=", True),
            ("sync_with_mc", "=", True),
        ]
        products = Product.search(domain)

        # Include multi-website or match current
        products = products.filtered(
            lambda p: not p.website_id or p.website_id.id == website.id
        )

        # ---------------------------------------------------------------------
        # Build Feed Data
        # ---------------------------------------------------------------------
        feed_info_array = products.get_google_feed_xml(website, currency_code)

        # ---------------------------------------------------------------------
        # Render Template
        # ---------------------------------------------------------------------
        content = View._render_template(
            "website_google_feed.feed_xml",
            {
                "website": website,
                "feed_info_array": feed_info_array,
            },
        )

        # Save to attachment cache
        create_feed_attachment(feed_url, content)

        return request.make_response(content, [("Content-Type", mimetype)])
