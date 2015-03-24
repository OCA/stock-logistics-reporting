## -*- coding: utf-8 -*-
<html>
<head>
    <style type="text/css">
        ${css}
    </style>
</head>

<body>
    <%page expression_filter="entity"/>
    <%
    def carriage_returns(text):
        return text.replace('\n', '<br />')
    %>
    %for picking in objects:
        <% setLang(picking.partner_id.lang) %>
        <%
        shipping_addr = shipping_address(picking)
        %>
        <div class="address">
            <table class="recipient">
                <tr><td class="address_title">${_("Contact info for shipping:")}</td></tr>
                %if picking.partner_id.phone:
                    <tr><td><b>${_("Phone:")}</b> ${picking.partner_id.phone }</td></tr>
                %endif
                %if picking.partner_id.mobile:
                    <tr><td><b>${_("Cell:")}</b> ${picking.partner_id.mobile }</td></tr>
                %endif
                %if picking.partner_id.email:
                    <tr><td><b>${_("Email:")}</b> ${picking.partner_id.email }</td></tr>
                %endif
                %if picking.partner_id.shipping_notes:
                    <tr><td><b>${_("Shipping Notes:")}</b> ${picking.partner_id.shipping_notes }</td></tr>
                %endif
            </table>
            <br />
            <%
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
        <div class="address">
            <table class="recipient">
                <tr><td class="address_title">${_("Ship to:")}</td></tr>
                <tr><td>${shipping_addr.title and shipping_addr.title.name or ''} ${shipping_addr.name }</td></tr>
                %if shipping_addr.contact_address:
                    <% address_lines = shipping_addr.contact_address.split("\n") %>
                    %for part in address_lines:
                        %if part:
                        <tr><td>${part}</td></tr>
                        %endif
                    %endfor
                %endif
            </table>
            <%
            picking_addr = picking_address(picking)
            %>
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
                <td>${picking.weight}</td>
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
        
        <br/>
        %if picking.note :
            <p class="std_text">${picking.note | carriage_returns}</p>
        %endif

        <p style="page-break-after: always"/>
        <br/>
    %endfor
</body>
</html>
