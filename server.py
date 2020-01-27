import ast
import base64
import json
import logging
import os
import os.path
import random
import re
import string
import time
import urllib
from io import BytesIO

import requests
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
from PIL import Image
from bs4 import BeautifulSoup
from requests_futures.sessions import FuturesSession

from db_access import *

DEFAULT_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) " \
             "Chrome/58.0.3029.110 Safari/537.36"
DEFAULT_UID = ''.join(random.choices(string.ascii_lowercase + string.digits, k=32))
captcha_path = os.path.join(os.path.dirname(__file__), 'captcha_img')

print(DEFAULT_UID)


# TODO: status_code not 200, retry ?
class BaseCourtCrawler:
    '抓取基础类'

    def __init__(self, conn, uid=DEFAULT_UID):
        self.uid = uid
        self.conn = conn
        self.base_url = None
        self.main_url = None
        self.page = 1
        self.total_page = 0
        self.cap_code = None
        self.name = None
        self.cardNum = None
        self.session = FuturesSession()
        self.jar = requests.cookies.RequestsCookieJar()

    # 准备方法
    def prepare(self):
        headers = {'User-Agent': DEFAULT_UA, 'Referer': self.base_url}
        self.session.headers.update(headers)

    # 获取验证码url
    def get_captcha_url(self):
        return None

    # 获取主要列表
    def get_main_list(self, cap_code):
        return None

    # 获取详情url
    def get_detail_url(self, case_id, cap_code):
        return None

    # 通知页面输入验证码
    def on_captcha_img(self, resp):
        print("on img %s" % resp)
        self.conn.send_progress("请输入验证码")
        if isinstance(self, ShixinCourtCrawler):
            captcha_type = 'shixin'
            Image.open(BytesIO(resp.content)).save(os.path.join(captcha_path, 'sx.png'))
        else:
            captcha_type = 'zhixing'
            Image.open(BytesIO(resp.content)).save(os.path.join(captcha_path, 'zx.png'))
        self.conn.send_image(resp.content, captcha_type)

    # 通知页面显示主要列表
    def on_main_list(self, resp):
        print("进入on_main_list")
        captcha_ok = True
        detail_counter = 0
        result_xml = BeautifulSoup(resp.text, 'lxml')

        if result_xml.__str__().find('验证码出现错误') != -1 or result_xml.__str__().find('验证码错误') != -1:
            captcha_ok = False

        print("on mainlist %s %s" % (resp, captcha_ok))

        if isinstance(self, ShixinCourtCrawler):
            captcha_src = 'shixin'
            saved_img = 'sx.png'
        else:
            captcha_src = 'zhixing'
            saved_img = 'zx.png'
        self.conn.send_captcha_result(captcha_ok, captcha_src)

        if captcha_ok:
            name = self.cap_code + '.png'
            try:
                os.rename(os.path.join(captcha_path, saved_img), os.path.join(captcha_path, name))
            except FileNotFoundError:
                print('')

        if not captcha_ok:
            self.start_fetch()
            logging.error('验证码过期')
            return

        # import pdb; pdb.set_trace()
        data = {}

        if '失信' in result_xml.text:
            data['type'] = 'shixin'
        else:
            data['type'] = 'zhixing'

        page_num = result_xml.find('input', id='pagenum')

        try:
            page_info = next(page_num.next_siblings).strip().encode('utf8')
            page_pattern = re.compile(r'页 (\d+)/(\d+) 共(\d+)条')
            m = page_pattern.match(page_info.decode('utf8'))
            if m:
                data['current_page'] = int(m.group(1))
                self.total_page = data['total_page'] = int(m.group(2))
                data['total'] = int(m.group(3))
        except:
            page_info = ''

        data['cases'] = []

        for row in result_xml.find_all('tr'):
            rows = row.find_all('td')
            if len(rows) > 0:
                _, name, case_time, case_name, case_info = rows
                data['cases'].append({
                    'name': name.get_text(),
                    'case_time': datetime.datetime.strftime(
                        datetime.datetime.strptime(case_time.get_text(), '%Y年%m月%d日'), '%Y-%m-%d'),
                    'case_name': case_name.get_text(),
                    'case_id': case_info.a['id']
                })
                detail_counter += 1

        data['pMark'] = self.name + '_' + self.cardNum  # 返回列表标记

        if len(data['cases']) == 0:
            if isinstance(self, ShixinCourtCrawler):
                for item in check_record_sx(self.cardNum, self.name):
                    data['cases'].append({
                        'name': check_name(self.cardNum),
                        'case_time': datetime.datetime.strftime(
                            datetime.datetime.strptime(item['regDate'], '%Y年%m月%d日'), '%Y-%m-%d'),
                        'case_name': item['caseCode'],
                        'case_id': item['id']
                    })
            else:
                for item in check_record_zx(self.cardNum, self.name):
                    data['cases'].append({
                        'name': check_name(self.cardNum),
                        'case_time': datetime.datetime.strftime(
                            datetime.datetime.strptime(item['caseCreateTime'], '%Y年%m月%d日'), '%Y-%m-%d'),
                        'case_name': item['caseCode'],
                        'case_id': item['id']
                    })

            self.conn.send_list_result(data)

            if isinstance(self, ShixinCourtCrawler):
                for item in check_record_sx(self.cardNum, self.name):
                    print('sending details from db')
                    item['option'] = 'shixin'
                    self.conn.send_list_detail(item)
            else:
                for item in check_record_zx(self.cardNum, self.name):
                    print('sending details from db')
                    item['option'] = 'zhixing'
                    self.conn.send_list_detail(item)
        else:
            self.conn.send_list_result(data)
            for case in data['cases']:
                detail_url = self.get_detail_url(case['case_id'], self.cap_code)
                r = requests.post(detail_url, cookies=self.jar)
                detail_result = ast.literal_eval(r.text)
                detail_result['id_card'] = self.cardNum
                detail_result.pop('caseState', None)
                detail_result.pop('partyTypeName', None)
                detail_result.pop('pname', None)
                detail_result.pop('iname', None)
                detail_result.pop('cardNum', None)
                detail_result.pop('partyCardNum', None)
                detail_result['name'] = self.name
                # detail类型
                if isinstance(self, ShixinCourtCrawler):
                    add_sxrecord(detail_result)
                    detail_result['option'] = 'shixin'
                else:
                    add_zxrecord(detail_result)
                    detail_result['option'] = 'zhixing'
                detail_counter -= 1
                print('sending details')
                self.conn.send_list_detail(detail_result)
                time.sleep(1)

        if detail_counter == 0:
            if isinstance(self, ShixinCourtCrawler):
                option = 'shixin'
            else:
                option = 'zhixing'
            self.conn.send_load_progress(option)

        print('当前 %s 页' % self.page)
        print('共 %s 页' % self.total_page)

        # fetch next page
        if self.page + 1 < self.total_page:
            self.page += 1
            self.fetch(self.cap_code, self.name, self.cardNum)

    def start_fetch(self):
        url = self.get_captcha_url()
        print("fetching captcha %s" % url)
        # self.conn.send_progress("正在下载第" + str(self.page) + "页")
        self.conn.send_progress("加载验证码")
        # self.session.get(url, cookies=self.jar, background_callback=self.on_captcha_img)
        r = requests.get(url, cookies=self.jar)
        self.on_captcha_img(r)
        # on user input captcha, continue

    def fetch(self, captcha_code, name, cardNum):
        print('fetching url %s', self.main_url)
        print(captcha_code)
        self.get_main_list(captcha_code, name, cardNum)


class ShixinCourtCrawler(BaseCourtCrawler):
    """失信抓取类，失信抓取类集成至抓取基类"""

    def __init__(self, conn, uid=DEFAULT_UID):
        BaseCourtCrawler.__init__(self, conn, uid)
        self.base_url = 'http://shixin.court.gov.cn/'
        self.main_url = 'http://shixin.court.gov.cn/findDisNew'

    def get_detail_url(self, case_id, cap_code):
        return 'http://shixin.court.gov.cn/disDetailNew?id=%s&pCode=%s&captchaId=%s' % (case_id, cap_code, self.uid)

    def get_captcha_url(self):
        return 'http://shixin.court.gov.cn/captchaNew.do?captchaId=%s&random=%s' % (self.uid, random.random())

    def get_main_list(self, cap_code, name, cardNum):
        self.cap_code = cap_code
        self.name = name
        self.cardNum = cardNum
        adduser(name, cardNum)
        global_province = 0
        if self.page == 1:
            data = urllib.parse.urlencode({
                'pName': name,
                'pProvince': global_province,
                'pCode': cap_code,
                'captchaId': self.uid,
                'pCardNum': cardNum
            })
        else:
            data = urllib.parse.urlencode({
                'pName': name,
                'pProvince': global_province,
                'pCode': cap_code,
                'captchaId': self.uid,
                'pCardNum': cardNum,
                'currentPage': self.page
            })
        print("====================抓取参数=======================");
        print(data);
        headers = {'Content-Type': 'application/x-www-form-urlencoded',
                   'Referer': 'http://shixin.court.gov.cn/findDisNew'}

        # if platform == 'win32':
        r = requests.post('http://shixin.court.gov.cn/findDisNew', data=data, headers=headers, cookies=self.jar)
        self.on_main_list(r)
        # else:
        #     self.session.post('http://shixin.court.gov.cn/findDisNew', data=data, headers=headers, cookies=self.jar,
        #                       background_callback=self.on_main_list)


class ZhixingCourtCrawler(BaseCourtCrawler):
    '执行抓取类，执行抓取类集成至抓取基础类'

    def __init__(self, conn, uid=DEFAULT_UID):
        BaseCourtCrawler.__init__(self, conn, uid)
        self.base_url = 'http://zhixing.court.gov.cn/search/'
        self.main_url = 'http://zhixing.court.gov.cn/search/newsearch'

    def get_detail_url(self, case_id, cap_code):
        return 'http://zhixing.court.gov.cn/search/newdetail?id=%s&j_captcha=%s&captchaId=%s' % (
            case_id, cap_code, self.uid)

    def get_captcha_url(self):
        return 'http://zhixing.court.gov.cn/search/captcha.do?captchaId=%s&random=%s' % (self.uid, random.random())

    def get_main_list(self, cap_code, name, cardNum):
        self.cap_code = cap_code
        self.name = name
        self.cardNum = cardNum
        adduser(name, cardNum)
        global_court = '全国法院（包含地方各级法院）'
        if self.page == 1:
            data = urllib.parse.urlencode({'searchCourtName': global_court,
                                           'selectCourtArrange': 1,
                                           'selectCourtId': 1,
                                           'j_captcha': cap_code,
                                           'captchaId': self.uid,
                                           'cardNum': cardNum,
                                           'pname': self.name
                                           })
        else:
            data = urllib.parse.urlencode({'selectCourtArrange': 1,
                                           'selectCourtId': 1,
                                           'j_captcha': cap_code,
                                           'captchaId': self.uid,
                                           'currentPage': self.page + 1,
                                           'cardNum': cardNum,
                                           'pname': self.name
                                           })

        print("====================抓取参数=======================")
        print(data)
        headers = {'Content-Type': 'application/x-www-form-urlencoded',
                   'Referer': 'http://zhixing.court.gov.cn/search/index_form.do'}

        r = requests.post('http://zhixing.court.gov.cn/search/newsearch', data=data, headers=headers,
                          cookies=self.jar)
        if not r.status_code == 200:
            print('验证码过期')
            self.start_fetch()
        self.on_main_list(r)


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('index.html')


# socket 服务
class CourtSocketHandler(tornado.websocket.WebSocketHandler):
    'socket 服务类继承至WebSocketHandler'
    socket_handlers = set()
    crawler = None

    # 发送列表结果
    def send_list_result(self, data):
        tmsg = json.dumps({'type': 'result', 'data': data})
        self.write_message(tmsg)

    # 发送详情
    def send_list_detail(self, data):
        tmsg = json.dumps({'type': 'detail', 'data': data})
        self.write_message(tmsg)

    def send_progress(self, stage):
        tmsg = json.dumps({'type': 'progress', 'data': stage})
        self.write_message(tmsg)

    # 发送验证码结果
    def send_captcha_result(self, is_ok, captcha_src):
        tmsg = json.dumps({'type': 'captcha_result', 'data': is_ok, 'option': captcha_src})
        self.write_message(tmsg)

    def send_load_progress(self, option):
        tmsg = json.dumps({'type': 'load_progress', 'option': option})
        self.write_message(tmsg)

    def send_finish(self, option):
        tmsg = json.dumps({'type': 'finish', 'option': option})
        self.write_message(tmsg)

    def send_image(self, data, captcha_type):
        message = base64.b64encode(data).decode('ascii')
        # with open('captcha.png', 'w') as f:
        #     print(base64.b64decode(message), file=f)
        #     f.close()
        tmsg = json.dumps({'type': 'image', 'data': message, 'option': captcha_type})
        self.write_message(tmsg)

    def check_origin(self, origin):
        return True

    def open(self):
        print('conn open')

    def on_close(self):
        logging.error('conn close')

    def on_message(self, message):
        global crawler
        print(message)
        jmsg = json.loads(message)
        # print(jmsg);
        # 查询
        # if jmsg['type'] == 'query':
        #     if jmsg['option'] == 'shixin':  # 失信
        #         crawler = ShixinCourtCrawler(conn=self)
        #     if jmsg['option'] == 'zhixing':  # 执行
        #         crawler = ZhixingCourtCrawler(conn=self)
        #     crawler.prepare()
        #     crawler.start_fetch()
        # 提交验证码
        if jmsg['type'] == 'captcha':
            if jmsg['option'] == 'shixin':
                crawler = ShixinCourtCrawler(conn=self)
            if jmsg['option'] == 'zhixing':  # 执行
                crawler = ZhixingCourtCrawler(conn=self)

            if jmsg['name'].isdigit() or jmsg['name'].endswith('X') or jmsg['name'].endswith('x'):
                jmsg['cardNum'] = jmsg['name']
                jmsg['name'] = ''

            crawler.fetch(
                jmsg['data'].strip(),
                jmsg['name'].strip(),
                jmsg['cardNum'].strip(),
            )

        if jmsg['type'] == 'refreshcaptcha':
            if jmsg['option'] == 'shixin':
                crawler = ShixinCourtCrawler(conn=self)
            if jmsg['option'] == 'zhixing':  # 执行
                crawler = ZhixingCourtCrawler(conn=self)
            crawler.start_fetch()

        if jmsg['type'] == 'createUA':
            if jmsg['option'] == 'shixin':
                crawler = ShixinCourtCrawler(conn=self)
            if jmsg['option'] == 'zhixing':  # 执行
                crawler = ZhixingCourtCrawler(conn=self)
            crawler.prepare()


def main():
    settings = {
        'template_path': os.path.join(os.path.dirname(__file__), 'templates'),
        'static_path': os.path.join(os.path.dirname(__file__), 'static')
    }
    application = tornado.web.Application([
        ('/', MainHandler),
        ('/court/socket', CourtSocketHandler)
    ], **settings)
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(8000)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    logging.basicConfig()
    main()
