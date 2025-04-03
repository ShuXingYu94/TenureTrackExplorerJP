"""
JRec-IN Portal爬虫 - Streamlit界面
用于控制爬虫参数、启动爬取过程并查看结果
"""

import streamlit as st
import pandas as pd
import json
import os
import sys
import time
from datetime import datetime

# import subprocess
# import importlib.util
# from jrecin_analyzer import *
# from jrecin_scraper import *
# from jrecin_llm_analyzer import *

# 导入爬虫模块
try:
    # 确保爬虫模块可以导入
    sys.path.append(os.path.abspath('.'))
    from jrecin_scraper import main as run_scraper
except ImportError:
    st.error("Unable to import the scraper module, please ensure that jrecin_scraper.py is in the same directory.")

# 页面配置
st.set_page_config(
    page_title="TenureTrack Explorer(JP)",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 标题和介绍
st.title("TenureTrack Explorer(JP)")
st.markdown(
    "[![Open in GitHub](https://img.shields.io/badge/GitHub-181717?style=flat&logo=github&logoColor=white)](https://github.com/ShuXingYu94/TenureTrackExplorerJP)&nbsp;&nbsp;  [![Built with streamlit](https://img.shields.io/badge/-Streamlit-FF4B4B?style=flat&logo=streamlit&logoColor=white)](https://streamlit.io/)&nbsp;&nbsp;  [![Static Badge](https://img.shields.io/badge/JREC--IN-PORTAL-test?logoSize=3&labelColor=grey&color=white)](https://jrecin.jst.go.jp/seek/SeekTop)")
st.markdown("")

st.markdown("""
#### Scrape job information from the **JRec-IN** Portal website""")

# 侧边栏 - 参数设置
st.sidebar.header("Parameters")

# 运行模式选择
run_mode = st.sidebar.radio(
    "Mode",
    ["Collect URL only", "Process details only", "Full workflow"],
    index=0
)

# 将显示名称转换为程序中的模式值
mode_map = {
    "Collect URL only": "urls_only",
    "Process details only": "details_only",
    "Full workflow": "full"
}

# 关键词设置
default_keywords = "理論経済学 経済学説 経済思想 経済政策"
keywords = st.sidebar.text_area("Keywords (with space in between)", default_keywords)

# 最大页数设置
max_pages = st.sidebar.slider("Max crawling pages", 1, 30, 10)

# 如果选择了处理详情页面，显示最大处理职位数量选项
if run_mode != "Collect URL only":
    max_jobs = st.sidebar.slider("Max jobs to process", 1, 100, 10,
                                 help="Limit the number of jobs to process. None means process all jobs")
    use_all_jobs = st.sidebar.checkbox("Process all jobs", value=False)
else:
    max_jobs = 10
    use_all_jobs = False

# 测试模式选项
test_mode = st.sidebar.checkbox("Test mode", value=False,
                                help="Enable test mode to save more intermediate files for debugging.")

execution = st.sidebar.button("Run")

# 主界面

# 显示当前状态
status_placeholder = st.empty()
status_placeholder.info("Please click the Run button to start scraping.")

# 运行按钮
if execution:
    # 准备运行参数
    mode = mode_map[run_mode]
    jobs_param = None if use_all_jobs else max_jobs

    # 更新状态
    status_placeholder.info(f"Running on: {run_mode}, Keywords: {keywords}, Max pages: {max_pages}")

    # 记录开始时间
    start_time = time.time()

    try:
        # 运行爬虫
        run_scraper(max_pages=max_pages,
                    max_jobs=jobs_param,
                    keywords=keywords,
                    mode=mode,
                    test_optimal=test_mode)

        # 计算运行时间
        end_time = time.time()
        elapsed_time = end_time - start_time

        # 更新状态
        status_placeholder.success(f"Complete! Time consumed: {elapsed_time:.2f} s")

    except Exception as e:
        status_placeholder.error(f"Error occurred: {str(e)}")

# 爬取结果查看
st.header("Result")

# New
st.markdown("#### List of new positions")

# 检查URL列表文件是否存在
all_urls_file = 'jrecin_data/all_job_urls.json'
new_urls_file = 'jrecin_data/new_job_urls.json'

if os.path.exists(new_urls_file):
    try:
        with open(new_urls_file, 'r', encoding='utf-8-sig') as f:
            all_urls = json.load(f)

        # 显示URL总数
        st.info(f"A total of {len(all_urls)} position detected.")

        # 将URL列表转换为DataFrame并显示
        url_df = pd.DataFrame(all_urls)
        st.dataframe(
            url_df,
            column_config={
                "url": st.column_config.LinkColumn(
                    "Link"
                )
            },
            hide_index=True,
        )

    except Exception as e:
        st.error(f"Error while trying to access file: {str(e)}")
else:
    st.warning("URL list file does not exist, please run the crawler to collect URLs first.")

# All
st.markdown("#### List of all positions")

# 检查URL列表文件是否存在
all_urls_file = 'jrecin_data/all_job_urls.json'
new_urls_file = 'jrecin_data/new_job_urls.json'

if os.path.exists(all_urls_file):
    try:
        with open(all_urls_file, 'r', encoding='utf-8-sig') as f:
            all_urls = json.load(f)

        # 显示URL总数
        st.info(f"A total of {len(all_urls)} position detected.")

        # 将URL列表转换为DataFrame并显示
        url_df = pd.DataFrame(all_urls)

        st.dataframe(
            url_df,
            column_config={
                "url": st.column_config.LinkColumn(
                    "Link"
                )
            },
            hide_index=True,
        )

    except Exception as e:
        st.error(f"Error while trying to access file: {str(e)}")
else:
    st.warning("URL list file does not exist, please run the crawler to collect URLs first.")

# 底部信息
st.markdown("---")
st.markdown(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
