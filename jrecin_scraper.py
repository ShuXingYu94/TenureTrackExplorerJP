"""
JRec-IN Portal 爬虫 with only regex analysis
用于爬取理论经济学相关职位信息并解析详情页

包含两个主要部分：
1. 爬取搜索结果页面并提取所有职位URL
2. 获取职位详情页面并解析关键信息
"""

import requests
from bs4 import BeautifulSoup
import os
import time
import json
import re
from urllib.parse import urljoin
from jrecin_analyzer import *


# 创建数据目录结构
def create_directories():
    """创建必要的数据目录，如果目录已存在则清空其内容"""
    directories = [
        'jrecin_data',
        'jrecin_data/search_pages',
        'jrecin_data/job_details',
        'jrecin_data/job_details/html',
        'jrecin_data/job_details/json',
        "jrecin_data/job_details/llm_json"
    ]
    for directory in directories:
        if not os.path.exists(directory):
            # 创建不存在的目录
            os.makedirs(directory)

    # 需要保留的文件列表
    files_to_keep = [
        'jrecin_data/all_job_urls.json',
        'jrecin_data/previous_job_urls.json',
        'jrecin_data/new_job_urls.json'
    ]

    for directory in ['jrecin_data/job_details/html']:
        # 如果目录存在，清空其内容
        if os.path.exists(directory):
            print(f"清空目录: {directory}")
            # 列出目录中的所有文件和子目录
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)
                try:
                    if os.path.isfile(item_path):
                        # 如果是文件，直接删除
                        os.unlink(item_path)
                except Exception as e:
                    print(f"清空过程中出错: {e}")


# 设置请求头，模拟浏览器
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',  # 设置为日语优先
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

# 目标URL
base_url = 'https://jrecin.jst.go.jp'
search_url = 'https://jrecin.jst.go.jp/seek/SeekJorSearch'


# 第一部分：获取职位URL列表
def submit_search_request(session, keywords='理論経済学 経済学説 経済思想 経済政策', page=1, test_optimal=False):
    """提交搜索请求并获取结果页面"""
    try:
        # 如果是第一页，先获取初始页面以获取必要的表单字段和cookies
        if page == 1:
            print(f"获取初始页面...")
            response = session.get(search_url, headers=headers)
            response.raise_for_status()
            if test_optimal == True:
                # 保存初始页面（可选，用于调试）
                with open('jrecin_data/initial_page.html', 'w', encoding='utf-8-sig') as f:
                    f.write(response.text)
                print(f"初始页面已保存至 jrecin_data/initial_page.html")

            # 从页面中提取CSRF令牌
            soup = BeautifulSoup(response.text, 'html.parser')
            csrf_meta = soup.find('meta', {'name': '_csrf'})
            if csrf_meta:
                csrf_token = csrf_meta['content']
                csrf_header = soup.find('meta', {'name': '_csrf_header'})['content']
                headers[csrf_header] = csrf_token

        # 准备搜索表单数据
        form_data = {
            'keyword_or': keywords,
            'sort': '0',  # 新着順（按最新排序）
            'fn': '0',  # 猜测是form number或function
            'page': str(page)  # 页码
        }

        # 提交GET请求
        print(f"提交第{page}页搜索请求...")
        search_response = session.get(
            search_url,
            params=form_data,
            headers=headers
        )
        search_response.raise_for_status()

        if test_optimal == True:
            # 保存搜索结果页面（可选，用于调试）
            with open(f'jrecin_data/search_pages/page{page}.html', 'w', encoding='utf-8-sig') as f:
                f.write(search_response.text)
            print(f"搜索结果第{page}页已保存至 jrecin_data/search_pages/page{page}.html")

        return search_response.text

    except requests.exceptions.RequestException as e:
        print(f"请求出错: {e}")
        return None


def parse_search_results(html_content, page=1):
    """解析搜索结果页面，提取职位链接"""
    soup = BeautifulSoup(html_content, 'html.parser')
    job_links = []

    # 查找职位链接 - 通常JRec-IN中职位链接包含"D?id="字样
    links = soup.find_all('a', href=lambda href: href and ('D?id=' in href or 'Detail' in href))

    for link in links:
        title_elem = link.find('h3') or link.find('strong') or link
        title = title_elem.get_text(strip=True)

        # 构建完整URL
        href = link['href']
        if not href.startswith('http'):
            href = urljoin(base_url, href)

        # 提取职位ID
        job_id_match = re.search(r'D\d+', href)
        job_id = job_id_match.group(0) if job_id_match else None

        job_links.append({
            'url': href,
            'title': title,
            'job_id': job_id
        })

    # 查找分页信息，检查是否有下一页
    has_next_page = False
    next_page = page + 1

    # 查找分页元素
    pagination = soup.find('ul', class_='pagination') or soup.find('div', class_='paging')

    if pagination:
        # 查找"次へ"(下一页)按钮或者页码链接
        next_link = pagination.find('a', string=lambda s: s and ('次' in s or '次へ' in s))
        if next_link:
            has_next_page = True
        else:
            # 查找当前页码后的下一个页码链接
            page_links = pagination.find_all('a')
            for link in page_links:
                if link.get_text(strip=True).isdigit() and int(link.get_text(strip=True)) == next_page:
                    has_next_page = True
                    break

    # 保存解析结果
    result = {
        'page': page,
        'job_links': job_links,
        'has_next_page': has_next_page
    }

    # 将结果保存为JSON文件
    with open(f'jrecin_data/search_pages/parsed_page{page}.json', 'w', encoding='utf-8-sig') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"第{page}页解析完成，找到{len(job_links)}个职位链接")
    return result


def collect_all_job_urls(max_pages=10, keywords='理論経済学 経済学説 経済思想 経済政策', test_optimal=False):
    """收集所有搜索页面中的职位URL，并进行去重"""
    session = requests.Session()
    all_job_links = []

    # 爬取指定页数的搜索结果
    for page in range(1, max_pages + 1):
        # 提交搜索请求
        search_result = submit_search_request(session, page=page, keywords=keywords, test_optimal=test_optimal)
        if not search_result:
            print(f"获取第{page}页失败，停止爬取")
            break

        # 解析搜索结果
        parsed_result = parse_search_results(search_result, page)

        # 添加职位链接到总列表
        all_job_links.extend(parsed_result['job_links'])

        # 如果没有下一页，结束爬取
        if not parsed_result['has_next_page']:
            print("没有更多页面，结束爬取")
            break

        # 页面间延迟，避免请求过快
        if page < max_pages:
            print("等待2秒后爬取下一页...")
            time.sleep(2)

    # 去重处理
    unique_job_links = []
    job_ids = set()

    for job in all_job_links:
        if job['job_id'] and job['job_id'] not in job_ids:
            job_ids.add(job['job_id'])
            unique_job_links.append(job)

    # 保存去重后的URL列表
    with open('jrecin_data/all_job_urls.json', 'w', encoding='utf-8-sig') as f:
        json.dump(unique_job_links, f, ensure_ascii=False, indent=2)

    print(f"成功收集并去重，共找到{len(unique_job_links)}个职位链接")
    return unique_job_links


def compare_with_previous_urls():
    """比较当前URL列表与之前保存的URL列表，找出新增的URL"""
    # 加载当前的URL列表
    try:
        with open('jrecin_data/all_job_urls.json', 'r', encoding='utf-8-sig') as f:
            current_urls = json.load(f)
    except FileNotFoundError:
        print("当前URL列表不存在，无法比较")
        return None

    # 尝试加载之前的URL列表
    try:
        with open('jrecin_data/previous_job_urls.json', 'r', encoding='utf-8-sig') as f:
            previous_urls = json.load(f)
    except FileNotFoundError:
        print("之前URL列表不存在，所有URL视为新增")
        # 将当前列表复制为之前的列表，用于下次比较
        with open('jrecin_data/previous_job_urls.json', 'w', encoding='utf-8-sig') as f:
            json.dump(current_urls, f, ensure_ascii=False, indent=2)
        return current_urls

    # 获取之前的job_id集合
    previous_job_ids = {job['job_id'] for job in previous_urls if job.get('job_id')}

    # 找出新增的URL
    new_urls = [job for job in current_urls if job.get('job_id') and job['job_id'] not in previous_job_ids]

    # 更新之前的URL列表
    with open('jrecin_data/previous_job_urls.json', 'w', encoding='utf-8-sig') as f:
        json.dump(current_urls, f, ensure_ascii=False, indent=2)

    print(f"与之前的URL列表比较，找到{len(new_urls)}个新增的职位链接")

    # 保存新增的URL列表
    with open('jrecin_data/new_job_urls.json', 'w', encoding='utf-8-sig') as f:
        json.dump(new_urls, f, ensure_ascii=False, indent=2)

    return new_urls


def main(max_pages=10, max_jobs=None, keywords='理論経済学 経済学説 経済思想 経済政策', mode='full', test_optimal=False):
    """主函数，执行整个爬取过程"""
    # 创建目录
    create_directories()

    if mode in ['full', 'urls_only']:
        # 第一部分：收集所有职位URL并去重
        print("开始收集职位URL...")
        all_job_urls = collect_all_job_urls(max_pages=max_pages, keywords=keywords, test_optimal=test_optimal)

        # 比较与之前的URL列表，找出新增的URL
        new_job_urls = compare_with_previous_urls()

        if mode == 'urls_only':
            print("已完成URL收集和比较")
            return

    if mode in ['full', 'details_only']:
        # 第二部分：处理职位详情
        # 加载URL列表
        try:
            if mode == 'details_only':
                # 尝试加载新增的URL列表
                try:
                    with open('jrecin_data/new_job_urls.json', 'r', encoding='utf-8-sig') as f:
                        job_urls = json.load(f)
                    print(f"加载了{len(job_urls)}个新增的职位URL")
                except FileNotFoundError:
                    # 如果没有新增URL列表，则使用完整URL列表
                    with open('jrecin_data/all_job_urls.json', 'r', encoding='utf-8-sig') as f:
                        job_urls = json.load(f)
                    print(f"未找到新增URL列表，加载了{len(job_urls)}个完整职位URL")
            else:
                # 在full模式下，使用刚刚获取的新增URL
                job_urls = new_job_urls if new_job_urls else all_job_urls
        except FileNotFoundError:
            print("找不到URL列表文件，请先执行URL收集步骤")
            return

        # 处理职位详情
        if job_urls:
            print(f"开始处理{min(len(job_urls), max_jobs or len(job_urls))}个职位详情...")
            job_data_list = process_job_urls(job_urls, max_jobs)

            # 保存为CSV
            if job_data_list:
                save_to_csv(job_data_list, encoding='utf-8-sig')
        else:
            print("没有职位URL需要处理")


if __name__ == "__main__":
    # 执行完整爬虫流程，最多爬取10页，每页职位全部处理
    main(max_pages=10, max_jobs=None, mode='urls_only')

    # 可选模式:
    # 'urls_only': 只收集URL
    # 'details_only': 只处理详情（使用之前保存的URL）
    # 'full': 完整流程（默认）
