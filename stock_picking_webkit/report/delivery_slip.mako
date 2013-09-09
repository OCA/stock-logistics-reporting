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
        <div class="address">
            <table class="recipient">
                %if picking.partner_id.parent_id:
                <tr><td class="name">${picking.partner_id.parent_id.name or ''}</td></tr>
                <tr><td>${picking.partner_id.title and picking.partner_id.title.name or ''} ${picking.partner_id.name }</td></tr>
                <% address_lines = picking.partner_id.contact_address.split("\n")[1:] %>
                %else:
                <tr><td class="name">${picking.partner_id.title and picking.partner_id.title.name or ''} ${picking.partner_id.name }</td></tr>
                <% address_lines = picking.partner_id.contact_address.split("\n") %>
                %endif
                %for part in address_lines:
                    %if part:
                    <tr><td>${part}</td></tr>
                    %endif
                %endfor
            </table>
        </div>
        
        <h1 style="clear:both;">${_(u'Delivery Order') } ${picking.name}</h1>
        
        <table class="basic_table" width="100%">
            <tr>
                <td style="font-weight:bold;">${_("Contact")}</td>
                <td style="font-weight:bold;">${_("Origin")}</td>
                <td style="font-weight:bold;">${_("Scheduled Date")}</td>
                <td style="font-weight:bold;">${_('Weight')}</td>
            </tr>
            <tr>
                <td>${user.name}</td>
                <td>${picking.origin or ''}</td>
                <td>${formatLang(picking.min_date, date=True)}</td>
                <td>${picking.weight}</td>
            </tr>
        </table>
    
        <table class="list_sale_table" width="100%" style="margin-top: 20px;">
            <thead>
                <tr>
                    <th style="text-align:left; ">${_("Description")}</th>
                    <th style="text-align:left; ">${_("Serial Number")}</th>
                    <th class="amount">${_("Quantity")}</th>
                </tr>
            </thead>
            <tbody>
            %for line in picking.move_lines:
                <tr class="line">
                    <td style="text-align:left; " >${ line.name }</td>
                    <td style="text-align:left; " >${ line.prodlot_id and line.prodlot_id.name or ''}</td>
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
