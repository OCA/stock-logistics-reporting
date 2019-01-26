# Copyright 2019 C2i Change 2 improve - Eduardo Magdalena <emagdalena@c2i.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestStockPickingReport(TransactionCase):
    at_install = False
    post_install = True

    def setUp(self):
        super(TestStockPickingReport, self).setUp()
        self.base_comment_model = self.env['base.comment.template']
        self.before_comment = self._create_comment('before_lines')
        self.after_comment = self._create_comment('after_lines')
        self.partner = self.env['res.partner'].create({
            'name': 'Partner Test'
        })
        self.picking_model = self.env['stock.picking']
        self.picking = self.picking_model.create({
            'partner_id': self.partner.id,
            'location_id': self.supplier_location.id,
            'comment_template1_id': self.before_comment.id,
            'comment_template2_id': self.after_comment.id
        })

        self.picking._set_note1()
        self.picking._set_note2()

    def _create_comment(self, position):
        return self.base_comment_model.create({
            'name': 'Comment ' + position,
            'position': position,
            'text': 'Text ' + position
        })
