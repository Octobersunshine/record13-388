import os
import sys
import shutil
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from batch_renamer import (
    BatchRenamer,
    create_prefix_rule,
    create_suffix_rule,
    create_replace_rule
)


def setup_test_directory(base_path: Path) -> Path:
    test_dir = base_path / "test_run"
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir()

    test_files = [
        "photo1.jpg",
        "photo2.jpg",
        "document.txt",
        "image_old_01.png",
        "image_old_02.png",
        "video_123.mp4",
        "audio_456.mp3",
    ]

    for f in test_files:
        (test_dir / f).touch()

    return test_dir


def test_prefix_rule():
    print("\n" + "=" * 60)
    print("测试 1: 前缀添加")
    print("=" * 60)

    test_dir = setup_test_directory(Path(__file__).parent)
    renamer = BatchRenamer(str(test_dir))

    rules = [create_prefix_rule("2025_")]
    previews = renamer.preview(rules)

    print("预览结果:")
    for p in previews:
        print(f"  {p.old_name} -> {p.new_name}")

    results = renamer.rename(rules, dry_run=False)
    assert all(r.success for r in results), "前缀添加失败"

    files = [f.name for f in test_dir.iterdir() if f.is_file()]
    assert all(f.startswith("2025_") for f in files), "并非所有文件都添加了前缀"

    print("✓ 前缀添加测试通过")
    shutil.rmtree(test_dir)


def test_suffix_rule():
    print("\n" + "=" * 60)
    print("测试 2: 后缀添加")
    print("=" * 60)

    test_dir = setup_test_directory(Path(__file__).parent)
    renamer = BatchRenamer(str(test_dir))

    rules = [create_suffix_rule("_backup")]
    previews = renamer.preview(rules)

    print("预览结果:")
    for p in previews:
        print(f"  {p.old_name} -> {p.new_name}")

    results = renamer.rename(rules, dry_run=False)
    assert all(r.success for r in results), "后缀添加失败"

    files = [f.stem for f in test_dir.iterdir() if f.is_file()]
    assert all(f.endswith("_backup") for f in files), "并非所有文件都添加了后缀"

    print("✓ 后缀添加测试通过")
    shutil.rmtree(test_dir)


def test_simple_replace():
    print("\n" + "=" * 60)
    print("测试 3: 简单文本替换")
    print("=" * 60)

    test_dir = setup_test_directory(Path(__file__).parent)
    renamer = BatchRenamer(str(test_dir))

    rules = [create_replace_rule("photo", "image")]
    previews = renamer.preview(rules)

    print("预览结果:")
    for p in previews:
        print(f"  {p.old_name} -> {p.new_name}")

    results = renamer.rename(rules, dry_run=False)
    assert all(r.success for r in results), "文本替换失败"

    files = [f.name for f in test_dir.iterdir() if f.is_file()]
    assert not any("photo" in f for f in files), "仍有文件包含 'photo'"
    assert any("image1.jpg" in f for f in files), "替换结果不正确"

    print("✓ 简单文本替换测试通过")
    shutil.rmtree(test_dir)


def test_regex_replace():
    print("\n" + "=" * 60)
    print("测试 4: 正则表达式替换（移除数字）")
    print("=" * 60)

    test_dir = setup_test_directory(Path(__file__).parent)
    renamer = BatchRenamer(str(test_dir))

    rules = [create_replace_rule(r"(\d+)", r"_\1", use_regex=True)]
    previews = renamer.preview(rules)

    print("预览结果:")
    for p in previews:
        print(f"  {p.old_name} -> {p.new_name}")

    results = renamer.rename(rules, dry_run=False)
    assert all(r.success for r in results), "正则替换失败"

    files = [f.stem for f in test_dir.iterdir() if f.is_file()]
    import re
    assert all(re.search(r"_\d", f) for f in files if re.search(r"\d", f)), "数字前未添加下划线"

    print("✓ 正则表达式替换测试通过")
    shutil.rmtree(test_dir)


def test_regex_replace_with_groups():
    print("\n" + "=" * 60)
    print("测试 5: 正则表达式替换（使用捕获组）")
    print("=" * 60)

    test_dir = setup_test_directory(Path(__file__).parent)
    renamer = BatchRenamer(str(test_dir))

    rules = [create_replace_rule(r"image_old_(\d+)", r"new_img_\1", use_regex=True)]
    previews = renamer.preview(rules, file_pattern="*.png")

    print("预览结果:")
    for p in previews:
        print(f"  {p.old_name} -> {p.new_name}")

    results = renamer.rename(rules, file_pattern="*.png", dry_run=False)
    assert all(r.success for r in results), "正则捕获组替换失败"

    png_files = [f.name for f in test_dir.glob("*.png")]
    assert "new_img_01.png" in png_files, "捕获组替换结果不正确"
    assert "new_img_02.png" in png_files, "捕获组替换结果不正确"

    print("✓ 正则表达式捕获组替换测试通过")
    shutil.rmtree(test_dir)


def test_dry_run():
    print("\n" + "=" * 60)
    print("测试 6: 预览模式 (dry run)")
    print("=" * 60)

    test_dir = setup_test_directory(Path(__file__).parent)
    renamer = BatchRenamer(str(test_dir))

    original_files = sorted([f.name for f in test_dir.iterdir() if f.is_file()])

    rules = [create_prefix_rule("TEST_")]
    results = renamer.rename(rules, dry_run=True)

    files_after = sorted([f.name for f in test_dir.iterdir() if f.is_file()])

    assert original_files == files_after, "dry run 模式下文件被修改了"
    assert all(r.success for r in results), "dry run 应该标记为成功"
    assert all("预览模式" in (r.error or "") for r in results), "dry run 应该有预览标记"

    print("✓ 预览模式测试通过")
    shutil.rmtree(test_dir)


def test_combined_rules():
    print("\n" + "=" * 60)
    print("测试 7: 组合规则（前缀 + 替换）")
    print("=" * 60)

    test_dir = setup_test_directory(Path(__file__).parent)
    renamer = BatchRenamer(str(test_dir))

    rules = [
        create_prefix_rule("2025_"),
        create_replace_rule("photo", "image"),
        create_suffix_rule("_processed")
    ]
    previews = renamer.preview(rules, file_pattern="*.jpg")

    print("预览结果:")
    for p in previews:
        print(f"  {p.old_name} -> {p.new_name}")

    results = renamer.rename(rules, file_pattern="*.jpg", dry_run=False)
    assert all(r.success for r in results), "组合规则执行失败"

    jpg_files = [f.name for f in test_dir.glob("*.jpg")]
    expected = ["2025_image1_processed.jpg", "2025_image2_processed.jpg"]
    for exp in expected:
        assert exp in jpg_files, f"期望文件 {exp} 不存在"

    print("✓ 组合规则测试通过")
    shutil.rmtree(test_dir)


def test_case_insensitive_replace():
    print("\n" + "=" * 60)
    print("测试 8: 不区分大小写替换")
    print("=" * 60)

    test_dir = setup_test_directory(Path(__file__).parent)
    (test_dir / "Photo1.jpg").touch()
    (test_dir / "PHOTO2.jpg").touch()

    renamer = BatchRenamer(str(test_dir))

    rules = [create_replace_rule("photo", "img", case_sensitive=False)]
    results = renamer.rename(rules, dry_run=False)
    assert all(r.success for r in results), "不区分大小写替换失败"

    files = [f.name for f in test_dir.iterdir() if f.is_file()]
    assert "img1.jpg" in files, "小写替换失败"
    assert any(f == "img2.jpg" for f in files), "大写替换失败"

    print("✓ 不区分大小写替换测试通过")
    shutil.rmtree(test_dir)


def test_file_pattern_filter():
    print("\n" + "=" * 60)
    print("测试 9: 文件模式过滤")
    print("=" * 60)

    test_dir = setup_test_directory(Path(__file__).parent)
    renamer = BatchRenamer(str(test_dir))

    rules = [create_prefix_rule("TXT_")]
    results = renamer.rename(rules, file_pattern="*.txt", dry_run=False)

    all_files = list(test_dir.iterdir())
    txt_files = [f for f in all_files if f.suffix == ".txt"]
    other_files = [f for f in all_files if f.suffix != ".txt"]

    assert all(f.name.startswith("TXT_") for f in txt_files), "txt 文件未被重命名"
    assert not any(f.name.startswith("TXT_") for f in other_files), "非 txt 文件被错误重命名"

    print("✓ 文件模式过滤测试通过")
    shutil.rmtree(test_dir)


def test_recursive():
    print("\n" + "=" * 60)
    print("测试 10: 递归处理子目录")
    print("=" * 60)

    test_dir = setup_test_directory(Path(__file__).parent)
    subdir1 = test_dir / "subdir1"
    subdir2 = test_dir / "subdir2"
    subdir1.mkdir()
    subdir2.mkdir()
    (subdir1 / "nested_file1.txt").touch()
    (subdir2 / "nested_file2.txt").touch()

    renamer = BatchRenamer(str(test_dir), recursive=True)
    rules = [create_prefix_rule("ALL_")]

    results = renamer.rename(rules, dry_run=False)
    assert all(r.success for r in results), "递归处理失败"

    all_files = list(test_dir.rglob("*"))
    all_files = [f for f in all_files if f.is_file()]
    assert len(all_files) >= 9, "文件数量不正确"
    assert all(f.name.startswith("ALL_") for f in all_files), "并非所有文件都被重命名"

    print("✓ 递归处理子目录测试通过")
    shutil.rmtree(test_dir)


def test_auto_rename_existing_file():
    print("\n" + "=" * 60)
    print("测试 11: 自动序号 - 目标文件已存在")
    print("=" * 60)

    test_dir = setup_test_directory(Path(__file__).parent)
    (test_dir / "photo.jpg").touch()

    renamer = BatchRenamer(str(test_dir))

    rules = [create_replace_rule("photo1", "photo")]
    results = renamer.rename(rules, file_pattern="photo1.jpg", auto_rename=True)

    assert all(r.success for r in results), "自动重命名失败"
    assert results[0].auto_renamed, "应该标记为自动重命名"
    assert results[0].new_path.name == "photo (1).jpg", f"文件名不正确: {results[0].new_path.name}"
    assert (test_dir / "photo.jpg").exists(), "原目标文件应该仍然存在"
    assert (test_dir / "photo (1).jpg").exists(), "自动重命名的文件应该存在"

    print("✓ 自动序号 - 目标文件已存在测试通过")
    shutil.rmtree(test_dir)


def test_auto_rename_multiple_conflicts():
    print("\n" + "=" * 60)
    print("测试 12: 自动序号 - 多个文件冲突")
    print("=" * 60)

    test_dir = setup_test_directory(Path(__file__).parent)

    renamer = BatchRenamer(str(test_dir))

    rules = [create_replace_rule(r"\d+", "", use_regex=True)]
    results = renamer.rename(rules, file_pattern="photo*.jpg", auto_rename=True)

    assert all(r.success for r in results), "所有文件都应该重命名成功"
    assert sum(1 for r in results if r.auto_renamed) >= 1, "应该有自动重命名的文件"

    jpg_files = sorted([f.name for f in test_dir.glob("photo*.jpg")])
    assert "photo.jpg" in jpg_files, "应该有 photo.jpg"
    assert "photo (1).jpg" in jpg_files, "应该有 photo (1).jpg"

    print("✓ 自动序号 - 多个文件冲突测试通过")
    shutil.rmtree(test_dir)


def test_auto_rename_preview():
    print("\n" + "=" * 60)
    print("测试 13: 自动序号 - 预览模式")
    print("=" * 60)

    test_dir = setup_test_directory(Path(__file__).parent)
    (test_dir / "photo.jpg").touch()

    renamer = BatchRenamer(str(test_dir))

    rules = [create_replace_rule("photo1", "photo")]
    previews = renamer.preview(rules, file_pattern="photo1.jpg", auto_rename=True)

    assert len(previews) == 1
    assert previews[0].new_name == "photo (1).jpg", f"预览名不正确: {previews[0].new_name}"

    results = renamer.rename(rules, file_pattern="photo1.jpg", dry_run=True, auto_rename=True)
    assert all(r.success for r in results)
    assert results[0].auto_renamed
    assert (test_dir / "photo.jpg").exists(), "dry run 不应修改文件"
    assert not (test_dir / "photo (1).jpg").exists(), "dry run 不应创建新文件"

    print("✓ 自动序号 - 预览模式测试通过")
    shutil.rmtree(test_dir)


def test_auto_rename_three_way_conflict():
    print("\n" + "=" * 60)
    print("测试 14: 自动序号 - 三重冲突")
    print("=" * 60)

    test_dir = Path(__file__).parent / "test_run"
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir()

    (test_dir / "image.jpg").touch()
    (test_dir / "pic1.jpg").touch()
    (test_dir / "pic2.jpg").touch()
    (test_dir / "pic3.jpg").touch()

    renamer = BatchRenamer(str(test_dir))

    rules = [create_replace_rule(r"pic\d*", "image", use_regex=True)]
    results = renamer.rename(rules, file_pattern="pic*.jpg", auto_rename=True)

    assert all(r.success for r in results), "所有文件都应该重命名成功"
    auto_count = sum(1 for r in results if r.auto_renamed)
    assert auto_count == 3, f"应该有 3 个自动重命名，实际有 {auto_count} 个"

    all_files = sorted([f.name for f in test_dir.glob("image*.jpg")])
    expected = ["image.jpg", "image (1).jpg", "image (2).jpg", "image (3).jpg"]
    for exp in expected:
        assert exp in all_files, f"缺少文件: {exp}"

    print("✓ 自动序号 - 三重冲突测试通过")
    shutil.rmtree(test_dir)


def test_auto_rename_with_extension():
    print("\n" + "=" * 60)
    print("测试 15: 自动序号 - 序号位置在扩展名前")
    print("=" * 60)

    test_dir = Path(__file__).parent / "test_run"
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir()

    (test_dir / "note.txt").touch()
    (test_dir / "file1.txt").touch()

    renamer = BatchRenamer(str(test_dir))

    rules = [create_replace_rule("file1", "note")]
    results = renamer.rename(rules, file_pattern="file1.txt", auto_rename=True)

    assert len(results) == 1, f"应该有 1 个结果，实际有 {len(results)} 个"
    assert all(r.success for r in results)
    assert results[0].new_path.name == "note (1).txt", f"序号位置不正确: {results[0].new_path.name}"
    assert (test_dir / "note.txt").exists(), "原 note.txt 应该存在"
    assert (test_dir / "note (1).txt").exists(), "note (1).txt 应该存在"

    print("✓ 自动序号 - 序号位置测试通过")
    shutil.rmtree(test_dir)


def test_preview_metadata():
    print("\n" + "=" * 60)
    print("测试 16: 预览功能 - 元数据")
    print("=" * 60)

    test_dir = setup_test_directory(Path(__file__).parent)

    renamer = BatchRenamer(str(test_dir))
    rules = [create_prefix_rule("test_")]
    previews = renamer.preview(rules, include_metadata=True)

    assert len(previews) > 0
    for p in previews:
        assert p.is_changed == (not p.old_name.startswith("test_"))
        assert p.file_size is not None
        assert p.modified_time is not None
        assert p.has_conflict == False
        assert p.will_auto_rename == False

    print("✓ 预览功能 - 元数据测试通过")
    shutil.rmtree(test_dir)


def test_preview_conflict_detection():
    print("\n" + "=" * 60)
    print("测试 17: 预览功能 - 冲突检测")
    print("=" * 60)

    test_dir = setup_test_directory(Path(__file__).parent)
    (test_dir / "photo.jpg").touch()

    renamer = BatchRenamer(str(test_dir))
    rules = [create_replace_rule("photo1", "photo")]

    previews = renamer.preview(rules, file_pattern="photo1.jpg", auto_rename=False)
    assert previews[0].has_conflict == True
    assert previews[0].will_auto_rename == False

    previews_auto = renamer.preview(rules, file_pattern="photo1.jpg", auto_rename=True)
    assert previews_auto[0].has_conflict == True
    assert previews_auto[0].will_auto_rename == True
    assert previews_auto[0].new_name == "photo (1).jpg"

    print("✓ 预览功能 - 冲突检测测试通过")
    shutil.rmtree(test_dir)


def test_preview_export_formats():
    print("\n" + "=" * 60)
    print("测试 18: 预览功能 - 导出格式")
    print("=" * 60)

    test_dir = setup_test_directory(Path(__file__).parent)

    renamer = BatchRenamer(str(test_dir))
    rules = [create_prefix_rule("2025_")]
    previews = renamer.preview(rules, include_metadata=False)

    dict_list = renamer.preview_to_dict(previews)
    assert isinstance(dict_list, list)
    assert len(dict_list) == len(previews)
    assert "old_name" in dict_list[0]
    assert "new_name" in dict_list[0]

    json_str = renamer.preview_to_json(previews)
    assert isinstance(json_str, str)
    assert "2025_" in json_str

    tuples = renamer.preview_to_tuples(previews)
    assert isinstance(tuples, list)
    assert len(tuples) == len(previews)
    assert isinstance(tuples[0], tuple)
    assert len(tuples[0]) == 2

    text = renamer.preview_to_text(previews)
    assert isinstance(text, str)
    assert "找到" in text
    assert "原文件名" in text

    mapping = renamer.get_mapping(previews)
    assert isinstance(mapping, dict)
    assert len(mapping) == len(previews)

    print("✓ 预览功能 - 导出格式测试通过")
    shutil.rmtree(test_dir)


def test_preview_filter_methods():
    print("\n" + "=" * 60)
    print("测试 19: 预览功能 - 过滤方法")
    print("=" * 60)

    test_dir = setup_test_directory(Path(__file__).parent)
    (test_dir / "photo.jpg").touch()

    renamer = BatchRenamer(str(test_dir))

    rules = [create_replace_rule("photo1", "photo")]
    previews = renamer.preview(rules, file_pattern="photo*.jpg", auto_rename=True)

    changed = renamer.get_changed_previews(previews)
    assert len(changed) <= len(previews)

    conflicts = renamer.get_conflict_previews(previews)
    assert len(conflicts) >= 1
    assert all(c.has_conflict for c in conflicts)

    print("✓ 预览功能 - 过滤方法测试通过")
    shutil.rmtree(test_dir)


def test_preview_to_tuple_and_dict():
    print("\n" + "=" * 60)
    print("测试 20: 预览功能 - RenamePreview 对象方法")
    print("=" * 60)

    test_dir = setup_test_directory(Path(__file__).parent)

    renamer = BatchRenamer(str(test_dir))
    rules = [create_prefix_rule("test_")]
    previews = renamer.preview(rules, file_pattern="photo1.jpg")

    p = previews[0]
    t = p.to_tuple()
    assert t == (p.old_name, p.new_name)

    d = p.to_dict()
    assert isinstance(d, dict)
    assert d["old_name"] == p.old_name
    assert d["new_name"] == p.new_name
    assert d["is_changed"] == p.is_changed

    print("✓ 预览功能 - RenamePreview 对象方法测试通过")
    shutil.rmtree(test_dir)


def test_preview_no_metadata():
    print("\n" + "=" * 60)
    print("测试 21: 预览功能 - 不包含元数据")
    print("=" * 60)

    test_dir = setup_test_directory(Path(__file__).parent)

    renamer = BatchRenamer(str(test_dir))
    rules = [create_prefix_rule("test_")]
    previews = renamer.preview(rules, include_metadata=False)

    for p in previews:
        assert p.file_size is None
        assert p.modified_time is None

    print("✓ 预览功能 - 不包含元数据测试通过")
    shutil.rmtree(test_dir)


def main():
    print("\n" + "#" * 60)
    print("#  文件批量重命名服务 - 单元测试")
    print("#" * 60)

    tests = [
        test_prefix_rule,
        test_suffix_rule,
        test_simple_replace,
        test_regex_replace,
        test_regex_replace_with_groups,
        test_dry_run,
        test_combined_rules,
        test_case_insensitive_replace,
        test_file_pattern_filter,
        test_recursive,
        test_auto_rename_existing_file,
        test_auto_rename_multiple_conflicts,
        test_auto_rename_preview,
        test_auto_rename_three_way_conflict,
        test_auto_rename_with_extension,
        test_preview_metadata,
        test_preview_conflict_detection,
        test_preview_export_formats,
        test_preview_filter_methods,
        test_preview_to_tuple_and_dict,
        test_preview_no_metadata,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ 测试失败: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ 测试异常: {type(e).__name__}: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"测试结果: {passed} 个通过, {failed} 个失败")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
