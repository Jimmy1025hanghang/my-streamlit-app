# app.py
import streamlit as st
import fitz  # PyMuPDF
from PIL import Image
import io
import zipfile
import os
import math

st.set_page_config(page_title="PDF全能工具箱", layout="wide")

# ===================================================================
# 工具一：二维码位置调试器 (高清预览版)
# ===================================================================
def tool_qr_placer():
    st.title("工具一：二维码位置调试器")
    st.info("说明：实时预览二维码在PDF上的位置与大小，获取精确的坐标值。")

    # --- 侧边栏：文件上传和参数调整 ---
    st.sidebar.header("上传文件")
    uploaded_pdf = st.sidebar.file_uploader("上传PDF底图", type=["pdf"], key="placer_pdf")
    uploaded_qrs = st.sidebar.file_uploader("上传二维码图片(可多选)", type=["png", "jpg", "jpeg"], accept_multiple_files=True, key="placer_qrs")

    if uploaded_pdf and uploaded_qrs:
        # 定义一个更高的DPI来获得更清晰的预览
        PREVIEW_DPI = 200

        # --- 文件处理逻辑 ---
        pdf_data = uploaded_pdf.read()
        doc = fitz.open(stream=pdf_data, filetype="pdf")
        
        # 【修改点1】先获取PDF页面的原始点尺寸，用于设置输入框的最大值
        page = doc[0]
        pdf_width_points = page.rect.width
        pdf_height_points = page.rect.height

        # 【修改点2】使用更高的DPI生成预览图
        pix = page.get_pixmap(dpi=PREVIEW_DPI)
        base_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        doc.close()

        qr_data = uploaded_qrs[0].read()
        qr_img = Image.open(io.BytesIO(qr_data)).convert("RGBA")

        # --- 参数调整控件 ---
        st.sidebar.header("参数调整 (可直接输入)")
        
        # 输入框的最大值使用原始点尺寸，这样用户的输入逻辑不变
        x_val = min(110, int(pdf_width_points))
        y_val = min(140, int(pdf_height_points))
        w_val = min(210, int(pdf_width_points))
        h_val = min(210, int(pdf_height_points))

        x_pos = st.sidebar.number_input("X 坐标：", min_value=0, max_value=int(pdf_width_points), value=x_val)
        y_pos = st.sidebar.number_input("Y 坐标：", min_value=0, max_value=int(pdf_height_points), value=y_val)
        width = st.sidebar.number_input("宽度 W：", min_value=1, max_value=int(pdf_width_points), value=w_val)
        height = st.sidebar.number_input("高度 H：", min_value=1, max_value=int(pdf_height_points), value=h_val)
        
        # --- 图像合成逻辑 ---
        if width > 0 and height > 0:
            # 【修改点3】计算缩放比例，并将坐标和尺寸按比例放大
            zoom_factor = PREVIEW_DPI / 72.0
            
            # 计算在高分辨率底图上，二维码应该有的像素尺寸和位置
            scaled_width = int(width * zoom_factor)
            scaled_height = int(height * zoom_factor)
            scaled_x = int(x_pos * zoom_factor)
            scaled_y = int(y_pos * zoom_factor)

            # 确保缩放后的尺寸至少是1x1像素
            if scaled_width < 1: scaled_width = 1
            if scaled_height < 1: scaled_height = 1

            resized_qr = qr_img.resize((scaled_width, scaled_height), Image.LANCZOS)
            final_image = base_img.copy()
            final_image.paste(resized_qr, (scaled_x, scaled_y), resized_qr)

            st.image(final_image, caption="实时预览效果", use_container_width=True)
            st.success(f"当前坐标: X={x_pos}, Y={y_pos} | 当前尺寸: W={width}, H={height}")
        else:
            st.error("错误：宽度和高度必须大于0。")

    else:
        st.warning("⚠️ 请在左侧上传PDF底图和二维码图片以开始操作。")

# ===================================================================
# 工具二：PDF 批量生成器 (ZIP优化版)
# ===================================================================
def tool_batch_processor():
    st.title("工具二：PDF 批量生成器 (单二维码)")
    st.info("说明：请将所有二维码图片打包成一个ZIP文件后上传。")

    template_pdf = st.file_uploader("上传PDF模板", type=["pdf"], key="processor_pdf_zip")
    # 【修改点】只接受单个ZIP文件上传
    qr_zip_file = st.file_uploader("上传包含所有二维码的ZIP压缩包", type=["zip"], key="processor_qrs_zip")
    
    # ... (参数输入部分不变) ...
    st.subheader("输入坐标和尺寸")
    with st.expander("从哪里获取这些值？"):
        st.markdown("请先使用左侧导航栏的 **“二维码位置调试器”** 工具获取。")
    col1, col2, col3, col4 = st.columns(4)
    with col1: x_val = st.number_input("X 坐标", value=45, format="%d", key="proc_x")
    with col2: y_val = st.number_input("Y 坐标", value=140, format="%d", key="proc_y")
    with col3: w_val = st.number_input("宽度 W", value=85, format="%d", key="proc_w")
    with col4: h_val = st.number_input("高度 H", value=85, format="%d", key="proc_h")

    if st.button("开始生成PDF并打包", type="primary", key="proc_btn_zip"):
        if not template_pdf or not qr_zip_file:
            st.error("❌ 错误：请务必上传PDF模板和二维码ZIP压缩包！")
        else:
            output_zip_buffer = io.BytesIO()
            tpl_data = template_pdf.read()
            qr_count = 0
            
            with st.spinner("正在读取ZIP包并处理..."):
                # 【修改点】处理ZIP包的逻辑
                with zipfile.ZipFile(qr_zip_file, 'r') as qr_zip:
                    # 获取ZIP包内所有图片文件
                    image_files = [f for f in qr_zip.namelist() if f.lower().endswith(('.png', '.jpg', '.jpeg')) and not f.startswith('__MACOSX')]
                    qr_count = len(image_files)
                    
                    with zipfile.ZipFile(output_zip_buffer, 'w', zipfile.ZIP_DEFLATED) as output_zip:
                        for image_name in image_files:
                            # 从ZIP中读取单个图片数据
                            with qr_zip.open(image_name) as image_file:
                                image_data = image_file.read()
                                
                                doc = fitz.open(stream=tpl_data, filetype="pdf")
                                page = doc[0]
                                rect = fitz.Rect(x_val, y_val, x_val + w_val, y_val + h_val)
                                page.insert_image(rect, stream=image_data, overlay=True)
                                
                                fname = f"{os.path.splitext(os.path.basename(image_name))[0]}.pdf"
                                output_zip.writestr(fname, doc.tobytes())
                                doc.close()

            st.success(f"✅ 处理完成！已成功处理 {qr_count} 个二维码并生成PDF。")
            st.download_button(label="📥 点击下载包含所有PDF的ZIP包", data=output_zip_buffer.getvalue(), file_name="generated_pdfs.zip", mime="application/zip")


# ===================================================================
# 工具二：PDF 批量生成器
# ===================================================================
def tool_batch_processor():
    st.title("工具二：PDF 批量生成器 (单二维码)")
    st.info("说明：将大量的二维码批量合成到PDF模板中。")

    # ... (代码与之前版本相同，为节省篇幅此处省略) ...
    # (The code for this function is identical to the previous version and is omitted for brevity)
    template_pdf = st.file_uploader("上传PDF模板", type=["pdf"], key="processor_pdf")
    qr_code_files = st.file_uploader("上传所有二维码图片", type=["png", "jpg", "jpeg"], accept_multiple_files=True, key="processor_qrs")
    st.subheader("输入坐标和尺寸")
    with st.expander("从哪里获取这些值？"):
        st.markdown("请先使用左侧导航栏的 **“二维码位置调试器”** 工具获取。")
    col1, col2, col3, col4 = st.columns(4)
    with col1: x_val = st.number_input("X 坐标", value=45, format="%d", key="proc_x")
    with col2: y_val = st.number_input("Y 坐标", value=140, format="%d", key="proc_y")
    with col3: w_val = st.number_input("宽度 W", value=85, format="%d", key="proc_w")
    with col4: h_val = st.number_input("高度 H", value=85, format="%d", key="proc_h")
    if st.button("开始生成PDF并打包", type="primary", key="proc_btn"):
        if not template_pdf or not qr_code_files: st.error("❌ 错误：请务必上传PDF模板和二维码文件！")
        else:
            zip_buffer = io.BytesIO()
            with st.spinner("正在处理中..."):
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as z:
                    tpl_data = template_pdf.read()
                    for f in qr_code_files:
                        doc = fitz.open(stream=tpl_data, filetype="pdf")
                        page = doc[0]
                        rect = fitz.Rect(x_val, y_val, x_val + w_val, y_val + h_val)
                        page.insert_image(rect, stream=f.read(), overlay=True)
                        fname = f"{os.path.splitext(f.name)[0]}.pdf"
                        z.writestr(fname, doc.tobytes())
                        doc.close()
            st.success(f"✅ 处理完成！已生成 {len(qr_code_files)} 个PDF。")
            st.download_button(label="📥 点击下载ZIP压缩包", data=zip_buffer.getvalue(), file_name="generated_pdfs.zip", mime="application/zip")


# ===================================================================
# 工具三：双二维码批量合成器 
# ===================================================================
def tool_dual_qr_processor():
    st.title("工具三：PDF 批量生成器 (双码)")
    st.info("说明：在同一个PDF模板上同时批量插入左右两个二维码。")

    # --- 文件上传 (这部分不变) ---
    template_pdf = st.file_uploader("上传PDF模板", type=["pdf"], key="dual_pdf")
    left_qrs = st.file_uploader("上传所有左侧二维码", type=["png", "jpg", "jpeg"], accept_multiple_files=True, key="dual_qrs_left")
    right_qrs = st.file_uploader("上传所有右侧二维码", type=["png", "jpg", "jpeg"], accept_multiple_files=True, key="dual_qrs_right")

    # --- 【修改点】参数输入 ---
    st.subheader("输入坐标和尺寸")
    st.markdown("同样建议使用 **“工具一”** 分别调试好左右两侧二维码的位置和尺寸。")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("##### 左侧二维码")
        # 明确使用 value= 设置初始值, min_value= 设置最小值
        xL = st.number_input("左 X", min_value=0, value=110, format="%d", key="dual_xL")
        yL = st.number_input("左 Y", min_value=0, value=140, format="%d", key="dual_yL")
    with col2:
        st.markdown("##### 右侧二维码")
        xR = st.number_input("右 X", min_value=0, value=463, format="%d", key="dual_xR")
        yR = st.number_input("右 Y", min_value=0, value=140, format="%d", key="dual_yR")

    st.markdown("##### 共享尺寸 (左右二维码使用相同宽高)")
    col_w, col_h = st.columns(2)
    with col_w:
        # 宽度和高度的最小值应为 1
        W = st.number_input("宽度 W", min_value=1, value=210, format="%d", key="dual_W")
    with col_h:
        H = st.number_input("高度 H", min_value=1, value=210, format="%d", key="dual_H")

    # --- 执行逻辑 (这部分不变) ---
    if st.button("开始合成双二维码PDF", type="primary", key="dual_btn"):
        if not all([template_pdf, left_qrs, right_qrs]):
            st.error("❌ 错误：请务必上传PDF模板以及左右两侧的二维码文件！")
        else:
            pair_count = min(len(left_qrs), len(right_qrs))
            if len(left_qrs) != len(right_qrs):
                st.warning(f"ℹ️ 提示：左右二维码数量不同，将按数量较少的一方（{pair_count}对）进行处理。")
            
            pairs = list(zip(left_qrs[:pair_count], right_qrs[:pair_count]))
            
            zip_buffer = io.BytesIO()
            with st.spinner(f"正在生成 {pair_count} 份PDF，请稍候..."):
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_archive:
                    template_pdf_data = template_pdf.read()
                    
                    for left_qr_file, right_qr_file in pairs:
                        doc = fitz.open(stream=template_pdf_data, filetype="pdf")
                        page = doc[0]
                        
                        rectL = fitz.Rect(xL, yL, xL + W, yL + H)
                        page.insert_image(rectL, stream=left_qr_file.read(), overlay=True)
                        
                        rectR = fitz.Rect(xR, yR, xR + W, yR + H)
                        page.insert_image(rectR, stream=right_qr_file.read(), overlay=True)
                        
                        left_base = os.path.splitext(left_qr_file.name)[0]
                        right_base = os.path.splitext(right_qr_file.name)[0]
                        output_pdf_name = f"{left_base}+{right_base}.pdf"
                        
                        pdf_bytes = doc.tobytes()
                        doc.close()
                        zip_archive.writestr(output_pdf_name, pdf_bytes)
                        
            st.success(f"✅ 处理完成！已成功生成 {pair_count} 份PDF并打包。")
            st.download_button(
                label="📥 点击下载包含双二维码PDF的ZIP包",
                data=zip_buffer.getvalue(),
                file_name="dual_qr_pdfs.zip",
                mime="application/zip"
            )

# ===================================================================
# 工具四：PDF 拼版工具 (已修复)
# ===================================================================
def tool_pdf_imposition():
    st.title("工具四：PDF 拼版工具")
    st.info("说明：将大量单页PDF文件，按照指定的网格布局，拼接到新的、更大的PDF页面上。")

    # --- 输入 (这部分不变) ---
    source_pdfs = st.file_uploader("上传所有需要拼版的源PDF文件", type=["pdf"], accept_multiple_files=True, key="imposition_pdfs")
    st.subheader("设置拼版参数")
    col1, col2, col3 = st.columns(3)
    with col1:
        cols = st.number_input("横向数量 (列)", min_value=1, value=8, format="%d")
    with col2:
        rows = st.number_input("竖向数量 (行)", min_value=1, value=5, format="%d")
    with col3:
        gap_mm = st.number_input("间距 (mm)", min_value=0.0, value=20.0, format="%.1f")

    # --- 执行 ---
    if st.button("🚀 开始拼版", type="primary", key="imposition_btn"):
        if not source_pdfs:
            st.error("❌ 错误：请先上传需要拼版的PDF文件！")
        else:
            logs = []
            zip_buffer = io.BytesIO()
            
            with st.spinner("🚀 拼版任务执行中，请耐心等待..."):
                try:
                    def mm_to_points(mm): return mm * 72 / 25.4
                    
                    batch_size = cols * rows
                    num_batches = math.ceil(len(source_pdfs) / batch_size)
                    gap_pt = mm_to_points(gap_mm)
                    
                    logs.append(f"✅ 配置确认: {cols}x{rows} 网格, 间距 {gap_mm}mm。")
                    logs.append(f"✅ 共 {len(source_pdfs)} 个PDF, 将生成 {num_batches} 个拼版文件。")
                    
                    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_archive:
                        for i in range(num_batches):
                            start_index = i * batch_size
                            end_index = min((i + 1) * batch_size, len(source_pdfs))
                            batch_files = source_pdfs[start_index:end_index]
                            
                            if not batch_files: continue
                            
                            logs.append(f"\n📄 正在处理第 {i+1}/{num_batches} 批...")
                            
                            # 读取第一个文件的数据一次，并暂存起来
                            first_pdf_data = batch_files[0].read()
                            
                            with fitz.open(stream=first_pdf_data, filetype="pdf") as doc:
                                item_rect = doc[0].rect
                                item_width, item_height = item_rect.width, item_rect.height

                            page_width = (cols * item_width) + (cols - 1) * gap_pt + (2 * gap_pt)
                            page_height = (rows * item_height) + (rows - 1) * gap_pt + (2 * gap_pt)
                            
                            output_filename = f"layout_{cols}x{rows}_batch_{i+1}.pdf"
                            
                            with fitz.open() as new_doc:
                                page = new_doc.new_page(width=page_width, height=page_height)
                                for idx, uploaded_file in enumerate(batch_files):
                                    row = idx // cols
                                    col = idx % cols
                                    x0 = gap_pt + col * (item_width + gap_pt)
                                    y0 = gap_pt + row * (item_height + gap_pt)
                                    target_rect = fitz.Rect(x0, y0, x0 + item_width, y0 + item_height)
                                    
                                    try:
                                        # --- 【修改点】在这里判断 ---
                                        # 如果是批次中的第一个文件，直接使用暂存的数据
                                        if idx == 0:
                                            pdf_data = first_pdf_data
                                        # 如果是其他文件，正常读取
                                        else:
                                            pdf_data = uploaded_file.read()

                                        with fitz.open(stream=pdf_data, filetype="pdf") as src_doc:
                                            page.show_pdf_page(target_rect, src_doc, 0)
                                            # 日志可以移到 try 成功之后
                                            logs.append(f"  -> 已将 '{uploaded_file.name}' 放置在第 {row + 1} 行, 第 {col + 1} 列")
                                    except Exception as e:
                                        logs.append(f"  -> ⚠️ 警告: 放置文件 '{uploaded_file.name}' 时出错: {e}")
                                
                                pdf_bytes = new_doc.tobytes(garbage=4, deflate=True)
                                zip_archive.writestr(output_filename, pdf_bytes)
                                logs.append(f"  -> ✅ 第 {i+1} 批拼版完成 -> {output_filename}")

                    logs.append("\n🎉 全部PDF拼版任务完成！")
                except Exception as e:
                    st.error(f"❌ 发生致命错误: {e}")
                    return

            st.success("🎉 任务成功结束！")
            st.code("\n".join(logs), language="text")
            st.download_button(
                label="📥 点击下载包含所有拼版文件的ZIP包",
                data=zip_buffer.getvalue(),
                file_name="pdf_layouts.zip",
                mime="application/zip"
            )

# ===================================================================
# 主程序：侧边栏导航
# ===================================================================
st.sidebar.title("PDF 全能工具箱")

tool_options = {
    "1. 二维码位置调试器": tool_qr_placer,
    "2. PDF 批量生成器 (单码)": tool_batch_processor,
    "3. PDF 批量生成器 (双码)": tool_dual_qr_processor,
    "4. PDF 拼版工具": tool_pdf_imposition
}

selected_tool_name = st.sidebar.radio("请从下方选择一个工具：", list(tool_options.keys()))

# 执行选择的工具函数
tool_options[selected_tool_name]()

st.sidebar.info("应用由 Streamlit 构建 | 蔡誉行 开发")