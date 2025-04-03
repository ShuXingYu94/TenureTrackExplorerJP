# TenureTrack Explorer(JP)

[![Open in GitHub](https://img.shields.io/badge/GitHub-181717?style=flat&logo=github&logoColor=white)](https://github.com/ShuXingYu94/TenureTrackExplorerJP)  [![Built with streamlit](https://img.shields.io/badge/-Streamlit-FF4B4B?style=flat&logo=streamlit&logoColor=white)](https://streamlit.io/)  [![Static Badge](https://img.shields.io/badge/JREC--IN-PORTAL-test?logoSize=3&labelColor=grey&color=white)](https://jrecin.jst.go.jp/seek/SeekTop)

A tool for scraping and analyzing academic job postings from JRec-IN Portal for academic positions.

* Contains AI generated codes.
* Due to the complexity of the information, using **"Collect URL only"** mode and manually review all pages is most
  recommended.

## Features

* Web crawler for JRec-IN Portal job listings
* Automated extraction of key information from job postings
* Incremental updates to track new job postings
* User-friendly Streamlit interface for controlling the scraper
* Analysis of tenure track status, salary, teaching requirements and more (LLM analysis also included
  in `jrecin_llm_analyzer.py`, but local deployment required)

## Installation

### Prerequisites

* Python 3.8+
* pip (Python package installer)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/ShuXingYu94/TenureTrackExplorerJP.git
   cd TenureTrackExplorerJP
   ```
2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

## File Structure

```
TenureTrackExplorerJP/
├── TTEJP_ui.py                  # Streamlit web interface
├── jrecin_scraper.py            # Main scraper module
├── jrecin_analyzer.py           # Job posting analyzer module
├── jrecin_LLM_analyzer.py       # Job posting analyzer module using local LLMs
├── requirements.txt             # Python dependencies
├── README.md                    # This documentation
└── jrecin_data/                 # Directory for scraped data (created automatically)
    ├── search_pages/            # Search results HTML and parsed JSON
    ├── job_details/             # Job details
    │   ├── html/                # Original HTML of job postings
    │   ├── json/                # Parsed job information in JSON format
    │   └── llm_json/            # Optional LLM-enhanced parsing results
    ├── all_job_urls.json        # All job URLs collected
    ├── previous_job_urls.json   # Previously collected job URLs
    ├── new_job_urls.json        # Newly discovered job URLs
    └── info_jobs.csv            # CSV export of all job data
```

## Usage

### Running the Application

Launch the Streamlit interface:

```bash
# cd TenureTrackExplorerJP/
streamlit run TTEJP_ui.py
```

This will open a web browser with the TenureTrack Explorer interface.

Also, direct execution of jrecin_scraper.py is also available.

### Using the Interface

The interface is divided into several sections:

#### Parameters (Sidebar)

* **Mode**: Choose between:
    * **Collect URL only**: Just gather job posting URLs for manual review
    * **Process details only**: Process already collected URLs
    * **Full workflow**: Collect URLs and process details
* **Keywords**: Enter search terms (space-separated)
    * Default: `理論経済学 経済学説 経済思想 経済政策`
* **Max crawling pages**: Set the maximum number of search result pages to process
* **Max jobs to process**: Limit the number of job details to process (when applicable)
* **Process all jobs**: Toggle to process all available jobs
* **Test mode**: Enable to save more intermediate files for debugging

#### Running the Scraper

1. Configure the desired parameters in the sidebar
2. Click the "Run" button at the bottom of the sidebar
3. The status display will show progress and completion information

#### Viewing Results

After running the scraper, you can view:

* **List of new positions**: Recently discovered job postings
* **List of all positions**: Complete database of all job postings found

The application automatically displays the number of positions and provides clickable links to the original job
postings.

### Command Line Usage

You can also run the scraper directly from the command line:

```bash
python -c "from jrecin_scraper import main; main(max_pages=10, max_jobs=None, keywords='理論経済学 経済学説 経済思想 経済政策', mode='urls_only')"
```

Available modes:

* `urls_only`: Only collect URLs
* `details_only`: Only process details from previously collected URLs
* `full`: Complete workflow (collect URLs and process details)

## Regular Updates

To keep your job database up-to-date:

1. Run the application periodically (e.g., weekly)
2. Use "Collect URL only" mode first to find new postings
3. Then use "Process details only" to analyze new postings
4. The system will automatically track which positions are new

## Data Format

Job postings are analyzed and stored with the following information structure:

```json
{
  "基本信息": {
    "position_title": "职位标题",
    "institution": "机构名称",
    "job_id": "职位ID",
    "institution_type": "机构类型",
    "update_date": "更新日期",
    "application_deadline": "申请截止日期"
  },
  "职位属性": {
    "location": "工作地点",
    "research_field": "研究领域",
    "position_type": "职位类型",
    "employment_type": "雇佣类型",
    "tenure_status": "任期状态",
    "trial_period": "试用期"
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
    "teaching_requirements": "教学要求",
    "application_method": "申请方法"
  },
  "其他信息": {
    "notes": "备注",
    "is_active": true,
    "original_url": "原始链接"
  }
}
```

## Requirements

The following Python packages are required:

```
streamlit>=1.26.0
pandas>=1.5.3
requests>=2.28.2
beautifulsoup4>=4.11.2
```

## Troubleshooting

### Common Issues

1. **No job postings found**:
    * Check your internet connection
    * Verify that the search keywords are appropriate
    * JRec-IN Portal might have changed their page structure
2. **Error accessing files**:
    * Ensure you have write permissions in the application directory
    * Check if antivirus software is blocking file operations
3. **Streamlit interface not loading**:
    * Verify that all dependencies are installed
    * Check for port conflicts (default port is 8501)

## Acknowledgments

* [JRec-IN Portal](https://jrecin.jst.go.jp/seek/SeekTop) for providing academic job information
* [Streamlit](https://streamlit.io/) for the web interface framework

## Contact

For issues, suggestions, or contributions, please open an issue on
the [GitHub repository](https://github.com/ShuXingYu94/TenureTrackExplorerJP).
