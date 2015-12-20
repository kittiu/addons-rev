##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 
#    2004-2010 Tiny SPRL (<http://tiny.be>). 
#    2009-2010 Veritos (http://veritos.nl).
#    All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.     
#
##############################################################################

from openerp.osv import osv

class account_invoice_line(osv.osv):
    _inherit = "account.invoice.line"

    def move_line_get(self, cr, uid, invoice_id, context=None):
        res = super(account_invoice_line,self).move_line_get(cr, uid, invoice_id, context=context)
        inv = self.pool.get('account.invoice').browse(cr, uid, invoice_id, context=context)
        company_currency = inv.company_id.currency_id.id        
        if inv.type in ('in_invoice','in_refund'):
            for i_line in inv.invoice_line:
                if i_line.product_id and i_line.product_id.valuation == 'real_time':
                    if i_line.product_id.type != 'service':
                        # get the price difference account at the product
                        acc = i_line.product_id.property_account_creditor_price_difference and i_line.product_id.property_account_creditor_price_difference.id
                        if not acc:
                            # if not found on the product get the price difference account at the category
                            acc = i_line.product_id.categ_id.property_account_creditor_price_difference_categ and i_line.product_id.categ_id.property_account_creditor_price_difference_categ.id
                        # calculate and write down the possible price difference between invoice price and product price
                        for line in res:
                            if acc == line['account_id'] and i_line.product_id.id == line['product_id']:
                                uom = i_line.product_id.uos_id or i_line.product_id.uom_id
                                standard_price = self.pool.get('product.uom')._compute_price(cr, uid, uom.id, i_line.product_id.standard_price, i_line.uos_id.id)
                                if inv.currency_id.id != company_currency:
                                    standard_price = self.pool.get('res.currency').compute(cr, uid, company_currency, inv.currency_id.id, standard_price, context={'date': inv.date_invoice})
                                if standard_price != i_line.price_unit and acc:
                                    #price_diff = i_line.price_unit - standard_price
                                    price_diff = i_line.price_subtotal - (line['quantity'] * standard_price)
                                    line.update({
                                        'price_unit': price_diff / line['quantity'],
                                        'price': price_diff
                                    })
        return res