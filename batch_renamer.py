import os
import re
import logging
from pathlib import Path
from typing import List, Tuple, Optional, Callable
from dataclasses import dataclass, field


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class RenameRule:
    rule_type: str
    prefix: Optional[str] = None
    suffix: Optional[str] = None
    pattern: Optional[str] = None
    replacement: Optional[str] = None
    use_regex: bool = False
    case_sensitive: bool = True
    include_extension: bool = False


@dataclass
class RenameResult:
    old_path: Path
    new_path: Path
    success: bool
    error: Optional[str] = None
    auto_renamed: bool = False


@dataclass
class RenamePreview:
    old_name: str
    new_name: str
    old_path: Path
    new_path: Path


class BatchRenamer:
    def __init__(self, directory: str, recursive: bool = False):
        self.directory = Path(directory)
        self.recursive = recursive
        if not self.directory.exists():
            raise FileNotFoundError(f"目录不存在: {directory}")
        if not self.directory.is_dir():
            raise NotADirectoryError(f"路径不是目录: {directory}")

    def _get_files(self, file_pattern: str = "*") -> List[Path]:
        files = []
        if self.recursive:
            for path in self.directory.rglob(file_pattern):
                if path.is_file():
                    files.append(path)
        else:
            for path in self.directory.glob(file_pattern):
                if path.is_file():
                    files.append(path)
        return sorted(files)

    @staticmethod
    def _apply_rule_to_text(text: str, rule: RenameRule) -> str:
        result = text

        if rule.rule_type == "prefix":
            result = rule.prefix + result
        elif rule.rule_type == "suffix":
            result = result + rule.suffix
        elif rule.rule_type == "replace":
            flags = 0 if rule.case_sensitive else re.IGNORECASE
            if rule.use_regex:
                try:
                    result = re.sub(rule.pattern, rule.replacement, result, flags=flags)
                except re.error as e:
                    raise ValueError(f"正则表达式错误: {e}")
            else:
                if rule.case_sensitive:
                    result = result.replace(rule.pattern, rule.replacement)
                else:
                    pattern = re.compile(re.escape(rule.pattern), flags)
                    result = pattern.sub(rule.replacement, result)

        return result

    def _generate_new_name(self, file_path: Path, rules: List[RenameRule]) -> str:
        name_part = file_path.stem
        ext_part = file_path.suffix

        has_include_ext_rule = any(r.include_extension for r in rules)

        if has_include_ext_rule:
            full_name = name_part + ext_part
            for rule in rules:
                text = full_name if rule.include_extension else name_part
                result = self._apply_rule_to_text(text, rule)
                if rule.include_extension:
                    full_name = result
                else:
                    name_part = result
                    full_name = name_part + ext_part
            return full_name
        else:
            for rule in rules:
                name_part = self._apply_rule_to_text(name_part, rule)
            return name_part + ext_part

    @staticmethod
    def _generate_unique_name(target_path: Path, used_names: set) -> Path:
        if target_path not in used_names and not target_path.exists():
            return target_path

        stem = target_path.stem
        suffix = target_path.suffix
        parent = target_path.parent
        counter = 1

        while True:
            candidate = parent / f"{stem} ({counter}){suffix}"
            if candidate not in used_names and not candidate.exists():
                return candidate
            counter += 1

    def preview(self, rules: List[RenameRule], file_pattern: str = "*", auto_rename: bool = False) -> List[RenamePreview]:
        files = self._get_files(file_pattern)
        previews = []
        used_names = set()

        for file_path in files:
            new_filename = self._generate_new_name(file_path, rules)
            new_path = file_path.with_name(new_filename)

            if auto_rename and new_path != file_path:
                new_path = self._generate_unique_name(new_path, used_names)

            used_names.add(new_path)
            previews.append(RenamePreview(
                old_name=file_path.name,
                new_name=new_path.name,
                old_path=file_path,
                new_path=new_path
            ))

        return previews

    def rename(
        self,
        rules: List[RenameRule],
        file_pattern: str = "*",
        dry_run: bool = False,
        overwrite: bool = False,
        stop_on_error: bool = True,
        auto_rename: bool = False
    ) -> List[RenameResult]:
        files = self._get_files(file_pattern)
        results = []
        used_names = set()

        for file_path in files:
            new_filename = self._generate_new_name(file_path, rules)
            new_path = file_path.with_name(new_filename)
            auto_renamed_flag = False

            if file_path == new_path:
                results.append(RenameResult(
                    old_path=file_path,
                    new_path=new_path,
                    success=True,
                    error="文件名未变化",
                    auto_renamed=False
                ))
                continue

            if new_path.exists() or new_path in used_names:
                if overwrite:
                    pass
                elif auto_rename:
                    new_path = self._generate_unique_name(new_path, used_names)
                    auto_renamed_flag = True
                else:
                    error_msg = f"目标文件已存在: {new_path.name}"
                    logger.warning(error_msg)
                    results.append(RenameResult(
                        old_path=file_path,
                        new_path=new_path,
                        success=False,
                        error=error_msg,
                        auto_renamed=False
                    ))
                    if stop_on_error:
                        break
                    continue

            used_names.add(new_path)

            if dry_run:
                results.append(RenameResult(
                    old_path=file_path,
                    new_path=new_path,
                    success=True,
                    error="预览模式，未执行" if not auto_renamed_flag else "预览模式，自动添加序号",
                    auto_renamed=auto_renamed_flag
                ))
                continue

            try:
                os.rename(file_path, new_path)
                if auto_renamed_flag:
                    logger.info(f"重命名成功（自动添加序号）: {file_path.name} -> {new_path.name}")
                else:
                    logger.info(f"重命名成功: {file_path.name} -> {new_path.name}")
                results.append(RenameResult(
                    old_path=file_path,
                    new_path=new_path,
                    success=True,
                    auto_renamed=auto_renamed_flag
                ))
            except OSError as e:
                error_msg = f"重命名失败: {str(e)}"
                logger.error(error_msg)
                results.append(RenameResult(
                    old_path=file_path,
                    new_path=new_path,
                    success=False,
                    error=error_msg,
                    auto_renamed=auto_renamed_flag
                ))
                if stop_on_error:
                    break

        return results

    @staticmethod
    def print_preview(previews: List[RenamePreview]) -> None:
        if not previews:
            print("没有找到匹配的文件")
            return

        print(f"找到 {len(previews)} 个文件，预览重命名效果:")
        print("-" * 80)
        print(f"{'原文件名':<40} {'新文件名':<40}")
        print("-" * 80)

        for preview in previews:
            old_name = preview.old_name
            new_name = preview.new_name
            if old_name == new_name:
                new_name = "(无变化)"
            print(f"{old_name:<40} {new_name:<40}")

        print("-" * 80)

    @staticmethod
    def print_results(results: List[RenameResult]) -> None:
        success_count = sum(1 for r in results if r.success)
        fail_count = len(results) - success_count
        auto_count = sum(1 for r in results if r.auto_renamed)

        summary = f"\n执行完成: 成功 {success_count} 个，失败 {fail_count} 个"
        if auto_count > 0:
            summary += f"，其中自动重命名 {auto_count} 个"
        print(summary)
        print("-" * 80)

        for result in results:
            status = "✓" if result.success else "✗"
            auto_tag = " [自动重命名]" if result.auto_renamed else ""
            error_info = f" ({result.error})" if result.error else ""
            print(f"{status} {result.old_path.name} -> {result.new_path.name}{auto_tag}{error_info}")

        print("-" * 80)


def create_prefix_rule(prefix: str, include_extension: bool = False) -> RenameRule:
    return RenameRule(
        rule_type="prefix",
        prefix=prefix,
        include_extension=include_extension
    )


def create_suffix_rule(suffix: str, include_extension: bool = False) -> RenameRule:
    return RenameRule(
        rule_type="suffix",
        suffix=suffix,
        include_extension=include_extension
    )


def create_replace_rule(
    pattern: str,
    replacement: str,
    use_regex: bool = False,
    case_sensitive: bool = True,
    include_extension: bool = False
) -> RenameRule:
    return RenameRule(
        rule_type="replace",
        pattern=pattern,
        replacement=replacement,
        use_regex=use_regex,
        case_sensitive=case_sensitive,
        include_extension=include_extension
    )
