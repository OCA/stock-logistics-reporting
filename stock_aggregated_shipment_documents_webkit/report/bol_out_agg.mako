## -*- coding: utf-8 -*-
<html>
<head>
    <style type="text/css">
        ${css}

.center {
    text-align: center;
}

.left {
    text-align: left;
}

.left {
    text-align: right;
}


.list_main_footers td,
.list_main_footers th {
    border-style: none;
    text-align:left;
    font-size:12;
    padding:0;
}
    </style>
</head>

<body>
    <%page expression_filter="entity"/>
    <%
    from datetime import date
    def carriage_returns(text):
        return text.replace('\n', '<br />')

    def get_price_total(line):
        if line.sale_line_id:
            return line.sale_line_id.price_subtotal
        else:
            return line.product_qty * line.product_id.list_price

    def get_price_unit(line):
        if line.sale_line_id:
            return line.sale_line_id.price_unit
        else:
            return line.product_id.list_price

    picking = merge_picking(objects)
    inv = picking
    %>
    %if picking is None:
        <font color="red">Error, you need to select items with same partner.</font>
    %else:
        <div class="address">
            <%
            setLang(picking.partner_id.lang)
            invoice_addr = invoice_address(picking)
            %>
            <table class="recipient">
                <tr><td class="address_title">${_("Contact info:")}</td></tr>
                %if invoice_addr.phone:
                    <tr><td><b>${_("Phone:")}</b> ${invoice_addr.phone }</td></tr>
                %endif
                %if invoice_addr.mobile:
                    <tr><td><b>${_("Cell:")}</b> ${invoice_addr.mobile }</td></tr>
                %endif
                %if invoice_addr.email:
                    <tr><td><b>${_("Email:")}</b> ${invoice_addr.email }</td></tr>
                %endif
            </table>
            <table class="invoice">
                <tr><td class="address_title">${_("Customer name & address:")}</td></tr>
                <tr><td>${invoice_addr.title and invoice_addr.title.name or ''} ${invoice_addr.name }</td></tr>
                %if invoice_addr.contact_address:
                    <% address_lines = invoice_addr.contact_address.split("\n") %>
                    %for part in address_lines:
                        %if part:
                        <tr><td>${part}</td></tr>
                        %endif
                    %endfor
                %endif
            </table>
        </div>
        <div class="address">
            <%
            picking_addr = picking_address(picking)
            %>
            <table class="recipient">
                <tr><td class="address_title">${_("Ship to:")}</td></tr>
                %if picking.partner_id.parent_id:
                <tr><td>${picking.partner_id.parent_id.name or ''}</td></tr>
                <tr><td>${picking.partner_id.parent_id.title and picking.partner_id.parent_id.title.name or ''} ${picking.partner_id.parent_id.name }</td></tr>
                <% address_lines = picking.partner_id.parent_id.contact_address.split("\n")[1:] %>
                %else:
                <tr><td >${picking.partner_id.title and picking.partner_id.title.name or ''} ${picking.partner_id.name }</td></tr>
                <% address_lines = picking.partner_id.contact_address.split("\n") %>
                %endif
                %for part in address_lines:
                    %if part:
                    <tr><td>${part}</td></tr>
                    %endif
                %endfor
            </table>
            <table class="invoice">
                <tr><td class="address_title">${_("Pick from:")}</td></tr>
                <tr><td>${picking_addr.title and picking_addr.title.name or ''} ${picking_addr.name }</td></tr>
                %if picking_addr.contact_address:
                    <% address_lines = picking_addr.contact_address.split("\n") %>
                    %for part in address_lines:
                        %if part:
                        <tr><td>${part}</td></tr>
                        %endif
                    %endfor
                %endif
            </table>
        </div>

        <h1 style="clear:both;">${_(u'Delivery Order') } ${picking.name}</h1>

        <table class="basic_table" width="100%">
            <tr>
                <th>${_("Customer Ref")}</th>
                <th>${_("Origin")}</th>
                <th>${_("Delivery Date")}</th>
                <th>${_('Total Weight')}</th>
            </tr>
            <tr>
                <td>${picking.sale_id.client_order_ref if picking.sale_id else ''}</td>
                <td>${picking.origin or ''}</td>
                <td>${formatLang(picking.min_date, date=True)}</td>
                <td>${sum([line.weight for line in objects])}</td>
            </tr>
            <tr>
                <th colspan="2">${_('Delivery Method')}</th>
                <th>${_('Pickup Date')}</td>
                <th>${_('Number of spots')}</th>
            </tr>
            <tr>
                <td colspan="2">${picking.carrier_id and picking.carrier_id.name or ''}</td>
                <td>${formatLang(picking.pickup_date, date_time=True) or ''}</td>
                <td>${picking.number_of_packages}</td>
            </tr>
        </table>

        <table class="list_sale_table" width="100%" style="margin-top: 20px;">
            <thead>
                <tr>
                    <th class="left">${_("Item")}</th>
                    <th class="left">${_("Description")}</th>
                    <th class="left">${_("Serial Number")}</th>
                    <th class="right">${_("Weight (kg)")}</th>
                    <th class="amount">${_("Quantity")}</th>
                </tr>
            </thead>
            <tbody>
            %for line in picking.move_lines:
                <%
                weight = line.product_id.weight * line.product_qty
                %>
                <tr class="line">
                    <td class="left" >${ line.product_id.name }</td>
                    <td class="left" >${ line.product_id.description or ''}</td>
                    <td class="left" >${ line.prodlot_id and line.prodlot_id.name or ''}</td>
                    <td class="right" >${ formatLang(weight) }</td>
                    <td class="amount" >${ formatLang(line.product_qty) } ${line.product_uom.name}</td>
                </tr>
            %endfor
        </table>
        
        <br/>
        %if picking.note :
            <p class="std_text">${picking.note | carriage_returns}</p>
        %endif

        <p style="page-break-after: always"/>
        <!-- account_commercial_invoice -->
        <div class="address" style="clear: both; padding-top: 20px;">
            <%
            setLang(picking.partner_id.lang)
            invoice_addr = invoice_address(picking)
            %>
            <table class="invoice">
                <tr><td class="address_title">${_("Customer name & address:")}</td></tr>
                <tr><td>${invoice_addr.title and invoice_addr.title.name or ''} ${invoice_addr.name }</td></tr>
                %if invoice_addr.contact_address:
                    <% address_lines = invoice_addr.contact_address.split("\n") %>
                    %for part in address_lines:
                        %if part:
                        <tr><td>${part}</td></tr>
                        %endif
                    %endfor
                %endif
            </table>
        </div>
    <h1 style="clear: both; padding-top: 20px;">
        ${_("Commercial Invoice")}
    </h1>

    <table class="basic_table" width="100%">
        <tr>
            <th class="date">${_("Invoice Date")}</th>
            <th class="date">${_("Due Date")}</th>
            <th class="center">${_("Payment Term")}</th>
            <th class="center">${_("Our reference")}</th>
            <th class="center">${_('Customer Ref')}</th>
        </tr>
        <tr>
            <td class="date">${formatLang(str(date.today()), date=True)}</td>
            <td class="date">${formatLang(str(date.today()), date=True)}</td>
            <td class="center">${inv.sale_id and inv.sale_id.payment_term and inv.sale_id.payment_term.note or ''}</td>
            <td class="center">${inv.name or ''}</td>
            <td class="center">${inv.sale_id and inv.sale_id.client_order_ref or ''}</td>
        </tr>
    </table>

    <div>
           <p class="std_text">Country of origin  ${inv.company_id.partner_id.country_id.name} </p>
    </div>


    <div class="nobreak">
        <table class="list_sale_table" width="100%" style="margin-top: 20px;">
            <thead>
                <tr>
                    <th class="left">${_("Item")}</th>
                    <th class="left">${_("Description")}</th>
                    <th class="left">${_("Qty")}</th>
                    <th class="right">${_("Unit Price")}</th>
                    <th class="right">${_("UoM")}</th>
                    <th class="amount">${_("Net Sub Total")}</th>
                </tr>
            </thead>
            <tbody>
            %for line in picking.move_lines:
                <%
                weight = line.product_id.weight * line.product_qty
                %>
                <tr class="line">
                    <td style="text-align:left; " >${ line.product_id.name }</td>
                    <td style="text-align:left; " >${ line.product_id.description or ''}</td>
                    <td style="text-align:left; " >${formatLang(line.product_qty or 0.0)} ${line.product_uom.name}</td>
                    <td style="text-align:right; " >${formatLang(get_price_unit(line))}</td>
                    <td style="text-align:right; " >${line.product_uos.name}</td>
                    <td class="amount" >${formatLang(get_price_total(line))}</td>
                </tr>
            %endfor
        </table>
    <div align="right">
      <table style="width:30%">
        <tr>
            <td/>
          <td class="total_empty_cell"/>
          <th>
            ${_("Net :")}
          </th>
          <td class="amount total_sum_cell">
            ${formatLang(sum([get_price_total(line) for line in picking.move_lines]))}
          </td>
        </tr>
        <tr>
        <td/>
          <td class="total_empty_cell"/>
          <th>
            ${_("Taxes:")}
          </th>
          <td class="amount total_sum_cell">
          ${formatLang(0.0)}
          </td>
        </tr>
        <tr>
        <td/>
          <td class="total_empty_cell"/>
          <th>
            ${_("Total:")}
          </th>
          <td class="amount total_sum_cell">
            <b>${formatLang(sum([get_price_total(line) for line in picking.move_lines]))}</b>
          </td>
        </tr>
        </table>
    </div>
        <br/>
        <h4>
                ${_("Thank you for your prompt payment")}
        </h4>
        <br/>
    <!-- end of account_commercial_invoice -->
    %endif
</body>
</html>
