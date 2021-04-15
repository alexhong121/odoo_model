# -*- coding: utf-8 -*-
import logging
import json
# import pyodbc
import requests
import random

from datetime import timedelta

from tornado import websocket
import tornado.ioloop

from odoo import models, fields, api, _, SUPERUSER_ID, exceptions

_logger = logging.getLogger(__name__)


# class DataEncoder(json.JSONEncoder):
#     def default(self, obj):
#         if isinstance(obj,datetime.datetime):
#             return obj.strftime('%Y-%m-%d %H:%M:%S')
#         elif isinstance(obj,date):
#             return obj.strftime("%Y-%m-%d")
#         else:
#             return json.JSONEncoder.default(self,obj)


class OdbcConnect():
    def __init__(self):
        self.headers = {"Content-Type": "application/json"}
        self.sql_config = {}

    def connect(self):
        load = json.dumps({
            "jsonrpc": "2.0",
            "method": 'call',
            "params": {
                'data':{'syncing':'t'}
            },
            "id": random.randint(0, 1000000000),
        })
        # 取得sql config 資料
        res = requests.post('http://localhost:8069/hr_attendace_extend/config', data=load, headers=self.headers).json()

        self.sql_config = {
            'driver': res['result'][0]['odbc'],
            'server': res['result'][0]['server'],
            'port': res['result'][0]['port'],
            'database': res['result'][0]['database'],
            'username': res['result'][0]['username'],
            'password': res['result'][0]['password'],
            'script':res['result'][0]['script'],
        }

        return pyodbc.connect(
            'DRIVER=%s;SERVER=%s,%s;DATABASE=%s;UID=%s;PWD=%s' %
            (self.sql_config['driver'], self.sql_config['server'], self.sql_config['port'],
             self.sql_config['database'], self.sql_config['username'], self.sql_config['password']))
    def sql_script(self):
        self.connect()
        return self.sql_config['script']

class EchoWebSocket(websocket.WebSocketHandler):
    temp = []

    def check_origin(self, origin):
        # 允许所有跨域通信
        return True

    def open(self):
        # 連上websocket
        _logger.info("wesocket opened")
        self.odbc = OdbcConnect().connect()
        self.write_message("You are connected")
        self.loop = tornado.ioloop.PeriodicCallback(self.run, 500)
        self.loop.start()

    def on_message(self, message):
        # 接收client
        pass

    def on_close(self):
        # 關閉連線
        self.loop.stop()
        self.odbc.close()
        _logger.info("wesocket closed")
        # self.write_message("You are closed")

    def run(self):
        # 每隔時間區間 log table 是否有資料
        cursor = self.odbc.cursor()
        cursor.execute("UPDATE CHECKINOUT_LOG SET reading='t'")
        cursor.commit()
        cursor.execute(self.tekau_punch_time_script())
        rows = cursor.fetchall()

        if self.temp != rows:
            res_dict = []
            for row in rows:
                self.write_message(u"you said:%s action is %s " % (row.CHECKTIME, row.action))

                res_dict.append({
                    'CHECKTIME': (row.CHECKTIME - timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S"),
                    'NAME': row.NAME,
                    'BADGENUMBER': row.BADGENUMBER,
                    'CHECKTYPE': row.CHECKTYPE,
                    'action': row.action,
                })
                # cursor.execute("delete CHECKINOUT_LOG where USERID='%s'" % row.USERID)
                # cursor.commit()

            headers = {'Content-Type': 'application/json'}
            data = {
                "jsonrpc": "2.0",
                "method": 'call',
                "params": {'data': res_dict},
                "id": random.randint(0, 1000000000),
            }
            res = requests.post('http://localhost:8069/hr_attendace_extend',
                                data=json.dumps(data), headers=headers)
            if res.status_code == 200:
                cursor.execute("DELETE CHECKINOUT_LOG WHERE reading='t'")
                cursor.commit()
                cursor.close()

            print(res.status_code, res.reason, res.status_code == 200)
        self.temp = rows

    def tekau_punch_time_script(self):
        # 德高打卡機資料庫腳本
        script="""
              SELECT
                  info.USERID,
                  info.BADGENUMBER,
                  info.NAME,
                  chk_log.CHECKTIME,
                  chk_log.CHECKTYPE,
                  chk_log.action
              FROM CHECKINOUT_LOG chk_log
              LEFT JOIN USERINFO info ON chk_log.USERID=info.USERID
              WHERE chk_log.reading='t'
        """
        # script.replace('/\\n|\\t|\"/','')
        # print(script)
        return script



