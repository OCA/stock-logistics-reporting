## -*- coding: utf-8 -*-
<html>
<head>
<style type="text/css">
${css}
</style>
</head>
<body>
<%from datetime import date %>
${_('Date')}: ${formatLang(str(date.today()), date=True)}  &nbsp;
&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; ${_('Done by')}: ${user.name}  &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;${_('Visa')}:_________________
<br/>
<br/>
<b>${_('Company')}: ${user.company_id.name}<b>
<br/>
<br/>
%for aggr in objects:
<table style="border:solid 1px" width="100%">
  <caption><b><u>${aggr.src_stock.name} => ${aggr.dest_stock.name}</u></b></caption>
  <tr align="left">
    <th>${_('Product Code')}</th>
    <th>${_('Delivery Order')}</th>
    <th>${_('Product')}</th>
    <th>${_('Qty')}</th>
    <th>${_('Origin')}</th>
    <th>${_('Carrier')}</th>
  </tr>
  %for move in aggr.moves_by_product():
  <tr align="left">
    <td>${move.product_id.default_code}</td>
    <td>${move.picking_id.name}</td>
    <td>${move.product_id.name}</td>
    <td>${formatLang(move.product_qty)}</td>
    <td>${move.picking_id.origin}</td>
    <td>${move.picking_id.carrier_id and move.picking_id.carrier_id.partner_id.name or ''}</td>
  </tr>
  %endfor
</table>
<br/>
%endfor
</body>
</html>
