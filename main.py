# -*- coding: utf-8 -*-
import os
import re
import time
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

# --- 用户配置 ---

# 1. 选择抓取模式: 'keyword' (关键词模式) 或 'category' (分类模式)
FETCH_METHOD = 'category' # <-- 在这里切换模式

# 2. 关键词模式配置
KEYWORDS = [
    "translational medicine",
    "systems biology",
    "synthetic biology",
    "genomics",
    "bioinformatics",
    "medical artificial intelligence",
    "medical ai"
]

# 3. 分类模式配置
# 您可以根据自己的兴趣修改下面的分类列表
ARXIV_CATEGORIES = [
    'cs.AI',    # 人工智能
    'cs.LG',    # 机器学习
    'cs.CV',    # 计算机视觉
    'q-bio.GN', # 基因组学
    'q-bio.MN', # 分子网络
    'q-bio.CB', # 细胞行为
    'q-bio.BM', # 生物分子
    'q-bio.QM'  # 定量方法
]

BIORXIV_CATEGORIES = [
    'bioengineering',
    'bioinformatics',
    'genomics',
    'synthetic biology',
    'systems biology',
    'molecular biology',
    'cancer biology'
]

# 4. 通用配置
BASE_DOWNLOAD_DIR = "ResearchPapers"
# 在分类模式下，获取过去多少天的论文 (1 = 只获取今天)
CATEGORY_FETCH_DAYS_AGO = 2
# 在分类模式下，每个来源最多获取的论文总数
MAX_PAPERS_PER_CATEGORY_FETCH = 10 
# 在分类模式下，是否确保每个子分类都抓取到论文 (推荐开启)
ENSURE_DIVERSITY_IN_CATEGORY_FETCH = True 
# 在分类模式下，每个子分类最少抓取的论文数 (仅在ENSURE_DIVERSITY_IN_CATEGORY_FETCH=True时生效)
MIN_PAPERS_PER_SUB_CATEGORY = 1
# 在分类模式下，每个子分类最多抓取的论文数 (防止单一分类占满名额)
MAX_PAPERS_PER_SUB_CATEGORY = 3

# 在关键词模式下，从bioRxiv获取过去多少天的论文
BIORXIV_DAYS_AGO = 3
# 在关键词模式下，从arXiv获取的最大论文数量
ARXIV_MAX_RESULTS_KW = 100

# --- 脚本核心代码 ---

def sanitize_filename(filename):
    """
    清理文件名，移除或替换Windows文件名中不支持的字符。
    """
    filename = re.sub(r'[\\/:*?"<>|]', '', filename)
    filename = filename.replace(':', ' ')
    filename = " ".join(filename.split())
    return filename[:150]

def make_api_request(url, max_retries=3, delay=5):
    """
    【新增】带有重试机制的网络请求函数，用于提高稳定性。
    """
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"\nWarning: API request failed (Attempt {attempt + 1}/{max_retries}). Retrying in {delay}s...")
            print(f"Error details: {e}")
            if attempt < max_retries - 1:
                time.sleep(delay)
    print(f"\nError: Failed to connect to API at {url} after {max_retries} attempts.")
    return None

def download_pdf(url, filepath, referer=None):
    """
    下载单个PDF文件并显示进度。
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36',
        }
        if referer:
            headers['Referer'] = referer

        response = requests.get(url, stream=True, timeout=30, headers=headers)
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024

        print(f"  Downloading: {os.path.basename(filepath)}")
        with open(filepath, 'wb') as f:
            downloaded_size = 0
            for data in response.iter_content(block_size):
                f.write(data)
                downloaded_size += len(data)
                done = int(50 * downloaded_size / total_size) if total_size > 0 else 0
                print(f"\r  [{'=' * done}{' ' * (50-done)}] {downloaded_size/1024/1024:.2f} MB", end='')
        print("\n  Download complete.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"\n  Error downloading {url}: {e}")
        if os.path.exists(filepath):
            os.remove(filepath)
        return False

# --- 关键词模式函数 ---

def fetch_from_arxiv_by_keyword():
    print("\n" + "="*50)
    print("Fetching papers from arXiv by KEYWORD...")
    print("="*50)
    today_str = datetime.now().strftime('%Y-%m-%d')
    download_dir = os.path.join(BASE_DOWNLOAD_DIR, 'arXiv', today_str)
    os.makedirs(download_dir, exist_ok=True)

    search_query = ' OR '.join([f'all:"{kw}"' for kw in KEYWORDS])
    query = f'search_query={search_query}&sortBy=submittedDate&sortOrder=descending&max_results={ARXIV_MAX_RESULTS_KW}'
    base_url = 'http://export.arxiv.org/api/query?'
    
    response = make_api_request(base_url + query)
    if not response:
        return

    ns = {'atom': 'http://www.w3.org/2005/Atom'}
    root = ET.fromstring(response.content)
    download_count = 0
    for entry in root.findall('atom:entry', ns):
        title = entry.find('atom:title', ns).text.strip()
        pdf_link = next((link.get('href') for link in entry.findall('atom:link', ns) if link.get('title') == 'pdf'), None)
        if not pdf_link: continue
        
        summary = entry.find('atom:summary', ns).text.strip().lower()
        title_lower = title.lower()

        if any(kw.lower() in title_lower or kw.lower() in summary for kw in KEYWORDS):
            filepath = os.path.join(download_dir, f"{sanitize_filename(title)}.pdf")
            if os.path.exists(filepath):
                print(f"Skipping '{title}', already exists.")
                continue
            print(f"Found on arXiv: '{title}'")
            if download_pdf(pdf_link, filepath):
                download_count += 1
                time.sleep(3)
            else:
                print(f"Failed to download '{title}'.")
    
    print(f"\nFinished fetching from arXiv. Downloaded {download_count} new papers.")


def fetch_from_biorxiv_by_keyword():
    print("\n" + "="*50)
    print("Fetching papers from bioRxiv by KEYWORD...")
    print("="*50)
    today_str = datetime.now().strftime('%Y-%m-%d')
    download_dir = os.path.join(BASE_DOWNLOAD_DIR, 'bioRxiv', today_str)
    os.makedirs(download_dir, exist_ok=True)
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=BIORXIV_DAYS_AGO)
    url = f"https://api.biorxiv.org/details/biorxiv/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
    
    response = make_api_request(url)
    if not response:
        return
    data = response.json()

    papers_found = []
    for paper in data.get('collection', []):
        title = paper.get('title', '').strip()
        abstract = paper.get('abstract', '').strip()
        if any(kw.lower() in (title + ' ' + abstract).lower() for kw in KEYWORDS):
            doi = paper.get('doi')
            version = paper.get('version')
            if not doi or not version: continue
            papers_found.append({
                "title": title,
                "page_url": f"https://www.biorxiv.org/content/{doi}v{version}",
                "pdf_url": f"https://www.biorxiv.org/content/{doi}v{version}.full.pdf"
            })
            print(f"Found on bioRxiv: '{title}'")

    if not papers_found:
        print("\nNo papers matching keywords found on bioRxiv.")
        return

    md_filepath = os.path.join(download_dir, f"biorxiv_links_{today_str}.md")
    with open(md_filepath, 'w', encoding='utf-8') as f:
        f.write(f"# bioRxiv Papers Found on {today_str} (Keywords)\n\n")
        for paper in papers_found:
            f.write(f"---\n\n## {paper['title']}\n\n- **Abstract Page:** [{paper['page_url']}]({paper['page_url']})\n- **Direct PDF Link:** [{paper['pdf_url']}]({paper['pdf_url']})\n\n")
    print(f"\nCreated a log file with {len(papers_found)} papers at: {md_filepath}")


# --- 分类模式函数 ---

def fetch_from_arxiv_by_category():
    print("\n" + "="*50)
    print("Fetching papers from arXiv by CATEGORY...")
    print("="*50)
    today_str = datetime.now().strftime('%Y-%m-%d')
    download_dir = os.path.join(BASE_DOWNLOAD_DIR, 'arXiv', today_str)
    os.makedirs(download_dir, exist_ok=True)

    base_url = 'http://export.arxiv.org/api/query?'
    ns = {'atom': 'http://www.w3.org/2005/Atom'}
    
    # 【逻辑重构】为每个分类单独请求，确保公平性
    all_papers_from_all_cats = []
    print("Fetching latest papers from each category individually...")
    for category in ARXIV_CATEGORIES:
        print(f"  - Querying for category: {category}")
        query = f'search_query=cat:{category}&sortBy=submittedDate&sortOrder=descending&max_results=50'
        response = make_api_request(base_url + query)
        if not response:
            continue

        root = ET.fromstring(response.content)
        for entry in root.findall('atom:entry', ns):
            paper_info = {
                'id': entry.find('atom:id', ns).text,
                'title': entry.find('atom:title', ns).text.strip(),
                'pdf_link': next((link.get('href') for link in entry.findall('atom:link', ns) if link.get('title') == 'pdf'), None),
                'categories': [c.get('term') for c in entry.findall('atom:category', ns)],
                'date': datetime.fromisoformat(entry.find('atom:published', ns).text.replace('Z', '+00:00')).date()
            }
            if paper_info['pdf_link']:
                all_papers_from_all_cats.append(paper_info)
        time.sleep(1) # API礼貌性停顿

    # 去重并按日期排序
    unique_papers_dict = {paper['id']: paper for paper in all_papers_from_all_cats}
    all_valid_papers = sorted(unique_papers_dict.values(), key=lambda p: p['date'], reverse=True)
    
    print(f"\nFound a total of {len(all_valid_papers)} unique papers across all categories.")

    papers_to_download = []
    if not ENSURE_DIVERSITY_IN_CATEGORY_FETCH:
        papers_to_download = all_valid_papers[:MAX_PAPERS_PER_CATEGORY_FETCH]
    else:
        # 按分类分组
        papers_by_category = {cat: [] for cat in ARXIV_CATEGORIES}
        for paper in all_valid_papers:
            for cat in paper['categories']:
                if cat in papers_by_category:
                    papers_by_category[cat].append(paper)

        added_paper_ids = set()
        
        # Stage 1: Fulfill minimums for each category
        for category in ARXIV_CATEGORIES:
            added_for_this_cat = 0
            for paper in papers_by_category[category]:
                if len(papers_to_download) >= MAX_PAPERS_PER_CATEGORY_FETCH: break
                if added_for_this_cat >= MIN_PAPERS_PER_SUB_CATEGORY: break
                
                if paper['id'] not in added_paper_ids:
                    papers_to_download.append(paper)
                    added_paper_ids.add(paper['id'])
                    added_for_this_cat += 1
            if len(papers_to_download) >= MAX_PAPERS_PER_CATEGORY_FETCH: break
        
        # Stage 2: Fill remaining slots, respecting sub-category maximums
        if len(papers_to_download) < MAX_PAPERS_PER_CATEGORY_FETCH:
            counts_per_cat = {cat: 0 for cat in ARXIV_CATEGORIES}
            for paper in papers_to_download:
                for cat in paper['categories']:
                    if cat in counts_per_cat:
                        counts_per_cat[cat] += 1
            
            for paper in all_valid_papers:
                if len(papers_to_download) >= MAX_PAPERS_PER_CATEGORY_FETCH: break
                if paper['id'] in added_paper_ids: continue

                can_add = True
                for cat in paper['categories']:
                    if cat in counts_per_cat and counts_per_cat[cat] >= MAX_PAPERS_PER_SUB_CATEGORY:
                        can_add = False
                        break
                
                if can_add:
                    papers_to_download.append(paper)
                    added_paper_ids.add(paper['id'])
                    for cat in paper['categories']:
                        if cat in counts_per_cat:
                            counts_per_cat[cat] += 1
    
    # 执行下载
    download_count = 0
    print("\nStarting download process...")
    for paper in papers_to_download:
        filepath = os.path.join(download_dir, f"{sanitize_filename(paper['title'])}.pdf")
        if os.path.exists(filepath):
            print(f"Skipping '{paper['title']}', already exists.")
            continue
        print(f"Found recent paper on arXiv ({paper['date']}): '{paper['title']}'")
        if download_pdf(paper['pdf_link'], filepath):
            download_count += 1
            time.sleep(3)
        else:
            print(f"Failed to download '{paper['title']}'.")

    print(f"\nFinished fetching from arXiv. Downloaded {download_count} newest paper(s) from selected categories.")


def fetch_from_biorxiv_by_category():
    print("\n" + "="*50)
    print("Fetching papers from bioRxiv by CATEGORY...")
    print("="*50)
    today_str = datetime.now().strftime('%Y-%m-%d')
    download_dir = os.path.join(BASE_DOWNLOAD_DIR, 'bioRxiv', today_str)
    os.makedirs(download_dir, exist_ok=True)

    end_date = datetime.now()
    start_date = end_date - timedelta(days=CATEGORY_FETCH_DAYS_AGO - 1)
    url = f"https://api.biorxiv.org/details/biorxiv/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
    
    response = make_api_request(url)
    if not response:
        return
    data = response.json()

    collection = sorted(data.get('collection', []), key=lambda p: p.get('date', ''), reverse=True)
    biorxiv_categories_lower = [cat.lower() for cat in BIORXIV_CATEGORIES]
    
    papers_found = []
    if not ENSURE_DIVERSITY_IN_CATEGORY_FETCH:
        for paper in collection:
            if len(papers_found) >= MAX_PAPERS_PER_CATEGORY_FETCH: break
            if paper.get('category', '').strip().lower() in biorxiv_categories_lower:
                papers_found.append(paper)
    else:
        papers_by_category = {cat: [] for cat in biorxiv_categories_lower}
        for paper in collection:
            category = paper.get('category', '').strip().lower()
            if category in papers_by_category:
                papers_by_category[category].append(paper)
        
        added_paper_dois = set()
        
        # Stage 1: Fulfill minimums
        for category in biorxiv_categories_lower:
            added_for_this_cat = 0
            for paper in papers_by_category[category]:
                if len(papers_found) >= MAX_PAPERS_PER_CATEGORY_FETCH: break
                if added_for_this_cat >= MIN_PAPERS_PER_SUB_CATEGORY: break
                
                doi = paper.get('doi')
                if doi and doi not in added_paper_dois:
                    papers_found.append(paper)
                    added_paper_dois.add(doi)
                    added_for_this_cat += 1
            if len(papers_found) >= MAX_PAPERS_PER_CATEGORY_FETCH: break

        # Stage 2: Fill remaining slots respecting max per category
        if len(papers_found) < MAX_PAPERS_PER_CATEGORY_FETCH:
            counts_per_cat = {cat: 0 for cat in biorxiv_categories_lower}
            for paper in papers_found:
                cat = paper.get('category', '').strip().lower()
                if cat in counts_per_cat:
                    counts_per_cat[cat] += 1
            
            for paper in collection:
                if len(papers_found) >= MAX_PAPERS_PER_CATEGORY_FETCH: break
                doi = paper.get('doi')
                if doi in added_paper_dois: continue

                category = paper.get('category', '').strip().lower()
                if category in counts_per_cat and counts_per_cat[category] < MAX_PAPERS_PER_SUB_CATEGORY:
                    papers_found.append(paper)
                    added_paper_dois.add(doi)
                    counts_per_cat[category] += 1

    if not papers_found:
        print(f"\nNo papers from selected categories found on bioRxiv for the last {CATEGORY_FETCH_DAYS_AGO} day(s).")
        return

    final_paper_list = []
    for paper in papers_found:
        doi = paper.get('doi')
        version = paper.get('version')
        date = paper.get('date', 'N/A')
        title = paper.get('title', 'No Title').strip()
        category = paper.get('category', 'N/A').strip()

        print(f"Found recent paper on bioRxiv ({date}): '{title}' in category '{category}'")
        final_paper_list.append({
            "title": title,
            "category": category.capitalize(),
            "date": date,
            "page_url": f"https://www.biorxiv.org/content/{doi}v{version}",
            "pdf_url": f"https://www.biorxiv.org/content/{doi}v{version}.full.pdf"
        })

    md_filepath = os.path.join(download_dir, f"biorxiv_links_{today_str}_by_category.md")
    with open(md_filepath, 'w', encoding='utf-8') as f:
        f.write(f"# bioRxiv Papers Found on {today_str} (By Category)\n\n")
        f.write(f"Showing top {len(final_paper_list)} results from the last **{CATEGORY_FETCH_DAYS_AGO}** day(s).\n")
        f.write(f"Categories searched: `{'`, `'.join(BIORXIV_CATEGORIES)}`.\n\n")
        for paper in final_paper_list:
            f.write(f"---\n\n## [{paper['category']}] {paper['title']}\n\n")
            f.write(f"**Posted on:** {paper['date']}\n\n")
            f.write(f"- **Abstract Page:** [{paper['page_url']}]({paper['page_url']})\n- **Direct PDF Link:** [{paper['pdf_url']}]({paper['pdf_url']})\n\n")
            
    print(f"\nCreated a log file with {len(final_paper_list)} papers at: {md_filepath}")


if __name__ == '__main__':
    print(f"Starting automatic paper script in '{FETCH_METHOD}' mode...")
    
    if FETCH_METHOD == 'keyword':
        fetch_from_arxiv_by_keyword()
        fetch_from_biorxiv_by_keyword()
    elif FETCH_METHOD == 'category':
        fetch_from_arxiv_by_category()
        fetch_from_biorxiv_by_category()
    else:
        print(f"Error: Unknown FETCH_METHOD '{FETCH_METHOD}'. Please use 'keyword' or 'category'.")

    print("\nAll tasks completed. Check the 'ResearchPapers' folder.")
