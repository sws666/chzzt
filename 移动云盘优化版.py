# 软件：中国移动云盘
# 功能：签到 每日任务
# 抓包 Cookie：任意uthorization
# 变量格式：export ydypCk= authorization#手机号 多个账号用 @ 隔开
# Draw = 1 抽奖次数，每天首次免费， 每天可抽次数50，draw=1，只会抽奖一次
# num = 15 摇一摇，戳一戳次数
# 定时：一天两三次
import json
import os
import time
import random
import requests

cookies = os.getenv("ydypCk")
ua = ''


class YP:
    token = None
    jwtToken = None
    draw = 1
    num = 15
    timestamp = str(int(round(time.time() * 1000)))
    cookies = {'sensors_stay_time': timestamp}

    def __init__(self, cookie):
        self.Authorization = cookie.split("#")[0]
        self.account = cookie.split("#")[1]
        self.jwtHeaders = {
            'User-Agent': ua,
            'Accept': '*/*',
            'Host': 'caiyun.feixin.10086.cn:7071',
            'Connection': 'keep-alive',
        }

    def run(self):
        self.sso()
        self.jwt()
        self.signin_status()
        self.click()
        print(f"\n---公众号任务---")
        self.wxsign()
        self.shake()
        self.surplus_num()
        self.receive()

    def send_request(self, url, headers, data=None, method='GET', cookies=None):
        try:
            if method == 'GET':
                response = requests.get(url, headers = headers, cookies = cookies, timeout = 10)
            elif method == 'POST':
                response = requests.post(url, headers = headers, json = data, cookies = cookies, timeout = 10)
            else:
                raise ValueError('Invalid HTTP method.')
            response.raise_for_status()
            return response.json()
        except requests.Timeout as e:
            print("请求超时:", str(e))

        except requests.RequestException as e:
            print("请求错误:", str(e))

        except Exception as e:
            print("其他错误:", str(e))

    # 随机延迟默认0.5-1s
    def sleep(self, min_delay=0.5, max_delay=1):
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)

    # 刷新令牌
    def sso(self):
        url = 'https://orches.yun.139.com/orchestration/auth-rebuild/token/v1.0/querySpecToken'
        headers = {
            'Authorization': self.Authorization,
            'User-Agent': ua,
            'Content-Type': 'application/json',
            'Accept': '*/*',
            'Host': 'orches.yun.139.com',
            'Connection': 'keep-alive'
        }
        data = {"account": self.account, "toSourceId": "001005"}
        return_data = self.send_request(url, headers = headers, data = data, method = 'POST')
        self.sleep()
        if 'success' in return_data:
            if return_data['success']:
                self.token = return_data['data']['token']
            else:
                print(return_data['message'])
        else:
            print("出现未知错误")

    # 获取jwttoken
    def jwt(self):
        url = f"https://caiyun.feixin.10086.cn:7071/portal/auth/tyrzLogin.action?ssoToken={self.token}"
        return_data = self.send_request(url = url, headers = self.jwtHeaders, method = 'POST')
        self.sleep()
        if return_data['code'] != 0:
            return print(return_data['msg'])
        self.jwtToken = return_data['result']['token']
        self.jwtHeaders['jwtToken'] = self.jwtToken
        self.cookies['jwtToken'] = self.jwtToken

    # 公众号签到
    def wxsign(self):
        url = 'https://caiyun.feixin.10086.cn/market/playoffic/followSignInfo?isWx=true'
        return_data = self.send_request(url, headers = self.jwtHeaders, cookies = self.cookies)
        self.sleep()
        if return_data['msg'] != 'success':
            return print(return_data['msg'])
        if not return_data['result'].get('todaySignIn'):
            return print('签到失败')
        return print('签到成功')

    # 摇一摇
    def shake(self):
        url = "https://caiyun.feixin.10086.cn:7071/market/shake-server/shake/shakeIt?flag=1"
        for _ in range(self.num):
            return_data = self.send_request(url = url, cookies = self.cookies, headers = self.jwtHeaders,
                                            method = 'POST')
            self.sleep()
            shake_prize_config = return_data["result"].get("shakePrizeconfig")
            if shake_prize_config is not None:
                print("⭕摇一摇成功，获得：" + str(shake_prize_config["name"]))
            elif shake_prize_config is None:
                print("未摇中")
            else:
                print("出错了")

    # 查询剩余抽奖次数
    def surplus_num(self):
        draw_info_url = 'https://caiyun.feixin.10086.cn/market/playoffic/drawInfo'
        draw_url = "https://caiyun.feixin.10086.cn/market/playoffic/draw"

        draw_info_data = self.send_request(draw_info_url, headers = self.jwtHeaders)
        self.sleep()
        if draw_info_data.get('msg') == 'success':
            num1 = draw_info_data['result'].get('surplusNumber', 0)
            print(f'---剩余抽奖次数{num1}---')
            if num1 > 50 - self.draw:
                for _ in range(self.draw):
                    draw_data = self.send_request(url = draw_url, headers = self.jwtHeaders)
                    self.sleep()
                    if draw_data.get("code") == 0:
                        prize_name = draw_data["result"].get("prizeName", "")
                        print("⭕ 抽奖成功，获得：" + prize_name)
                    else:
                        print("❌ 抽奖失败")
            else:
                pass
        else:
            print(draw_info_data.get('msg'))

    # 签到查询
    def signin_status(self):
        url = 'https://caiyun.feixin.10086.cn/market/signin/page/info?client=app'
        return_data = self.send_request(url, headers = self.jwtHeaders, cookies = self.cookies)
        self.sleep()
        if return_data['msg'] == 'success':
            today_sign_in = return_data['result'].get('todaySignIn', False)

            if today_sign_in:
                return print('已经签到了')
            else:
                print('未签到，去签到')
                config_url = 'https://caiyun.feixin.10086.cn/market/manager/commonMarketconfig/getByMarketRuleName?marketName=sign_in_3'
                config_data = self.send_request(config_url, headers = self.jwtHeaders, cookies = self.cookies)

                if config_data['msg'] == 'success':
                    print('签到成功')
                else:
                    print(config_data['msg'])
        else:
            print(return_data['msg'])

    # 戳一下
    def click(self):
        url = "https://caiyun.feixin.10086.cn/market/signin/task/click?key=task&id=319"
        for _ in range(self.num):
            return_data = self.send_request(url, headers = self.jwtHeaders, cookies = self.cookies)
            self.sleep()
            if 'result' in return_data:
                print(f'{return_data["result"]}')
            elif return_data.get('msg') == 'success':
                print('未获得')

    # 领取云朵
    def receive(self):
        url = "https://caiyun.feixin.10086.cn/market/signin/page/receive"
        return_data = self.send_request(url, headers = self.jwtHeaders, cookies = self.cookies)
        if return_data['msg'] == 'success':
            receive_amount = return_data["result"].get("receive", "")
            total_amount = return_data["result"].get("total", "")
            print(f'当前待领取:{receive_amount}云朵')
            print(f'当前云朵数量:{total_amount}云朵')
        else:
            print(return_data['msg'])


if __name__ == "__main__":
    cookies = cookies.split("@")
    ydypqd = f"移动硬盘共获取到{len(cookies)}个账号"
    print(ydypqd)

    for i, cookie in enumerate(cookies, start = 1):
        print(f"\n======== ▷ 第 {i} 个账号 ◁ ========")
        YP(cookie).run()
        print("\n随机等待5-10s进行下一个账号")
        time.sleep(random.randint(5, 10))
