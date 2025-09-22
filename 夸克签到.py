import os 
import re 
import sys 
import requests 
import json
#修改自作者Liu8Can夸克签到代码,感谢
# 尝试导入同文件夹中的sendNotify.py
try:
    import sendNotify
    has_send_notify = True
except ImportError:
    print("未找到sendNotify.py，将使用默认打印通知")
    has_send_notify = False

# 调用sendNotify.py的通知功能
def send(title, message):
    if has_send_notify:
        try:
            # 调用sendNotify.py中的发送函数
            sendNotify.send(title, message)
        except Exception as e:
            print(f"调用sendNotify失败: {str(e)}")
            print(f"{title}: {message}")
    else:
        # 未找到sendNotify.py时使用打印
        print(f"{title}\n{message}")

# 获取环境变量 
def get_env(): 
    # 判断 QUARK_COOKIE是否存在于环境变量 
    if "QUARK_COOKIE" in os.environ: 
        # 读取系统变量以 \n 或 && 分割变量 
        cookie_list = re.split('\n|&&', os.environ.get('__pus=aad01bdb05284b1a3e87857fa90883f6AAQcJmfO0JegcqGAARkf350uuLImMD+eyP9jexErFwpIYObeOoQDp78Hoz2Cs1ob4aFF4A/aF4lNon2J4siqrO8q;')) 
        # 过滤空字符串
        cookie_list = [cookie for cookie in cookie_list if cookie.strip()]
    else: 
        # 标准日志输出 
        print('❌ 未添加QUARK_COOKIE变量') 
        send('夸克自动签到', '❌ 未添加QUARK_COOKIE变量') 
        # 脚本退出 
        sys.exit(0) 

    return cookie_list 

class Quark:
    '''
    Quark类封装了签到、领取签到奖励的方法
    '''
    def __init__(self, user_data, user_index):
        '''
        初始化方法
        :param user_data: 用户信息，用于后续的请求
        :param user_index: 用户索引，用于日志标识
        '''
        self.param = user_data
        self.user_index = user_index
        self.session = requests.Session()
        # 设置请求头，模拟手机客户端
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://pan.quark.cn",
            "Referer": "https://pan.quark.cn/"
        }

    def convert_bytes(self, b):
        '''
        将字节转换为 MB GB TB
        :param b: 字节数
        :return: 返回 MB GB TB
        '''
        try:
            b = int(b)
            units = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
            i = 0
            while b >= 1024 and i < len(units) - 1:
                b /= 1024
                i += 1
            return f"{b:.2f} {units[i]}"
        except Exception as e:
            print(f"字节转换失败: {str(e)}")
            return f"{b} B"

    def get_growth_info(self):
        '''
        获取用户当前的签到信息
        :return: 返回一个字典，包含用户当前的签到信息
        '''
        try:
            url = "https://drive-m.quark.cn/1/clouddrive/capacity/growth/info"
            querystring = {
                "pr": "ucpro",
                "fr": "android",
                "kps": self.param.get('kps'),
                "sign": self.param.get('sign'),
                "vcode": self.param.get('vcode')
            }
            response = self.session.get(
                url=url, 
                params=querystring,
                headers=self.headers
            ).json()
            
            if response.get("data"):
                return response["data"]
            else:
                print(f"用户{self.user_index}获取成长信息失败: {response.get('message', '未知错误')}")
                return False
        except Exception as e:
            print(f"用户{self.user_index}获取成长信息异常: {str(e)}")
            return False

    def get_growth_sign(self):
        '''
        执行签到操作
        :return: 返回签到结果和奖励信息
        '''
        try:
            url = "https://drive-m.quark.cn/1/clouddrive/capacity/growth/sign"
            querystring = {
                "pr": "ucpro",
                "fr": "android",
                "kps": self.param.get('kps'),
                "sign": self.param.get('sign'),
                "vcode": self.param.get('vcode')
            }
            data = {"sign_cyclic": True}
            response = self.session.post(
                url=url, 
                json=data, 
                params=querystring,
                headers=self.headers
            ).json()
            
            if response.get("data"):
                return True, response["data"]["sign_daily_reward"]
            else:
                return False, response.get("message", "未知错误")
        except Exception as e:
            return False, f"签到请求异常: {str(e)}"

    def queryBalance(self):
        '''
        查询抽奖余额
        '''
        try:
            url = "https://coral2.quark.cn/currency/v1/queryBalance"
            querystring = {
                "moduleCode": "1f3563d38896438db994f118d4ff53cb",
                "kps": self.param.get('kps'),
            }
            response = self.session.get(
                url=url, 
                params=querystring,
                headers=self.headers
            ).json()
            
            if response.get("data"):
                return response["data"]["balance"]
            else:
                return f"查询失败: {response.get('msg', '未知错误')}"
        except Exception as e:
            return f"查询异常: {str(e)}"

    def do_sign(self):
        '''
        执行签到任务
        :return: 返回一个字符串，包含签到结果
        '''
        log = f"\n🙍🏻‍♂️ 第{self.user_index}个账号签到情况：\n"
        try:
            # 每日领空间
            growth_info = self.get_growth_info()
            if growth_info:
                # 账号类型和容量信息
                user_type = "88VIP用户" if growth_info.get('88VIP') else "普通用户"
                log += f"  账号类型：{user_type}\n"
                
                total_capacity = self.convert_bytes(growth_info.get('total_capacity', 0))
                log += f"  💾 网盘总容量：{total_capacity}\n"
                
                # 签到累计容量
                sign_reward = growth_info.get('cap_composition', {}).get('sign_reward', 0)
                log += f"  累计签到容量：{self.convert_bytes(sign_reward)}\n"
                
                # 签到状态判断
                cap_sign = growth_info.get('cap_sign', {})
                if cap_sign.get("sign_daily"):
                    daily_reward = self.convert_bytes(cap_sign.get('sign_daily_reward', 0))
                    progress = f"{cap_sign.get('sign_progress', 0)}/{cap_sign.get('sign_target', 0)}"
                    log += f"  ✅ 今日已签到，获得：{daily_reward}\n"
                    log += f"  🔄 连签进度：{progress}\n"
                else:
                    # 执行签到
                    sign_success, sign_result = self.get_growth_sign()
                    if sign_success:
                        daily_reward = self.convert_bytes(sign_result)
                        progress = f"{cap_sign.get('sign_progress', 0) + 1}/{cap_sign.get('sign_target', 0)}"
                        log += f"  ✅ 签到成功，获得：{daily_reward}\n"
                        log += f"  🔄 连签进度：{progress}\n"
                    else:
                        log += f"  ❌ 签到失败：{sign_result}\n"
                
                # 查询余额（如果需要）
                # balance = self.queryBalance()
                # log += f"  💰 余额：{balance}\n"
            else:
                log += "  ❌ 无法获取签到信息，可能是Cookie失效\n"
                
        except Exception as e:
            log += f"  ❌ 签到过程发生错误：{str(e)}\n"
            
        return log


def main():
    '''
    主函数
    :return: 返回一个字符串，包含签到结果
    '''
    msg = ""
    try:
        global cookie_quark
        cookie_quark = get_env()

        print(f"✅ 检测到共 {len(cookie_quark)} 个夸克账号，开始执行签到\n")
        msg += f"检测到共 {len(cookie_quark)} 个夸克账号，签到结果如下：\n"

        for i in range(len(cookie_quark)):
            try:
                # 获取user_data参数
                user_data = {}  # 用户信息
                cookie_str = cookie_quark[i].strip()
                # 解析cookie
                for item in cookie_str.replace(" ", "").split(';'):
                    if '=' in item:
                        key, value = item.split('=', 1)
                        user_data[key] = value
                
                # 执行签到
                quark = Quark(user_data, i + 1)
                log = quark.do_sign()
                msg += log
                print(log)
                
            except Exception as err:
                error_msg = f"第{i + 1}个账号处理出错：{str(err)}\n"
                msg += error_msg
                print(error_msg)
                continue  # 继续处理下一个账号

        # 发送通知
        send('夸克自动签到', msg)
        
    except Exception as err:
        error_msg = f"脚本执行出错：{str(err)}"
        print(error_msg)
        send('夸克自动签到', error_msg)

    return msg


if __name__ == "__main__":
    print("----------夸克网盘开始签到----------")
    main()
    print("----------夸克网盘签到完毕----------")
