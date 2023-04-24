# Copyright (C) 2022 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class TestModule(TransactionCase):
    def setUp(self):
        super().setUp()
        self.PickingReportWizard = self.env["picking.summary.wizard"]
        self.StockPicking = self.env["stock.picking"]
        self.outPickingType = self.env.ref("stock.picking_type_out")

    def _test_wizard(self, pickings):
        wizard = self.PickingReportWizard.with_context(
            active_model="stock.picking",
            active_ids=pickings.ids,
        ).create({})

        custom_note = "La Rabia Del Pueblo - Keny Arkana"
        pickings[0].note = custom_note
        report = self.env.ref("stock_picking_report_summary.report_picking_summary")
        res = str(report.render_qweb_html(wizard.ids)[0])
        self.assertIn(custom_note, res)

    def test_wizard(self):
        pickings = self.StockPicking.search(
            [
                ("picking_type_id", "=", self.outPickingType.id),
            ]
        )
        self._test_wizard(pickings)
