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
import re
import shutil
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


# ============================================================
# 常量
# ============================================================

DEPLOY_STATE_FILE = "deploy-state.json"


# ============================================================
# 类型定义
# ============================================================


@dataclass
class CopyResult:
    """copy_dir 的返回结果。"""

    copied: int = 0
    skipped: int = 0


@dataclass
class DeployRecord:
    """deploy-state.json 中的单条记录。"""

    name: str
    path: str
    last_deployed_iso: str


# ============================================================
# 部署状态管理
# ============================================================


def _state_file_path() -> Path:
    """返回 deploy-state.json 的完整路径。"""
    return _get_toolkit_root() / DEPLOY_STATE_FILE


def _normalize_path(p: str) -> str:
    """统一路径格式：绝对路径 + 系统原生分隔符。"""
    return str(Path(p).resolve())


def load_deploy_state() -> dict[str, Any]:
    """加载部署状态文件，不存在时返回空字典。

    自动合并因路径格式不同导致的重复条目（以最新时间为准）。
    """
    fp = _state_file_path()
    if not fp.exists():
        return {}

    try:
        with open(fp, "r", encoding="utf-8") as f:
            raw: dict[str, Any] = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}

    merged: dict[str, Any] = {}
    for path, info in raw.items():
        norm = _normalize_path(path)
        if norm in merged:
            old_ts = merged[norm].get("last_deployed", 0)
            new_ts = info.get("last_deployed", 0)
            if new_ts > old_ts:
                merged[norm] = info
        else:
            merged[norm] = info

    if len(merged) != len(raw):
        save_deploy_state(merged)

    return merged


def save_deploy_state(state: dict[str, Any]) -> None:
    """保存部署状态到文件。"""
    fp = _state_file_path()
    fp.parent.mkdir(parents=True, exist_ok=True)
    with open(fp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def record_deployment(
    target_path: str,
    stats: dict[str, Any],
    name: str = "",
) -> None:
    """记录一次部署到状态文件。"""
    resolved = _normalize_path(target_path)
    state = load_deploy_state()
    state[resolved] = {
        "name": name or Path(resolved).name,
        "last_deployed": time.time(),
        "last_deployed_iso": datetime.now().isoformat(),
        "stats": stats,
    }
    save_deploy_state(state)


def is_previously_deployed(target_path: str) -> dict[str, Any] | None:
    """检查目标路径是否曾部署过。返回状态记录或 None。"""
    state = load_deploy_state()
    resolved = _normalize_path(target_path)
    return state.get(resolved)


def prune_stale_entries() -> int:
    """清理 deploy-state.json 中路径已不存在的条目。返回被清理的条目数。"""
    state = load_deploy_state()
    stale = [path for path in state if not Path(path).exists()]
    if not stale:
        return 0

    for path in stale:
        name = state[path].get("name", Path(path).name)
        print(f"  [CLEAN] 路径不存在，已从记录中移除: {name} ({path})")
        del state[path]
    save_deploy_state(state)
    return len(stale)


def list_deployed_projects() -> dict[str, DeployRecord]:
    """从 deploy-state.json 读取所有已部署项目。

    自动清理失效条目，返回按时间倒序排列的 DeployRecord 字典。
    """
    prune_stale_entries()
    state = load_deploy_state()

    items = sorted(
        state.items(),
        key=lambda kv: kv[1].get("last_deployed", 0),
        reverse=True,
    )

    result: dict[str, DeployRecord] = {}
    for path, info in items:
        label: str = info.get("name", "") or Path(path).name
        result[label] = DeployRecord(
            name=label,
            path=path,
            last_deployed_iso=info.get("last_deployed_iso", "未知"),
        )
    return result


# ============================================================
# 路径解析
# ============================================================


def _get_toolkit_root() -> Path:
    """获取 toolkit 仓库根目录（即本脚本所在目录）。"""
    return Path(__file__).resolve().parent


def _pick_from_list(deployed: dict[str, DeployRecord]) -> Path:
    """交互模式：从已部署列表中选择目标项目，或手动输入新路径。"""
    labels = list(deployed.keys())

    if deployed:
        print("已部署的目标项目 (deploy-state.json):")
        for i, label in enumerate(labels, 1):
            record = deployed[label]
            print(f"  [{i}] {label}  [+] 上次部署: {record.last_deployed_iso}")
            print(f"       {record.path}")
    else:
        print("尚未部署过任何项目。")

    print("  [0] 输入新的目标路径")

    try:
        choice = input("\n请选择目标项目 (输入序号): ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\n已取消。")
        sys.exit(0)

    if choice == "0" or not deployed:
        return _prompt_manual_path()

    try:
        idx = int(choice) - 1
        if 0 <= idx < len(labels):
            p = Path(deployed[labels[idx]].path)
            if p.exists():
                return p.resolve()
            print(f"[ERROR] 目标目录不存在: {p}")
            sys.exit(1)
    except (ValueError, IndexError):
        pass

    print(f"[ERROR] 无效选择: {choice}")
    sys.exit(1)


def _prompt_manual_path() -> Path:
    """交互模式：提示用户手动输入路径。"""
    path = input("请输入目标项目路径: ").strip()
    p = Path(path)
    if p.exists():
        return p.resolve()
    print(f"[ERROR] 路径不存在: {path}")
    sys.exit(1)


def _try_match_record(
    target_arg: str,
    deployed: dict[str, DeployRecord],
) -> Path | None:
    """尝试将 --target 参数匹配到已部署记录的路径。"""
    for record in deployed.values():
        if target_arg.lower() in (record.name.lower(), record.path.lower()):
            candidate = Path(record.path)
            if candidate.exists():
                return candidate.resolve()
    return None


def _diagnose_bad_target(target_arg: str) -> None:
    """诊断 --target 参数为何无法解析。"""
    print(f"[ERROR] 目标不存在或未记录: {target_arg}")

    if re.match(r"^[A-Za-z]:[^\\]", target_arg):
        print("  [!] 看起来像一个 Windows 路径，但反斜杠丢失了。")
        print("     在 PowerShell 中请用引号包裹路径:")
        print(f"       python deploy.py -t \"{target_arg[:2]}\\{target_arg[2:]}\"")
        print("     或使用正斜杠:")
        print(f"       python deploy.py -t \"{target_arg[:2]}/{target_arg[2:]}\"")
    else:
        print("  提示: 先用交互模式 (python deploy.py) 部署一次，")
        print("        或输入完整路径。")


def _prompt_mode() -> tuple[bool, bool]:
    """交互模式：提示用户选择部署模式。返回 (force, update)。"""
    print("\n部署模式:")
    print("  [1] 安装（跳过已有文件，默认）")
    print("  [2] 更新（覆盖已有文件）")
    print("  [3] 强制刷新（先删除旧目录再重新复制）")

    choice = input("\n请选择部署模式 (输入序号，直接回车默认 1): ").strip()

    match choice:
        case "2": return (False, True)
        case "3": return (True, False)
        case _:   return (False, False)


def resolve_target(target_arg: str | None) -> Path:
    """解析目标项目路径。

    数据来源（按优先级）:
      1. --target 参数（直接路径或已记录的名称/路径）
      2. 交互模式 — 从 deploy-state.json 读取已部署项目列表
    """
    if target_arg is not None:
        p = Path(target_arg)
        if p.exists():
            return p.resolve()

        deployed = list_deployed_projects()
        matched = _try_match_record(target_arg, deployed)
        if matched is not None:
            return matched

        _diagnose_bad_target(target_arg)
        sys.exit(1)

    deployed = list_deployed_projects()
    return _pick_from_list(deployed)


# ============================================================
# 文件复制
# ============================================================


def copy_dir(
    src: Path,
    dst: Path,
    *,
    update: bool = False,
    dry_run: bool = False,
    exclude: set[str] | None = None,
) -> CopyResult:
    """递归复制目录内容。"""
    exclude_set: set[str] = exclude or set()
    result = CopyResult()

    if not src.exists():
        print(f"  [SKIP] 源目录不存在: {src}")
        return result

    for item in src.iterdir():
        if item.name in exclude_set:
            continue

        dst_item = dst / item.name

        if item.is_dir():
            sub = copy_dir(
                item, dst_item,
                update=update, dry_run=dry_run, exclude=exclude,
            )
            result.copied += sub.copied
            result.skipped += sub.skipped
        else:
            if dst_item.exists() and not update:
                result.skipped += 1
                continue

            if not dry_run:
                dst_item.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dst_item)
            result.copied += 1

    return result


# ============================================================
# 部署步骤
# ============================================================


def _print_step(number: str, title: str) -> None:
    """打印步骤标题。"""
    print(f"\n{'=' * 60}")
    print(f"  [{number}] {title}")
    print("=" * 60)


def _print_copy_result(
    result: CopyResult,
    dry_run: bool,
) -> None:
    """打印复制结果。"""
    action = "预览" if dry_run else "复制"
    print(f"  结果: {result.copied} 个文件已{action}, {result.skipped} 个跳过")


def _collect_copy_stats(
    key: str,
    src: Path,
    dst: Path,
    *,
    update: bool,
    dry_run: bool,
    exclude: set[str] | None = None,
) -> dict[str, Any]:
    """复制目录并返回统计字典。"""
    r = copy_dir(src, dst, update=update, dry_run=dry_run, exclude=exclude)
    print(f"  源: {src}\n  目标: {dst}")
    _print_copy_result(r, dry_run)
    return {key: {"copied": r.copied, "skipped": r.skipped}}


def deploy_skills(
    toolkit_root: Path,
    target_root: Path,
    *,
    update: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    """部署 skills/workflows 和 skills/qt (排除 references)。"""
    stats: dict[str, Any] = {}
    _print_step("1/3", "部署 Skills")

    print("\n  --- 工作流技能 ---")
    stats.update(
        _collect_copy_stats(
            "workflows",
            toolkit_root / "skills" / "workflows",
            target_root / ".agents" / "skills",
            update=update,
            dry_run=dry_run,
        )
    )

    print("\n  --- Qt 技能 ---")
    stats.update(
        _collect_copy_stats(
            "qt_skills",
            toolkit_root / "skills" / "qt",
            target_root / ".agents" / "skills",
            update=update,
            dry_run=dry_run,
            exclude={"references"},
        )
    )

    return stats


def deploy_references(
    toolkit_root: Path,
    target_root: Path,
    *,
    update: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    """部署 references（审查清单/参考资料）。"""
    _print_step("2/3", "部署 References")
    return _collect_copy_stats(
        "references",
        toolkit_root / "skills" / "qt" / "references",
        target_root / ".agents" / "references",
        update=update,
        dry_run=dry_run,
    )


def deploy_instructions(
    toolkit_root: Path,
    target_root: Path,
    *,
    update: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    """部署 instructions 到项目 .github/instructions。"""
    _print_step("3/3", "部署 Instructions")
    return _collect_copy_stats(
        "instructions",
        toolkit_root / "instructions",
        target_root / ".github" / "instructions",
        update=update,
        dry_run=dry_run,
    )


def clean_target(target_root: Path, *, dry_run: bool = False) -> None:
    """删除目标项目中由部署脚本创建的文件/目录。"""
    dirs_to_remove = [
        target_root / ".agents",
        target_root / ".github" / "instructions",
    ]
    for d in dirs_to_remove:
        if d.exists():
            if dry_run:
                print(f"  [DRY-RUN] 将会删除: {d}")
            else:
                shutil.rmtree(d)
                print(f"  已删除旧目录: {d}")
        else:
            print(f"  无需清理: {d}")


# ============================================================
# 入口
# ============================================================


def _print_summary(
    all_stats: dict[str, Any],
    mode: str,
    dry_run: bool,
) -> None:
    """打印部署完成汇总。"""
    total_copied = sum(v.get("copied", 0) for v in all_stats.values())
    total_skipped = sum(v.get("skipped", 0) for v in all_stats.values())

    suffix = " [DRY-RUN — 未实际修改]" if dry_run else ""
    print(f"\n{'=' * 60}")
    print(f"  部署完成 ({mode}模式){suffix}")
    if not dry_run:
        print(f"  新增/更新: {total_copied} 个文件 | 跳过: {total_skipped} 个文件")
    print("=" * 60)


def _build_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器。"""
    parser = argparse.ArgumentParser(
        description="toolkit → 目标项目 自动部署脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python deploy.py                              # 交互模式
  python deploy.py --target keeprix_dev          # 按名称匹配
  python deploy.py --target <路径>                # 按路径部署
  python deploy.py --target <路径> --dry-run     # 预览
  python deploy.py --target <路径> --update      # 覆盖已有
  python deploy.py --target <路径> --force       # 强制刷新
  python deploy.py --list-deployed               # 列出已部署项目
        """,
    )
    parser.add_argument("-t", "--target", help="目标项目路径或已记录的名称/路径")
    parser.add_argument(
        "-u", "--update", action="store_true",
        help="更新模式：覆盖已存在的文件（默认跳过）",
    )
    parser.add_argument(
        "-f", "--force", action="store_true",
        help="强制重新部署：删除旧目录后再重新复制所有文件",
    )
    parser.add_argument(
        "-n", "--dry-run", action="store_true",
        help="预览模式：只显示将要执行的操作，不实际复制",
    )
    parser.add_argument(
        "--list-deployed", action="store_true",
        help="列出所有已部署项目及其路径、上次部署时间，然后退出",
    )
    return parser


def _run_list_deployed() -> None:
    """处理 --list-deployed 逻辑。"""
    toolkit_root = _get_toolkit_root()
    print(f"Toolkit 根目录: {toolkit_root}")
    deployed = list_deployed_projects()

    if not deployed:
        print("\n尚未部署过任何项目。")
        print("运行 python deploy.py 进入交互模式开始部署。")
        return

    print(f"\n已部署的项目 ({len(deployed)} 个):")
    for record in deployed.values():
        icon = "[+]" if Path(record.path).exists() else "[x]"
        print(f"  {record.name}")
        print(f"    路径: {record.path}  {icon}")
        print(f"    上次部署: {record.last_deployed_iso}")


def _run_deploy(args: argparse.Namespace) -> None:
    """执行部署流程。"""
    toolkit_root = _get_toolkit_root()
    print(f"Toolkit 根目录: {toolkit_root}")

    is_interactive = args.target is None
    target_root = resolve_target(args.target)
    target_name = target_root.name

    print(f"目标项目: {target_root}")

    # 交互模式且未指定 --update/--force 时，让用户选择模式
    if is_interactive and not args.update and not args.force:
        interactive_force, interactive_update = _prompt_mode()
        # 命令行参数优先级高于交互选择
        force = args.force or interactive_force
        update = args.update or interactive_update
    else:
        force = args.force
        update = args.update

    if args.dry_run:
        print("\n*** DRY-RUN 模式 — 不会实际修改文件 ***")

    effective_update = update or force

    if force:
        print("[INFO] 强制刷新模式：将清除目标项目中的旧文件再重新部署。")
        clean_target(target_root, dry_run=args.dry_run)

    match (force, update):
        case (True, _):     mode = "强制部署"
        case (_, True):     mode = "更新"
        case _:             mode = "安装"

    all_stats: dict[str, Any] = {}
    all_stats.update(
        deploy_skills(toolkit_root, target_root, update=effective_update, dry_run=args.dry_run)
    )
    all_stats.update(
        deploy_references(toolkit_root, target_root, update=effective_update, dry_run=args.dry_run)
    )
    all_stats.update(
        deploy_instructions(toolkit_root, target_root, update=effective_update, dry_run=args.dry_run)
    )

    if not args.dry_run:
        record_deployment(str(target_root), all_stats, name=target_name)

    _print_summary(all_stats, mode, dry_run=args.dry_run)


def main() -> None:
    """脚本入口。"""
    parser = _build_parser()
    args = parser.parse_args()

    if args.list_deployed:
        # --list-deployed 是独占参数，不应与其他操作参数混用
        if any([args.target, args.update, args.force, args.dry_run]):
            print("[ERROR] --list-deployed 是独占参数，不能与 --target/--update/--force/--dry-run 同时使用")
            sys.exit(2)
        _run_list_deployed()
        return

    _run_deploy(args)


if __name__ == "__main__":
    main()
