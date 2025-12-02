# -*- coding: utf-8 -*-

from odoo import fields, models


class Website(models.Model):
    _inherit = 'website'

    google_feed_expire_time = fields.Integer(
        default=12, help="Time in hours after which the google feed will be regenerated.")
