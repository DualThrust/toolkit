#!/usr/bin/env python3
"""
toolkit → 目标项目 自动部署脚本

将 toolkit 仓库中的 skills、references、instructions 自动同步到目标项目。
支持 Windows / macOS / Linux。

用法:
    python deploy.py                          # 交互模式，选择目标项目
    python deploy.py --target <项目路径>       # 部署到指定项目
    python deploy.py --target <路径> --dry-run # 预览模式，不实际复制
    python deploy.py --target <路径> --update  # 更新模式（覆盖已有文件）
"""

import argparse
import os
import shutil
import sys
from pathlib import Path
from typing import Dict


# ============================================================
# 配置 — 按需修改
# ============================================================

# 预置的目标项目列表（可以添加更多）
PRESET_TARGETS: Dict[str, str] = {
    "keeprix": r"C:\Users\DualThrust\Projects\Keeprix\Keeprix_dev",
}

# VS Code 用户级 prompts 目录（instructions 也会部署到这里）
VSCODE_PROMPTS_DIR: str = os.path.join(
    os.environ.get("APPDATA", os.path.expanduser("~")),
    "Code", "User", "prompts",
)


# ============================================================
# 核心逻辑
# ============================================================

def getToolkitRoot() -> Path:
    """获取 toolkit 仓库根目录（即本脚本所在目录）。"""
    return Path(__file__).resolve().parent


def resolveTarget(targetArg: str | None) -> Path:
    """解析目标项目路径。"""
    if targetArg:
        p = Path(targetArg)
        if p.exists():
            return p.resolve()
        # 尝试匹配预置别名
        key = targetArg.lower()
        if key in PRESET_TARGETS:
            p = Path(PRESET_TARGETS[key])
            if p.exists():
                return p.resolve()
        print(f"[ERROR] 目标路径不存在: {targetArg}")
        sys.exit(1)

    # 交互模式
    print("可用的预置目标项目:")
    for i, (name, path) in enumerate(PRESET_TARGETS.items(), 1):
        exists = "✓" if Path(path).exists() else "✗"
        print(f"  [{i}] {name}  {exists}  {path}")

    print(f"  [0] 手动输入路径")

    try:
        choice = input("\n请选择目标项目 (输入序号): ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\n已取消。")
        sys.exit(0)

    if choice == "0":
        path = input("请输入目标项目路径: ").strip()
        p = Path(path)
        if not p.exists():
            print(f"[ERROR] 路径不存在: {path}")
            sys.exit(1)
        return p.resolve()

    try:
        idx = int(choice) - 1
        if 0 <= idx < len(PRESET_TARGETS):
            name = list(PRESET_TARGETS.keys())[idx]
            p = Path(PRESET_TARGETS[name])
            if not p.exists():
                print(f"[ERROR] 预置目标不存在: {PRESET_TARGETS[name]}")
                sys.exit(1)
            return p.resolve()
    except ValueError:
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
) -> None:
    """部署 skills/workflows 和 skills/qt (排除 references)。"""
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
    print(f"  结果: {c} 个文件已{'预览' if dryRun else '复制'}, {s} 个跳过")

    # 1b. qt skills (排除 references/)
    src = toolkitRoot / "skills" / "qt"
    dst = targetRoot / ".agents" / "skills"
    print(f"\n  --- Qt 技能 ---")
    print(f"  源: {src}")
    print(f"  目标: {dst}")
    c, s = copyDir(src, dst, update=update, dryRun=dryRun, exclude={"references"})
    print(f"  结果: {c} 个文件已{'预览' if dryRun else '复制'}, {s} 个跳过")


def deployReferences(
    toolkitRoot: Path,
    targetRoot: Path,
    *,
    update: bool = False,
    dryRun: bool = False,
) -> None:
    """部署 references（审查清单/参考资料）。"""
    print("\n" + "=" * 60)
    print("  [2/3] 部署 References")
    print("=" * 60)

    src = toolkitRoot / "skills" / "qt" / "references"
    dst = targetRoot / ".agents" / "references"
    print(f"\n  源: {src}")
    print(f"  目标: {dst}")
    c, s = copyDir(src, dst, update=update, dryRun=dryRun)
    print(f"  结果: {c} 个文件已{'预览' if dryRun else '复制'}, {s} 个跳过")


def deployInstructions(
    toolkitRoot: Path,
    targetRoot: Path,
    *,
    update: bool = False,
    dryRun: bool = False,
) -> None:
    """部署 instructions 到项目 .github/instructions。"""
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


def main():
    parser = argparse.ArgumentParser(
        description="toolkit → 目标项目 自动部署脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python deploy.py                              # 交互模式
  python deploy.py --target keeprix             # 按别名部署
  python deploy.py --target /path/to/project    # 按路径部署
  python deploy.py --target keeprix --dry-run   # 预览
  python deploy.py --target keeprix --update    # 强制覆盖
        """,
    )
    parser.add_argument(
        "-t", "--target",
        help="目标项目路径或预置别名",
    )
    parser.add_argument(
        "-u", "--update",
        action="store_true",
        help="更新模式：覆盖已存在的文件（默认跳过）",
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

    args = parser.parse_args()

    toolkitRoot = getToolkitRoot()
    print(f"Toolkit 根目录: {toolkitRoot}")

    targetRoot = resolveTarget(args.target)
    print(f"目标项目: {targetRoot}")

    if args.dry_run:
        print("\n*** DRY-RUN 模式 — 不会实际修改文件 ***")

    mode = "更新" if args.update else "安装"

    deploySkills(toolkitRoot, targetRoot, update=args.update, dryRun=args.dry_run)
    deployReferences(toolkitRoot, targetRoot, update=args.update, dryRun=args.dry_run)
    deployInstructions(toolkitRoot, targetRoot, update=args.update, dryRun=args.dry_run)

    # VS Code prompts
    if not args.no_vscode:
        print("\n" + "=" * 60)
        print("  [附] VS Code 全局 Prompts")
        print("=" * 60)
        src = toolkitRoot / "instructions"
        dstVscode = Path(VSCODE_PROMPTS_DIR)
        print(f"\n  源: {src}")
        print(f"  目标: {dstVscode}")
        if dstVscode.exists():
            c, s = copyDir(src, dstVscode, update=args.update, dryRun=args.dry_run)
            print(f"  结果: {c} 个文件已{'预览' if args.dry_run else '复制'}, {s} 个跳过")
        else:
            print(f"  [SKIP] 目录不存在: {dstVscode}")
            print(f"  提示: 请确认 VS Code 已安装，或使用 --no-vscode 跳过此步骤")

    print("\n" + "=" * 60)
    print(f"  部署完成 ({mode}模式){' [DRY-RUN]' if args.dry_run else ''}")
    print("=" * 60)


if __name__ == "__main__":
    main()
