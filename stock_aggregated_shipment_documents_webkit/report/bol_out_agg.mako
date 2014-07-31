## -*- coding: utf-8 -*-
<html>
<head>
    <style type="text/css">
        ${css}

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
                <tr><td>${picking.partner_id.title and picking.partner_id.title.name or ''} ${picking.partner_id.name }</td></tr>
                <% address_lines = picking.partner_id.contact_address.split("\n")[1:] %>
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
                <td style="font-weight:bold;">${_("Customer Ref")}</td>
                <td style="font-weight:bold;">${_("Origin")}</td>
                <td style="font-weight:bold;">${_("Scheduled Date")}</td>
                <td style="font-weight:bold;">${_('Total Weight')}</td>
                <td style="font-weight:bold;">${_('Delivery Method')}</td>
            </tr>
            <tr>
                <td>${picking.sale_id.client_order_ref if picking.sale_id else ''}</td>
                <td>${picking.origin or ''}</td>
                <td>${formatLang(picking.min_date, date=True)}</td>
                <td>${sum([line.weight for line in objects])}</td>
                <td>${picking.carrier_id and picking.carrier_id.name or ''}</td>
            </tr>
        </table>

        <table class="list_sale_table" width="100%" style="margin-top: 20px;">
            <thead>
                <tr>
                    <th style="text-align:left; ">${_("Item")}</th>
                    <th style="text-align:left; ">${_("Description")}</th>
                    <th style="text-align:left; ">${_("Serial Number")}</th>
                    <th style="text-align:right; ">${_("Weight (kg)")}</th>
                    <th class="amount">${_("Quantity")}</th>
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
                    <td style="text-align:left; " >${ line.prodlot_id and line.prodlot_id.name or ''}</td>
                    <td style="text-align:right; " >${ formatLang(weight) }</td>
                    <td class="amount" >${ formatLang(line.product_qty) } ${line.product_uom.name}</td>
                </tr>
            %endfor
        </table>

        <p style="page-break-after: always"/>
        <!-- account_commercial_invoice -->
    <div class="address">
      <table class="recipient">
        <% address_lines = inv.partner_id.contact_address.split("\n") %>
        %for part in address_lines:
            %if part:
            <tr><td>${part}</td></tr>
            %endif
        %endfor
      </table>
    </div>
    <h1 style="clear: both; padding-top: 20px;">
        ${_("Commercial Invoice")}
    </h1>

    <table class="basic_table" width="100%">
        <tr>
            <th class="date">${_("Invoice Date")}</td>
            <th class="date">${_("Due Date")}</td>
            <th style="text-align:center;width:120px;">${_("Responsible")}</td>
            <th style="text-align:center">${_("Payment Term")}</td>
            <th style="text-align:center">${_("Your reference")}</td>
        </tr>
        <tr>
            <td class="date">${formatLang(str(date.today()), date=True)}</td>
            <td class="date">${formatLang(str(date.today()), date=True)}</td>
            <td style="text-align:center;width:120px;">${current_user().name}</td>
            <td style="text-align:center">${inv.sale_id.payment_term and inv.sale_id.payment_term.note or ''}</td>
            <td style="text-align:center">${inv.name or ''}</td>
        </tr>
    </table>

    <div>
           <p class="std_text">Country of origin  ${inv.company_id.partner_id.country_id.name} </p>
    </div>


    <div class="nobreak">
        <table class="list_sale_table" width="100%" style="margin-top: 20px;">
            <thead>
                <tr>
                    <th style="text-align:left; ">${_("Item")}</th>
                    <th style="text-align:left; ">${_("Description")}</th>
                    <th style="text-align:left; ">${_("Qty")}</th>
                    <th style="text-align:right; ">${_("Unit Price")}</th>
                    <th style="text-align:right; ">${_("UoM")}</th>
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
                    <td style="text-align:right; " >${formatLang(line.product_id.list_price)}</td>
                    <td style="text-align:right; " >${line.product_uos.name}</td>
                    <td class="amount" >${formatLang(line.product_qty * line.product_id.list_price)}</td>
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
            ${formatLang(sum([line.product_qty * line.product_id.list_price for line in picking.move_lines]))}
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
            <b>${formatLang(sum([line.product_qty * line.product_id.list_price for line in picking.move_lines]))}</b>
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
