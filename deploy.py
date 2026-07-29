#!/usr/bin/env python3
"""
toolkit → 目标项目 自动部署脚本

将 toolkit 仓库中的 skills、references、instructions 自动同步到目标项目。
所有已部署的项目路径自动记录在 deploy-state.json 中，无需预设。

支持 Windows / macOS / Linux。

用法:
    python deploy.py                              # 交互模式，选择/输入目标项目
    python deploy.py --target <路径>               # 部署到指定项目
    python deploy.py --target <路径> --dry-run     # 预览模式，不实际复制
    python deploy.py --target <路径> --update      # 更新模式（覆盖已有文件）
    python deploy.py --target <路径> --force       # 强制重新部署
    python deploy.py --list-deployed               # 列出所有已部署项目
"""

import argparse
import json
import os
import re
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


# ============================================================
# 常量
# ============================================================

# 部署状态文件名（存放在 toolkit 根目录）
DEPLOY_STATE_FILE = "deploy-state.json"


# VS Code 用户级 prompts 目录（instructions 也会部署到这里）
def _get_vscode_prompts_dir() -> str:
    """跨平台获取 VS Code prompts 目录。"""
    if sys.platform == "win32" and "APPDATA" in os.environ:
        base = os.environ["APPDATA"]
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
    return os.path.join(base, "Code", "User", "prompts")

VSCODE_PROMPTS_DIR: str = _get_vscode_prompts_dir()


# ============================================================
# 部署状态管理
# ============================================================

def _stateFilePath() -> Path:
    return getToolkitRoot() / DEPLOY_STATE_FILE


def _normalizePath(p: str) -> str:
    """统一路径格式：绝对路径 + 系统原生分隔符（Windows 用反斜杠）。"""
    return os.path.normpath(os.path.abspath(p))


def loadDeployState() -> dict:
    """加载部署状态文件，不存在时返回空字典。
    自动合并因路径格式不同导致的重复条目（以最新时间为准）。
    """
    fp = _stateFilePath()
    if fp.exists():
        try:
            with open(fp, "r", encoding="utf-8") as f:
                raw: dict = json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}

        # 按标准化路径去重合并
        merged: dict = {}
        for path, info in raw.items():
            norm = _normalizePath(path)
            if norm in merged:
                # 保留较新的记录
                old = merged[norm].get("last_deployed", 0)
                new = info.get("last_deployed", 0)
                if new > old:
                    merged[norm] = info
            else:
                merged[norm] = info

        # 如果发生了合并，写回文件
        if len(merged) != len(raw):
            saveDeployState(merged)

        return merged
    return {}


def saveDeployState(state: dict) -> None:
    """保存部署状态到文件。"""
    fp = _stateFilePath()
    fp.parent.mkdir(parents=True, exist_ok=True)
    with open(fp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def recordDeployment(targetPath: str, stats: dict, name: str = "") -> None:
    """
    记录一次部署到状态文件。

    targetPath: 目标项目的绝对路径
    stats: 统计信息，如 {"skills": 10, "references": 3}
    name: 项目可读名称（可选，从目录名自动推断）
    """
    resolved = _normalizePath(targetPath)
    state = loadDeployState()
    state[resolved] = {
        "name": name or Path(resolved).name,
        "last_deployed": time.time(),
        "last_deployed_iso": datetime.now().isoformat(),
        "stats": stats,
    }
    saveDeployState(state)


def isPreviouslyDeployed(targetPath: str) -> Optional[dict]:
    """检查目标路径是否曾部署过。返回状态记录或 None。"""
    state = loadDeployState()
    resolved = _normalizePath(targetPath)
    return state.get(resolved)


def listDeployedProjects() -> dict:
    """
    从 deploy-state.json 读取所有已部署项目。
    自动清理路径已不存在的失效条目。
    返回 { "可读名称": {"path": "绝对路径", "last_deployed_iso": "...", ...} }
    按最后部署时间倒序排列。
    """
    pruneStaleEntries()
    state = loadDeployState()
    # 按时间倒序
    items = sorted(
        state.items(),
        key=lambda kv: kv[1].get("last_deployed", 0),
        reverse=True,
    )
    result = {}
    for path, info in items:
        label = info.get("name", "") or Path(path).name
        result[label] = {
            "path": path,
            "last_deployed_iso": info.get("last_deployed_iso", "未知"),
        }
    return result


def pruneStaleEntries() -> int:
    """
    清理 deploy-state.json 中路径已不存在的条目。
    返回被清理的条目数。
    """
    state = loadDeployState()
    stale = [path for path in state if not Path(path).exists()]
    if not stale:
        return 0

    for path in stale:
        name = state[path].get("name", Path(path).name)
        print(f"  [CLEAN] 路径不存在，已从记录中移除: {name} ({path})")
        del state[path]
    saveDeployState(state)
    return len(stale)


def formatTimestamp(ts: float) -> str:
    """将时间戳格式化为可读字符串。"""
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


# ============================================================
# 核心逻辑
# ============================================================

def getToolkitRoot() -> Path:
    """获取 toolkit 仓库根目录（即本脚本所在目录）。"""
    return Path(__file__).resolve().parent


def resolveTarget(targetArg: str | None) -> Path:
    """
    解析目标项目路径。

    数据来源（按优先级）:
      1. --target 参数（直接路径或已记录的名称/路径）
      2. 交互模式 — 从 deploy-state.json 读取已部署项目列表
    """
    if targetArg:
        p = Path(targetArg)
        if p.exists():
            return p.resolve()
        # 尝试匹配已部署记录中的名称或路径
        deployed = listDeployedProjects()
        for name, info in deployed.items():
            if targetArg.lower() == name.lower() or targetArg.lower() == info["path"].lower():
                candidate = Path(info["path"])
                if candidate.exists():
                    return candidate.resolve()
        print(f"[ERROR] 目标不存在或未记录: {targetArg}")
        # 诊断：是否像 Windows 路径但反斜杠被吞了？
        if re.match(r"^[A-Za-z]:[^\\]", targetArg):
            print(f"  💡 看起来像一个 Windows 路径，但反斜杠丢失了。")
            print(f"     在 PowerShell 中请用引号包裹路径:")
            print(f"       python deploy.py -t \"{targetArg[:2]}{chr(92)}{targetArg[2:]}\"")
            print(f"     或使用正斜杠:")
            print(f"       python deploy.py -t \"{targetArg[:2]}/{targetArg[2:]}\"")
        else:
            print(f"  提示: 先用交互模式 (直接运行 python deploy.py) 部署一次，")
            print(f"        或输入完整路径。")
        sys.exit(1)

    # 交互模式 — 读取已部署项目（自动清理失效条目）
    deployed = listDeployedProjects()

    if deployed:
        print("已部署的目标项目 (deploy-state.json):")
        labels = list(deployed.keys())
        for i, label in enumerate(labels, 1):
            info = deployed[label]
            # 走到这里路径一定存在（pruneStaleEntries 已清理过）
            print(f"  [{i}] {label}  ✅ 上次部署: {info['last_deployed_iso']}")
            print(f"       {info['path']}")
    else:
        print("尚未部署过任何项目。")

    print(f"  [0] 输入新的目标路径")

    try:
        choice = input("\n请选择目标项目 (输入序号): ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\n已取消。")
        sys.exit(0)

    if choice == "0" or not deployed:
        path = input("请输入目标项目路径: ").strip()
        p = Path(path)
        if not p.exists():
            print(f"[ERROR] 路径不存在: {path}")
            sys.exit(1)
        return p.resolve()

    try:
        idx = int(choice) - 1
        if 0 <= idx < len(labels):
            p = Path(deployed[labels[idx]]["path"])
            if not p.exists():
                print(f"[ERROR] 目标目录不存在: {p}")
                sys.exit(1)
            return p.resolve()
    except (ValueError, IndexError):
        pass

    print(f"[ERROR] 无效选择: {choice}")
    sys.exit(1)


def copyDir(
    src: Path,
    dst: Path,
    *,
    update: bool = False,
    dryRun: bool = False,
    exclude: set[str] | None = None,
) -> tuple[int, int]:
    """
    递归复制目录内容。

    返回 (新增/更新数, 跳过数)。
    """
    exclude = exclude or set()
    created = 0
    skipped = 0

    if not src.exists():
        print(f"  [SKIP] 源目录不存在: {src}")
        return 0, 0

    for item in src.iterdir():
        if item.name in exclude:
            continue

        dstItem = dst / item.name

        if item.is_dir():
            c, s = copyDir(item, dstItem, update=update, dryRun=dryRun)
            created += c
            skipped += s
        else:
            if dstItem.exists() and not update:
                skipped += 1
                continue

            if not dryRun:
                dstItem.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dstItem)
            created += 1

    return created, skipped


def deploySkills(
    toolkitRoot: Path,
    targetRoot: Path,
    *,
    update: bool = False,
    dryRun: bool = False,
) -> dict:
    """部署 skills/workflows 和 skills/qt (排除 references)。返回统计。"""
    stats = {}
    print("\n" + "=" * 60)
    print("  [1/3] 部署 Skills")
    print("=" * 60)

    # 1a. workflows
    src = toolkitRoot / "skills" / "workflows"
    dst = targetRoot / ".agents" / "skills"
    print(f"\n  --- 工作流技能 ---")
    print(f"  源: {src}")
    print(f"  目标: {dst}")
    c, s = copyDir(src, dst, update=update, dryRun=dryRun)
    stats["workflows"] = {"copied": c, "skipped": s}
    print(f"  结果: {c} 个文件已{'预览' if dryRun else '复制'}, {s} 个跳过")

    # 1b. qt skills (排除 references/)
    src = toolkitRoot / "skills" / "qt"
    dst = targetRoot / ".agents" / "skills"
    print(f"\n  --- Qt 技能 ---")
    print(f"  源: {src}")
    print(f"  目标: {dst}")
    c, s = copyDir(src, dst, update=update, dryRun=dryRun, exclude={"references"})
    stats["qt_skills"] = {"copied": c, "skipped": s}
    print(f"  结果: {c} 个文件已{'预览' if dryRun else '复制'}, {s} 个跳过")
    return stats


def deployReferences(
    toolkitRoot: Path,
    targetRoot: Path,
    *,
    update: bool = False,
    dryRun: bool = False,
) -> dict:
    """部署 references（审查清单/参考资料）。返回统计。"""
    print("\n" + "=" * 60)
    print("  [2/3] 部署 References")
    print("=" * 60)

    src = toolkitRoot / "skills" / "qt" / "references"
    dst = targetRoot / ".agents" / "references"
    print(f"\n  源: {src}")
    print(f"  目标: {dst}")
    c, s = copyDir(src, dst, update=update, dryRun=dryRun)
    print(f"  结果: {c} 个文件已{'预览' if dryRun else '复制'}, {s} 个跳过")
    return {"references": {"copied": c, "skipped": s}}


def deployInstructions(
    toolkitRoot: Path,
    targetRoot: Path,
    *,
    update: bool = False,
    dryRun: bool = False,
) -> dict:
    """部署 instructions 到项目 .github/instructions。返回统计。"""
    print("\n" + "=" * 60)
    print("  [3/3] 部署 Instructions")
    print("=" * 60)

    src = toolkitRoot / "instructions"

    # 项目级 .github/instructions/
    dstProject = targetRoot / ".github" / "instructions"
    print(f"\n  源: {src}")
    print(f"  目标: {dstProject}")
    c, s = copyDir(src, dstProject, update=update, dryRun=dryRun)
    print(f"  结果: {c} 个文件已{'预览' if dryRun else '复制'}, {s} 个跳过")
    return {"instructions": {"copied": c, "skipped": s}}


def cleanTarget(targetRoot: Path, *, dryRun: bool = False) -> None:
    """删除目标项目中由部署脚本创建的文件/目录。"""
    dirsToRemove = [
        targetRoot / ".agents",
        targetRoot / ".github" / "instructions",
    ]
    for d in dirsToRemove:
        if d.exists():
            if dryRun:
                print(f"  [DRY-RUN] 将会删除: {d}")
            else:
                shutil.rmtree(d)
                print(f"  已删除旧目录: {d}")
        else:
            print(f"  无需清理: {d}")


def main():
    parser = argparse.ArgumentParser(
        description="toolkit → 目标项目 自动部署脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python deploy.py                              # 交互模式（从 state 列出已部署项目）
  python deploy.py --target <路径>               # 部署到指定项目
  python deploy.py --target keeprix_dev          # 按已记录的名称匹配
  python deploy.py --target <路径> --dry-run     # 预览模式
  python deploy.py --target <路径> --update      # 覆盖已有文件
  python deploy.py --target <路径> --force       # 强制重新部署
  python deploy.py --list-deployed               # 列出所有已部署项目
        """,
    )
    parser.add_argument(
        "-t", "--target",
        help="目标项目路径，或已在 deploy-state.json 中记录的名称/路径",
    )
    parser.add_argument(
        "-u", "--update",
        action="store_true",
        help="更新模式：覆盖已存在的文件（默认跳过）",
    )
    parser.add_argument(
        "-f", "--force",
        action="store_true",
        help=(
            "强制重新部署：先删除目标项目中的 .agents/ 和 .github/instructions/，"
            "再重新复制所有文件。适用于 toolkit 重大更新后需要完全刷新的场景。"
        ),
    )
    parser.add_argument(
        "-n", "--dry-run",
        action="store_true",
        help="预览模式：只显示将要执行的操作，不实际复制",
    )
    parser.add_argument(
        "--no-vscode",
        action="store_true",
        help="跳过 VS Code 全局 prompts 部署",
    )
    parser.add_argument(
        "--list-deployed",
        action="store_true",
        help="列出所有已部署项目及其路径、上次部署时间，然后退出",
    )

    args = parser.parse_args()

    toolkitRoot = getToolkitRoot()

    # --list-deployed: 只列出状态，不执行部署
    if args.list_deployed:
        print(f"Toolkit 根目录: {toolkitRoot}")
        deployed = listDeployedProjects()
        if deployed:
            print(f"\n已部署的项目 ({len(deployed)} 个):")
            for name, info in deployed.items():
                exists = "✓" if Path(info["path"]).exists() else "✗"
                print(f"  {name}")
                print(f"    路径: {info['path']}  {exists}")
                print(f"    上次部署: {info['last_deployed_iso']}")
        else:
            print("\n尚未部署过任何项目。")
            print("运行 python deploy.py 进入交互模式开始部署。")
        return

    # --force: 自动启用 --update，并先删除目标目录再重新部署
    effectiveUpdate = args.update or args.force
    if args.force:
        print("[INFO] --force 模式：将清除目标项目中的旧文件再重新部署。")
        cleanTarget(targetRoot, dryRun=args.dry_run)

    print(f"Toolkit 根目录: {toolkitRoot}")

    targetRoot = resolveTarget(args.target)
    targetName = targetRoot.name
    print(f"目标项目: {targetRoot}")

    if args.dry_run:
        print("\n*** DRY-RUN 模式 — 不会实际修改文件 ***")

    mode = "强制部署" if args.force else ("更新" if args.update else "安装")

    allStats = {}
    allStats.update(
        deploySkills(toolkitRoot, targetRoot, update=effectiveUpdate, dryRun=args.dry_run)
    )
    allStats.update(
        deployReferences(toolkitRoot, targetRoot, update=effectiveUpdate, dryRun=args.dry_run)
    )
    allStats.update(
        deployInstructions(toolkitRoot, targetRoot, update=effectiveUpdate, dryRun=args.dry_run)
    )

    # VS Code prompts
    vscodeStats = {}
    if not args.no_vscode:
        print("\n" + "=" * 60)
        print("  [附] VS Code 全局 Prompts")
        print("=" * 60)
        src = toolkitRoot / "instructions"
        dstVscode = Path(VSCODE_PROMPTS_DIR)
        print(f"\n  源: {src}")
        print(f"  目标: {dstVscode}")
        if dstVscode.exists():
            c, s = copyDir(src, dstVscode, update=effectiveUpdate, dryRun=args.dry_run)
            vscodeStats = {"vscode_prompts": {"copied": c, "skipped": s}}
            print(f"  结果: {c} 个文件已{'预览' if args.dry_run else '复制'}, {s} 个跳过")
        else:
            print(f"  [SKIP] 目录不存在: {dstVscode}")
            print(f"  提示: 请确认 VS Code 已安装，或使用 --no-vscode 跳过此步骤")

    # 记录部署状态（仅在实际部署后，非 dry-run）
    if not args.dry_run:
        recordDeployment(str(targetRoot), {**allStats, **vscodeStats}, name=targetName)

        # 打印汇总
        totalCopied = sum(
            v.get("copied", 0) for v in {**allStats, **vscodeStats}.values()
        )
        totalSkipped = sum(
            v.get("skipped", 0) for v in {**allStats, **vscodeStats}.values()
        )
        print(f"\n{'=' * 60}")
        print(f"  部署完成 ({mode}模式)")
        print(f"  新增/更新: {totalCopied} 个文件 | 跳过: {totalSkipped} 个文件")
        print(f"{'=' * 60}")
    else:
        print(f"\n{'=' * 60}")
        print(f"  部署完成 ({mode}模式) [DRY-RUN — 未实际修改]")
        print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
