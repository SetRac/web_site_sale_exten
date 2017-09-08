# -*- coding: utf-8 -*-
import werkzeug

from odoo import SUPERUSER_ID
from odoo import http
from odoo.http import request
from odoo import api, fields, models, tools, _
from odoo.addons.website.models.website import slug

PPG = 20 # Products Per Page
PPR = 4  # Products Per Row

class web_site_sale_exten(http.Controller):

    def get_pricelist(self):
        return get_pricelist()
        
    def get_attribute_value_ids_ext(self, product):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        currency_obj = pool['res.currency']
        attribute_value_ids = []
        visible_attrs = set(l.attribute_id.id
                                for l in product.attribute_line_ids
                                    if len(l.value_ids) > 1)
        if request.website.currency_id != product.currency_id:
            for p in product.product_variant_ids:
                price = currency_obj.compute(cr, uid, product.currency_id.id, request.website.currency_id.id, p.lst_price, p.qty_available)
                attribute_value_ids.append([p.id, [v.id for v in p.attribute_value_ids if v.attribute_id.id in visible_attrs], p.price, price])
        else:
            attribute_value_ids = [[p.id, [v.id for v in p.attribute_value_ids if v.attribute_id.id in visible_attrs], p.price, p.lst_price, p.qty_available]
                for p in product.product_variant_ids]
        return attribute_value_ids
        
        
    @http.route(['/shop/product/<model("product.template"):product>'], type='http', auth="public", website=True)
    def product(self, product, category='', search='', **kwargs):
        cr, uid, stdcontext, pool = request.cr, request.uid, request.context, request.registry
        category_obj = request.env['product.public.category']
        template_obj = request.env['product.template']
        pool = request.env
        print '$$$$$$$$$$$$', stdcontext
        context = stdcontext.copy()
        context.update(active_id=product.id)

        if category:
            category = category_obj.with_context(context or {}).browse(cr, uid, int(category))
            category = category if category.exists() else False

        attrib_list = request.httprequest.args.getlist('attrib')
        attrib_values = [map(int,v.split("-")) for v in attrib_list if v]
        attrib_set = set([v[1] for v in attrib_values])

        keep = QueryURL('/shop', category=category and category.id, search=search, attrib=attrib_list)

        categs = category_obj.with_context(context or {}).search([('parent_id', '=', False)])
        #categs = category_obj.browse(cr, uid, category_ids, context=context)

        pricelist = self.get_pricelist()

        from_currency = pool['res.users'].with_context(context or {}).browse(uid).company_id.currency_id
        to_currency = pricelist.currency_id
        compute_currency = lambda price: pool['res.currency'].with_context(context or {})._compute(from_currency, to_currency, price)

        # get the rating attached to a mail.message, and the rating stats of the product
        Rating = pool['rating.rating']
        ratings = Rating.with_context(context or {}).search([('message_id', 'in', product.website_message_ids.ids)])
        #ratings = Rating.browse(cr, uid, rating_ids, context=context)
        rating_message_values = dict([(record.message_id.id, record.rating) for record in ratings])
        rating_product = product.rating_get_stats([('website_published', '=', True)])

        if not context.get('pricelist'):
            context['pricelist'] = int(self.get_pricelist())
            product = template_obj.with_context(context or {}).browse(int(product))

        values = {
            'search': search,
            'category': category,
            'pricelist': pricelist,
            'attrib_values': attrib_values,
            'compute_currency': compute_currency,
            'attrib_set': attrib_set,
            'keep': keep,
            'categories': categs,
            'main_object': product,
            'product': product,
            'get_attribute_value_ids': self.get_attribute_value_ids_ext,
            'rating_message_values' : rating_message_values,
            'rating_product' : rating_product
        }
        return request.render("website_sale.product", values)

        
    @http.route(['/shop/cart/get_added_qty_product_json'], type='json', auth="public", methods=['POST'], website=True)
    def cart_stock_for_product_json(self, product_id):
        cr, uid, context = request.cr, request.uid, request.context
        qty = request.website.added_to_cart_product_qty_variant(product_id)
        return qty;
        
class QueryURL(object):
    def __init__(self, path='', **args):
        self.path = path
        self.args = args

    def __call__(self, path=None, **kw):
        if not path:
            path = self.path
        for k,v in self.args.items():
            kw.setdefault(k,v)
        l = []
        for k,v in kw.items():
            if v:
                if isinstance(v, list) or isinstance(v, set):
                    l.append(werkzeug.url_encode([(k,i) for i in v]))
                else:
                    l.append(werkzeug.url_encode([(k,v)]))
        if l:
            path += '?' + '&'.join(l)
        return path
        
def get_pricelist():
    return request.website.get_current_pricelist()
    if not pricelist:
        _logger.error('Fail to find pricelist for partner "%s" (id %s)', partner.name, partner.id)



# vim:expandtab:tabstop=4:softtabstop=4:shiftwidth=4:
