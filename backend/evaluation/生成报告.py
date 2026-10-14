"""从v2逐批原始结果重新汇总指标、错例和对话证据；不调用模型、不改原始响应。"""

import json
import statistics
import sys
from collections import Counter
from pathlib import Path

from 运行评测 import read, save, classify


def main(run):
    # 新结果采用分类目录；旧结果保留原始输入布局，仍可生成报告。
    inputs = run / "输入"
    master_path = inputs / "共用资料/样本与标注.json"
    master = read(master_path if master_path.exists() else inputs / "样本与标注.json")
    sample_by_message = {c["message"]: c for c in master["intent_samples"]}
    intents, all_cases = {}, []
    for split in ("开发", "验收"):
        cases = []
        for p in sorted(run.glob(f"意图{split}_*结果.json")):
            for raw_case in read(p)["results"][0]["metadata"]["cases"]:
                # 冻结输入将ID置于context.case_id；按唯一原文关联，保留原始API响应不变。
                case = dict(raw_case, id=sample_by_message[raw_case["message"]]["id"])
                assert case["expected"] == sample_by_message[case["message"]]["expected_intent"]
                cases.append(case)
        intents[split] = classify(cases)
        all_cases.extend(cases)
    intents["全部"] = classify(all_cases)
    dialogs = [r for p in sorted(run.glob("对话_D*结果.json")) for r in read(p)["results"]]
    assert len(all_cases) == 200 and len(dialogs) == 60, "未完整运行，不能生成最终报告"
    assert len({c['id'] for c in all_cases}) == 200
    assert len({r['test_id'] for r in dialogs}) == 60
    dialog_path = inputs / "对话质量/对话评测请求.json"
    dialog_input = read(dialog_path if dialog_path.exists() else inputs / "对话评测请求.json")
    expected_dialogs = {c["id"]: c for c in dialog_input["dialog_cases"]}
    for result in dialogs:
        meta = result["metadata"]
        sample = expected_dialogs[result["test_id"].split("_turn_")[0]]
        assert meta["question"] == sample["turns"][meta["turn"]]
        if meta["judge_failed"]:
            assert result["scores"] == {} and not result["passed"]
        else:
            assert [c["criterion"] for c in meta["checks"]] == sample["checks"][meta["turn"]]
            mean = statistics.mean(result["scores"][k] for k in ("relevance", "accuracy", "completeness", "helpfulness"))
            assert abs(mean - result["scores"]["overall"]) < 1e-10
            assert result["passed"] == (mean >= .75 and all(c["passed"] for c in meta["checks"]))
    valid = [r for r in dialogs if not r["metadata"]["judge_failed"]]
    group_ids = {r["metadata"]["conv_id"] for r in dialogs}
    checks = [c for r in valid for c in r["metadata"]["checks"]]
    dialog = dict(total=60, valid=len(valid), coverage=len(valid)/60,
        passed=sum(r["passed"] for r in dialogs), pass_rate=sum(r["passed"] for r in dialogs)/60,
        judge_failed=60-len(valid), group_total=len(group_ids),
        group_passed=sum(all(r["passed"] for r in dialogs if r["metadata"]["conv_id"] == gid) for gid in group_ids),
        avg_scores={k: statistics.mean(r["scores"][k] for r in valid)
                    for k in ("relevance", "accuracy", "completeness", "helpfulness", "overall")} if valid else {},
        first_attempt_failed=sum(not r["metadata"]["judge_attempts"][0]["valid"] for r in dialogs),
        retries=sum(len(r["metadata"]["judge_attempts"]) > 1 for r in dialogs),
        check_gate_rejected=sum(r["scores"].get("overall", 0) >= .75 and not r["passed"] for r in valid),
        checks_total=len(checks), checks_passed=sum(c["passed"] for c in checks),
        failed_ids=[r["test_id"] for r in dialogs if not r["passed"]])
    summary = dict(intent=intents, dialog=dialog)
    save(run / "汇总.json", summary)
    save(run / "意图逐条预测.json", all_cases)
    lines = ["# ServiceWeave v2 本轮评测报告", "", "## 范围与口径", "",
        "本轮使用冻结v2合成样本：19类意图200条（开发150、预留验收50），对话30组60轮。业务配置保持不变，未根据本轮错例调参；不引用v1结果。",
        "参考知识只传给Judge，未传给业务Agent；运行知识库6篇文档与冻结参考逐字一致。实际调用Orchestrator并传入多轮历史，不覆盖/chat持久化记忆读写。",
        "模型配置名为deepseek-flash；Judge温度0、输出预算2048。四维均分≥0.75且该轮全部关键检查项满足才通过。评分结构错误最多重试一次，低分不重试。最终评分失败不参与均分，但仍计入60轮的通过率分母。", "",
        "## 意图识别", "", "|集合|正确/总数|Accuracy|Macro-F1|LLM失败兜底|", "|---|---:|---:|---:|---:|"]
    for name, item in intents.items():
        lines.append(f"|{name}|{item['correct']}/{item['total']}|{item['accuracy']:.2%}|{item['macro_f1']:.4f}|{item['llm_failed']}|")
    lines += ["", "Macro-F1从每类P/R/F1重新计算；全部指标从200条预测重算，不是两组Macro-F1的平均值。API意图聚合结果的pass_rate不是样本准确率，本报告不采用它。",
        "", "### 全部样本逐类指标", "", "|类别|样本数|Precision|Recall|F1|", "|---|---:|---:|---:|---:|"]
    for label, item in intents["全部"]["per_class"].items():
        lines.append(f"|{label}|{item['support']}|{item['precision']:.4f}|{item['recall']:.4f}|{item['f1']:.4f}|")
    lines += ["", "### 全部错例", "", "|ID|输入|标注|预测|LLM失败|", "|---|---|---|---|---|"]
    for c in intents["全部"]["errors"]:
        lines.append(f"|{c['id']}|{c['message']}|{c['expected']}|{c['predicted']}|{c['llm_failed']}|")
    lines += ["", "## 对话质量", "",
        f"- 逐轮通过：{dialog['passed']}/60（{dialog['pass_rate']:.2%}）。",
        f"- 有效评分：{dialog['valid']}/60（{dialog['coverage']:.2%}）；最终评分失败{dialog['judge_failed']}轮。",
        f"- 首次评分失败{dialog['first_attempt_failed']}轮，实际重试{dialog['retries']}轮。",
        f"- 所有轮次均通过的对话：{dialog['group_passed']}/30。",
        f"- 均分达标但被关键检查项拦截：{dialog['check_gate_rejected']}轮。",
        f"- 有效评分中的关键项通过：{dialog['checks_passed']}/{dialog['checks_total']}；这不是轮次通过率。",
        "- 有效评分均值：" + "、".join(f"{k}={v:.4f}" for k, v in dialog["avg_scores"].items()) + "。",
        "", "## 证据与限制", "",
        "冻结输入、原始预测、回复、Judge原文/停止原因/用量、逐项理由、源码快照和依赖版本均保留在本目录。Judge失败只保存异常类型，避免导出上游敏感信息。",
        "合成样本未经独立人工盲标；预留验收集与开发集来自同一作者。一次离线运行不能代表线上效果或重复稳定性。Judge与业务Agent采用同一配置模型，存在同源评价偏差；关键项也是模型判定，需要抽查。",
        "本轮没有业务优化前后对照，因此报告只记录当前实测成绩及评测机制，不写提升幅度。",
        "", "## 实际发现与运行核对", "",
        (run / "本轮发现.md").read_text(encoding="utf-8") if (run / "本轮发现.md").exists() else "本次未提供单独的结果审阅说明。",
        "", "## 全部对话与逐轮判定", ""]
    for r in dialogs:
        m = r["metadata"]
        lines += [f"### {r['test_id']} · {'通过' if r['passed'] else '未通过'}", "",
            f"用户：{m['question']}", "", "回复：", "", m["response"], "",
            "评分：" + json.dumps(r["scores"], ensure_ascii=False), ""]
        if m["judge_failed"]:
            lines.append(f"Judge失败：{m['judge_error']}。")
        for c in m["checks"]:
            lines.append(f"- {'通过' if c['passed'] else '未通过'}：{c['criterion']}；依据：{c['reason']}")
        lines.append("")
    (run / "评测报告.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"intent": {k: {x:v[x] for x in ['total','correct','accuracy','macro_f1','llm_failed']}
          for k,v in intents.items()}, "dialog": dialog}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
