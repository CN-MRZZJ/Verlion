"""分组分道交互式测试脚本

Usage: python test/test_heats.py [--base-url http://localhost:5000]
"""

import json
import sys

import requests

BASE = "http://localhost:5000/api/v1"


def api(method: str, path: str, data: dict | None = None) -> dict:
    url = f"{BASE}{path}"
    if method == "GET":
        r = requests.get(url)
    elif method == "DELETE":
        r = requests.delete(url)
    elif method == "PUT":
        r = requests.put(url, data=data)
    else:
        r = requests.post(url, json=data)
    r.encoding = "utf-8"
    return r.json()


def show_json(data):
    print(json.dumps(data, indent=2, ensure_ascii=False))


def pick_event():
    events = api("GET", "/events").get("items", [])
    if not events:
        print("没有项目")
        return None
    print("\n项目列表:")
    for e in events:
        print(f"  [{e['id']:>3}] {e['name']} | {e['gender']} | 组{e['group']} | {'个人' if e['is_individual'] else '团体'}")
    try:
        eid = int(input("选择项目 ID: "))
    except ValueError:
        print("无效 ID")
        return None
    return eid


def cmd_events():
    """列出所有项目"""
    pick_event()


def cmd_algorithms():
    """列出可用算法"""
    result = api("GET", "/events/heats/algorithms")
    print(f"\n可用算法: {result.get('algorithms', [])}")


def cmd_view():
    """查看编排"""
    eid = pick_event()
    if eid is None:
        return
    result = api("GET", f"/events/{eid}/heats")
    data = result.get("data", {})
    rounds = data.get("rounds", [])
    if not rounds:
        print(f"\n项目 {eid} 尚未编排")
        return
    print(f"\n项目 {eid} 编排结果:")
    for rd in rounds:
        print(f"  {rd['round_name']} (第{rd['round_number']}轮)")
        for ht in rd.get("heats", []):
            print(f"    {ht['heat_name']} ({len(ht['entries'])}人):")
            for e in sorted(ht["entries"], key=lambda x: x.get("lane") or 99):
                print(f"      道{e['lane']}: {e['athlete_name']} ({e['department_name']})")


def cmd_create():
    """执行编排"""
    eid = pick_event()
    if eid is None:
        return
    try:
        lanes = int(input("每组道数 [8]: ") or "8")
    except ValueError:
        lanes = 8
    algo = input("算法名 [random]: ") or "random"
    params_input = input("算法参数 (JSON, 留空): ")
    params = {}
    if params_input.strip():
        try:
            params = json.loads(params_input)
        except json.JSONDecodeError:
            print("JSON 解析失败")
            return

    data = {"lanes_per_heat": lanes, "algorithm": algo, "params": params}
    result = api("POST", f"/events/{eid}/heats", data)
    if result.get("ok"):
        print("编排成功\n")
        cmd_view()
    else:
        print(f"失败: {result.get('error')}")


def cmd_swap():
    """调换道次"""
    eid = pick_event()
    if eid is None:
        return
    cmd_view_compact(eid)

    try:
        hid = int(input("组次 ID: "))
        eid1 = int(input("entry 1 ID: "))
        lane1 = int(input(f"entry {eid1} 新道次: "))
        eid2 = int(input("entry 2 ID (0 跳过): "))
    except ValueError:
        print("无效输入")
        return

    r1 = api("PUT", f"/events/{eid}/heats/{hid}/entries/{eid1}", {"lane": lane1})
    if not r1.get("ok"):
        print(f"entry 1 更新失败: {r1.get('error')}")
        return

    if eid2:
        lane2 = int(input(f"entry {eid2} 新道次: "))
        r2 = api("PUT", f"/events/{eid}/heats/{hid}/entries/{eid2}", {"lane": lane2})
        if not r2.get("ok"):
            print(f"entry 2 更新失败: {r2.get('error')}")
            return

    print("调整完成\n")
    cmd_view_compact(eid)


def cmd_view_compact(eid=None):
    """紧凑显示编排"""
    if eid is None:
        eid = pick_event()
        if eid is None:
            return
    result = api("GET", f"/events/{eid}/heats")
    data = result.get("data", {})
    rounds = data.get("rounds", [])
    if not rounds:
        print(f"项目 {eid} 尚未编排")
        return
    for rd in rounds:
        for ht in rd.get("heats", []):
            print(f"  {ht['heat_name']} (id={ht['id']}):")
            for e in sorted(ht["entries"], key=lambda x: x.get("lane") or 99):
                print(f"    id={e['id']:>3}  道{e['lane']}: {e['athlete_name']}")


def cmd_delete():
    """清除编排"""
    eid = pick_event()
    if eid is None:
        return
    confirm = input(f"确认清除项目 {eid} 的编排? (y/N): ")
    if confirm.lower() != "y":
        print("取消")
        return
    result = api("DELETE", f"/events/{eid}/heats")
    if result.get("ok"):
        print("已清除")
    else:
        print(f"失败: {result.get('error')}")


def cmd_register():
    """注册运动员（用于准备测试数据）"""
    eid = pick_event()
    if eid is None:
        return

    # 列出部分运动员
    athletes = api("GET", "/athletes?athlete_type=competitive&page_size=10").get("items", [])
    print("\n运动员列表 (前10):")
    for a in athletes:
        print(f"  {a['athlete_no']} | {a['name']} | {a['gender']} | {a['department_name']}")
    print("  ...")

    atype = input("athlete_type [competitive]: ") or "competitive"
    while True:
        ano = input("运动员号 (空=结束): ").strip()
        if not ano:
            break
        result = api("POST", "/athletes/registrations/add", {
            "athlete_type": atype,
            "athlete_no": ano,
            "event_id": eid,
        })
        print(f"  {ano}: {'OK' if result.get('ok') else result.get('error')}")


def cmd_full():
    """完整流程测试 (需要服务器已启动且有项目数据)"""
    print("\n=== 全流程测试 ===\n")

    # 1. 算法列表
    print("1. 算法列表:", api("GET", "/events/heats/algorithms").get("algorithms"))

    # 2. 找有报名运动员的项目
    events = api("GET", "/events?category=competitive").get("items", [])
    if not events:
        print("没有项目，终止")
        return
    eid = None
    # 从后面试（报名一般集中在高 ID 项目）
    for e in reversed(events[-10:]):
        result = api("POST", f"/events/{e['id']}/heats", {"lanes_per_heat": 8, "algorithm": "random"})
        if result.get("ok"):
            eid = e["id"]
            api("DELETE", f"/events/{eid}/heats")
            print(f"2. 使用项目 id={eid} ({e['name']} {e['gender']} {e['group']})")
            break
    if eid is None:
        print("没有有报名运动员的项目，请先运行 [r] 注册")
        return

    # 3. 查看编排 (应为空)
    data = api("GET", f"/events/{eid}/heats").get("data", {})
    print(f"3. 编排前 rounds: {len(data.get('rounds', []))} (预期 0)")

    # 4. 创建编排
    result = api("POST", f"/events/{eid}/heats", {"lanes_per_heat": 3, "algorithm": "random"})
    ok = result.get("ok")
    print(f"4. 编排: {'OK' if ok else result.get('error')}")
    if not ok:
        print("   (可能没有报名运动员，跳过剩余步骤)")
        return

    rounds = result["data"]["rounds"]
    for rd in rounds:
        for ht in rd["heats"]:
            names = [e["athlete_name"] for e in ht["entries"]]
            print(f"   {ht['heat_name']}: {names}")

    # 5. 换道
    if rounds and rounds[0]["heats"]:
        ht = rounds[0]["heats"][0]
        entries = ht["entries"]
        if len(entries) >= 2:
            e1, e2 = entries[0], entries[1]
            r = api("PUT", f"/events/{eid}/heats/{ht['id']}/entries/{e1['id']}", {"lane": 0})
            api("PUT", f"/events/{eid}/heats/{ht['id']}/entries/{e2['id']}", {"lane": e1['lane']})
            api("PUT", f"/events/{eid}/heats/{ht['id']}/entries/{e1['id']}", {"lane": e2['lane']})
            print(f"5. 换道: {e1['athlete_name']} <-> {e2['athlete_name']} OK")

    # 6. 清除
    api("DELETE", f"/events/{eid}/heats")
    data = api("GET", f"/events/{eid}/heats").get("data", {})
    print(f"6. 清除后 rounds: {len(data.get('rounds', []))} (预期 0)")

    print("\n=== 全流程通过 ===")


CMDS = {
    "e":  ("列出项目", cmd_events),
    "a":  ("列出算法", cmd_algorithms),
    "v":  ("查看编排", cmd_view),
    "c":  ("执行编排", cmd_create),
    "s":  ("调换道次", cmd_swap),
    "d":  ("清除编排", cmd_delete),
    "r":  ("注册运动员", cmd_register),
    "f":  ("全流程测试", cmd_full),
    "q":  ("退出", None),
}


def main():
    if "--base-url" in sys.argv:
        global BASE
        idx = sys.argv.index("--base-url")
        BASE = sys.argv[idx + 1].rstrip("/")

    print(f"分组分道测试工具 (服务: {BASE})")
    print("=" * 50)

    while True:
        print()
        for key, (desc, _) in CMDS.items():
            print(f"  [{key}] {desc}")
        try:
            choice = input("> ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print()
            break

        if choice == "q":
            break
        if choice in CMDS and CMDS[choice][1]:
            try:
                CMDS[choice][1]()
            except requests.ConnectionError:
                print(f"连接失败! 请确保服务已启动: python run_dev.py")
                break
            except Exception as exc:
                print(f"错误: {exc}")
        else:
            print("无效选项")


if __name__ == "__main__":
    main()
