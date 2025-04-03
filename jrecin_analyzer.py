import csv
from datetime import datetime


# 第二部分：获取并解析职位详情
def fetch_job_details(session, job_url, job_id):
    """获取职位详情页面"""
    try:
        print(f"获取职位详情: {job_url}")
        response = session.get(job_url, headers=headers)
        response.raise_for_status()

        # 保存详情页面
        file_path = f'jrecin_data/job_details/html/{job_id}.html'
        with open(file_path, 'w', encoding='utf-8-sig') as f:
            f.write(response.text)

        print(f"职位详情已保存至 {file_path}")
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"获取职位详情出错: {e}")
        return None


def parse_job_details(html_content, job_url, job_id):
    """解析职位详情页面，提取关键信息"""
    soup = BeautifulSoup(html_content, 'html.parser')

    # 初始化结果字典
    job_data = {
        "基本信息": {
            "position_title": "",
            "institution": "",
            "job_id": job_id,
            "institution_type": "",
            "update_date": "",
            "application_deadline": ""
        },
        "职位属性": {
            "location": "",
            "research_field": "",
            "position_type": "",
            "employment_type": "",
            "tenure_status": "",
            "trial_period": ""
        },
        "薪资和工作条件": {
            "salary": "",
            "salary_description": "",
            "working_hours_description": ""
        },
        "职位详情": {
            "job_description": "",
            "department": "",
            "qualifications": "",
            "teaching_requirements": "",
            "application_method": ""
        },
        "其他信息": {
            "notes": "",
            "is_active": True,
            "original_url": job_url
        }
    }

    # 提取基本信息
    # 职位标题
    title_elem = soup.find('h5', class_='card_title_min')
    if title_elem:
        job_data["基本信息"]["position_title"] = title_elem.get_text(strip=True)

    # 机构名称
    institution_elem = soup.find('p', class_=lambda c: c and 'orgModalLink' in c)
    if institution_elem:
        job_data["基本信息"]["institution"] = re.sub(r'<i.*', '', institution_elem.get_text(strip=True))

    # 机构类型
    institution_type_elem = soup.find('span', class_='tag_line')
    if institution_type_elem:
        job_data["基本信息"]["institution_type"] = institution_type_elem.get_text(strip=True)

    # 日期信息
    date_elements = soup.find_all('span', string=lambda s: s and ('更新日' in s or '募集終了日' in s))
    for date_elem in date_elements:
        date_text = date_elem.get_text(strip=True)
        if '更新日' in date_text:
            job_data["基本信息"]["update_date"] = date_text.replace('更新日', '').replace(':', '').strip()
        elif '募集終了日' in date_text:
            job_data["基本信息"]["application_deadline"] = date_text.replace('募集終了日', '').replace(':', '').strip()

    # 提取职位属性
    # 工作地点
    location_elem = soup.find('p', string=lambda s: s and '勤務地' in s)
    if location_elem:
        location_text = location_elem.get_text(strip=True).replace('勤務地 : ', '')
        job_data["职位属性"]["location"] = location_text

    # 研究领域
    research_field_elem = soup.find('p', string=lambda s: s and '研究分野' in s)
    if research_field_elem:
        research_field_text = research_field_elem.get_text(strip=True).replace('研究分野 : ', '')
        job_data["职位属性"]["research_field"] = research_field_text

    # 职位类型和雇佣信息
    position_elem = soup.find('i', class_='fa-solid fa-briefcase')
    if position_elem and position_elem.find_next('p'):
        position_text = position_elem.find_next('p').get_text(strip=True)
        # 尝试从文本中提取各种信息
        position_parts = position_text.split(':')
        if len(position_parts) >= 2:
            job_data["职位属性"]["position_type"] = position_parts[0].strip()

            employment_info = position_parts[1].strip()
            info_parts = employment_info.split('-')

            # 提取雇佣类型
            if len(info_parts) >= 1:
                job_data["职位属性"]["employment_type"] = info_parts[0].strip()

            # 提取任期状态
            tenure_pattern = r'任期(あり|なし)|テニュアトラック'
            tenure_match = re.search(tenure_pattern, employment_info)
            if tenure_match:
                job_data["职位属性"]["tenure_status"] = tenure_match.group(0)

            # 提取试用期
            trial_pattern = r'試用期間(あり|なし)'
            trial_match = re.search(trial_pattern, employment_info)
            if trial_match:
                job_data["职位属性"]["trial_period"] = trial_match.group(0)

    # 提取薪资和工作条件
    # 薪资信息
    salary_elems = soup.find_all('p', string=lambda s: s and '年収' in s)
    for elem in salary_elems:
        salary_text = elem.get_text(strip=True)
        if '年収' in salary_text:
            job_data["薪资和工作条件"]["salary"] = salary_text.replace('年収 : ', '')

    # 薪资说明
    salary_section = soup.find('p', class_='card_subTitle', string='給与')
    if salary_section and salary_section.find_next('p'):
        salary_desc = salary_section.find_next('p').get_text(strip=True)
        job_data["薪资和工作条件"]["salary_description"] = salary_desc

    # 工作时间说明
    work_time_section = soup.find('p', class_='card_subTitle', string='勤務時間')
    if work_time_section:
        work_time_desc = ""
        next_elems = work_time_section.find_next_siblings('ul')
        if next_elems:
            for elem in next_elems[0].find_all('p'):
                work_time_desc += elem.get_text(strip=True) + " "
        job_data["薪资和工作条件"]["working_hours_description"] = work_time_desc.strip()

    # 提取职位详情
    # 职位描述
    job_desc_elem = soup.find('p', class_='card_listTitle', string='仕事内容・職務内容')
    if job_desc_elem and job_desc_elem.find_next('p'):
        job_data["职位详情"]["job_description"] = job_desc_elem.find_next('p').get_text(strip=True)

        # 提取教学要求
        teaching_pattern = r'担当科目：.*|教育負担：.*|授業：.*'
        teaching_match = re.search(teaching_pattern, job_data["职位详情"]["job_description"])
        if teaching_match:
            job_data["职位详情"]["teaching_requirements"] = teaching_match.group(0)

    # 部门信息
    department_elem = soup.find('p', class_='card_listTitle', string='配属部署')
    if department_elem and department_elem.find_next('p'):
        job_data["职位详情"]["department"] = department_elem.find_next('p').get_text(strip=True)

    # 资格要求
    qualifications_section = soup.find('p', class_='card_subTitle', string='応募資格')
    if qualifications_section:
        quals_text = ""
        for elem in qualifications_section.find_next_siblings('ul')[0].find_all('p'):
            quals_text += elem.get_text(strip=True) + " "
        job_data["职位详情"]["qualifications"] = quals_text.strip()

    # 申请方法
    application_section = soup.find('p', class_='card_subTitle', string='応募方法')
    if application_section:
        app_text = ""
        for elem in application_section.find_next_siblings('ul')[0].find_all('p'):
            app_text += elem.get_text(strip=True) + " "
        job_data["职位详情"]["application_method"] = app_text.strip()

    # 提取其他信息
    # 备注
    notes_section = soup.find('p', class_='card_subTitle', string='備考')
    if notes_section and notes_section.find_next('div'):
        job_data["其他信息"]["notes"] = notes_section.find_next('div').get_text(strip=True)

    # 判断职位是否有效（基于当前日期和截止日期）
    if job_data["基本信息"]["application_deadline"]:
        try:
            # 假设日期格式为"YYYY年MM月DD日"
            deadline_str = job_data["基本信息"]["application_deadline"]
            # 将日期转换为datetime对象
            deadline_parts = re.findall(r'\d+', deadline_str)
            if len(deadline_parts) >= 3:
                year, month, day = int(deadline_parts[0]), int(deadline_parts[1]), int(deadline_parts[2])
                deadline_date = datetime(year, month, day)
                current_date = datetime.now()
                job_data["其他信息"]["is_active"] = (deadline_date >= current_date)
        except Exception as e:
            print(f"日期解析错误: {e}")

    return job_data


def process_job_urls(urls, max_jobs=None):
    """处理职位URL列表，获取并解析详情页面"""
    session = requests.Session()
    all_job_data = []

    # 限制处理的职位数量
    if max_jobs is not None:
        urls = urls[:max_jobs]

    for i, job in enumerate(urls, 1):
        print(f"处理第 {i}/{len(urls)} 个职位 - {job['job_id']}")

        # 获取职位详情页面
        job_html = fetch_job_details(session, job['url'], job['job_id'])

        if job_html:
            # 解析职位详情
            job_data = parse_job_details(job_html, job['url'], job['job_id'])

            # 保存解析结果
            with open(f'jrecin_data/job_details/json/{job["job_id"]}.json', 'w', encoding='utf-8-sig') as f:
                json.dump(job_data, f, ensure_ascii=False, indent=2)

            all_job_data.append(job_data)

            # 添加延迟，避免请求过快
            if i < len(urls):
                time.sleep(1)

    # 保存所有职位数据
    with open('jrecin_data/all_job_data.json', 'w', encoding='utf-8-sig') as f:
        json.dump(all_job_data, f, ensure_ascii=False, indent=2)

    print(f"成功处理 {len(all_job_data)} 个职位详情")
    return all_job_data


def save_to_csv(job_data_list, filename='jrecin_data/economic_jobs.csv', encoding='utf-8-sig'):
    """将职位数据保存为CSV文件"""
    if not job_data_list:
        print("没有职位数据可保存")
        return

    # 准备CSV表头
    fieldnames = [
        "职位标题", "机构名称", "职位ID", "机构类型", "更新日期", "申请截止日期",
        "工作地点", "研究领域", "职位类型", "雇佣类型", "任期状态", "试用期",
        "薪资", "薪资说明", "工作时间说明",
        "职位描述", "部门", "资格要求", "教学要求", "申请方法",
        "备注", "是否有效", "原始链接"
    ]

    # 准备CSV数据
    csv_data = []
    for job in job_data_list:
        row = {
            "职位标题": job["基本信息"]["position_title"],
            "机构名称": job["基本信息"]["institution"],
            "职位ID": job["基本信息"]["job_id"],
            "机构类型": job["基本信息"]["institution_type"],
            "更新日期": job["基本信息"]["update_date"],
            "申请截止日期": job["基本信息"]["application_deadline"],
            "工作地点": job["职位属性"]["location"],
            "研究领域": job["职位属性"]["research_field"],
            "职位类型": job["职位属性"]["position_type"],
            "雇佣类型": job["职位属性"]["employment_type"],
            "任期状态": job["职位属性"]["tenure_status"],
            "试用期": job["职位属性"]["trial_period"],
            "薪资": job["薪资和工作条件"]["salary"],
            "薪资说明": job["薪资和工作条件"]["salary_description"],
            "工作时间说明": job["薪资和工作条件"]["working_hours_description"],
            "职位描述": job["职位详情"]["job_description"],
            "部门": job["职位详情"]["department"],
            "资格要求": job["职位详情"]["qualifications"],
            "教学要求": job["职位详情"]["teaching_requirements"],
            "申请方法": job["职位详情"]["application_method"],
            "备注": job["其他信息"]["notes"],
            "是否有效": job["其他信息"]["is_active"],
            "原始链接": job["其他信息"]["original_url"],
        }
        csv_data.append(row)

    # 写入CSV文件
    with open(filename, 'w', encoding='utf-8-sig', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in csv_data:
            writer.writerow(row)

    print(f"已将{len(csv_data)}条职位信息保存至{filename}")
