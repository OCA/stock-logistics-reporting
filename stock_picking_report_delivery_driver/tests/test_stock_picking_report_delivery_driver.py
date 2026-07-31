# Copyright 2026 Sadiq-OSI
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from unittest.mock import patch

from lxml import html

from odoo import Command
from odoo.tests.common import TransactionCase

from odoo.addons.base.models.ir_actions_report import IrActionsReport


class TestStockPickingReportDeliveryDriver(TransactionCase):
    report_xmlids = (
        "stock.action_report_delivery",
        "stock.action_report_picking",
    )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.env["res.partner"].create(
            {"name": "Report Driver Test Customer"}
        )
        cls.driver = cls.env["res.partner"].create(
            {"name": "Unique Report Driver Test Name"}
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Report Driver Test Product",
                "type": "consu",
                "is_storable": True,
            }
        )
        cls.delivery_product = cls.env["product.product"].create(
            {
                "name": "Report Driver Test Delivery Product",
                "type": "service",
                "list_price": 10.0,
                "categ_id": cls.env.ref("delivery.product_category_deliveries").id,
            }
        )
        carrier_values = {
            "fixed_price": 10.0,
            "delivery_type": "fixed",
            "product_id": cls.delivery_product.id,
        }
        cls.carrier_with_driver = cls.env["delivery.carrier"].create(
            {
                **carrier_values,
                "name": "Report Carrier With Driver",
                "driver_id": cls.driver.id,
            }
        )
        cls.carrier_without_driver = cls.env["delivery.carrier"].create(
            {
                **carrier_values,
                "name": "Report Carrier Without Driver",
            }
        )

    def _create_picking(self, picking_code, carrier=None, driver=None):
        picking_configuration = {
            "outgoing": (
                self.env.ref("stock.picking_type_out"),
                self.env.ref("stock.stock_location_stock"),
                self.env.ref("stock.stock_location_customers"),
            ),
            "incoming": (
                self.env.ref("stock.picking_type_in"),
                self.env.ref("stock.stock_location_suppliers"),
                self.env.ref("stock.stock_location_stock"),
            ),
            "internal": (
                self.env.ref("stock.picking_type_internal"),
                self.env.ref("stock.stock_location_stock"),
                self.env.ref("stock.stock_location_output"),
            ),
        }
        picking_type, location, destination = picking_configuration[picking_code]
        picking = self.env["stock.picking"].create(
            {
                "partner_id": self.customer.id,
                "picking_type_id": picking_type.id,
                "location_id": location.id,
                "location_dest_id": destination.id,
                "carrier_id": carrier.id if carrier else False,
                "move_ids": [
                    Command.create(
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 1.0,
                            "product_uom": self.product.uom_id.id,
                            "location_id": location.id,
                            "location_dest_id": destination.id,
                        }
                    )
                ],
            }
        )
        if driver is not None:
            picking.driver_id = driver
        return picking

    def _render_report(self, report_xmlid, picking):
        with patch.object(IrActionsReport, "barcode", return_value=b""):
            report_html = self.env["ir.actions.report"]._render_qweb_html(
                report_xmlid, picking.ids
            )[0]
        return html.fromstring(report_html)

    def _assert_driver(self, report_tree, visible, parenthesized=False):
        driver_nodes = report_tree.xpath(
            "//span[normalize-space(text())=$driver_name]",
            driver_name=self.driver.name,
        )
        self.assertEqual(len(driver_nodes), int(visible))
        if visible:
            self.assertFalse(
                driver_nodes[0].xpath("ancestor::div[@name='div_shipping_method']")
            )
            driver_paragraph = "".join(driver_nodes[0].getparent().itertext()).strip()
            expected = f"({self.driver.name})" if parenthesized else self.driver.name
            self.assertEqual(
                "".join(driver_paragraph.split()), "".join(expected.split())
            )

    def test_outgoing_report_matrix(self):
        scenarios = (
            (
                "carrier_and_driver",
                self.carrier_with_driver,
                self.driver,
                True,
                True,
            ),
            ("driver_only", None, self.driver, True, False),
            ("carrier_only", self.carrier_without_driver, None, False, False),
            ("neither", None, None, False, False),
        )
        for scenario, carrier, driver, driver_visible, parenthesized in scenarios:
            picking = self._create_picking("outgoing", carrier, driver)
            for report_xmlid in self.report_xmlids:
                with self.subTest(report=report_xmlid, scenario=scenario):
                    report_tree = self._render_report(report_xmlid, picking)
                    self._assert_driver(
                        report_tree, driver_visible, parenthesized=parenthesized
                    )
                    report_text = report_tree.text_content()
                    carrier_labels = report_tree.xpath(
                        "//strong[normalize-space(text())='Carrier' or "
                        "normalize-space(text())='Carrier:']"
                    )
                    self.assertEqual(
                        len(carrier_labels), int(bool(carrier or driver_visible))
                    )
                    if carrier:
                        self.assertIn(carrier.name, report_text)
                    else:
                        self.assertNotIn("Report Carrier", report_text)

    def test_driver_hidden_on_non_outgoing_reports(self):
        for picking_code in ("incoming", "internal"):
            picking = self._create_picking(
                picking_code, self.carrier_with_driver, self.driver
            )
            for report_xmlid in self.report_xmlids:
                with self.subTest(report=report_xmlid, picking_code=picking_code):
                    report_tree = self._render_report(report_xmlid, picking)
                    self._assert_driver(report_tree, False)
                    self.assertIn(
                        self.carrier_with_driver.name, report_tree.text_content()
                    )
