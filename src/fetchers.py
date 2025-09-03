import os
import time
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from .utils import sanitize_filename, make_api_request, download_pdf

logger = logging.getLogger(__name__)

# --- 关键词模式函数 ---

def fetch_from_arxiv_by_keyword(config):
    logger.info("="*50)
    logger.info("正在从 arXiv 按关键词抓取论文...")
    logger.info("="*50)
    
    base_download_dir = config.get('base_download_dir', 'paper')
    today_str = datetime.now().strftime('%Y-%m-%d')
    download_dir = os.path.join(base_download_dir, 'arXiv', today_str)
    os.makedirs(download_dir, exist_ok=True)

    keywords = config['keywords']
    max_results = config['fetch_settings']['arxiv_max_results_kw']
    
    search_query = ' OR '.join([f'all:"{kw}"' for kw in keywords])
    query = f'search_query={search_query}&sortBy=submittedDate&sortOrder=descending&max_results={max_results}'
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

        if any(kw.lower() in title_lower or kw.lower() in summary for kw in keywords):
            filepath = os.path.join(download_dir, f"{sanitize_filename(title)}.pdf")
            if os.path.exists(filepath):
                logger.info(f"跳过 '{title}', 文件已存在。")
                continue
            logger.info(f"在 arXiv 找到: '{title}'")
            if download_pdf(pdf_link, filepath):
                download_count += 1
                time.sleep(3)
            else:
                logger.error(f"下载失败 '{title}'.")
    
    logger.info(f"完成从 arXiv 的抓取。共下载 {download_count} 篇新论文。")


def fetch_from_biorxiv_by_keyword(config):
    logger.info("="*50)
    logger.info("正在从 bioRxiv 按关键词抓取论文...")
    logger.info("="*50)

    base_download_dir = config.get('base_download_dir', 'paper')
    today_str = datetime.now().strftime('%Y-%m-%d')
    download_dir = os.path.join(base_download_dir, 'bioRxiv', today_str)
    os.makedirs(download_dir, exist_ok=True)
    
    days_ago = config['fetch_settings']['biorxiv_days_ago']
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_ago)
    url = f"https://api.biorxiv.org/details/biorxiv/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
    
    response = make_api_request(url)
    if not response:
        return
    data = response.json()

    papers_found = []
    keywords = config['keywords']
    include_abstract = config['output_settings']['biorxiv_include_abstract_in_md']

    for paper in data.get('collection', []):
        title = paper.get('title', '').strip()
        abstract = paper.get('abstract', '').strip()
        if any(kw.lower() in (title + ' ' + abstract).lower() for kw in keywords):
            doi = paper.get('doi')
            version = paper.get('version')
            if not doi or not version: continue
            
            paper_data = {
                "title": title,
                "page_url": f"https://www.biorxiv.org/content/{doi}v{version}",
                "pdf_url": f"https://www.biorxiv.org/content/{doi}v{version}.full.pdf"
            }
            if include_abstract:
                paper_data["abstract"] = abstract
            papers_found.append(paper_data)
            logger.info(f"在 bioRxiv 找到: '{title}'")

    if not papers_found:
        logger.info("在 bioRxiv 未找到匹配关键词的论文。")
        return

    md_filepath = os.path.join(download_dir, f"biorxiv_links_{today_str}.md")
    with open(md_filepath, 'w', encoding='utf-8') as f:
        f.write(f"# bioRxiv Papers Found on {today_str} (Keywords)\n\n")
        for paper in papers_found:
            f.write(f"---\n\n## {paper['title']}\n\n")
            if include_abstract and "abstract" in paper:
                f.write(f"**摘要:**\n\n> {paper['abstract']}\n\n")
            f.write(f"- **摘要页:** [{paper['page_url']}]({paper['page_url']})\n- **PDF 直链:** [{paper['pdf_url']}]({paper['pdf_url']})\n\n")
    logger.info(f"已创建包含 {len(papers_found)} 篇论文的日志文件: {md_filepath}")


# --- 分类模式函数 ---

def fetch_from_arxiv_by_category(config):
    logger.info("="*50)
    logger.info("正在从 arXiv 按分类抓取论文...")
    logger.info("="*50)

    base_download_dir = config.get('base_download_dir', 'paper')
    today_str = datetime.now().strftime('%Y-%m-%d')
    download_dir = os.path.join(base_download_dir, 'arXiv', today_str)
    os.makedirs(download_dir, exist_ok=True)

    arxiv_categories = config['categories']['arxiv']
    fetch_days_ago = config['fetch_settings']['category_fetch_days_ago']
    max_papers = config['fetch_settings']['max_papers_per_category_fetch']
    ensure_diversity = config['fetch_settings']['ensure_diversity_in_category_fetch']
    min_per_sub = config['fetch_settings']['min_papers_per_sub_category']
    max_per_sub = config['fetch_settings']['max_papers_per_sub_category']

    base_url = 'http://export.arxiv.org/api/query?'
    ns = {'atom': 'http://www.w3.org/2005/Atom'}
    
    all_papers_from_all_cats = []
    logger.info("正在从每个分类单独获取最新论文...")
    for category in arxiv_categories:
        logger.info(f"  - 查询分类: {category}")
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
        time.sleep(1)

    unique_papers_dict = {paper['id']: paper for paper in all_papers_from_all_cats}
    all_valid_papers = sorted(unique_papers_dict.values(), key=lambda p: p['date'], reverse=True)
    date_limit = datetime.now().date() - timedelta(days=fetch_days_ago - 1)
    all_valid_papers = [p for p in all_valid_papers if p['date'] >= date_limit]
    logger.info(f"在所有分类中经过日期过滤后共找到 {len(all_valid_papers)} 篇独立论文。")

    papers_to_download = []
    if not ensure_diversity:
        papers_to_download = all_valid_papers[:max_papers]
    else:
        papers_by_category = {cat: [] for cat in arxiv_categories}
        for paper in all_valid_papers:
            for cat in paper['categories']:
                if cat in papers_by_category:
                    papers_by_category[cat].append(paper)

        added_paper_ids = set()
        
        for category in arxiv_categories:
            added_for_this_cat = 0
            for paper in papers_by_category.get(category, []):
                if len(papers_to_download) >= max_papers: break
                if added_for_this_cat >= min_per_sub: break
                
                if paper['id'] not in added_paper_ids:
                    papers_to_download.append(paper)
                    added_paper_ids.add(paper['id'])
                    added_for_this_cat += 1
            if len(papers_to_download) >= max_papers: break
        
        if len(papers_to_download) < max_papers:
            counts_per_cat = {cat: 0 for cat in arxiv_categories}
            for paper in papers_to_download:
                for cat in paper['categories']:
                    if cat in counts_per_cat:
                        counts_per_cat[cat] += 1
            
            for paper in all_valid_papers:
                if len(papers_to_download) >= max_papers: break
                if paper['id'] in added_paper_ids: continue

                can_add = True
                for cat in paper['categories']:
                    if cat in counts_per_cat and counts_per_cat[cat] >= max_per_sub:
                        can_add = False
                        break
                
                if can_add:
                    papers_to_download.append(paper)
                    added_paper_ids.add(paper['id'])
                    for cat in paper['categories']:
                        if cat in counts_per_cat:
                            counts_per_cat[cat] += 1
    
    download_count = 0
    logger.info("开始下载...")
    for paper in papers_to_download:
        filepath = os.path.join(download_dir, f"{sanitize_filename(paper['title'])}.pdf")
        if os.path.exists(filepath):
            logger.info(f"跳过 '{paper['title']}', 文件已存在。")
            continue
        logger.info(f"找到 arXiv 近期论文 ({paper['date']}): '{paper['title']}'")
        if download_pdf(paper['pdf_link'], filepath):
            download_count += 1
            time.sleep(3)
        else:
            logger.error(f"下载失败 '{paper['title']}'.")

    logger.info(f"完成从 arXiv 的抓取。从选定分类中下载了 {download_count} 篇最新论文。")


def fetch_from_biorxiv_by_category(config):
    logger.info("="*50)
    logger.info("正在从 bioRxiv 按分类抓取论文...")
    logger.info("="*50)

    base_download_dir = config.get('base_download_dir', 'paper')
    today_str = datetime.now().strftime('%Y-%m-%d')
    download_dir = os.path.join(base_download_dir, 'bioRxiv', today_str)
    os.makedirs(download_dir, exist_ok=True)

    fetch_days_ago = config['fetch_settings']['category_fetch_days_ago']
    max_papers = config['fetch_settings']['max_papers_per_category_fetch']
    ensure_diversity = config['fetch_settings']['ensure_diversity_in_category_fetch']
    min_per_sub = config['fetch_settings']['min_papers_per_sub_category']
    max_per_sub = config['fetch_settings']['max_papers_per_sub_category']
    biorxiv_categories = config['categories']['biorxiv']
    include_abstract = config['output_settings']['biorxiv_include_abstract_in_md']

    end_date = datetime.now()
    start_date = end_date - timedelta(days=fetch_days_ago - 1)
    url = f"https://api.biorxiv.org/details/biorxiv/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
    
    response = make_api_request(url)
    if not response:
        return
    data = response.json()

    collection = sorted(data.get('collection', []), key=lambda p: p.get('date', ''), reverse=True)
    biorxiv_categories_lower = [cat.lower() for cat in biorxiv_categories]
    
    papers_found = []
    if not ensure_diversity:
        for paper in collection:
            if len(papers_found) >= max_papers: break
            if paper.get('category', '').strip().lower() in biorxiv_categories_lower:
                papers_found.append(paper)
    else:
        papers_by_category = {cat: [] for cat in biorxiv_categories_lower}
        for paper in collection:
            category = paper.get('category', '').strip().lower()
            if category in papers_by_category:
                papers_by_category[category].append(paper)
        
        added_paper_dois = set()
        
        for category in biorxiv_categories_lower:
            added_for_this_cat = 0
            for paper in papers_by_category.get(category, []):
                if len(papers_found) >= max_papers: break
                if added_for_this_cat >= min_per_sub: break
                
                doi = paper.get('doi')
                if doi and doi not in added_paper_dois:
                    papers_found.append(paper)
                    added_paper_dois.add(doi)
                    added_for_this_cat += 1
            if len(papers_found) >= max_papers: break

        if len(papers_found) < max_papers:
            counts_per_cat = {cat: 0 for cat in biorxiv_categories_lower}
            for paper in papers_found:
                cat = paper.get('category', '').strip().lower()
                if cat in counts_per_cat:
                    counts_per_cat[cat] += 1
            
            for paper in collection:
                if len(papers_found) >= max_papers: break
                doi = paper.get('doi')
                if doi in added_paper_dois: continue

                category = paper.get('category', '').strip().lower()
                if category in counts_per_cat and counts_per_cat[category] < max_per_sub:
                    papers_found.append(paper)
                    added_paper_dois.add(doi)
                    counts_per_cat[category] += 1

    if not papers_found:
        logger.info(f"在过去 {fetch_days_ago} 天内，在 bioRxiv 未找到选定分类的论文。")
        return

    final_paper_list = []
    for paper in papers_found:
        doi = paper.get('doi')
        version = paper.get('version')
        date = paper.get('date', 'N/A')
        title = paper.get('title', 'No Title').strip()
        category = paper.get('category', 'N/A').strip()
        abstract = paper.get('abstract', 'N/A').strip()

        logger.info(f"找到 bioRxiv 近期论文 ({date}): '{title}' 在分类 '{category}'")
        
        paper_data = {
            "title": title,
            "category": category.capitalize(),
            "date": date,
            "page_url": f"https://www.biorxiv.org/content/{doi}v{version}",
            "pdf_url": f"https://www.biorxiv.org/content/{doi}v{version}.full.pdf"
        }
        if include_abstract:
            paper_data["abstract"] = abstract
        final_paper_list.append(paper_data)

    md_filepath = os.path.join(download_dir, f"biorxiv_links_{today_str}_by_category.md")
    with open(md_filepath, 'w', encoding='utf-8') as f:
        f.write(f"# bioRxiv Papers Found on {today_str} (By Category)\n\n")
        f.write(f"显示最近 **{fetch_days_ago}** 天内的前 {len(final_paper_list)} 个结果。\n")
        f.write(f"搜索的分类: `{'`, `'.join(biorxiv_categories)}`.\n\n")
        for paper in final_paper_list:
            f.write(f"---\n\n## [{paper['category']}] {paper['title']}\n\n")
            f.write(f"**发布于:** {paper['date']}\n\n")
            if include_abstract and "abstract" in paper:
                f.write(f"**摘要:**\n\n> {paper['abstract']}\n\n")
            f.write(f"- **摘要页:** [{paper['page_url']}]({paper['page_url']})\n- **PDF 直链:** [{paper['pdf_url']}]({paper['pdf_url']})\n\n")
            
    logger.info(f"已创建包含 {len(final_paper_list)} 篇论文的日志文件: {md_filepath}")
