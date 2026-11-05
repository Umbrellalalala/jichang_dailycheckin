import os
import sys
from urllib.parse import urlparse

import requests

BASE_URL = os.environ.get("IKUUU_BASE_URL", "").strip().rstrip("/")
COOKIES = [value.strip() for value in os.environ.get("IKUUU_COOKIE", "").split("||") if value.strip()]
SCKEY = os.environ.get("SCKEY", "").strip()
TOKEN = os.environ.get("TOKEN", "").strip()


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
    """Optional push notifications only; this script has no email sender."""
    try:
        if SCKEY and SCKEY != "1":
            requests.post(
                f"https://sctapi.ftqq.com/{SCKEY}.send",
                params={"title": "ikuuu签到", "desp": message}, timeout=15,
            ).raise_for_status()
            print("签到推送已发送")
        elif TOKEN and TOKEN != "1":
            response = requests.post(
                "https://www.pushplus.plus/send",
                json={"token": TOKEN, "title": "ikuuu签到", "content": message, "template": "json"},
                timeout=15,
            )
            response.raise_for_status()
            print("签到推送已发送")
    except Exception as exc:
        print(f"签到推送失败（{type(exc).__name__}）")


def main():
    if not COOKIES:
        print("未配置 IKUUU_COOKIE，请从官网登录后复制 Cookie 并保存到仓库 Secrets。")
        return 1
    parsed = urlparse(BASE_URL)
    if parsed.scheme != "https" or not parsed.netloc:
        print("未配置有效的 IKUUU_BASE_URL；请填写获取 Cookie 时使用的 https 官网地址。")
        return 1

    failures = []
    for index, cookie in enumerate(COOKIES, start=1):
        try:
            response = requests.post(
                f"{BASE_URL}/user/checkin",
                headers={
                    "Cookie": cookie,
                    "Origin": BASE_URL,
                    "Referer": f"{BASE_URL}/user",
                    "Accept": "application/json, text/javascript, */*; q=0.01",
                    "X-Requested-With": "XMLHttpRequest",
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/132.0.0.0 Safari/537.36"
                    ),
                },
                timeout=(15, 30),
            )
            if response.url.rstrip("/").endswith("/auth/login"):
                raise RuntimeError("Cookie已失效，或官网地址与该Cookie不匹配")

            result = response_json(response, "签到")
            ret = str(result.get("ret"))
            message = str(result.get("msg") or result.get("message") or "签到接口未返回说明")
            already_done = ret == "0" and any(
                word in message.lower() for word in ("已签到", "签到过", "already")
            )
            if ret != "1" and not already_done:
                raise RuntimeError(f"签到接口未确认成功：{message[:160]}")

            state = "今日已签到" if already_done else "签到成功"
            summary = f"账号 {index}：{state}。{message}"
            print(summary)
            notify(summary)
        except Exception as exc:
            print(f"账号 {index}：签到失败（{type(exc).__name__}: {str(exc)[:180]}）")
            failures.append(index)

    if failures:
        print(f"失败账号数：{len(failures)}")
        return 1
    print(f"全部账号处理完成：{len(COOKIES)} 个。")
    return 0


if __name__ == "__main__":
    sys.exit(main())