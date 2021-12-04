# Copyright 2020, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import _, fields, models
import textwrap


class StockKardexReportWiz(models.TransientModel):
    _name = 'stock.kardex.report.wiz'
    _description = 'Wizard to create kardex reports of stock moves'

    date_from = fields.Datetime(
        string='From', required=True, default=fields.Datetime.now)
    date_to = fields.Datetime(
        string='To', required=True, default=fields.Datetime.now)
    product = fields.Many2one('product.product', required=True)
    location = fields.Many2one('stock.location', required=True)

    def open_table(self):
        self.env['stock.kardex.report'].search([]).unlink()
        self._cr.execute('''
        SELECT
        a.done - b.done
        AS
        total
        FROM
        (
            SELECT sum(qty_done)
            AS
            done
            FROM
            stock_move_line
            WHERE
            product_id = %s
            AND
            state = \'done\'
            AND
            date < %s
            AND
            location_dest_id = %s
        )
        a
        CROSS JOIN
        (
            SELECT sum(qty_done)
            AS
            done
            FROM
            stock_move_line
            WHERE
            product_id = %s
            AND
            state = \'done\'
            AND
            date < %s
            AND
            location_id = %s
        )
        b
        ''', [
            self.product.id, self.date_from, self.location.id,
            self.product.id, self.date_from, self.location.id
            ])
        start_qty = self._cr.dictfetchall()
        total = 0
        if start_qty[0]['total']:
            total = start_qty[0]['total']
        self._cr.execute("""WITH one AS (
            SELECT
            sml.product_id, sml.product_uom_id,
            sml.lot_id, sml.owner_id, sml.package_id,
            sml.qty_done, sml.move_id, sml.location_id,
            sml.location_dest_id, sm.date, sm.origin,
            sm.state
            FROM stock_move_line sml
            INNER JOIN stock_move sm
            ON sml.move_id = sm.id
            WHERE
            sm.date >= %s
            AND sm.date <= %s),
            two AS (
                SELECT *
                FROM one
                WHERE location_id = %s
                OR location_dest_id = %s)
            SELECT *
            FROM two
            WHERE product_id = %s
            AND state = 'done'
            ORDER BY date;""", [
            self.date_from, self.date_to,
            self.location.id, self.location.id,
            self.product.id
            ])
        moves = self._cr.dictfetchall()
        report_list = []
        report_list.append({
            'product_id': self.product.id,
            'qty_done': 0,
            'date': self.date_from,
            'origin': _('Initial Balance'),
            'balance': total,
        })
        for rec in moves:
            done_qty = rec['qty_done']
            if rec['location_id'] == self.location.id:
                done_qty = -rec['qty_done']
            total += done_qty
            origin = rec['origin']
            if origin:
                origin = textwrap.shorten(
                    rec['origin'], width=80, placeholder="...")
            line = {
                'move_id': rec['move_id'],
                'product_id': rec['product_id'],
                'product_uom_id': rec['product_uom_id'],
                'lot_id': rec['lot_id'],
                'owner_id': rec['owner_id'],
                'package_id': rec['package_id'],
                'qty_done': done_qty,
                'location_id': rec['location_id'],
                'location_dest_id': rec['location_dest_id'],
                'date': rec['date'],
                'balance': total,
                'origin': origin,
            }
            report_list.append(line)
        self.env['stock.kardex.report'].create(report_list)
        tree_view_id = self.env.ref(
            'stock_kardex_report.stock_kardex_report_tree_view').id
        action = {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree')],
            'view_id': tree_view_id,
            'view_mode': 'tree',
            'name': _('Stock Report'),
            'res_model': 'stock.kardex.report',
        }
        return action
