# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.tests import tagged

from odoo.addons.sale_section_and_note_revamp.tests.common import (
    TestDisplayLineMixinCommon,
)


@tagged("post_install", "-at_install")
class TestStockDeliverySaleSectionNoteCommon(TestDisplayLineMixinCommon):
    def setUp(self):
        super().setUp()
        self.sale_order.order_line._compute_product_updatable()
        self.sale_order.action_confirm()
        self.sale_order.order_line._compute_product_updatable()
