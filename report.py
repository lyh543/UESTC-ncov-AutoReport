# encoding=utf8
from time import sleep

import requests
import os
import json

os.environ['NO_PROXY'] = 'jzsz.uestc.edu.cn'


class Report(object):
    def __init__(self):
        self.session = requests.Session()
        self.baseUrl = "https://jzsz.uestc.edu.cn"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/53.0.2785.143 Safari/537.36 MicroMessenger/7.0.9.501 NetType/WIFI "
                          "MiniProgramEnv/Windows WindowsWechat",
            "X-Tag": "flyio",
            "content-type": "application/json",
            "encode": "false",
            "Referer": "https://servicewechat.com/wx521c0c16b77041a0/28/page-frame.html"  # 小程序的 id
        }
        # 读取配置文件
        with open('config.json', 'r', encoding='utf-8') as config_file:
            self.data = json.load(config_file)
        # 确认坐标
        self.location = self.data.pop('location', '')

    # 登陆/绑定
    def login(self) -> bool:
        self.session.post(self.baseUrl + "/wxvacation/api/epidemic/login/checkBind", json={}, 
                          headers=self.headers)  # 获取 SESSION，否则登录不上
        response = self.session.post(self.baseUrl + "/wxvacation/api/epidemic/login/bindUserInfo", json=self.data,
                                           headers=self.headers)  # 登录，并将 SESSION ID 和用户绑定
        # 输出 SESSION ID。要是忘记解绑，小程序无法登陆，就得拿 SESSION ID 解绑
        if response.json()['code'] == 0:
            session_id = self.session.cookies["SESSION"]
            print(f'登录成功，session 为 {session_id}，请妥善保管！')
            return True
        else:
            print(f'登录失败，response 为 {response.json()}')
            return False

    # 打卡
    def report(self) -> bool:
        # 检查是否已经打卡
        # 重复打卡会报数据库错，外包的代码 异常处理还是 8 行
        response = self.session.get(self.baseUrl + "/wxvacation/checkRegisterNew", headers=self.headers)
        if not response.ok:
            print(f'获取打卡状态失败：{response.status_code}, text 为：{response.text}')
            return False
        if response.json()['data']['appliedTimes'] == 1:
            print('今日已打卡，跳过打卡')
            return True
        print('今日未打卡，开始打卡...')
        if response.json()['data']['schoolStatus'] == 1:    # 在校
            return self.report_in_school()
        else:
            raise NotImplementedError('暂未实现校外打卡')

    # 校内打卡
    def report_in_school(self) -> bool:
        data = {
            "healthCondition":"正常",
            "todayMorningTemperature":"36°C~36.5°C",
            "yesterdayEveningTemperature":"36°C~36.5°C",
            "yesterdayMiddayTemperature":"36°C~36.5°C",
            "location":self.location
        }
        response = self.session.post(self.baseUrl + "/wxvacation/monitorRegisterForReturned", json=data, headers=self.headers)
        if response.json()['code'] == 0:
            print(f'校内打卡成功，“请明日 10:00 之前继续填写~”')
            return True
        else:
            print(f'校外打卡失败，response 为 {response.json()}')
            return False

    # 注销/解绑
    # 每次打完卡都必须解绑 session_id 和账户，否则下次登录不上
    def logout(self) -> bool:
        response_logout = self.session.post(self.baseUrl + "/wxvacation/api/epidemic/login/cancelBind")
        response_logout.json()
        if response_logout.json()['code'] == 0:
            print(f'注销成功，session 已失效')
            return True
        else:
            print(f'注销失败，response 为 {response_logout.json()}')
            return False

    def run(self) -> bool:
        ret = True
        try:
            if not self.login() or not self.report():
                ret = False
            if not self.logout():
                ret = False
        except Exception as e:
            self.logout()
            raise e
        return ret


if __name__ == "__main__":
    auto_reporter = Report()
    for i in range(1, 6):
        ret = auto_reporter.run()
        if ret:
            print('程序执行成功，退出')
            exit(0)
        if i == 5:
            print('程序连续 5 次执行失败，退出')
            exit(-1)
        sleep(1)
        print(f"程序第 {i} 次执行失败，重试中...\n")
