"""运行冻结v2合成集，保留逐批原始结果、运行配置和知识快照；不读写旧基线。"""

import hashlib
import json
import os
import shutil
import statistics
import subprocess
import time
import urllib.request
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
DATA = HERE / "测试用例"
BASE = os.getenv("SERVICEWEAVE_API_URL", "http://127.0.0.1:8000")
COMPOSE = ["docker", "compose", "-f", str(ROOT / "docker-compose.yml")]


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def docker(*args):
    return subprocess.check_output(COMPOSE + list(args), cwd=ROOT).decode("utf-8")


def get(path):
    with urllib.request.urlopen(BASE + path, timeout=30) as res:
        return json.load(res)


def classify(cases):
    labels = sorted({c["expected"] for c in cases} | {c["predicted"] for c in cases})
    per_class = {}
    for label in labels:
        tp = sum(c["expected"] == label and c["predicted"] == label for c in cases)
        fp = sum(c["expected"] != label and c["predicted"] == label for c in cases)
        fn = sum(c["expected"] == label and c["predicted"] != label for c in cases)
        precision = tp / (tp + fp) if tp + fp else 0
        recall = tp / (tp + fn) if tp + fn else 0
        per_class[label] = dict(support=tp + fn, precision=precision, recall=recall,
            f1=2 * precision * recall / (precision + recall) if precision + recall else 0)
    correct = sum(c["expected"] == c["predicted"] for c in cases)
    return dict(total=len(cases), correct=correct, accuracy=correct / len(cases),
                macro_f1=statistics.mean(c["f1"] for c in per_class.values()), per_class=per_class,
                llm_failed=sum(c["llm_failed"] for c in cases),
                errors=[c for c in cases if c["expected"] != c["predicted"]])


def summarize(run):
    intents = {}
    all_cases = []
    for split in ("开发", "验收"):
        cases = []
        for p in sorted(run.glob(f"意图{split}_*结果.json")):
            cases.extend(read(p)["results"][0]["metadata"]["cases"])
        if cases:
            intents[split] = classify(cases)
            all_cases.extend(cases)
    if all_cases:
        intents["全部"] = classify(all_cases)
    dialogs = []
    for p in sorted(run.glob("对话_D*结果.json")):
        dialogs.extend(read(p)["results"])
    summary = dict(intent=intents, dialog={})
    if dialogs:
        valid = [r for r in dialogs if not r["metadata"]["judge_failed"]]
        groups = {}
        for r in dialogs:
            groups.setdefault(r["metadata"]["conv_id"], []).append(r)
        summary["dialog"] = dict(
            total=len(dialogs), valid=len(valid), judge_failed=len(dialogs) - len(valid),
            coverage=len(valid) / len(dialogs), passed=sum(r["passed"] for r in dialogs),
            pass_rate=sum(r["passed"] for r in dialogs) / len(dialogs),
            group_total=len(groups), group_passed=sum(all(r["passed"] for r in rs) for rs in groups.values()),
            avg_scores={k: statistics.mean(r["scores"][k] for r in valid)
                        for k in ("relevance", "accuracy", "completeness", "helpfulness", "overall")} if valid else {},
            first_attempt_failed=sum(not r["metadata"]["judge_attempts"][0]["valid"] for r in dialogs),
            retries=sum(len(r["metadata"]["judge_attempts"]) > 1 for r in dialogs),
            check_gate_rejected=sum(r["scores"].get("overall", 0) >= 0.75 and not r["passed"] for r in valid),
            failed_ids=[r["test_id"] for r in dialogs if not r["passed"]])
    save(run / "汇总.json", summary)
    return summary


def main():
    frozen = read(DATA / "冻结清单.json")
    for name, expected in frozen["sha256"].items():
        if hashlib.sha256((DATA / name).read_bytes()).hexdigest() != expected:
            raise SystemExit(f"冻结文件变化，停止: {name}")
    run = HERE / "结果" / (datetime.now().strftime("%Y%m%d-%H%M%S") + "-v2")
    run.mkdir(parents=True, exist_ok=False)
    shutil.copytree(DATA, run / "输入")
    shutil.copy2(__file__, run / "运行脚本.py")
    print(f"结果目录: {run}", flush=True)
    save(run / "启动健康状态.json", get("/health"))
    save(run / "Skills状态.json", get("/skills"))
    save(run / "开始监控.json", get("/monitor"))
    # 仅读取允许公开的配置和源码摘要；不导出环境变量或密钥。
    code = '''import os,json,hashlib,pathlib,importlib.metadata,chromadb
root=pathlib.Path('/app')
# 评测目录已包含样本和历史源码，只核对实际运行的评测器，避免递归复制历史结果。
paths=[p for folder in ['api','core','agents','mcp','memory','monitor','skills'] for p in (root/folder).rglob('*') if p.suffix in ['.py','.md']]
paths.append(root/'evaluation/evaluator.py')
client=chromadb.HttpClient(host=os.getenv('CHROMA_HOST','chromadb'),port=int(os.getenv('CHROMA_PORT','8000')),settings=chromadb.Settings(anonymized_telemetry=False))
kb=client.get_collection('knowledge_base').get(include=['documents','metadatas'])
print(json.dumps({'model':os.getenv('ANTHROPIC_MODEL'),'knowledge':kb,'code_sha256':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},'dependencies':{k:importlib.metadata.version(k) for k in ['anthropic','fastapi','pydantic','chromadb']}},ensure_ascii=False))
'''
    runtime = json.loads(docker("exec", "-T", "backend", "python", "-c", code))
    save(run / "运行时配置与知识快照.json", runtime)
    ref = read(DATA / "对话质量/参考知识快照.json")["documents"]
    actual = sorted((m["title"], d) for m, d in zip(runtime["knowledge"]["metadatas"], runtime["knowledge"]["documents"]))
    if actual != sorted((d["title"], d["content"]) for d in ref):
        raise SystemExit("实时知识库与冻结参考不一致，停止评测")
    for name, digest in runtime["code_sha256"].items():
        source = ROOT / "backend" / name
        if not source.exists() or hashlib.sha256(source.read_bytes()).hexdigest() != digest:
            raise SystemExit(f"本地与容器源码不一致: {name}")
        target = run / "源码" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    manifest = dict(started_at=datetime.now().astimezone().isoformat(), runs=[],
        dataset="v2", model=runtime["model"], knowledge_matches=True,
        judge=dict(max_tokens=2048, temperature=0, max_parse_retries=1,
                   threshold=0.75, require_all_checks=True, failed_score=None),
        cache_policy="后端进程全新启动；每条意图仅运行一次；对话工具保留默认300秒TTL缓存",
        baseline="禁用比较及写入", tuning="本轮未调节业务提示词、模型或识别策略")
    save(run / "运行记录.json", manifest)
    jobs = []
    for split in ("开发", "验收"):
        cases = read(DATA / "意图识别" / f"意图{split}集请求.json")["intent_cases"]
        for i in range(0, len(cases), 25):
            jobs.append((f"意图{split}_{i // 25 + 1:02d}", dict(intent_cases=cases[i:i+25], dialog_cases=[])))
    for case in read(DATA / "对话质量/对话评测请求.json")["dialog_cases"]:
        jobs.append((f"对话_{case['id']}", dict(intent_cases=[], dialog_cases=[case])))
    for name, payload in jobs:
        payload["use_baseline"] = False
        entry = dict(name=name, started_at=datetime.now().astimezone().isoformat(), status="running")
        manifest["runs"].append(entry)
        save(run / "运行记录.json", manifest)
        save(run / f"{name}请求.json", payload)
        print(f"开始 {name}", flush=True)
        start = time.monotonic()
        try:
            req = urllib.request.Request(BASE + "/eval/run", data=json.dumps(payload, ensure_ascii=False).encode(),
                headers={"Content-Type": "application/json; charset=utf-8"}, method="POST")
            # 请求失败不整批重跑，避免把重复尝试混入样本成绩。
            with urllib.request.urlopen(req, timeout=2400) as res:
                raw = res.read()
            (run / f"{name}结果.json").write_bytes(raw)
            entry.update(status="completed", seconds=round(time.monotonic()-start, 2))
            summarize(run)
        except Exception as ex:
            entry.update(status="failed", error=type(ex).__name__, seconds=round(time.monotonic()-start, 2))
            save(run / "运行记录.json", manifest)
            print(json.dumps(entry, ensure_ascii=False), flush=True)
            raise SystemExit(1)
        save(run / "运行记录.json", manifest)
        print(json.dumps(entry, ensure_ascii=False), flush=True)
    manifest["completed_at"] = datetime.now().astimezone().isoformat()
    save(run / "运行记录.json", manifest)
    save(run / "结束监控.json", get("/monitor"))
    print("本轮全部完成", flush=True)


if __name__ == "__main__":
    main()
