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
# 工具一：二维码位置调试器
# ===================================================================
def tool_qr_placer():
    st.title("工具一：二维码位置调试器")
    st.info("说明：实时预览二维码在PDF上的位置与大小，获取精确的坐标值。")

    st.sidebar.header("上传文件")
    uploaded_pdf = st.sidebar.file_uploader("上传PDF底图", type=["pdf"], key="placer_pdf")
    uploaded_qrs = st.sidebar.file_uploader("上传二维码图片(可多选)", type=["png", "jpg", "jpeg"], accept_multiple_files=True, key="placer_qrs")

    if uploaded_pdf and uploaded_qrs:
        # ... (代码与之前版本相同，为节省篇幅此处省略) ...
        # (The code for this function is identical to the previous version and is omitted for brevity)
        pdf_data = uploaded_pdf.read()
        doc = fitz.open(stream=pdf_data, filetype="pdf")
        pix = doc[0].get_pixmap(dpi=72)
        base_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        doc.close()
        qr_data = uploaded_qrs[0].read()
        qr_img = Image.open(io.BytesIO(qr_data)).convert("RGBA")
        st.sidebar.header("参数调整")
        x_pos = st.sidebar.slider("X 坐标：", min_value=0, max_value=base_img.width, value=110)
        y_pos = st.sidebar.slider("Y 坐标：", min_value=0, max_value=base_img.height, value=140)
        width = st.sidebar.slider("宽度 W：", min_value=1, max_value=base_img.width, value=210)
        height = st.sidebar.slider("高度 H：", min_value=1, max_value=base_img.height, value=210)
        resized_qr = qr_img.resize((width, height), Image.LANCZOS)
        final_image = base_img.copy()
        final_image.paste(resized_qr, (x_pos, y_pos), resized_qr)
        st.image(final_image, caption="实时预览效果", use_column_width=True)
        st.success(f"当前坐标: X={x_pos}, Y={y_pos} | 当前尺寸: W={width}, H={height}")
    else:
        st.warning("⚠️ 请在左侧上传PDF底图和二维码图片以开始操作。")


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
    with col1: x_val = st.number_input("X 坐标", value=43, format="%d", key="proc_x")
    with col2: y_val = st.number_input("Y 坐标", value=137, format="%d", key="proc_y")
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
    st.title("工具三：双二维码批量合成器")
    st.info("说明：在同一个PDF模板上同时批量插入左右两个二维码。")

    # ... (代码与之前版本相同，为节省篇幅此处省略) ...
    # (The code for this function is identical to the previous version and is omitted for brevity)
    template_pdf = st.file_uploader("上传PDF模板", type=["pdf"], key="dual_pdf")
    left_qrs = st.file_uploader("上传所有左侧二维码", type=["png", "jpg", "jpeg"], accept_multiple_files=True, key="dual_qrs_left")
    right_qrs = st.file_uploader("上传所有右侧二维码", type=["png", "jpg", "jpeg"], accept_multiple_files=True, key="dual_qrs_right")
    st.subheader("输入坐标和尺寸")
    col1, col2 = st.columns(2)
    with col1: st.markdown("##### 左侧二维码"); xL = st.number_input("左 X", 110, format="%d", key="dual_xL"); yL = st.number_input("左 Y", 140, format="%d", key="dual_yL")
    with col2: st.markdown("##### 右侧二维码"); xR = st.number_input("右 X", 463, format="%d", key="dual_xR"); yR = st.number_input("右 Y", 140, format="%d", key="dual_yR")
    st.markdown("##### 共享尺寸"); col_w, col_h = st.columns(2)
    with col_w: W = st.number_input("宽度 W", 210, format="%d", key="dual_W")
    with col_h: H = st.number_input("高度 H", 210, format="%d", key="dual_H")
    if st.button("开始合成双二维码PDF", type="primary", key="dual_btn"):
        if not all([template_pdf, left_qrs, right_qrs]): st.error("❌ 错误：请务必上传所有文件！")
        else:
            pair_count = min(len(left_qrs), len(right_qrs))
            if len(left_qrs) != len(right_qrs): st.warning(f"ℹ️ 提示：两侧数量不同，已按最短的 {pair_count} 对处理。")
            pairs = list(zip(left_qrs, right_qrs))
            zip_buffer = io.BytesIO()
            with st.spinner(f"正在生成 {pair_count} 份PDF..."):
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as z:
                    tpl_data = template_pdf.read()
                    for l_qr, r_qr in pairs:
                        doc = fitz.open(stream=tpl_data, filetype="pdf")
                        page = doc[0]
                        page.insert_image(fitz.Rect(xL, yL, xL + W, yL + H), stream=l_qr.read(), overlay=True)
                        page.insert_image(fitz.Rect(xR, yR, xR + W, yR + H), stream=r_qr.read(), overlay=True)
                        fname = f"{os.path.splitext(l_qr.name)[0]}+{os.path.splitext(r_qr.name)[0]}.pdf"
                        z.writestr(fname, doc.tobytes())
                        doc.close()
            st.success(f"✅ 处理完成！已生成 {pair_count} 份PDF。")
            st.download_button(label="📥 点击下载ZIP压缩包", data=zip_buffer.getvalue(), file_name="dual_qr_pdfs.zip", mime="application/zip")


# ===================================================================
# 工具四：PDF 拼版工具
# ===================================================================
def tool_pdf_imposition():
    st.title("工具四：PDF 拼版工具")
    st.info("说明：将大量单页PDF文件，按照指定的网格布局，拼接到新的、更大的PDF页面上。")

    # --- 输入 ---
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
                            
                            # 获取基准尺寸
                            first_pdf_data = batch_files[0].read()
                            with fitz.open(stream=first_pdf_data, filetype="pdf") as doc:
                                item_rect = doc[0].rect
                                item_width, item_height = item_rect.width, item_rect.height

                            # 计算新页面尺寸
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
                                        # 读取每个PDF文件的数据
                                        pdf_data = uploaded_file.read()
                                        with fitz.open(stream=pdf_data, filetype="pdf") as src_doc:
                                            page.show_pdf_page(target_rect, src_doc, 0)
                                    except Exception as e:
                                        logs.append(f"  -> ⚠️ 警告: 放置文件 '{uploaded_file.name}' 时出错: {e}")
                                
                                pdf_bytes = new_doc.tobytes(garbage=4, deflate=True)
                                zip_archive.writestr(output_filename, pdf_bytes)
                                logs.append(f"  -> ✅ 第 {i+1} 批拼版完成 -> {output_filename}")

                    logs.append("\n🎉 全部PDF拼版任务完成！")
                except Exception as e:
                    st.error(f"❌ 发生致命错误: {e}")
                    return

            # --- 显示结果 ---
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

st.sidebar.info("应用由 Streamlit 构建 | 蔡誉行开发")