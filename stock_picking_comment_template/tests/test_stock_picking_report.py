# Copyright 2019 C2i Change 2 improve - Eduardo Magdalena <emagdalena@c2i.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestStockPickingReport(TransactionCase):
    def setUp(self):
        super().setUp()
        self.company = self.env.ref("base.main_company")
        self.base_comment_model = self.env["base.comment.template"]
        # Create comment related to sale model
        self.picking_obj = self.env.ref("stock.model_stock_picking")
        self.before_comment = self._create_comment(self.picking_obj, "before_lines")
        self.after_comment = self._create_comment(self.picking_obj, "after_lines")
        # Create partner
        self.partner = self.env["res.partner"].create({"name": "Partner Test"})
        self.partner.base_comment_template_ids = [
            (4, self.before_comment.id),
            (4, self.after_comment.id),
        ]
        self.picking_model = self.env["stock.picking"]
        self.picking = self.picking_model.create(
            {
                "partner_id": self.partner.id,
                "location_id": self.ref("stock.stock_location_stock"),
                "location_dest_id": self.ref("stock.stock_location_customers"),
                "picking_type_id": self.ref("stock.picking_type_out"),
            }
        )

    def _create_comment(self, model, position):
        return self.base_comment_model.create(
            {
                "name": "Comment " + position,
                "company_id": self.company.id,
                "position": position,
                "text": "Text " + position,
                "model_ids": [(6, 0, model.ids)],
            }
        )

    def test_comments_in_deliveryslip(self):
        res = (
            self.env["ir.actions.report"]
            ._get_report_from_name("stock.report_deliveryslip")
            ._render_qweb_html(self.picking.ids)
        )
        self.assertRegex(str(res[0]), self.before_comment.text)
        self.assertRegex(str(res[0]), self.after_comment.text)

    def test_comments_in_report_picking(self):
        res = (
            self.env["ir.actions.report"]
            ._get_report_from_name("stock.report_picking")
            ._render_qweb_html(self.picking.ids)
        )
        self.assertRegex(str(res[0]), self.before_comment.text)
        self.assertRegex(str(res[0]), self.after_comment.text)
