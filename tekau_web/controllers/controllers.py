# -*- coding: utf-8 -*-
from odoo import http

class TekauWeb(http.Controller):
    def Paging(self,page,limit):
        return 0 if page==1 else (page-1)*6-1

    @http.route('/tekau_web/factory/', auth='public',method=['POST'],type='json')
    def factory(self, **kw):
        page = http.request.params.get('page')
        offset=self.Paging(page,6)
        factory = http.request.env['tekau_factory'].sudo()
        factorys=factory.search([],limit=6,offset=offset)
        result=[]
        for record in factorys:
            result.append(
                {
                    'name': record['name'],
                    'description': record['description'],
                    'image': record['image'],
                }
            )
        return {"factory":result}

    @http.route('/tekau_web/products/', auth='public',method=['POST'],type='json')
    def products(self, **kw):

        page = http.request.params.get('page')
        type = http.request.params.get('type')
        offset=self.Paging(page,9)
        product = http.request.env['tekau_products'].sudo()
        products=product.search([('type','=',type)],limit=9,offset=offset)
        result=[]
        for record in products:
            result.append(
                {
                    'name': record['name'],
                    'type': record['type'],
                    'description': record['description'],
                    'image': record['image'],
                    'dimensions': record['dimensions'],
                    'value': record['value']
                }
            )
        return {"products":result}

    @http.route('/tekau_web/contact/', auth='public',method=['POST'],type='json')
    def contact(self, **kw):
        name = http.request.params.get('name')
        email = http.request.params.get('email')
        phone = http.request.params.get('phone')
        content = http.request.params.get('content')

        contact = http.request.env['tekau_contacts'].sudo()
        contact.create({"name":name,"email":email,"phone":phone,"content":content})

        return {"contact":"data has saved in the database !!"}
