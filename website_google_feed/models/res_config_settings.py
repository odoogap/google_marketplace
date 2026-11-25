from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    google_merchant_center_file_timeout = fields.Integer(
        string="GMC File timeout", related='website_id.google_feed_expire_time', readonly=False)

    def update_website_file(self):
        for record in self:
            self.env['ir.attachment'].sudo().search([
                ('type', '=', 'binary'),
                ('url', '=like', '/google-feed/%%/%d.xml' % record.website_id.id),
            ]).unlink()
