"""
检查模板路径和加载情况
"""
import sys
import os
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from master.utils import get_config


def main():
    print("=" * 80)
    print("模板路径诊断")
    print("=" * 80)

    # 加载配置
    config_path = 'config/androws_config.yaml'
    print(f"\n[1] 加载配置: {config_path}")
    config = get_config(config_path)

    # 获取模板路径配置
    template_base = config.get('templates.base_path', 'pics')
    print(f"\n[2] 配置中的模板路径: '{template_base}'")

    # 计算实际路径
    print(f"\n[3] 路径计算过程:")
    print(f"  当前文件: {__file__}")
    print(f"  当前目录: {os.path.dirname(__file__)}")
    print(f"  父目录:   {os.path.dirname(os.path.dirname(__file__))}")

    templates_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        template_base
    )
    print(f"  拼接结果: {templates_dir}")
    print(f"  绝对路径: {os.path.abspath(templates_dir)}")

    # 检查目录是否存在
    print(f"\n[4] 检查目录:")
    if os.path.exists(templates_dir):
        print(f"  ✓ 目录存在")
        if os.path.isdir(templates_dir):
            print(f"  ✓ 是有效目录")
        else:
            print(f"  ✗ 不是目录")
            return
    else:
        print(f"  ✗ 目录不存在")
        print(f"\n可能的原因:")
        print(f"  1. 配置文件中的路径不正确")
        print(f"  2. pics 目录不在正确的位置")
        return

    # 检查模板文件
    print(f"\n[5] 检查模板文件:")

    ui_elements = [
        'chat', 'chat2', 'laotou', 'continue',
        'jiaodizhu_btn', 'jiabei_btn',
        'start', 'quick_start', 'win', 'lose'
    ]

    existing = []
    missing = []

    for element in ui_elements:
        template_path = os.path.join(templates_dir, f"{element}.png")
        abs_path = os.path.abspath(template_path)

        if os.path.exists(template_path):
            file_size = os.path.getsize(template_path)
            existing.append(element)
            print(f"  ✓ {element}.png ({file_size} bytes)")
            if element == 'chat':
                print(f"    路径: {abs_path}")
        else:
            missing.append(element)
            print(f"  ✗ {element}.png (不存在)")
            if element == 'chat':
                print(f"    查找: {abs_path}")

    print(f"\n[6] 统计:")
    print(f"  存在: {len(existing)}/{len(ui_elements)}")
    print(f"  缺失: {len(missing)}/{len(ui_elements)}")

    if missing:
        print(f"\n  缺失的模板: {', '.join(missing)}")

    # 测试加载
    print(f"\n[7] 测试模板加载:")
    if 'chat' in existing:
        chat_path = os.path.join(templates_dir, "chat.png")
        try:
            import cv2
            template = cv2.imread(chat_path)
            if template is not None:
                print(f"  ✓ chat.png 可以被 cv2 加载")
                print(f"    尺寸: {template.shape}")
            else:
                print(f"  ✗ chat.png cv2.imread 返回 None")
                print(f"    可能是文件损坏或格式不支持")
        except Exception as e:
            print(f"  ✗ 加载失败: {e}")
    else:
        print(f"  ✗ chat.png 不存在，无法测试加载")

    # 列出 pics 目录中所有 .png 文件
    print(f"\n[8] pics 目录中的所有 PNG 文件:")
    try:
        all_files = sorted([f for f in os.listdir(templates_dir) if f.endswith('.png')])
        print(f"  共 {len(all_files)} 个文件:")
        for i, f in enumerate(all_files[:20], 1):  # 只显示前 20 个
            print(f"    {i:2d}. {f}")
        if len(all_files) > 20:
            print(f"    ... 还有 {len(all_files) - 20} 个文件")
    except Exception as e:
        print(f"  ✗ 无法列出文件: {e}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
