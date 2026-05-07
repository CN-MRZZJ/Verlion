"""生成大规模测试数据库

Usage: python test/seed_db.py [--db path/to/test.db]

生成内容:
  - 15 个部门
  - 200 竞技运动员 + 50 趣味运动员
  - 12 径赛 + 6 田赛 + 3 趣味项目 (A/B/ALL, 男/女/混合)
  - 400+ 报名记录 (每个竞技运动员报 1-3 个项目)
  - event_types, point_rules, group_options 种子数据
"""

import os
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models.database import Database
from app.models.repositories import SportsRepository

random.seed(42)

DB_PATH = Path(__file__).resolve().parent / "test_meet.db"


def generate(db_path: str):
    if os.path.exists(db_path):
        os.remove(db_path)

    db = Database(db_path)
    db.initialize()

    with db.connect() as conn:
        repo = SportsRepository(conn)

        # ── Departments ──────────────────────────────────────────────
        dept_names = [
            "林学院", "园林学院", "水土保持学院", "经济管理学院",
            "生物科学与技术学院", "工学院", "材料科学与技术学院",
            "人文社会科学学院", "外语学院", "信息学院",
            "理学院", "生态与自然保护学院", "环境科学与工程学院",
            "艺术设计学院", "马克思主义学院",
        ]
        dept_ids: list[int] = []
        for name in dept_names:
            dept_id = repo.insert_department(name, random.randint(30, 120))
            dept_ids.append(dept_id)
        print(f"[1/5] 部门: {len(dept_ids)}")

        # ── Athletes ─────────────────────────────────────────────────
        surnames = "赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张孔曹严华金魏陶姜戚谢邹喻柏水窦章云苏潘葛奚范彭郎鲁韦昌马苗凤花方俞任袁柳酆鲍史唐费廉岑薛雷贺倪汤滕殷罗毕郝邬安常乐于时傅皮下齐康伍余元卜顾孟平黄和穆萧尹姚邵湛汪祁毛禹狄米贝明臧计伏成戴谈宋茅庞熊纪舒屈项祝董梁"
        male_names = "伟强军勇斌杰涛明文超浩宇轩峰辉毅翔鹏飞龙刚华磊瑞凯健泽宁博涵俊威远哲瀚辰晔鑫旭"
        female_names = "芳敏静丽娟婷雪花蕾玲萍红梅兰菊燕芬霞云彩虹瑶茜薇颖萱瑜菲雯琳珊蓉欣倩"

        athletes_inserted = 0

        def _make_no(idx):
            return f"{idx:04d}"

        # 200 competitive athletes
        for i in range(1, 201):
            surname = surnames[i % len(surnames)]
            gender = "male" if i % 2 == 1 else "female"
            name_pool = male_names if gender == "male" else female_names
            given = name_pool[(i * 7) % len(name_pool)] + name_pool[(i * 13 + 1) % len(name_pool)]
            dept_id = dept_ids[i % len(dept_ids)]
            grp = random.choice(["A", "B"])
            try:
                repo.insert_athlete("competitive", _make_no(i), f"{surname}{given}", gender, dept_id, grp)
                athletes_inserted += 1
            except Exception:
                pass

        # 50 fun athletes
        for i in range(201, 251):
            surname = surnames[i % len(surnames)]
            gender = "male" if i % 3 == 0 else "female"
            name_pool = male_names if gender == "male" else female_names
            given = name_pool[(i * 11) % len(name_pool)] + name_pool[(i * 17 + 2) % len(name_pool)]
            dept_id = dept_ids[i % len(dept_ids)]
            try:
                repo.insert_athlete("fun", _make_no(i), f"{surname}{given}", gender, dept_id, None)
                athletes_inserted += 1
            except Exception:
                pass

        print(f"[2/5] 运动员: {athletes_inserted} (200 竞技 + 50 趣味)")

        # ── Events ────────────────────────────────────────────────────
        track_events = [
            ("100米", "track", "time", "male", "A"), ("100米", "track", "time", "male", "B"),
            ("100米", "track", "time", "female", "A"), ("100米", "track", "time", "female", "B"),
            ("200米", "track", "time", "male", "A"), ("200米", "track", "time", "female", "A"),
            ("400米", "track", "time", "male", "B"), ("400米", "track", "time", "female", "B"),
            ("800米", "track", "time", "male", "ALL"), ("800米", "track", "time", "female", "ALL"),
            ("4x100米接力", "track", "time", "male", "ALL"), ("4x100米接力", "track", "time", "female", "ALL"),
        ]
        field_events = [
            ("跳远", "field", "length", "male", "A"), ("跳远", "field", "length", "female", "A"),
            ("跳高", "field", "length", "male", "B"), ("跳高", "field", "length", "female", "B"),
            ("铅球", "field", "length", "male", "ALL"), ("铅球", "field", "length", "female", "ALL"),
        ]
        # Fun events use restructured tuples with same length: (name, event_type, strategy, gender, group)
        fun_events: list[tuple[str, str, str, str, str]] = [
            ("定点投篮", "fun", "count", "mixed", "ALL"),
            ("跳绳", "fun", "count", "mixed", "ALL"),
            ("拔河", "fun", "count", "mixed", "ALL"),
        ]

        all_events: list[tuple[str, str, str, str, str, str]] = []
        for name, etype, strategy, gender, grp in track_events + field_events:
            all_events.append((name, etype, strategy, gender, grp, "competitive"))
        for name, etype, strategy, gender, grp in fun_events:
            all_events.append((name, etype, strategy, gender, grp, "fun"))

        event_ids: list[int] = []
        for name, etype, strategy, gender, grp, category in all_events:
            is_individual = 0 if "接力" in name or name in ("拔河",) else 1
            try:
                eid = repo.insert_event(name, category, etype, strategy, gender, grp, is_individual)
                event_ids.append(eid)
                # create progress record
                repo.upsert_event_progress(eid, False, False, False, False)
            except Exception as exc:
                print(f"  跳过 event {name}: {exc}")

        print(f"[3/5] 项目: {len(event_ids)} ({len(track_events)} 径赛 + {len(field_events)} 田赛 + {len(fun_events)} 趣味)")

        # ── Registrations ─────────────────────────────────────────────
        reg_count = 0
        competitive_ids = list(range(1, 201))

        # Individual events (exclude relay races)
        individual_events = [
            eid for eid, (name, _, _, _, _, _) in zip(event_ids, all_events)
            if "接力" not in name and name != "拔河"
        ]

        for athlete_id in competitive_ids:
            gender = "male" if athlete_id % 2 == 1 else "female"
            grp = "A" if athlete_id % 3 != 0 else "B"

            # Find events matching this athlete's gender and group
            matching = []
            for idx, (name, etype, strategy, ev_gender, ev_grp, category) in enumerate(all_events):
                if "接力" in name or name == "拔河":
                    continue
                eid = event_ids[idx]
                if ev_gender == gender or ev_gender == "mixed":
                    if ev_grp == grp or ev_grp == "ALL":
                        matching.append(eid)

            if matching:
                # Each athlete registers for 1-3 events
                n = random.randint(1, min(3, len(matching)))
                chosen = random.sample(matching, n)
                for eid in chosen:
                    try:
                        repo.insert_athlete_registration("competitive", athlete_id, eid)
                        reg_count += 1
                    except Exception:
                        pass

        # Fun registrations: 10-20 per fun event
        fun_event_ids = event_ids[-len(fun_events):]
        fun_athlete_ids = list(range(201, 251))
        for eid in fun_event_ids:
            n = random.randint(10, 20)
            for aid in random.sample(fun_athlete_ids, n):
                try:
                    repo.insert_athlete_registration("fun", aid, eid)
                    reg_count += 1
                except Exception:
                    pass

        print(f"[4/5] 报名记录: {reg_count}")

        # ── Settings ──────────────────────────────────────────────────
        repo.set_setting("rule.attempt_policy", "best")
        repo.set_setting("rule.team_event_default", "ALL")

        conn.commit()

    # Report
    db_size = os.path.getsize(db_path)
    print(f"[5/5] 数据库: {db_path} ({db_size / 1024:.1f} KB)")
    print()

    # Stats
    with db.connect() as conn:
        repo = SportsRepository(conn)
        dept_count = conn.execute("SELECT COUNT(*) AS c FROM departments").fetchone()["c"]
        ath_count = conn.execute("SELECT COUNT(*) AS c FROM athletes").fetchone()["c"]
        evt_count = conn.execute("SELECT COUNT(*) AS c FROM events").fetchone()["c"]
        regs = conn.execute("SELECT COUNT(*) AS c FROM athlete_registrations").fetchone()["c"]
        print(f"部门 {dept_count} | 运动员 {ath_count} | 项目 {evt_count} | 报名 {regs}")
        print()

        # Per-event registration counts (for verifying grouping test targets)
        print("各项目报名人数 (前10):")
        rows = conn.execute("""
            SELECT e.id, e.name, e.gender, e."group", COUNT(*) AS cnt
            FROM athlete_registrations r
            JOIN events e ON e.id = r.event_id
            GROUP BY e.id
            ORDER BY cnt DESC
            LIMIT 10
        """).fetchall()
        for r in rows:
            print(f"  [{r['id']:>3}] {r['name']} {r['gender']} {r['group']}: {r['cnt']}人")

    print(f"\n导出: SPORTS_MEET_DB={db_path} python run_dev.py")
    return db_path


if __name__ == "__main__":
    path = sys.argv[2] if "--db" in sys.argv and len(sys.argv) > 2 else str(DB_PATH)
    generate(path)
