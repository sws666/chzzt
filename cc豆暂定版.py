# 软件:建行活动，奋斗季cc豆 功能：每日营收，签到 浏览任务，答题，抽奖，翻翻卡，商户任务
# 先开抓包抓的是微信https://event.ccbft.com/api/flow/nf/shortLink/redirect/ccb_gjb，抓请求体全部,
# ture改成True填入self.w_param中，即w_param={xx}，客服端有所差异
# 定时：一天一次
import time
import random
import requests
from datetime import datetime
import re

ua = ''
w_param ={}

# self.bus_token可以刷新
class CCD:
    user_region = None
    zhc_token = None
    base_header = {
        'Host': 'm3.dmsp.ccb.com',
        'accept': 'application/json, text/plain, */*',
        'user-agent': ua,
        'origin': 'https://m3.dmsp.ccb.com',
        'x-requested-with': 'com.tencent.mm',
        'accept-language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        'content-type': 'application/json',
        'Connection': 'keep-alive'
    }

    def __init__(self):
        pass

    def run(self):
        self.get_token()
        self.region()
        self.user_info()
        self.sign_in()
        self.getlist()
        self.answer_state()
        self.get_user_ccd()

    # 随机延迟默认1-1.5
    def sleep(self, min_delay=1, max_delay=1.5):
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)

    def send_request(self, url, headers, data=None, method='GET', cookies=None):
        try:
            if method == 'GET':
                response = requests.get(url, headers = headers, cookies = cookies, timeout = 10)
            elif method == 'POST':
                response = requests.post(url, headers = headers, json = data, cookies = cookies, timeout = 10)
            else:
                raise ValueError('Invalid HTTP method.')

            response.raise_for_status()  # Raises an exception for 4xx or 5xx status codes
            return response.json()

        except requests.Timeout as e:
            print("请求超时:", str(e))
            # Handle timeout error

        except requests.RequestException as e:
            print("请求错误:", str(e))
            # Handle other request errors

        except Exception as e:
            print("其他错误:", str(e))
            # Handle any other exceptions

    # 获取token
    def get_token(self):
        url = 'https://event.ccbft.com/api/flow/nf/shortLink/redirect/ccb_gjb?shareMDID=ZHCMD_8460172f-48b2-4612-a069-f04611760445&shareDepth=1&CCB_Chnl=6000199'
        headers = {
            'Host': 'event.ccbft.com',
            'accept': 'application/json, text/plain, */*',
            'user-agent': ua,
            'origin': 'https://event.ccbft.com',
            'Content-Length': '750',
            'x-requested-with': 'com.tencent.mm',
            'accept-language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'content-type': 'application/json',
            'Connection': 'keep-alive'
        }
        payload = w_param
        return_data = self.send_request(url, headers = headers, data = payload, method = 'POST')
        if return_data['code'] != 200:
            print(return_data['message'])
            return
        redirect_url = return_data['data'].get('redirectUrl')
        token = self.extract_token(redirect_url)
        if token:
            self.zhc_token = token
            self.auth_login(token)

    def extract_token(self, redirect_url):
        start_index = redirect_url.find("__dmsp_token=") + len("__dmsp_token=")
        end_index = redirect_url.find("&", start_index)

        if start_index != -1 and end_index != -1:
            token = redirect_url[start_index:end_index]
            return token
        return None

    # 登录
    def auth_login(self, token):
        url = 'https://m3.dmsp.ccb.com/api/businessCenter/auth/login'
        payload = {"token": token, "channelId": "wx"}
        return_data = self.send_request(url, headers = self.base_header, data = payload, method = 'POST')
        self.sleep()
        if return_data['code'] != 200:
            print(return_data['message'])
            return

    # 获取用户地区代码
    def region(self):
        url = f'https://m3.dmsp.ccb.com/api/businessCenter/gis/getAddress?zhc_token={self.zhc_token}'
        payload = {"lgt": 116.118792, "ltt": 40.2274059, "flag": 1}
        return_data = self.send_request(url, headers = self.base_header, data = payload, method = 'POST')
        self.sleep()
        if return_data['code'] != 200:
            print(return_data['message'])
            return
        self.user_region = return_data['data'].get('code')

    # 查询用户等级
    def user_info(self):
        url = f'https://m3.dmsp.ccb.com/api/businessCenter/mainVenue/getUserState?zhc_token={self.zhc_token}'
        return_data = self.send_request(url, headers = self.base_header, method = 'POST')

        if return_data['code'] != 200:
            print(return_data['message'])
            return
        current_level = return_data['data'].get('currentLevel')
        need_exp = return_data['data'].get('nextMonthProtectLevelNeedGrowthExp') - return_data['data'].get('growthExp')
        level = return_data['data'].get('level')
        reward_id = return_data['data'].get('zhcRewardInfo').get('id')
        reward_type = return_data['data'].get('zhcRewardInfo').get('rewardType')
        reward_value = return_data['data'].get('zhcRewardInfo').get('rewardValue')
        print(f"当前用户等级{current_level}级")
        print(f"距下一级还需{need_exp}成长值")
        self.income(level, reward_id, reward_type, reward_value)

    # 每日营收
    def income(self, level, reward_id, reward_type, reward_value):
        url = f'https://m3.dmsp.ccb.com/api/businessCenter/mainVenue/receiveLevelReward?zhc_token={self.zhc_token}'
        payload = {"level": level, "rewardId": reward_id, "levelRewardType": reward_type}
        return_data = self.send_request(url, headers = self.base_header, data = payload, method = 'POST')
        self.sleep()
        if return_data['code'] != 200:
            print(return_data['message'])
            return

        print(f"今日营收: {reward_value}cc豆")

    # 签到
    def sign_in(self):
        signin_url = f'https://m3.dmsp.ccb.com/api/businessCenter/taskCenter/signin?zhc_token={self.zhc_token}'
        signin_payload = {"taskId": 96}
        return_data = self.send_request(url = signin_url, headers = self.base_header, data = signin_payload,
                                        method = 'POST')
        self.sleep()
        if return_data['code'] != 200:
            print(return_data['message'])
            return
        print(return_data['message'])

        # print('未知错误')

    # 获取浏览任务列表
    def getlist(self):
        list_url = f'https://m3.dmsp.ccb.com/api/businessCenter/taskCenter/getTaskList?zhc_token={self.zhc_token}'
        payload = {"publishChannels": "03", "regionId": self.user_region}  # 440300

        return_data = self.send_request(url = list_url, headers = self.base_header, data = payload, method = 'POST')
        self.sleep()
        if return_data['code'] != 200:
            print(return_data['message'])
            return

        task_list = return_data['data'].get('浏览任务')
        for value in task_list:
            complete_status = value['taskDetail'].get('completeStatus')
            if complete_status == '02':
                print(f"{value['taskName']}:已完成")
                continue
            task_id = value['id']
            task_name = value['taskName']
            print(f'去完成{task_name}')
            self.browse(task_id, task_name)
            self.receive(task_id)

    # 执行浏览任务
    def browse(self, task_id, task_name):
        url = f'https://m3.dmsp.ccb.com/api/businessCenter/taskCenter/browseTask?zhc_token={self.zhc_token}'
        payload = {"taskId": task_id, "browseSec": 1}
        return_data = self.send_request(url, headers = self.base_header, data = payload, method = 'POST')
        self.sleep()
        if return_data['code'] != 200:
            print(return_data['message'])
            return
        print(return_data['message'])

    # 领取奖励
    def receive(self, task_id):
        url = f'https://m3.dmsp.ccb.com/api/businessCenter/taskCenter/receiveReward?zhc_token={self.zhc_token}'
        payload = {"taskId": task_id}
        return_data = self.send_request(url, headers = self.base_header, data = payload, method = 'POST')
        self.sleep()
        if return_data['code'] != 200:
            print(return_data['message'])
            return
        print(return_data['message'])

    # 获取答题state
    def answer_state(self):
        url = f'https://m3.dmsp.ccb.com/api/businessCenter/zhcUserDayAnswer/getAnswerStatus?zhc_token={self.zhc_token}'
        return_data = self.send_request(url, headers = self.base_header)
        if return_data['code'] == 200:
            if return_data['data'].get('answerState') == 'Y':
                return print(return_data['message'])
            else:
                # 获取今日题目
                print('获取今日题目')
                self.get_question()
        else:
            return print(return_data['message'])

    # 获取题目
    def get_question(self):
        url = f'https://m3.dmsp.ccb.com/api/businessCenter/zhcUserDayAnswer/queryQuestionToday?zhc_token={self.zhc_token}'
        return_data = self.send_request(url, headers = self.base_header)
        self.sleep()
        if return_data['code'] != 200:
            print(return_data['message'])
            return
        question_id = return_data['data'].get('questionId')
        remark = return_data['data'].get('remark')
        answer_list = return_data['data'].get('answerList')
        if remark:
            # 匹配答案
            print('开始匹配正确答案')
            # 去除标点符号的正则表达式模式
            pattern = r"[，。？！“”、]"

            remark_cleaned = re.sub(pattern, "", remark)

            max_match_count = 0
            right_answer_id = None

            # 遍历答案列表，与remark进行匹配
            for answer in answer_list:
                answer_id = answer["id"]
                answer_result = answer["answerResult"]
                answer_cleaned = re.sub(pattern, "", answer_result)

                match_count = 0
                for word in answer_cleaned:
                    if word in remark_cleaned:
                        match_count += 1
                        remark_cleaned = remark_cleaned.replace(word, "", 1)

                if match_count > max_match_count:
                    max_match_count = match_count
                    right_answer_id = answer_id
            print("匹配成功，开始答题")
            self.answer(question_id, right_answer_id)
        else:
            print('暂无提示随机答题')
            right_answer_id = random.choice(answer_list)['id']
            self.answer(question_id, right_answer_id)

    # 答题
    def answer(self, question_id, answer_ids):
        url = f'https://m3.dmsp.ccb.com/api/businessCenter/zhcUserDayAnswer/userAnswerQuestion?zhc_token={self.zhc_token}'
        payload = {"questionId": question_id, "answerIds": answer_ids}
        return_data = self.send_request(url, headers = self.base_header, data = payload, method = 'POST')
        self.sleep()
        if return_data['code'] != 200:
            print(return_data['message'])
            return
        print(return_data['message'])

    # 查询cc豆及过期cc豆时间
    def get_user_ccd(self):
        url_get_ccd = f'https://m3.dmsp.ccb.com/api/businessCenter/user/getUserCCD?zhc_token={self.zhc_token}'
        url_get_expired_ccd = f'https://m3.dmsp.ccb.com/api/businessCenter/user/getUserCCDExpired?zhc_token={self.zhc_token}'
        payload_get_ccd = {}
        payload_get_expired_ccd = {}

        try:
            return_data1 = self.send_request(url_get_ccd, headers = self.base_header, data = payload_get_ccd,
                                             method = 'POST')
            self.sleep()
            return_data2 = self.send_request(url_get_expired_ccd, headers = self.base_header,
                                             data = payload_get_expired_ccd, method = 'POST')

            if return_data1['code'] != 200:
                raise Exception(return_data1['message'])
            elif return_data2['code'] != 200:
                raise Exception(return_data2['message'])

            count1 = return_data1['data'].get('userCCBeanInfo').get('count')
            count2 = return_data2['data'].get('userCCBeanExpiredInfo').get('count')
            expire_date_str = return_data2['data'].get('userCCBeanExpiredInfo').get('expireDate')

            if expire_date_str:
                expire_date = datetime.fromisoformat(expire_date_str)
                formatted_date = expire_date.strftime('%Y-%m-%d %H:%M:%S')
                print(f'当前cc豆:{count1}，有{count2} cc豆将于{formatted_date}过期')
            else:
                print("expire_date_str is empty")

        except Exception as e:
            print(str(e))


CCD().run()
