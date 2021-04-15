# -*- coding: utf-8 -*-
import logging
import requests
from bs4 import BeautifulSoup

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class VacationDaysComparison(models.Model):
    _name = 'vacation.days.comparison'
    _description = 'vacation days comparison table'

    seniority = fields.Char()
    value = fields.Integer()


class Base(models.AbstractModel):
    _inherit = 'base'

    @api.model
    def get_comparison_table(self, domain):
        records = self.search(domain)
        record_dict = []
        for record in records:
            record_dict.append({
                "seniority": record['seniority'],
                "value": record['value'],
                "write_date": record['write_date']
            })
        return record_dict

    def crawler_seniority(self):
        res = requests.get('https://calc.mol.gov.tw/Trail_New/html/RestDays.html')
        if res.status_code == 200:
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, "html.parser")
            table = soup.find_all('table', {'class': 'MsoNormalTable'})
            rows = list()
            result = []
            for tr in table:
                rows.append([td.text.replace('\n', '').replace('\xa0', '') for td in tr.find_all('td')])
            for tr in rows:
                result.append([tr[i:i + 3] for i in range(0, len(tr), 3)])
            return result
        else:
            _logger.error("Error: crawler_seniority Http_code:%s", res.status_code)

    @api.model
    def update_comparison_table(self, domain):
        for record in self.crawler_seniority():
            for r in record:
                records = self.search([('seniority', '=', r[0])])
                records.write({'value': r[1]})

        return self.get_comparison_table(domain)
