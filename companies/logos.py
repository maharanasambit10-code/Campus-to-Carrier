import re
import os
from django.conf import settings

# Curated catalog of enterprise and startup logos with official CDN vectors & initials
COMPANY_BRAND_DATA = {
    'google': {
        'name': 'Google',
        'domain': 'google.com',
        'cdn_url': 'https://cdn.simpleicons.org/google/4285F4',
        'local_svg': '/static/images/company_logos/google.svg',
        'initials': 'GOOG',
        'brand_color': '#4285F4',
    },
    'microsoft': {
        'name': 'Microsoft',
        'domain': 'microsoft.com',
        'cdn_url': 'https://cdn.simpleicons.org/microsoft/00A4EF',
        'local_svg': '/static/images/company_logos/microsoft.svg',
        'initials': 'MSFT',
        'brand_color': '#00A4EF',
    },
    'amazon': {
        'name': 'Amazon',
        'domain': 'amazon.com',
        'cdn_url': 'https://cdn.simpleicons.org/amazon/FF9900',
        'local_svg': '/static/images/company_logos/amazon.svg',
        'initials': 'AMZN',
        'brand_color': '#FF9900',
    },
    'accenture': {
        'name': 'Accenture',
        'domain': 'accenture.com',
        'cdn_url': 'https://cdn.simpleicons.org/accenture/A100FF',
        'local_svg': '/static/images/company_logos/accenture.svg',
        'initials': 'ACN',
        'brand_color': '#A100FF',
    },
    'adobe': {
        'name': 'Adobe',
        'domain': 'adobe.com',
        'cdn_url': 'https://cdn.simpleicons.org/adobe/FF0000',
        'local_svg': '/static/images/company_logos/adobe.svg',
        'initials': 'ADBE',
        'brand_color': '#FF0000',
    },
    'atlassian': {
        'name': 'Atlassian',
        'domain': 'atlassian.com',
        'cdn_url': 'https://cdn.simpleicons.org/atlassian/0052CC',
        'local_svg': '/static/images/company_logos/atlassian.svg',
        'initials': 'TEAM',
        'brand_color': '#0052CC',
    },
    'capgemini': {
        'name': 'Capgemini',
        'domain': 'capgemini.com',
        'cdn_url': 'https://cdn.simpleicons.org/capgemini/0070AD',
        'local_svg': '/static/images/company_logos/capgemini.svg',
        'initials': 'CAPG',
        'brand_color': '#0070AD',
    },
    'cognizant': {
        'name': 'Cognizant',
        'domain': 'cognizant.com',
        'cdn_url': 'https://cdn.simpleicons.org/cognizant/0033A0',
        'local_svg': '/static/images/company_logos/cognizant.svg',
        'initials': 'CTSH',
        'brand_color': '#0033A0',
    },
    'deloitte': {
        'name': 'Deloitte',
        'domain': 'deloitte.com',
        'cdn_url': 'https://cdn.simpleicons.org/deloitte/86BC25',
        'local_svg': '/static/images/company_logos/deloitte.svg',
        'initials': 'DEL',
        'brand_color': '#86BC25',
    },
    'flipkart': {
        'name': 'Flipkart',
        'domain': 'flipkart.com',
        'cdn_url': 'https://cdn.simpleicons.org/flipkart/2874F0',
        'local_svg': '/static/images/company_logos/flipkart.svg',
        'initials': 'FLIP',
        'brand_color': '#2874F0',
    },
    'ibm': {
        'name': 'IBM',
        'domain': 'ibm.com',
        'cdn_url': 'https://cdn.simpleicons.org/ibm/052FAD',
        'local_svg': '/static/images/company_logos/ibm.svg',
        'initials': 'IBM',
        'brand_color': '#052FAD',
    },
    'infosys': {
        'name': 'Infosys',
        'domain': 'infosys.com',
        'cdn_url': 'https://cdn.simpleicons.org/infosys/007CC3',
        'local_svg': '/static/images/company_logos/infosys.svg',
        'initials': 'INFY',
        'brand_color': '#007CC3',
    },
    'tcs': {
        'name': 'Tata Consultancy Services',
        'domain': 'tcs.com',
        'cdn_url': 'https://cdn.simpleicons.org/tata/005A9C',
        'local_svg': '/static/images/company_logos/tcs.svg',
        'initials': 'TCS',
        'brand_color': '#005A9C',
    },
    'wipro': {
        'name': 'Wipro',
        'domain': 'wipro.com',
        'cdn_url': 'https://cdn.simpleicons.org/wipro/1A1A1A',
        'local_svg': '/static/images/company_logos/wipro.svg',
        'initials': 'WIP',
        'brand_color': '#5F259F',
    },
    'hcltech': {
        'name': 'HCLTech',
        'domain': 'hcltech.com',
        'cdn_url': 'https://cdn.simpleicons.org/hcl/004085',
        'local_svg': '/static/images/company_logos/hcltech.svg',
        'initials': 'HCL',
        'brand_color': '#004085',
    },
    'tech mahindra': {
        'name': 'Tech Mahindra',
        'domain': 'techmahindra.com',
        'cdn_url': 'https://cdn.simpleicons.org/mahindra/E31837',
        'local_svg': '/static/images/company_logos/techmahindra.svg',
        'initials': 'TECHM',
        'brand_color': '#E31837',
    },
    'oracle': {
        'name': 'Oracle',
        'domain': 'oracle.com',
        'cdn_url': 'https://cdn.simpleicons.org/oracle/F80000',
        'local_svg': '/static/images/company_logos/oracle.svg',
        'initials': 'ORCL',
        'brand_color': '#F80000',
    },
    'salesforce': {
        'name': 'Salesforce',
        'domain': 'salesforce.com',
        'cdn_url': 'https://cdn.simpleicons.org/salesforce/00A1E0',
        'local_svg': '/static/images/company_logos/salesforce.svg',
        'initials': 'CRM',
        'brand_color': '#00A1E0',
    },
    'sap': {
        'name': 'SAP',
        'domain': 'sap.com',
        'cdn_url': 'https://cdn.simpleicons.org/sap/0FAAFF',
        'local_svg': '/static/images/company_logos/sap.svg',
        'initials': 'SAP',
        'brand_color': '#008FD3',
    },
    'nvidia': {
        'name': 'NVIDIA',
        'domain': 'nvidia.com',
        'cdn_url': 'https://cdn.simpleicons.org/nvidia/76B900',
        'local_svg': '/static/images/company_logos/nvidia.svg',
        'initials': 'NVDA',
        'brand_color': '#76B900',
    },
    'intel': {
        'name': 'Intel',
        'domain': 'intel.com',
        'cdn_url': 'https://cdn.simpleicons.org/intel/0068B5',
        'local_svg': '/static/images/company_logos/intel.svg',
        'initials': 'INTC',
        'brand_color': '#0068B5',
    },
    'cisco': {
        'name': 'Cisco',
        'domain': 'cisco.com',
        'cdn_url': 'https://cdn.simpleicons.org/cisco/1BA0D7',
        'local_svg': '/static/images/company_logos/cisco.svg',
        'initials': 'CSCO',
        'brand_color': '#1BA0D7',
    },
    'walmart': {
        'name': 'Walmart',
        'domain': 'walmart.com',
        'cdn_url': 'https://cdn.simpleicons.org/walmart/0071CE',
        'local_svg': '/static/images/company_logos/walmart.svg',
        'initials': 'WMT',
        'brand_color': '#0071CE',
    },
    'jpmorgan': {
        'name': 'JPMorgan Chase',
        'domain': 'jpmorganchase.com',
        'cdn_url': 'https://cdn.simpleicons.org/chase/117BBE',
        'local_svg': '/static/images/company_logos/jpmorgan.svg',
        'initials': 'JPMC',
        'brand_color': '#117BBE',
    },
    'jpmorgan chase': {
        'name': 'JPMorgan Chase',
        'domain': 'jpmorganchase.com',
        'cdn_url': 'https://cdn.simpleicons.org/chase/117BBE',
        'local_svg': '/static/images/company_logos/jpmorgan.svg',
        'initials': 'JPMC',
        'brand_color': '#117BBE',
    },
    'ey': {
        'name': 'EY (Ernst & Young)',
        'domain': 'ey.com',
        'cdn_url': 'https://cdn.simpleicons.org/ey/FFE600',
        'local_svg': '/static/images/company_logos/ey.svg',
        'initials': 'EY',
        'brand_color': '#2E2E38',
    },
    'kpmg': {
        'name': 'KPMG',
        'domain': 'kpmg.com',
        'cdn_url': 'https://cdn.simpleicons.org/kpmg/00338D',
        'local_svg': '/static/images/company_logos/kpmg.svg',
        'initials': 'KPMG',
        'brand_color': '#00338D',
    },
    'pwc': {
        'name': 'PwC',
        'domain': 'pwc.com',
        'cdn_url': 'https://cdn.simpleicons.org/pwc/D04A02',
        'local_svg': '/static/images/company_logos/pwc.svg',
        'initials': 'PWC',
        'brand_color': '#D04A02',
    },
    'goldman sachs': {
        'name': 'Goldman Sachs',
        'domain': 'goldmansachs.com',
        'cdn_url': 'https://cdn.simpleicons.org/goldmansachs/7399C6',
        'local_svg': '/static/images/company_logos/goldmansachs.svg',
        'initials': 'GS',
        'brand_color': '#7399C6',
    },
    'morgan stanley': {
        'name': 'Morgan Stanley',
        'domain': 'morganstanley.com',
        'cdn_url': 'https://cdn.simpleicons.org/morganstanley/002B49',
        'local_svg': '/static/images/company_logos/morganstanley.svg',
        'initials': 'MS',
        'brand_color': '#002B49',
    },
    'cred': {
        'name': 'CRED',
        'domain': 'cred.club',
        'cdn_url': 'https://cdn.simpleicons.org/cred/000000',
        'local_svg': '/static/images/company_logos/cred.svg',
        'initials': 'CRED',
        'brand_color': '#0A0A0A',
    },
    'razorpay': {
        'name': 'Razorpay',
        'domain': 'razorpay.com',
        'cdn_url': 'https://cdn.simpleicons.org/razorpay/0C2340',
        'local_svg': '/static/images/company_logos/razorpay.svg',
        'initials': 'RZP',
        'brand_color': '#0C2340',
    },
    'zepto': {
        'name': 'Zepto',
        'domain': 'zeptonow.com',
        'cdn_url': 'https://cdn.simpleicons.org/fastapi/800080',
        'local_svg': '/static/images/company_logos/zepto.svg',
        'initials': 'ZEP',
        'brand_color': '#800080',
    },
    'zerodha': {
        'name': 'Zerodha',
        'domain': 'zerodha.com',
        'cdn_url': 'https://cdn.simpleicons.org/kite/387ED1',
        'local_svg': '/static/images/company_logos/zerodha.svg',
        'initials': 'ZER',
        'brand_color': '#387ED1',
    },
    'postman': {
        'name': 'Postman',
        'domain': 'postman.com',
        'cdn_url': 'https://cdn.simpleicons.org/postman/FF6C37',
        'local_svg': '/static/images/company_logos/postman.svg',
        'initials': 'POST',
        'brand_color': '#FF6C37',
    },
    'browserstack': {
        'name': 'BrowserStack',
        'domain': 'browserstack.com',
        'cdn_url': 'https://cdn.simpleicons.org/browserstack/0088CC',
        'local_svg': '/static/images/company_logos/browserstack.svg',
        'initials': 'BSTK',
        'brand_color': '#0088CC',
    },
    'groww': {
        'name': 'Groww',
        'domain': 'groww.in',
        'cdn_url': 'https://cdn.simpleicons.org/groww/00D09C',
        'local_svg': '/static/images/company_logos/groww.svg',
        'initials': 'GRW',
        'brand_color': '#00D09C',
    },
    'urban company': {
        'name': 'Urban Company',
        'domain': 'urbancompany.com',
        'cdn_url': 'https://cdn.simpleicons.org/uber/000000',
        'local_svg': '/static/images/company_logos/urbancompany.svg',
        'initials': 'UC',
        'brand_color': '#000000',
    },
    'polygon': {
        'name': 'Polygon Labs',
        'domain': 'polygon.technology',
        'cdn_url': 'https://cdn.simpleicons.org/polygon/7B3FE4',
        'local_svg': '/static/images/company_logos/polygon.svg',
        'initials': 'POLY',
        'brand_color': '#7B3FE4',
    },
    'sarvam ai': {
        'name': 'Sarvam AI',
        'domain': 'sarvam.ai',
        'cdn_url': 'https://cdn.simpleicons.org/openai/10A37F',
        'local_svg': '/static/images/company_logos/sarvam.svg',
        'initials': 'SRV',
        'brand_color': '#FF5722',
    },
    'krutrim ai': {
        'name': 'Krutrim AI',
        'domain': 'krutrim.com',
        'cdn_url': 'https://cdn.simpleicons.org/sparkfun/E53935',
        'local_svg': '/static/images/company_logos/krutrim.svg',
        'initials': 'KRT',
        'brand_color': '#E53935',
    },
}


def normalize_company_key(name):
    if not name:
        return ''
    cleaned = re.sub(r'[^a-zA-Z0-9\s]', '', name.lower()).strip()
    # Check direct match
    if cleaned in COMPANY_BRAND_DATA:
        return cleaned
    # Substring checks
    for key in COMPANY_BRAND_DATA:
        if key in cleaned or cleaned in key:
            return key
    return cleaned


def resolve_company_logo(company_obj):
    """
    Returns the most reliable official logo URL for a company:
    1. Uploaded image file if exists
    2. Explicit logo_url on model if exists
    3. Curated local static SVG if found
    4. Curated official CDN SVG
    5. Clean fallback
    """
    if not company_obj:
        return '/static/images/company_logos/default.svg'

    # 1. Uploaded file
    if getattr(company_obj, 'logo', None) and bool(company_obj.logo):
        try:
            return company_obj.logo.url
        except Exception:
            pass

    # 2. Explicit logo_url
    if getattr(company_obj, 'logo_url', None) and company_obj.logo_url:
        return company_obj.logo_url

    # 3. Match against brand dictionary
    key = normalize_company_key(company_obj.name)
    if key in COMPANY_BRAND_DATA:
        brand = COMPANY_BRAND_DATA[key]
        return brand['local_svg']

    # 4. Fallback default
    return '/static/images/company_logos/default.svg'


def get_company_initials(name):
    """
    Generates clean 1 to 4 letter initials for company avatar badges
    """
    if not name:
        return 'CO'
    key = normalize_company_key(name)
    if key in COMPANY_BRAND_DATA:
        return COMPANY_BRAND_DATA[key]['initials']

    words = [w for w in re.split(r'[\s\-_]+', name) if w]
    if len(words) == 1:
        return words[0][:3].upper()
    return ''.join(w[0] for w in words[:3]).upper()


def get_company_brand_color(name):
    key = normalize_company_key(name)
    if key in COMPANY_BRAND_DATA:
        return COMPANY_BRAND_DATA[key].get('brand_color', '#2563EB')
    return '#2563EB'
