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
