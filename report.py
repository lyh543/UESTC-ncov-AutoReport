# encoding=utf8
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
        with open('config.json', 'r') as config_file:
            self.data = json.load(config_file)
        # 确认坐标
        self.location = self.data.pop('location', 'qingshuihe')
        if self.location == 'qingshuihe':
            pass
        elif self.location == 'shahe':
            raise NotImplementedError
        else:
            raise ValueError(f'location 参数错误: {self.location}')

    # 登陆/绑定
    def login(self) -> bool:
        response_checkbind = self.session.post(self.baseUrl + "/wxvacation/api/epidemic/login/checkBind", json={},
                                               headers=self.headers)  # 获取 SESSION，否则登录不上
        response_login = self.session.post(self.baseUrl + "/wxvacation/api/epidemic/login/bindUserInfo", json=self.data,
                                           headers=self.headers)  # 登录，并将 SESSION ID 和用户绑定
        # 输出 SESSION ID。要是忘记解绑，小程序无法登陆，就得拿 SESSION ID 解绑
        if response_login.json()['code'] == 0:
            session_id = self.session.cookies["SESSION"]
            print(f'登录成功，session 为 {session_id}，请妥善保管！')
            return True
        else:
            print(f'登录失败，response 为 {response_login.json()}')
            return False

    # 打卡
    def report(self) -> bool:
        return True

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
        except:
            ret = False
        return ret


if __name__ == "__main__":
    auto_reporter = Report()
    count = 5
    while count != 0:
        ret = auto_reporter.run()
        if ret:
            break
        print("打卡失败，重试中...\n")
        count = count - 1

    if count != 0:
        print('打卡成功')
        exit(0)
    else:
        print('打卡失败，退出程序')
        exit(-1)
