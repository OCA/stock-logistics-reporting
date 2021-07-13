# Copyright 2019 Eficent Business and IT Consulting Services, S.L.
# Copyright 2019 Aleph Objects, Inc.
from odoo import models
import pytz
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class StockQuantityHistory(models.TransientModel):
    _inherit = 'stock.quantity.history'

    def open_table(self):
        action = super(StockQuantityHistory, self).open_table()
        if self.env.user.tz:
            user = self.env.user
            tz = pytz.timezone(user.tz) or pytz.utc
            to_date_datetime = datetime.strptime(
                self.date, DEFAULT_SERVER_DATETIME_FORMAT)
            to_date = pytz.utc.localize(
                to_date_datetime).astimezone(tz).replace(tzinfo=None)
        else:
            to_date = self.date
        if self.compute_at_date:
            action['name'] = '%s (%s)' % (action['name'], to_date)
        return action
