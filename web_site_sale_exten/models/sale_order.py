# -*- coding: utf-8 -*-
import random

from odoo import SUPERUSER_ID
from openerp.http import request
from odoo import api, fields, models, tools, _


class sale_order(models.Model):
    _inherit = "sale.order"
    
    @api.multi
    def _cart_update(self, product_id=None, line_id=None, add_qty=0, set_qty=0, **kwargs):
        ret = super(sale_order,self)._cart_update(product_id=product_id, line_id=line_id, add_qty=add_qty, set_qty=set_qty, **kwargs)
        return ret
        
        
class website(models.Model):
    _inherit = 'website'

    @api.multi
    def added_to_cart_product_qty(self, product_id):
        ret = {}
        quantity = 0.00
        sale_order_obj = self.env['sale.order']
        sale_order_id = request.session.get('sale_order_id')
        if sale_order_id:
            for line in sale_order_obj.browse(sale_order_id).website_order_line:
                if product_id and product_id == line.product_id.product_tmpl_id.id:               
                    quantity+=line.product_uom_qty
                    ret[line.product_id.id] = line.product_uom_qty
        return ret
               

