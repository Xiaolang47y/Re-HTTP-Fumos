#!/usr/bin/env python3
"""What Meme 快速生成程序"""

import os
import sys
import yaml
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path


def load_config(config_path):
    """加载配置文件"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def get_font(font_config, size):
    """获取字体对象"""
    font_file = font_config.get('file')
    font_index = font_config.get('index')
    font_name = font_config.get('name')
    
    if font_file and os.path.isfile(font_file):
        try:
            if font_index is not None:
                return ImageFont.truetype(font_file, size, index=font_index)
            else:
                return ImageFont.truetype(font_file, size)
        except:
            pass
    
    font_path_map = {
        "Noto Sans CJK SC": ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 2),
        "Noto Sans CJK TC": ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 3),
        "Noto Sans CJK JP": ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 0),
        "Noto Serif CJK SC": ("/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc", 2),
        "DejaVu Sans": ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", None),
        "DejaVu Serif": ("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf", None),
        "Liberation Sans": ("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", None),
        "Arial": ("C:/Windows/Fonts/arial.ttf", None),
        "Microsoft YaHei": ("C:/Windows/Fonts/msyh.ttc", None),
    }
    
    if font_name and font_name in font_path_map:
        path, index = font_path_map[font_name]
        if os.path.isfile(path):
            try:
                if index is not None:
                    return ImageFont.truetype(path, size, index=index)
                else:
                    return ImageFont.truetype(path, size)
            except:
                pass
    
    fallback_paths = [
        ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 2),
        ("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc", 2),
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", None),
        ("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", None),
        ("/usr/share/fonts/TTF/DejaVuSans.ttf", None),
        ("C:/Windows/Fonts/arial.ttf", None),
        ("C:/Windows/Fonts/msyh.ttc", None),
    ]
    
    for path, index in fallback_paths:
        if os.path.isfile(path):
            try:
                if index is not None:
                    return ImageFont.truetype(path, size, index=index)
                else:
                    return ImageFont.truetype(path, size)
            except:
                continue
    
    return ImageFont.load_default()


def process_image(source_path, output_path, target_width):
    """处理图片：清除元数据、调整尺寸、转换为PNG"""
    img = Image.open(source_path)
    
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    width_percent = target_width / float(img.size[0])
    target_height = int(float(img.size[1]) * width_percent)
    img_resized = img.resize((target_width, target_height), Image.LANCZOS)
    
    img_resized.save(output_path, 'PNG', optimize=True)
    print(f"  已处理: {os.path.basename(source_path)} -> {os.path.basename(output_path)}")
    return output_path


def draw_text_centered(draw, text, font, y_position, width, color='white'):
    """在指定位置居中绘制文字（支持多行）"""
    lines = text.split('\n')
    line_heights = []
    
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_heights.append(bbox[3] - bbox[1])
    
    total_height = sum(line_heights)
    current_y = y_position
    
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) // 2
        draw.text((x, current_y), line, font=font, fill=color)
        current_y += line_heights[i]
    
    return current_y


def generate_meme(processed_image_path, meme_config, global_config, output_path):
    """生成 What Meme 图片"""
    img = Image.open(processed_image_path)
    img_width, img_height = img.size
    
    inner_border = global_config['image']['inner_border']
    outer_border = global_config['image']['outer_border']
    side_margin = global_config['image'].get('side_margin', 20)
    top_margin = global_config['image'].get('top_margin', 20)
    
    title_size = meme_config.get('title_size', global_config['font']['title_size'])
    subtitle_size = meme_config.get('subtitle_size', global_config['font']['subtitle_size'])
    
    title_font = get_font(global_config['font'], title_size)
    subtitle_font = get_font(global_config['font'], subtitle_size)
    
    title = meme_config['title']
    subtitle = meme_config.get('subtitle', '')
    
    title_bbox = ImageDraw.Draw(Image.new('RGB', (1, 1))).textbbox((0, 0), title, font=title_font)
    title_height = title_bbox[3] - title_bbox[1]
    
    subtitle_height = 0
    if subtitle:
        subtitle_bbox = ImageDraw.Draw(Image.new('RGB', (1, 1))).textbbox((0, 0), subtitle, font=subtitle_font)
        subtitle_height = subtitle_bbox[3] - subtitle_bbox[1]
    
    text_gap_title = global_config['text'].get('gap_title', 0)
    text_gap_subtitle = global_config['text'].get('gap_subtitle', 25)
    text_bottom_margin = global_config['text'].get('bottom_margin', 25)
    
    if subtitle:
        text_area_height = title_height + subtitle_height + text_gap_title + text_gap_subtitle + text_bottom_margin
    else:
        text_area_height = title_height + text_bottom_margin
    
    canvas_width = img_width + side_margin * 2
    canvas_height = img_height + outer_border + inner_border + text_area_height + top_margin
    
    canvas = Image.new('RGB', (canvas_width, canvas_height), 'black')
    
    img_x = side_margin
    img_y = top_margin + outer_border
    
    canvas.paste(img, (img_x, img_y))
    
    draw = ImageDraw.Draw(canvas)
    
    inner_rect = [
        img_x - inner_border,
        img_y - inner_border,
        img_x + img_width + inner_border - 1,
        img_y + img_height + inner_border - 1
    ]
    draw.rectangle(inner_rect, outline='black', width=inner_border)
    
    outer_rect = [
        img_x - inner_border - outer_border,
        img_y - inner_border - outer_border,
        img_x + img_width + inner_border + outer_border - 1,
        img_y + img_height + inner_border + outer_border - 1
    ]
    draw.rectangle(outer_rect, outline='white', width=outer_border)
    
    text_start_y = img_y + img_height + outer_border + inner_border + text_gap_title
    draw_text_centered(draw, title, title_font, text_start_y, canvas_width)
    
    if subtitle:
        subtitle_y = text_start_y + title_height + text_gap_subtitle
        draw_text_centered(draw, subtitle, subtitle_font, subtitle_y, canvas_width)
    
    canvas.save(output_path, 'PNG', optimize=True)
    print(f"  已生成: {os.path.basename(output_path)}")


def main():
    base_dir = Path(__file__).parent
    config_path = base_dir / 'config.yaml'
    source_dir = base_dir / 'source_images'
    processed_dir = base_dir / 'processed_images'
    output_dir = base_dir / 'output'
    
    source_dir.mkdir(exist_ok=True)
    processed_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)
    
    if not config_path.exists():
        print(f"错误: 配置文件 {config_path} 不存在")
        sys.exit(1)
    
    print("加载配置文件...")
    config = load_config(config_path)
    
    target_width = config['image']['width']
    memes = config['memes']
    
    print(f"\n找到 {len(memes)} 个 Meme 配置")
    font_display = config['font'].get('file', config['font'].get('name', '未知'))
    print(f"字体: {font_display}")
    print(f"图片宽度: {target_width}px")
    print()
    
    for i, meme in enumerate(memes, 1):
        source_file = meme['source_file']
        source_path = source_dir / source_file
        
        if not source_path.exists():
            print(f"[{i}/{len(memes)}] 跳过: 源文件不存在 - {source_file}")
            continue
        
        base_name = Path(source_file).stem
        processed_path = processed_dir / f"{base_name}.png"
        output_path = output_dir / f"{base_name}_meme.png"
        
        print(f"[{i}/{len(memes)}] 处理: {source_file}")
        process_image(str(source_path), str(processed_path), target_width)
        generate_meme(str(processed_path), meme, config, str(output_path))
        print()
    
    print("全部完成！")
    print(f"处理后的图片: {processed_dir}")
    print(f"Meme 输出: {output_dir}")


if __name__ == '__main__':
    main()
