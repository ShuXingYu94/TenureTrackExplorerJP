"""
JRec-IN Portal职位详情LLM分析器
使用本地Ollama的DeepSeek-R1模型解析职位详情HTML文件
"""

import json
import os
import requests
import argparse
from bs4 import BeautifulSoup
import time

# Ollama API设置
OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "gemma3:12b"


# MODEL_NAME = "deepseek-r1:14b"


def load_html_file(file_path):
    """加载HTML文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        return html_content
    except Exception as e:
        print(f"读取HTML文件时出错: {e}")
        return None


def preprocess_html(html_content):
    """预处理HTML内容，简化以适应LLM处理"""
    try:
        # 使用BeautifulSoup解析HTML
        soup = BeautifulSoup(html_content, 'html.parser')

        # 提取主要内容区域，减少不必要的内容
        main_content = soup.find('div', class_='card')
        if main_content:
            return str(main_content)

        # 如果找不到特定区域，则尝试提取body内容并移除脚本和样式
        if soup.body:
            for script in soup.body.find_all(['script', 'style']):
                script.decompose()
            return str(soup.body)

        # 如果以上都失败，返回原始内容
        return html_content
    except Exception as e:
        print(f"预处理HTML时出错: {e}")
        return html_content


def generate_prompt(html_content):
    """生成发送给LLM的提示"""
    prompt = """
你是一名专业的HTML文档分析器，专门负责从JRec-IN Portal的职位详情页面提取结构化信息。
我会提供一个职位详情页面的HTML内容，请你分析并提取以下信息，并且以json的格式输出：



请仔细阅读HTML内容，尽可能准确地提取每个字段的信息。如果无法找到某个字段的信息，请将该字段值设为空字符串""或适当的默认值。
特别注意tenure_status字段，需要判断职位是否为テニュアトラック（终身教职轨道）。
对于teaching_requirements，请从职位描述中提取与教学相关的要求。

HTML内容:
"""

    prompt_end = """
    {
  "基本信息": {
    "position_title": "职位标题(比如教授，副教授，讲师，或者几个的组合？)",
    "institution": "机构名称",
    "institution_type": "机构类型（比如大学，民间公司等）",
  },
  "职位属性": {
    "location": "工作地点",
    "research_field": "研究领域",
    "position_type": "职位类型",
    "employment_type": "雇佣类型",
    "tenure_status": "任期状态"
  },
  "薪资和工作条件": {
    "salary": "薪资范围",
    "salary_description": "薪资说明",
    "working_hours_description": "工作时间说明"
  },
  "职位详情": {
    "job_description": "职位描述",
    "department": "所属部门",
    "qualifications": "资格要求",
    "teaching_requirements": "教学要求（具体教学哪几门课，是否可以日语教学）"
  }
}
以上是我所需要的信息。具体如何申请并不是我所关心的。请以以上给出的JSON格式返回提取的相关信息，不要包含任何其他解释或评论。"""

    return prompt + html_content + prompt_end


def query_ollama(prompt, max_retries=3, retry_delay=2):
    """向Ollama API发送请求并获取响应"""
    data = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }

    for attempt in range(max_retries):
        try:
            response = requests.post(OLLAMA_API_URL, json=data)
            response.raise_for_status()
            response_data = response.json()
            return response_data.get('response', '')
        except requests.exceptions.RequestException as e:
            print(f"尝试 {attempt + 1}/{max_retries} 请求Ollama API时出错: {e}")
            if attempt < max_retries - 1:
                print(f"等待 {retry_delay} 秒后重试...")
                time.sleep(retry_delay)
            else:
                print("已达到最大重试次数，放弃请求")
                return None


def extract_json_from_response(response_text):
    """从LLM响应中提取JSON部分"""
    print("The response of deepseek is: \n", response_text)
    try:
        # 尝试查找JSON块的开始和结束
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1

        if json_start >= 0 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            # 验证JSON是否有效
            return json.loads(json_str)
        else:
            print("无法在响应中找到JSON块")
            return None
    except json.JSONDecodeError as e:
        print(f"解析JSON时出错: {e}")
        print(f"问题的JSON字符串: {response_text}")
        return None


def analyze_job_html(file_path, output_file=None):
    """分析职位HTML文件并提取信息"""
    # 加载HTML文件
    html_content = load_html_file(file_path)
    if not html_content:
        return None

    # 预处理HTML
    print("预处理HTML内容...")
    processed_html = preprocess_html(html_content)

    # 生成提示
    print("生成提示并发送到Ollama...")
    prompt = generate_prompt(processed_html)

    # 查询Ollama
    start_time = time.time()
    response_text = query_ollama(prompt)
    end_time = time.time()

    if not response_text:
        print("未能从Ollama获取有效响应")
        return None

    print(f"LLM处理用时: {end_time - start_time:.2f}秒")

    # 提取JSON
    job_data = extract_json_from_response(response_text)

    # 保存结果
    if job_data and output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(job_data, f, ensure_ascii=False, indent=2)
        print(f"分析结果已保存至 {output_file}")

    return job_data


def main():
    # 设置命令行参数
    parser = argparse.ArgumentParser(description='使用LLM分析JRec-IN Portal职位HTML')
    parser.add_argument('html_file', help='要分析的HTML文件路径')
    parser.add_argument('--output', '-o', help='输出JSON文件路径')
    args = parser.parse_args()

    # 生成默认输出文件名
    if not args.output:
        base_name = os.path.splitext(os.path.basename(args.html_file))[0]
        args.output = f"{base_name}_llm_analysis.json"

    # 分析HTML
    print(f"开始分析HTML文件: {args.html_file}")
    job_data = analyze_job_html(args.html_file, args.output)

    if job_data:
        print("分析成功完成")
        # 打印部分结果以供预览
        preview = {
            "职位标题": job_data["基本信息"]["position_title"],
            "机构名称": job_data["基本信息"]["institution"],
            "任期状态": job_data["职位属性"]["tenure_status"]
        }
        print("结果预览:")
        print(json.dumps(preview, ensure_ascii=False, indent=2))
    else:
        print("分析失败")


if __name__ == "__main__":
    main()
