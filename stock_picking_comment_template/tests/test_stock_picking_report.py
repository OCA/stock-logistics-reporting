# Copyright 2019 C2i Change 2 improve - Eduardo Magdalena <emagdalena@c2i.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestStockPickingReport(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")
        cls.base_comment_model = cls.env["base.comment.template"]
        # Create comment related to sale model
        cls.picking_obj = cls.env.ref("stock.model_stock_picking")
        cls.before_comment = cls._create_comment(cls, "before_lines")
        cls.after_comment = cls._create_comment(cls, "after_lines")
        # Create partner
        cls.partner = cls.env["res.partner"].create({"name": "Partner Test"})
        cls.partner.base_comment_template_ids = [
            (4, cls.before_comment.id),
            (4, cls.after_comment.id),
        ]
        cls.picking_model = cls.env["stock.picking"]
        cls.picking = cls.picking_model.create(
            {
                "partner_id": cls.partner.id,
                "location_id": cls.env.ref("stock.stock_location_stock").id,
                "location_dest_id": cls.env.ref("stock.stock_location_customers").id,
                "picking_type_id": cls.env.ref("stock.picking_type_out").id,
            }
        )

    def _create_comment(self, position):
        return self.base_comment_model.create(
            {
                "name": "Comment " + position,
                "company_id": self.company.id,
                "position": position,
                "text": "Text " + position,
                "models": "stock.picking",
                "model_ids": [(6, 0, self.picking_obj.ids)],
            }
        )

    def test_comments_in_deliveryslip(self):
        res = self.env["ir.actions.report"]._render_qweb_html(
            "stock.report_deliveryslip", self.picking.ids
        )
        self.assertRegex(str(res[0]), self.before_comment.text)
        self.assertRegex(str(res[0]), self.after_comment.text)

    def test_comments_in_report_picking(self):
        res = self.env["ir.actions.report"]._render_qweb_html(
            "stock.report_picking", self.picking.ids
        )
        self.assertRegex(str(res[0]), self.before_comment.text)
        self.assertRegex(str(res[0]), self.after_comment.text)
