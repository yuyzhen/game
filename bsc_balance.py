#!/usr/bin/env python3
"""
BSC 钱包余额查询脚本

用法：
    python bsc_balance.py 0x你的钱包地址

示例：
    python bsc_balance.py 0x0000000000000000000000000000000000001000

如果没有提供地址作为参数，脚本会提示输入。
"""

import json
import sys
import urllib.request
import urllib.error


# BSC 公共 RPC 节点（也可换成其他节点）
BSC_RPC_URL = "https://bsc-dataseed1.binance.org/"


def get_bnb_balance(address: str) -> float:
    """
    通过 JSON-RPC 调用查询 BSC 上的 BNB 余额。

    参数:
        address: 钱包地址（0x 开头）

    返回:
        BNB 余额（float）

    抛出:
        Exception: 当 RPC 调用失败时
    """
    # 确保地址是有效的以太坊格式
    address = address.strip().lower()
    if not address.startswith("0x") or len(address) != 42:
        raise ValueError(f"无效的地址格式: {address}")

    # 构造 JSON-RPC 请求
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_getBalance",
        "params": [address, "latest"],
        "id": 1,
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        BSC_RPC_URL,
        data=data,
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as e:
        raise Exception(f"网络请求失败: {e}")
    except json.JSONDecodeError as e:
        raise Exception(f"响应解析失败: {e}")

    # 检查 RPC 返回是否有错误
    if "error" in result and result["error"]:
        err = result["error"]
        raise Exception(f"RPC 错误: {err.get('message', err)}")

    # 余额以 Wei（十六进制字符串）返回，转为 BNB
    balance_wei = int(result["result"], 16)
    balance_bnb = balance_wei / 10**18

    return balance_bnb


def main():
    # 从命令行参数或用户输入获取地址
    if len(sys.argv) > 1:
        address = sys.argv[1]
    else:
        address = input("请输入钱包地址: ").strip()

    if not address:
        print("[!] 地址不能为空")
        sys.exit(1)

    print(f"[*] 正在查询地址: {address}")
    print(f"[*] 网络: BSC (BNB Smart Chain)")
    print("-" * 50)

    try:
        balance = get_bnb_balance(address)
        print(f"[+] 余额: {balance:.6f} BNB")
        print(f"[+] 精确值: {balance:.18f} BNB")
    except Exception as e:
        print(f"[!] 查询失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
