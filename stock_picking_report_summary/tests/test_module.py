# Copyright (C) 2022 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.base.tests.common import BaseCommon


class TestModule(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.PickingReportWizard = cls.env["picking.summary.wizard"]
        cls.StockPicking = cls.env["stock.picking"]
        cls.outPickingType = cls.env.ref("stock.picking_type_out")
        cls.ir_actions_report = cls.env["ir.actions.report"]
        cls.report_name = "stock_picking_report_summary.report_picking_summary"

    def test_01_wizard(self):
        pickings = self.StockPicking.search(
            [
                ("picking_type_id", "=", self.outPickingType.id),
            ]
        )

        wizard = self.PickingReportWizard.with_context(
            active_model="stock.picking",
            active_ids=pickings.ids,
        ).create({})

        # Test fields Compute
        sum_th = sum(wizard.mapped("product_line_ids.standard_price_total"))
        wizard._compute_standard_price_total()
        self.assertEqual(sum_th, wizard.standard_price_total)

        # Test PDF render
        custom_note = "La Rabia Del Pueblo - Keny Arkana"
        pickings[0].note = custom_note
        res = str(
            self.ir_actions_report._render_qweb_html(self.report_name, wizard.ids)[0]
        )
        self.assertIn(custom_note, res)
