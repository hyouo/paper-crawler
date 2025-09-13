# src/fetchers.py

import logging
from datetime import datetime, timedelta
from . import utils
import arxiv

logger = logging.getLogger(__name__)


def get_arxiv_categories():
    """
    Returns a hardcoded list of common arXiv categories.
    """
    logger.info("Returning hardcoded arXiv categories...")
    return [
        {
            "group": "Physics",
            "categories": [
                {"code": "astro-ph", "name": "Astrophysics"},
                {"code": "cond-mat", "name": "Condensed Matter"},
                {"code": "gr-qc", "name": "General Relativity and Quantum Cosmology"},
                {"code": "hep-ex", "name": "High Energy Physics - Experiment"},
                {"code": "hep-lat", "name": "High Energy Physics - Lattice"},
                {"code": "hep-ph", "name": "High Energy Physics - Phenomenology"},
                {"code": "hep-th", "name": "High Energy Physics - Theory"},
                {"code": "nucl-ex", "name": "Nuclear Experiment"},
                {"code": "nucl-th", "name": "Nuclear Theory"},
                {"code": "physics", "name": "Physics (Other)"},
                {"code": "quant-ph", "name": "Quantum Physics"},
            ],
        },
        {
            "group": "Mathematics",
            "categories": [
                {"code": "math.AG", "name": "Algebraic Geometry"},
                {"code": "math.AP", "name": "Analysis of PDEs"},
                {"code": "math.CA", "name": "Classical Analysis and ODEs"},
                {"code": "math.CO", "name": "Combinatorics"},
                {"code": "math.CT", "name": "Category Theory"},
                {"code": "math.CV", "name": "Complex Variables"},
                {"code": "math.DG", "name": "Differential Geometry"},
                {"code": "math.DS", "name": "Dynamical Systems"},
                {"code": "math.FA", "name": "Functional Analysis"},
                {"code": "math.GM", "name": "General Mathematics"},
                {"code": "math.GN", "name": "General Topology"},
                {"code": "math.GR", "name": "Group Theory"},
                {"code": "math.GT", "name": "Geometric Topology"},
                {"code": "math.HO", "name": "History and Overview"},
                {"code": "math.IT", "name": "Information Theory"},
                {"code": "math.KT", "name": "K-Theory and Homology"},
                {"code": "math.LO", "name": "Logic"},
                {"code": "math.MG", "name": "Metric Geometry"},
                {"code": "math.MP", "name": "Mathematical Physics"},
                {"code": "math.NA", "name": "Numerical Analysis"},
                {"code": "math.NT", "name": "Number Theory"},
                {"code": "math.OA", "name": "Operator Algebras"},
                {"code": "math.OC", "name": "Optimization and Control"},
                {"code": "math.PR", "name": "Probability"},
                {"code": "math.QA", "name": "Quantum Algebra"},
                {"code": "math.RA", "name": "Rings and Algebras"},
                {"code": "math.RT", "name": "Representation Theory"},
                {"code": "math.SG", "name": "Symplectic Geometry"},
                {"code": "math.SP", "name": "Spectral Theory"},
                {"code": "math.ST", "name": "Statistics Theory"},
            ],
        },
        {
            "group": "Computer Science",
            "categories": [
                {"code": "cs.AI", "name": "Artificial Intelligence"},
                {"code": "cs.AR", "name": "Hardware Architecture"},
                {"code": "cs.CC", "name": "Computational Complexity"},
                {
                    "code": "cs.CE",
                    "name": "Computational Engineering, Finance, and Science",
                },
                {"code": "cs.CG", "name": "Computational Geometry"},
                {"code": "cs.CL", "name": "Computation and Language"},
                {"code": "cs.CR", "name": "Cryptography and Security"},
                {"code": "cs.CV", "name": "Computer Vision and Pattern Recognition"},
                {"code": "cs.CY", "name": "Computers and Society"},
                {"code": "cs.DB", "name": "Databases"},
                {
                    "code": "cs.DC",
                    "name": "Distributed, Parallel, and Cluster Computing",
                },
                {"code": "cs.DL", "name": "Digital Libraries"},
                {"code": "cs.DM", "name": "Discrete Mathematics"},
                {"code": "cs.DS", "name": "Data Structures and Algorithms"},
                {"code": "cs.ET", "name": "Emerging Technologies"},
                {"code": "cs.FL", "name": "Formal Languages and Automata Theory"},
                {"code": "cs.GA", "name": "General Algorithms"},
                {"code": "cs.GR", "name": "Graphics"},
                {"code": "cs.GT", "name": "Computer Science and Game Theory"},
                {"code": "cs.HC", "name": "Human-Computer Interaction"},
                {"code": "cs.IR", "name": "Information Retrieval"},
                {"code": "cs.IT", "name": "Information Theory"},
                {"code": "cs.LG", "name": "Machine Learning"},
                {"code": "cs.LO", "name": "Logic in Computer Science"},
                {"code": "cs.MA", "name": "Multiagent Systems"},
                {"code": "cs.MM", "name": "Multimedia"},
                {"code": "cs.MS", "name": "Mathematical Software"},
                {"code": "cs.NA", "name": "Numerical Analysis"},
                {"code": "cs.NE", "name": "Neural and Evolutionary Computing"},
                {"code": "cs.NI", "name": "Networking and Internet Architecture"},
                {"code": "cs.OS", "name": "Operating Systems"},
                {"code": "cs.PF", "name": "Performance"},
                {"code": "cs.PL", "name": "Programming Languages"},
                {"code": "cs.RO", "name": "Robotics"},
                {"code": "cs.SC", "name": "Symbolic Computation"},
                {"code": "cs.SD", "name": "Sound"},
                {"code": "cs.SE", "name": "Software Engineering"},
                {"code": "cs.SI", "name": "Social and Information Networks"},
                {"code": "cs.SY", "name": "Systems and Control"},
            ],
        },
        {
            "group": "Quantitative Biology",
            "categories": [
                {"code": "q-bio.BM", "name": "Biomolecules"},
                {"code": "q-bio.CB", "name": "Cell Behavior"},
                {"code": "q-bio.GN", "name": "Genomics"},
                {"code": "q-bio.MN", "name": "Molecular Networks"},
                {"code": "q-bio.NC", "name": "Neurons and Cognition"},
                {"code": "q-bio.PE", "name": "Populations and Evolution"},
                {"code": "q-bio.QM", "name": "Quantitative Methods"},
                {"code": "q-bio.SC", "name": "Subcellular Processes"},
                {"code": "q-bio.TO", "name": "Tissues and Organs"},
            ],
        },
        {
            "group": "Quantitative Finance",
            "categories": [
                {"code": "q-fin.CP", "name": "Computational Finance"},
                {"code": "q-fin.EC", "name": "Economics"},
                {"code": "q-fin.GN", "name": "General Finance"},
                {"code": "q-fin.MF", "name": "Mathematical Finance"},
                {"code": "q-fin.PM", "name": "Portfolio Management"},
                {"code": "q-fin.PR", "name": "Pricing of Securities"},
                {"code": "q-fin.RM", "name": "Risk Management"},
                {"code": "q-fin.ST", "name": "Statistical Finance"},
                {"code": "q-fin.TR", "name": "Trading and Market Microstructure"},
            ],
        },
        {
            "group": "Statistics",
            "categories": [
                {"code": "stat.AP", "name": "Applications"},
                {"code": "stat.CO", "name": "Computation"},
                {"code": "stat.ML", "name": "Machine Learning"},
                {"code": "stat.ME", "name": "Methodology"},
                {"code": "stat.OT", "name": "Other Statistics"},
                {"code": "stat.TH", "name": "Theory"},
            ],
        },
        {
            "group": "Electrical Engineering and Systems Science",
            "categories": [
                {"code": "eess.AS", "name": "Audio and Speech Processing"},
                {"code": "eess.IV", "name": "Image and Video Processing"},
                {"code": "eess.SP", "name": "Signal Processing"},
                {"code": "eess.SY", "name": "Systems and Control"},
            ],
        },
        {
            "group": "Economics",
            "categories": [
                {"code": "econ.EM", "name": "Econometrics"},
                {"code": "econ.GN", "name": "General Economics"},
                {"code": "econ.TH", "name": "Theoretical Economics"},
            ],
        },
    ]


def get_biorxiv_categories():
    """
    Returns a hardcoded list of bioRxiv categories.
    """
    logger.info("Fetching bioRxiv categories...")
    return [
        "Animal Behavior and Cognition",
        "Biochemistry",
        "Bioengineering",
        "Bioinformatics",
        "Biophysics",
        "Cancer Biology",
        "Cell Biology",
        "Developmental Biology",
        "Ecology",
        "Evolutionary Biology",
        "Genetics",
        "Genomics",
        "Immunology",
        "Microbiology",
        "Molecular Biology",
        "Neuroscience",
        "Paleontology",
        "Pathology",
        "Pharmacology and Toxicology",
        "Physiology",
        "Plant Biology",
        "Scientific Communication and Education",
        "Synthetic Biology",
        "Systems Biology",
        "Zoology",
    ]


# --- arXiv Fetchers ---


def _arxiv_result_to_paper_data(result):
    """
    Converts an arxiv.Result object to the standard paper data dictionary.
    """
    pdf_url = result.pdf_url  # Directly use the pdf_url attribute

    if not pdf_url:
        logger.warning(f"无法从 arXiv 结果中找到 PDF URL: {result.entry_id}")
        return None

    return {
        "title": result.title.strip(),
        "authors": ", ".join([author.name for author in result.authors]),
        "source": "arXiv",
        "category": ", ".join(result.categories),
        "paper_url": result.entry_id,
        "pdf_url": pdf_url,
        "published_date": result.published.date().isoformat(),
        "abstract": result.summary.strip().replace("\n", " "),
    }


def _build_arxiv_query(fetch_settings, keywords, categories=[]):
    """Helper to build the arXiv query string."""
    query_parts = []

    # Keywords
    if keywords:
        field = fetch_settings.get("keyword_search_field", "all")
        field_prefix = {"all": "all", "title": "ti", "abstract": "abs"}.get(field, "all")
        keyword_query = " OR ".join([f'{field_prefix}:"{kw}"' for kw in keywords])
        query_parts.append(f"({keyword_query})")

    # Authors
    authors = fetch_settings.get("search_by_authors", [])
    if authors:
        author_query = " OR ".join([f'au:"{author}"' for author in authors])
        query_parts.append(f"({author_query})")

    # Categories
    if categories:
        category_query = " OR ".join([f'cat:{cat}' for cat in categories])
        query_parts.append(f"({category_query})")

    # Date Range
    start_date = fetch_settings.get("search_start_date")
    end_date = fetch_settings.get("search_end_date")
    if start_date and end_date:
        # Format: YYYYMMDDHHMMSS
        start_str = start_date.replace('-', '') + "000000"
        end_str = end_date.replace('-', '') + "235959"
        query_parts.append(f"submittedDate:[{start_str} TO {end_str}]")

    return " AND ".join(query_parts)


def fetch_from_arxiv_by_keyword(config):
    logger.info("开始从 arXiv 按关键词获取论文列表...")
    fetch_settings = config["fetch_settings"]
    keywords = config.get("keywords", [])
    id_list = fetch_settings.get("search_by_ids", [])

    search_query = _build_arxiv_query(fetch_settings, keywords)

    if id_list:
        logger.info(f"正在通过 ID 列表精确查找: {id_list}")
        search_query = "" # id_list overrides query
    elif not search_query:
        logger.warning("未提供关键词、作者或日期范围，arXiv 查询为空，将不会返回任何结果。")
        return

    sort_by_str = fetch_settings.get("arxiv_sort_by", "SubmittedDate")
    sort_order_str = fetch_settings.get("arxiv_sort_order", "Descending")

    sort_criterion_map = {
        "Relevance": arxiv.SortCriterion.Relevance,
        "LastUpdatedDate": arxiv.SortCriterion.LastUpdatedDate,
        "SubmittedDate": arxiv.SortCriterion.SubmittedDate,
    }
    sort_by = sort_criterion_map.get(sort_by_str, arxiv.SortCriterion.SubmittedDate)
    sort_order = arxiv.SortOrder.Ascending if sort_order_str == "Ascending" else arxiv.SortOrder.Descending

    client = arxiv.Client(page_size=100, delay_seconds=3, num_retries=5)
    search = arxiv.Search(
        query=search_query,
        id_list=id_list,
        max_results=fetch_settings.get("arxiv_max_results_kw", 100),
        sort_by=sort_by,
        sort_order=sort_order,
    )

    try:
        results = list(client.results(search))
        logger.info(f"arXiv 关键词查询找到 {len(results)} 篇论文。")
        for result in results:
            yield _arxiv_result_to_paper_data(result)
    except Exception as e:
        logger.error(f"执行 arXiv 查询时出错: {e}", exc_info=True)


def fetch_from_arxiv_by_category(config, selected_categories_list):
    logger.info("开始从 arXiv 按分类获取论文列表...")
    fetch_settings = config["fetch_settings"]

    all_arxiv_categories = get_arxiv_categories()
    expanded_categories = []
    for selected_cat_code in selected_categories_list:
        is_group = any(selected_cat_code == group_data["group"] for group_data in all_arxiv_categories)
        if is_group:
            for group_data in all_arxiv_categories:
                if selected_cat_code == group_data["group"]:
                    expanded_categories.extend(sub_cat["code"] for sub_cat in group_data["categories"])
                    break
        else:
            expanded_categories.append(selected_cat_code)

    search_query = _build_arxiv_query(fetch_settings, [], categories=list(set(expanded_categories)))

    if not search_query:
        logger.warning("未提供分类、作者或日期范围，arXiv 查询为空，将不会返回任何结果。")
        return

    sort_by_str = fetch_settings.get("arxiv_sort_by", "SubmittedDate")
    sort_order_str = fetch_settings.get("arxiv_sort_order", "Descending")

    sort_criterion_map = {
        "Relevance": arxiv.SortCriterion.Relevance,
        "LastUpdatedDate": arxiv.SortCriterion.LastUpdatedDate,
        "SubmittedDate": arxiv.SortCriterion.SubmittedDate,
    }
    sort_by = sort_criterion_map.get(sort_by_str, arxiv.SortCriterion.SubmittedDate)
    sort_order = arxiv.SortOrder.Ascending if sort_order_str == "Ascending" else arxiv.SortOrder.Descending

    client = arxiv.Client(page_size=100, delay_seconds=3, num_retries=5)
    search = arxiv.Search(
        query=search_query,
        max_results=fetch_settings.get("max_papers_per_category_fetch", 10) * len(expanded_categories),
        sort_by=sort_by,
        sort_order=sort_order,
    )

    try:
        results = list(client.results(search))
        logger.info(f"arXiv 分类查询找到 {len(results)} 篇论文。")
        unique_paper_urls = set()
        for result in results:
            paper_data = _arxiv_result_to_paper_data(result)
            if paper_data and paper_data["paper_url"] not in unique_paper_urls:
                unique_paper_urls.add(paper_data["paper_url"])
                yield paper_data
    except Exception as e:
        logger.error(f"执行 arXiv 分类查询时出错: {e}", exc_info=True)


# --- bioRxiv Fetchers ---

def _get_biorxiv_date_range(fetch_settings):
    start_date_str = fetch_settings.get("search_start_date")
    end_date_str = fetch_settings.get("search_end_date")

    if start_date_str and end_date_str:
        return f"{start_date_str}/{end_date_str}"
    else:
        # Fallback to a default of last 7 days if no range is provided
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        return f"{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"


def _query_biorxiv_api(date_range):
    url = f"https://api.biorxiv.org/details/biorxiv/{date_range}"
    response = utils.make_api_request(url)
    if not response:
        return []
    return response.json().get("collection", [])


def _parse_biorxiv_entry(paper):
    doi = paper.get("doi")
    version = paper.get("version")
    if not doi or not version:
        return None

    return {
        "title": paper.get("title", "N/A").strip(),
        "authors": paper.get("authors", "N/A").strip(),
        "source": "bioRxiv",
        "category": paper.get("category", "N/A").strip(),
        "paper_url": f"https://www.biorxiv.org/content/{doi}v{version}",
        "pdf_url": f"https://www.biorxiv.org/content/{doi}v{version}.full.pdf",
        "abstract": paper.get("abstract", "N/A").strip(),
    }


def _biorxiv_matches_filters(paper, keywords, authors, search_field='all'):
    """
    Helper to check if a bioRxiv paper matches keyword and author filters.
    """
    title = paper.get("title", "").lower()
    abstract = paper.get("abstract", "").lower()
    paper_authors = paper.get("authors", "").lower()

    # Keyword check
    keyword_match = not keywords
    if keywords:
        if search_field == 'title':
            keyword_match = any(kw in title for kw in keywords)
        elif search_field == 'abstract':
            keyword_match = any(kw in abstract for kw in keywords)
        else: # 'all'
            keyword_match = any(kw in title or kw in abstract for kw in keywords)

    if not keyword_match:
        return False

    # Author check
    author_match = not authors or any(author.lower() in paper_authors for author in authors)
    if not author_match:
        return False

    return True


def fetch_from_biorxiv_by_keyword(config):
    logger.info("开始从 bioRxiv 按关键词获取论文列表...")
    fetch_settings = config["fetch_settings"]
    date_range = _get_biorxiv_date_range(fetch_settings)
    all_papers = _query_biorxiv_api(date_range)

    keywords = [kw.lower() for kw in config.get("keywords", [])]
    authors = fetch_settings.get("search_by_authors", [])
    search_field = fetch_settings.get("keyword_search_field", "all")

    if not keywords and not authors:
        logger.warning("未提供关键词或作者，bioRxiv (关键词模式) 查询将不会返回任何结果。")
        return

    for paper in all_papers:
        if _biorxiv_matches_filters(paper, keywords, authors, search_field):
            paper_data = _parse_biorxiv_entry(paper)
            if paper_data:
                yield paper_data


def fetch_from_biorxiv_by_category(config, selected_categories_list):
    logger.info("开始从 bioRxiv 按分类获取论文列表...")
    fetch_settings = config["fetch_settings"]
    date_range = _get_biorxiv_date_range(fetch_settings)
    all_papers = _query_biorxiv_api(date_range)

    categories = [cat.lower() for cat in selected_categories_list]
    authors = fetch_settings.get("search_by_authors", [])

    for paper in all_papers:
        # Category check
        category_match = paper.get("category", "").lower() in categories
        if not category_match:
            continue

        # Author check (only if authors are specified)
        if authors:
            paper_authors = paper.get("authors", "").lower()
            author_match = any(author.lower() in paper_authors for author in authors)
            if not author_match:
                continue

        paper_data = _parse_biorxiv_entry(paper)
        if paper_data:
            yield paper_data
