import os
import sys
import requests

BASE_URL = "https://ikuuu.eu"
EMAILS = [item.strip() for item in os.environ.get("EMAIL", "").split(",") if item.strip()]
PASSWORDS = [item.strip() for item in os.environ.get("PASSWD", "").split(",")]
SCKEY = os.environ.get("SCKEY", "")
TOKEN = os.environ.get("TOKEN", "")

HEADERS = {
    "origin": BASE_URL,
    "referer": f"{BASE_URL}/auth/login",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
}


def response_json(response, step):
    response.raise_for_status()
    try:
        result = response.json()
    except ValueError as exc:
        raise RuntimeError(f"{step}接口未返回JSON（HTTP {response.status_code}）") from exc
    if not isinstance(result, dict):
        raise RuntimeError(f"{step}接口返回格式异常")
    return result


def notify(message):
    try:
        if SCKEY and SCKEY != "1":
            requests.post(
                f"https://sctapi.ftqq.com/{SCKEY}.send",
                params={"title": "ikuuu签到", "desp": message}, timeout=15,
            ).raise_for_status()
            print("通知已发送")
        elif TOKEN and TOKEN != "1":
            response = requests.post(
                "https://www.pushplus.plus/send",
                json={"token": TOKEN, "title": "ikuuu签到", "content": message, "template": "json"},
                timeout=15,
            )
            response.raise_for_status()
            print("通知已发送")
        else:
            print("未配置签到通知")
    except Exception as exc:
        # 通知失败不能改变签到本身的结果。
        print(f"通知发送失败（{type(exc).__name__}）")


def main():
    if not EMAILS or len(EMAILS) != len(PASSWORDS):
        print("签到凭据未配置完整：请检查 EMAIL 和 PASSWD Secrets。")
        return 1

    failures = []
    for index, (email, password) in enumerate(zip(EMAILS, PASSWORDS), start=1):
        session = requests.Session()
        session.headers.update(HEADERS)
        try:
            login = response_json(session.post(
                f"{BASE_URL}/auth/login",
                data={"email": email, "passwd": password}, timeout=(15, 30),
            ), "登录")
            if str(login.get("ret")) != "1":
                raise RuntimeError("登录接口未确认登录成功")

            check_headers = {
                "accept": "application/json, text/javascript, */*; q=0.01",
                "x-requested-with": "XMLHttpRequest",
            }
            result = response_json(session.post(
                f"{BASE_URL}/user/checkin", headers=check_headers, timeout=(15, 30),
            ), "签到")
            ret = str(result.get("ret"))
            message = str(result.get("msg") or "签到接口未返回说明")
            already_done = ret == "0" and any(
                word in message.lower() for word in ("已签到", "签到过", "already")
            )
            if ret != "1" and not already_done:
                raise RuntimeError(f"签到接口未确认成功：{message[:160]}")

            state = "今日已签到" if already_done else "签到成功"
            print(f"账号 {index}：{state}。{message}")
            notify(f"账号 {index}：{state}。{message}")
        except Exception as exc:
            # 不打印账号、密码、Cookie、响应正文或请求 URL。
            print(f"账号 {index}：签到失败（{type(exc).__name__}: {str(exc)[:180]}）")
            failures.append(index)

    if failures:
        print(f"失败账号数：{len(failures)}")
        return 1
    print(f"全部账号处理完成：{len(EMAILS)} 个。")
    return 0


if __name__ == "__main__":
    sys.exit(main())