from odoo.tests.common import TransactionCase


class TestStockReportQuantityByLocationReport(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.with_quantity = True
        location1 = cls.env["stock.location"].create(
            {
                "name": "Test Location 1",
                "usage": "internal",
                "display_name": "Test Location 1",
                "location_id": cls.env.ref("stock.stock_location_stock").id,
            }
        )
        location2 = cls.env["stock.location"].create(
            {
                "name": "Test Location 2",
                "usage": "internal",
                "location_id": cls.env.ref("stock.stock_location_stock").id,
                "display_name": "Test Location 2",
            }
        )
        location3 = cls.env["stock.location"].create(
            {
                "name": "Test Location 3",
                "usage": "internal",
                "location_id": cls.env.ref("stock.stock_location_stock").id,
                "display_name": "Test Location 3",
            }
        )
        location4 = cls.env["stock.location"].create(
            {
                "name": "Test Location 4",
                "usage": "internal",
                "location_id": cls.env.ref("stock.stock_location_stock").id,
                "display_name": "Test Location 4",
            }
        )
        cls.location_ids = [location1.id, location2.id, location3.id, location4.id]

    def test_get_report_html(self):
        report = self.env["report.stock.report.quantity.by.location.pdf"].create(
            {
                "with_quantity": self.with_quantity,
                "location_ids": self.location_ids,
            }
        )
        report._compute_results()
        report.get_html(given_context={"active_id": report.id})

    def test_wizard(self):
        wizard = self.env["stock.report.quantity.by.location.prepare"].create({})
        wizard.button_export_html()
        wizard.button_export_pdf()

    def test_stock_report_result(self):
        """
        Check that report shows the products present
        at each location
        """

        product1 = self.env["product.product"].create(
            {
                "name": "test product report by location",
                "type": "product",
                "display_name": "product1",
            }
        )

        quant_pro_loc1 = self.env["stock.quant"].create(
            {
                "product_id": product1.id,
                "location_id": self.location_ids[0],
                "quantity": 100.0,
                "reserved_quantity": 80.0,
            }
        )

        quant_pro_loc2 = self.env["stock.quant"].create(
            {
                "product_id": product1.id,
                "location_id": self.location_ids[1],
                "quantity": 140.0,
                "reserved_quantity": 60.0,
            }
        )

        product2 = self.env["product.product"].create(
            {
                "name": "test product 2 report by location",
                "type": "product",
                "display_name": "product2",
            }
        )

        quant_pro2_loc1 = self.env["stock.quant"].create(
            {
                "product_id": product2.id,
                "location_id": self.location_ids[0],
                "quantity": 100.0,
                "reserved_quantity": 50.0,
            }
        )

        product3 = self.env["product.product"].create(
            {
                "name": "test product 3 report by location",
                "type": "product",
                "display_name": "product3",
            }
        )

        quant_pro3_loc3 = self.env["stock.quant"].create(
            {
                "product_id": product3.id,
                "location_id": self.location_ids[3],
                "quantity": 100.0,
                "reserved_quantity": 50.0,
            }
        )

        # Report should have a line with two products and all the location in which it exist
        report = self.env["report.stock.report.quantity.by.location.pdf"].create(
            {
                "with_quantity": self.with_quantity,
                "location_ids": [self.location_ids[0], self.location_ids[1]],
            }
        )
        product_row = report.results.filtered(
            lambda r: (
                r.name == product1.display_name or r.name == product2.display_name
            )
        )
        self.assertEqual(
            len(product_row),
            2,
            msg="There should be two product lines in the report",
        )
        location1_row = report.results_location.filtered(
            lambda r: (
                r.loc_name == quant_pro_loc1.location_id.display_name
                and r.product_name == product1.display_name
            )
        )
        self.assertEqual(
            location1_row[0].quantity_on_hand,
            quant_pro_loc1.quantity,
            msg="The product quantity at location 1 should match",
        )
        location2_row = report.results_location.filtered(
            lambda r: (
                r.loc_name == quant_pro_loc2.location_id.display_name
                and r.product_name == product1.display_name
            )
        )
        self.assertEqual(
            location2_row[0].quantity_on_hand,
            quant_pro_loc2.quantity,
            msg="The product quantity at location 2 should match",
        )

        # Report should not have any lines with the product
        # No locations displayed as product does not exist on location 2
        report = self.env["report.stock.report.quantity.by.location.pdf"].create(
            {
                "with_quantity": self.with_quantity,
                "location_ids": [self.location_ids[2]],
            }
        )

        product_row = report.results.filtered(
            lambda r: (
                r.name == product1.display_name
                or r.name == product2.display_name
                or r.name == product3.display_name
            )
        )
        self.assertEqual(
            len(product_row),
            0,
            msg="There should not be any product lines in the report",
        )
        location_row = report.results_location.filtered(
            lambda r: (
                r.loc_name == quant_pro_loc1.location_id.display_name
                or r.loc_name == quant_pro2_loc1.location_id.display_name
                or r.loc_name == quant_pro3_loc3.location_id.display_name
            )
        )
        self.assertEqual(
            len(location_row),
            0,
            msg="No locations should be displayed on the report",
        )
