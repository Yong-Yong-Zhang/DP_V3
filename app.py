import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import io

# 設定頁面配置
st.set_page_config(page_title="Data Plotting Tool Web", layout="wide")

# 初始化 Session State (用於儲存跨次互動的變數)
if 'markers' not in st.session_state:
    st.session_state.markers = {'Plot 1': [], 'Plot 2': []}
if 'file_configs' not in st.session_state:
    st.session_state.file_configs = {}  # 儲存檔案的顏色、標籤設定

def get_file_config_key(filename, tab_name):
    return f"{tab_name}_{filename}"

def main():
    st.title("Data Plotting Tool (Web Version)")
    
    # 建立分頁
    tab1, tab2 = st.tabs(["Plot 1", "Plot 2"])
    
    # 渲染每個分頁的內容
    render_tab(tab1, "Plot 1")
    render_tab(tab2, "Plot 2")

def render_tab(tab_obj, tab_name):
    with tab_obj:
        col_left, col_right = st.columns([1, 2])
        
        # --- 左側控制面板 ---
        with col_left:
            st.subheader("Data Selection")
            
            # 1. 檔案上傳 (取代原本的選擇資料夾)
            uploaded_files = st.file_uploader(
                f"Upload CSV Files for {tab_name}", 
                type=['csv'], 
                accept_multiple_files=True,
                key=f"uploader_{tab_name}"
            )
            
            if not uploaded_files:
                st.info("Please upload CSV files to begin.")
                return

            # 2. 數據設定 (跳過行數)
            with st.expander("Data Read Settings", expanded=False):
                c1, c2 = st.columns(2)
                skip_rows = c1.number_input("Skip Rows", min_value=0, value=0, key=f"skip_{tab_name}")
                header_row = c2.number_input("Header Row (0-index)", min_value=0, value=0, key=f"header_{tab_name}")

            # 讀取所有檔案的預覽以獲取欄位名稱
            try:
                # 讀取第一個檔案來獲取欄位
                first_df = pd.read_csv(uploaded_files[0], skiprows=skip_rows, header=header_row)
                columns = first_df.columns.tolist()
            except Exception as e:
                st.error(f"Error reading file: {e}")
                return

            # 3. 軸向選擇
            st.subheader("Axis Selection")
            c1, c2 = st.columns(2)
            x_col = c1.selectbox("X-axis Column", options=columns, index=0 if columns else 0, key=f"x_col_{tab_name}")
            y_col = c2.selectbox("Y-axis Column", options=columns, index=1 if len(columns)>1 else 0, key=f"y_col_{tab_name}")

            # 4. 檔案列表與設定 (使用 Data Editor 取代原本的 Treeview)
            st.subheader("File Management")
            
            # 準備 Data Editor 的資料
            file_data = []
            default_colors = ['red', 'blue', 'orange', 'green', 'brown', 'purple', '#8B008B', '#006400']
            
            for i, file in enumerate(uploaded_files):
                config_key = get_file_config_key(file.name, tab_name)
                
                # 如果沒有設定過，初始化預設值
                if config_key not in st.session_state.file_configs:
                    st.session_state.file_configs[config_key] = {
                        "selected": i < 6, # 預設選前6個
                        "label": file.name.replace(".csv", ""),
                        "color": default_colors[i % len(default_colors)]
                    }
                
                config = st.session_state.file_configs[config_key]
                file_data.append({
                    "Select": config["selected"],
                    "Filename": file.name,
                    "Label": config["label"],
                    "Color": config["color"]
                })
            
            df_files = pd.DataFrame(file_data)
            
            # 顯示可編輯的表格
            edited_df = st.data_editor(
                df_files,
                column_config={
                    "Select": st.column_config.CheckboxColumn("Show", help="Select to plot"),
                    "Color": st.column_config.ColorPickerColumn("Color"),
                    "Label": st.column_config.TextColumn("Label")
                },
                disabled=["Filename"],
                hide_index=True,
                key=f"editor_{tab_name}",
                use_container_width=True
            )
            
            # 更新 session state 中的設定
            for index, row in edited_df.iterrows():
                config_key = get_file_config_key(row["Filename"], tab_name)
                st.session_state.file_configs[config_key]["selected"] = row["Select"]
                st.session_state.file_configs[config_key]["label"] = row["Label"]
                st.session_state.file_configs[config_key]["color"] = row["Color"]

            # 5. 圖表設定 (Axis Limits & Labels)
            with st.expander("Chart Settings (Title, Limits, Ticks)"):
                title = st.text_input("Chart Title", value="Gain vs Input Power", key=f"title_{tab_name}")
                
                c1, c2 = st.columns(2)
                x_label = c1.text_input("X Label", value="Input Power (dBm)", key=f"xl_{tab_name}")
                y_label = c2.text_input("Y Label", value="Gain (dB)", key=f"yl_{tab_name}")
                
                st.markdown("**X-axis Limits**")
                c1, c2, c3 = st.columns(3)
                x_min = c1.number_input("Min", value=-10.0, step=1.0, key=f"xmin_{tab_name}")
                x_max = c2.number_input("Max", value=20.0, step=1.0, key=f"xmax_{tab_name}")
                x_step = c3.number_input("Step", value=5.0, step=1.0, key=f"xstep_{tab_name}")
                
                st.markdown("**Y-axis Limits**")
                c1, c2, c3 = st.columns(3)
                y_min = c1.number_input("Min", value=45.0, step=1.0, key=f"ymin_{tab_name}")
                y_max = c2.number_input("Max", value=50.0, step=1.0, key=f"ymax_{tab_name}")
                y_step = c3.number_input("Step", value=1.0, step=0.5, key=f"ystep_{tab_name}")
                
                st.markdown("**Style**")
                c1, c2 = st.columns(2)
                fig_width = c1.slider("Width", 5.0, 20.0, 10.0, key=f"fw_{tab_name}")
                fig_height = c2.slider("Height", 3.0, 15.0, 6.0, key=f"fh_{tab_name}")

        # --- 右側繪圖區域 ---
        with col_right:
            # 準備繪圖數據
            plot_data = []
            selected_files_map = {row["Filename"]: row for i, row in edited_df.iterrows() if row["Select"]}
            
            # 讀取並處理選中的檔案
            for file in uploaded_files:
                if file.name in selected_files_map:
                    cfg = selected_files_map[file.name]
                    try:
                        # 每次讀取需重置指標位置
                        file.seek(0)
                        df = pd.read_csv(file, skiprows=skip_rows, header=header_row)
                        
                        if x_col in df.columns and y_col in df.columns:
                            plot_data.append({
                                'x': df[x_col].values,
                                'y': df[y_col].values,
                                'label': cfg["Label"],
                                'color': cfg["Color"],
                                'filename': file.name
                            })
                    except Exception as e:
                        st.warning(f"Skipping {file.name}: {e}")

            if plot_data:
                fig, ax = plt.subplots(figsize=(fig_width, fig_height))
                
                # 繪製線條
                for item in plot_data:
                    ax.plot(item['x'], item['y'], '-o', label=item['label'], 
                           color=item['color'], linewidth=1.0, markersize=3.0)
                
                # 設定軸與標籤
                ax.set_title(title)
                ax.set_xlabel(x_label)
                ax.set_ylabel(y_label)
                
                # 設定刻度與範圍
                ax.set_xlim(x_min, x_max)
                ax.set_ylim(y_min, y_max)
                ax.set_xticks(np.arange(x_min, x_max + x_step, x_step))
                ax.set_yticks(np.arange(y_min, y_max + y_step, y_step))
                
                ax.grid(True, which='major', linestyle='-')
                ax.grid(True, which='minor', linestyle=':', alpha=0.5)
                ax.minorticks_on()
                ax.legend()

                # --- Marker 邏輯 ---
                markers_list = st.session_state.markers[tab_name]
                
                # 繪製現有的 Markers
                for m in markers_list:
                    ax.plot(m['x'], m['y'], 'ro', markersize=8)
                    ax.axhline(y=m['y'], color='r', linestyle='--', alpha=0.5)
                    ax.axvline(x=m['x'], color='r', linestyle='--', alpha=0.5)
                    ax.annotate(f"{m['name']}\n({m['x']:.2f}, {m['y']:.2f})",
                                xy=(m['x'], m['y']), xytext=(10, 10),
                                textcoords='offset points',
                                bbox=dict(boxstyle="round,pad=0.3", fc="yellow", alpha=0.8))
                
                # 顯示圖表
                st.pyplot(fig)
                
                st.divider()
                
                # --- Marker 控制區 ---
                st.subheader("Marker Tools")
                m_col1, m_col2, m_col3 = st.columns([1, 1, 2])
                
                with m_col1:
                    target_x = st.number_input("Target X Value", value=0.0, key=f"tx_{tab_name}")
                
                with m_col2:
                    target_line_label = st.selectbox("Select Line", 
                                                   options=[d['label'] for d in plot_data],
                                                   key=f"tl_{tab_name}")

                with m_col3:
                    st.write("Actions")
                    col_btn1, col_btn2, col_btn3 = st.columns(3)
                    
                    # 功能：新增標記
                    if col_btn1.button("Add Marker", key=f"add_m_{tab_name}"):
                        # 找到對應的線數據
                        line_d = next((d for d in plot_data if d['label'] == target_line_label), None)
                        if line_d:
                            idx = np.abs(line_d['x'] - target_x).argmin()
                            new_x, new_y = line_d['x'][idx], line_d['y'][idx]
                            
                            new_marker = {
                                'name': f"M{len(markers_list)+1}",
                                'x': new_x,
                                'y': new_y,
                                'line': target_line_label
                            }
                            st.session_state.markers[tab_name].append(new_marker)
                            st.rerun()

                    # 功能：OP1dB 計算
                    if col_btn2.button("Find OP1dB", key=f"op1_{tab_name}"):
                        if not markers_list:
                            st.error("Add a reference marker first (Linear point).")
                        else:
                            # 取最後一個標記當作參考點
                            ref_m = markers_list[-1]
                            line_d = next((d for d in plot_data if d['label'] == ref_m['line']), None)
                            
                            if line_d:
                                target_y = ref_m['y'] - 1.0
                                # 在 X > ref_x 的範圍內找
                                mask = line_d['x'] > ref_m['x']
                                valid_x = line_d['x'][mask]
                                valid_y = line_d['y'][mask]
                                
                                if len(valid_x) > 0:
                                    # 找最接近 target_y 的點
                                    idx = np.abs(valid_y - target_y).argmin()
                                    op1_x, op1_y = valid_x[idx], valid_y[idx]
                                    
                                    st.session_state.markers[tab_name].append({
                                        'name': "OP1dB",
                                        'x': op1_x,
                                        'y': op1_y,
                                        'line': ref_m['line']
                                    })
                                    st.success(f"OP1dB found at ({op1_x:.2f}, {op1_y:.2f})")
                                    st.rerun()
                                else:
                                    st.warning("Cannot find point -1dB drop in data range.")

                    # 功能：清除標記
                    if col_btn3.button("Clear All", key=f"clr_{tab_name}"):
                        st.session_state.markers[tab_name] = []
                        st.rerun()

                # 顯示標記表格
                if markers_list:
                    st.write("Current Markers:")
                    st.dataframe(pd.DataFrame(markers_list))

            else:
                st.info("Select files on the left to plot data.")

if __name__ == "__main__":
    main()