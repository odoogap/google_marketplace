# -*- coding: utf-8 -*-

from odoo import api, models, fields, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    google_merchant_center_file_timeout = fields.Integer(string="GMC File timeout", related='website_id.google_feed_expire_time', readonly=False)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        return res

    def set_values(self):
        super().set_values()

    def update_website_file(self):
        for record in self:
            dom = [('url', '=', '/google-feed-%d.xml' % record.website_id.id), ('type', '=', 'binary')]
            self.env['ir.attachment'].sudo().search(dom).unlink()
