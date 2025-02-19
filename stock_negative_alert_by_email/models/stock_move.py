# Copyright (C) 2025-Today:
# Dinamiche Aziendali Srl (<http://www.dinamicheaziendali.it/>)
# @author: Giuseppe Borruso <gborruso@dinamicheaziendali.it>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import _, api, fields, models


class StockMoveInherit(models.Model):
    _inherit = "stock.move"

    @api.model
    def _compute_domain_negative_stock(self, company):
        interval_number = company.negative_stock_interval_number
        interval_type = company.negative_stock_interval_type
        if not (interval_number or interval_type):
            return False

        date_end = fields.Datetime.now()
        if interval_type == "minutes":
            date_start = fields.Datetime.now() - timedelta(minutes=interval_number)
        elif interval_type == "hours":
            date_start = fields.Datetime.now() - timedelta(hours=interval_number)
        elif interval_type == "days":
            date_start = fields.Datetime.now() - timedelta(days=interval_number)
        else:
            date_start = fields.Datetime.now() - timedelta(weeks=interval_number)
        return [
            ("write_date", ">", date_start),
            ("write_date", "<", date_end),
            ("company_id", "=", company.id),
        ]

    @api.model
    def _compute_table_products_negative_stock(self, products, company):
        quantity_type = company.negative_stock_quantity_type
        table_products = _(
            """
            <table class="table table-sm">
                <thead>
                    <tr>
                        <th name="th_product">Product</th>
                        <th name="th_%(quantity_type)s">%(quantity_type_name)s</th>
                    </tr>
                </thead>
                <tbody>
        """
            % {
                "quantity_type": quantity_type,
                "quantity_type_name": (
                    "Quantity On Hand"
                    if quantity_type == "qty_available"
                    else "Forecast Quantity"
                ),
            }
        )
        for product in products:
            if quantity_type == "qty_available":
                product_quantity = product.with_company(company.id).qty_available
            else:
                product_quantity = product.with_company(company.id).virtual_available
            if product_quantity >= 0:
                continue
            table_products += f"""
                <tr>
                   <td name="product">{product.display_name}</td>
                   <td name="{quantity_type}">{product_quantity}</td>
                </tr>
            """
        table_products += """
                </tbody>
            </table>
        """
        return table_products

    @api.model
    def _compute_body_htm_negative_stock(self, products, company):
        return _(
            """
            <p>Dear</p>
            <br />
            <p>
                We would like to inform you that negative quantities have been
                detected in the warehouse for the following items:
            </p>
            <br />
            %(table_products)s
            <p>
                We kindly ask you to take immediate action to rectify this situation
                in order to ensure proper stock management and avoid any
                inconveniences.
            </p>
            <br /><br />
            <p>Kind regards,</p>
            <p>%(company)s</p>
        """
            % {
                "table_products": self._compute_table_products_negative_stock(
                    products, company
                ),
                "company": company.display_name,
            }
        )

    def action_negative_stock(self):
        for company in self.env["res.company"].search([]):
            record = self.sudo().with_company(company.id)
            domain = record._compute_domain_negative_stock(company)
            if isinstance(domain, bool):
                continue
            products = record.search(domain).mapped("product_id")
            mail_from = company.negative_stock_mail_from or self.env.user.email
            mail_to = company.negative_stock_mail_to
            if products and mail_from and mail_to:
                mail = self.env["mail.mail"].create(
                    {
                        "subject": "Negative Stock Alert",
                        "email_from": mail_from,
                        "email_to": mail_to,
                        "body_html": record._compute_body_htm_negative_stock(
                            products, company
                        ),
                    }
                )
                mail.send()
