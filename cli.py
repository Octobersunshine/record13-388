import argparse
import sys
from pathlib import Path

from batch_renamer import (
    BatchRenamer,
    create_prefix_rule,
    create_suffix_rule,
    create_replace_rule,
    RenameRule
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="文件批量重命名工具 - 支持前缀、后缀、正则替换等多种重命名规则",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 添加前缀
  python cli.py --dir ./files --prefix "2025_"
  
  # 添加后缀
  python cli.py --dir ./files --suffix "_backup"
  
  # 简单文本替换
  python cli.py --dir ./files --replace "old" --with "new"
  
  # 正则替换（将文件名中的数字替换为空）
  python cli.py --dir ./files --regex --replace "\\d+" --with ""
  
  # 组合使用：先添加前缀，再替换文本
  python cli.py --dir ./files --prefix "img_" --replace "photo" --with "image"
  
  # 预览模式（不实际执行）
  python cli.py --dir ./files --prefix "test_" --dry-run
  
  # 递归处理子目录
  python cli.py --dir ./files --prefix "2025_" --recursive
  
  # 只处理特定类型的文件
  python cli.py --dir ./files --prefix "doc_" --pattern "*.txt"
  
  # 自动处理重名冲突（添加序号）
  python cli.py --dir ./files --prefix "new_" --auto-rename
        """
    )

    parser.add_argument(
        "--dir", "-d",
        required=True,
        help="目标目录路径"
    )

    parser.add_argument(
        "--prefix",
        help="添加文件名前缀"
    )

    parser.add_argument(
        "--suffix",
        help="添加文件名后缀（在扩展名之前）"
    )

    parser.add_argument(
        "--replace",
        help="要替换的文本或正则表达式模式"
    )

    parser.add_argument(
        "--with",
        dest="replacement",
        help="替换后的文本"
    )

    parser.add_argument(
        "--regex",
        action="store_true",
        default=False,
        help="使用正则表达式进行替换"
    )

    parser.add_argument(
        "--case-insensitive", "-i",
        action="store_true",
        default=False,
        help="替换时不区分大小写"
    )

    parser.add_argument(
        "--include-extension",
        action="store_true",
        default=False,
        help="重命名时包含文件扩展名"
    )

    parser.add_argument(
        "--pattern", "-p",
        default="*",
        help="文件匹配模式（如 *.txt, *.jpg），默认: *"
    )

    parser.add_argument(
        "--recursive", "-r",
        action="store_true",
        default=False,
        help="递归处理子目录"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="预览模式，不实际执行重命名"
    )

    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="如果目标文件存在则覆盖"
    )

    parser.add_argument(
        "--auto-rename",
        action="store_true",
        default=False,
        help="如果目标文件存在则自动添加序号（如 file (1).jpg）"
    )

    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        default=False,
        help="遇到错误时继续执行"
    )

    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        default=False,
        help="跳过确认提示，直接执行"
    )

    parser.add_argument(
        "--interactive",
        action="store_true",
        default=False,
        help="交互模式，逐个确认每个文件"
    )

    return parser


def parse_rules(args: argparse.Namespace) -> list:
    rules = []

    if args.prefix:
        rules.append(create_prefix_rule(args.prefix, args.include_extension))

    if args.suffix:
        rules.append(create_suffix_rule(args.suffix, args.include_extension))

    if args.replace:
        if args.replacement is None:
            print("错误: 使用 --replace 时必须同时指定 --with 参数")
            sys.exit(1)
        rules.append(create_replace_rule(
            pattern=args.replace,
            replacement=args.replacement,
            use_regex=args.regex,
            case_sensitive=not args.case_insensitive,
            include_extension=args.include_extension
        ))

    if not rules:
        print("错误: 至少需要指定一个重命名规则（--prefix, --suffix, 或 --replace）")
        sys.exit(1)

    return rules


def interactive_confirm(preview) -> bool:
    while True:
        response = input(
            f"重命名: {preview.old_name} -> {preview.new_name} [y/n/a/q]: "
        ).lower()
        if response in ('y', 'yes'):
            return True
        elif response in ('n', 'no'):
            return False
        elif response in ('a', 'all'):
            return True
        elif response in ('q', 'quit'):
            print("已取消操作")
            sys.exit(0)
        else:
            print("请输入 y(是), n(否), a(全部), q(退出)")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        renamer = BatchRenamer(args.dir, recursive=args.recursive)
    except (FileNotFoundError, NotADirectoryError) as e:
        print(f"错误: {e}")
        return 1

    try:
        rules = parse_rules(args)
    except SystemExit:
        return 1

    previews = renamer.preview(rules, args.pattern, auto_rename=args.auto_rename)

    if not previews:
        print("没有找到匹配的文件")
        return 0

    renamer.print_preview(previews)

    if args.dry_run:
        print("\n预览模式，未执行任何操作")
        return 0

    if not args.yes:
        response = input(f"\n确定要重命名 {len(previews)} 个文件吗？(y/N): ").lower()
        if response not in ('y', 'yes'):
            print("已取消操作")
            return 0

    if args.interactive:
        results = []
        for preview in previews:
            if interactive_confirm(preview):
                result = renamer.rename(
                    rules=[rules[0]] if len(rules) == 1 else rules,
                    file_pattern=preview.old_path.name,
                    dry_run=False,
                    overwrite=args.overwrite,
                    stop_on_error=not args.continue_on_error,
                    auto_rename=args.auto_rename
                )
                results.extend(result)
        renamer.print_results(results)
    else:
        results = renamer.rename(
            rules=rules,
            file_pattern=args.pattern,
            dry_run=False,
            overwrite=args.overwrite,
            stop_on_error=not args.continue_on_error,
            auto_rename=args.auto_rename
        )
        renamer.print_results(results)

    success_count = sum(1 for r in results if r.success)
    fail_count = len(results) - success_count

    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
