import os

def create_logos():
    out_dir = os.path.join('static', 'images', 'company_logos')
    os.makedirs(out_dir, exist_ok=True)

    svgs = {
        'google': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/><path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/><path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/><path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/></svg>',
        'microsoft': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><rect x="2" y="2" width="20" height="20" fill="#F25022"/><rect x="26" y="2" width="20" height="20" fill="#7FBA00"/><rect x="2" y="26" width="20" height="20" fill="#00A4EF"/><rect x="26" y="26" width="20" height="20" fill="#FFB900"/></svg>',
        'amazon': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 50"><path fill="#232F3E" d="M18 10h6v18c0 3 1.5 5 4.5 5 3.5 0 5.5-2 5.5-6V10h6v24h-5.5v-3.5C32.5 33 29.5 35 25 35c-6 0-9-3.5-9-9V10z"/><path fill="#232F3E" d="M44 14h6v3c2-2.5 4.5-3.5 8-3.5 6 0 9 4 9 10v11h-6V24c0-3-1.5-4.5-4.5-4.5-3.5 0-5.5 2-5.5 5.5v9.5h-6V14z"/><path fill="#FF9900" d="M10 40c22 10 52 10 74-2 2-1 4 2 2 3-24 13-56 12-80 1-2-1 1-3 4-2z"/><path fill="#FF9900" d="M83 37c2 2 4 4 6 5-1 2-2 4-2 7 2-3 5-7 6-10-3-1-7-1-10-2z"/></svg>',
        'accenture': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 50"><text x="5" y="32" font-family="Arial, sans-serif" font-size="22" font-weight="bold" fill="#000">accenture</text><path fill="#A100FF" d="M58 8l8 6-8 6V8z"/></svg>',
        'adobe': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><rect width="48" height="48" rx="8" fill="#FA0F00"/><path fill="#FFF" d="M6 6h12.5L7 38.5h11.5L24 23.5l5.5 15h11.5L29.5 6H42v36H6V6z"/></svg>',
        'atlassian': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><path fill="#0052CC" d="M23.5 20.3C23.2 20 22.8 19.8 22.4 20l-10.9 6.2c-.4.2-.6.7-.4 1.1l7.8 14.1c.2.4.6.6 1 .6h.6c.4-.2.6-.7.4-1.1L23.5 20.3z"/><path fill="#2684FF" d="M24.5 7.6c-.3-.4-.8-.5-1.2-.2l-5.6 4.2c-.4.3-.5.8-.2 1.2l9.7 13.9c.3.4.8.5 1.2.2l5.6-4.2c.4-.3.5-.8.2-1.2L24.5 7.6z"/></svg>',
        'capgemini': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><path fill="#0070AD" d="M24 4C14 4 6 12 6 22c0 8 5 15 12 18l3-8c-4-2-7-6-7-10 0-6 4-10 10-10s10 4 10 10c0 4-3 8-7 10l3 8c7-3 12-10 12-18 0-10-8-18-18-18z"/><circle cx="24" cy="22" r="5" fill="#1B365D"/></svg>',
        'cognizant': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><path fill="#0033A0" d="M24 6C14.1 6 6 14.1 6 24s8.1 18 18 18c6.6 0 12.4-3.6 15.5-9l-7.2-4.2C30.6 31.4 27.5 33 24 33c-5 0-9-4-9-9s4-9 9-9c3.5 0 6.6 1.6 8.3 4.2l7.2-4.2C36.4 9.6 30.6 6 24 6z"/><circle cx="36" cy="24" r="4.5" fill="#1B75BC"/></svg>',
        'deloitte': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 40"><text x="2" y="28" font-family="Arial, sans-serif" font-size="24" font-weight="bold" fill="#000">Deloitte</text><circle cx="92" cy="26" r="4" fill="#86BC25"/></svg>',
        'flipkart': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><rect width="48" height="48" rx="8" fill="#2874F0"/><path fill="#FFE11B" d="M14 18h20l-3 18H17L14 18z"/><path fill="#FFF" d="M20 18v-4c0-2.2 1.8-4 4-4s4 1.8 4 4v4" stroke="#FFF" stroke-width="3" fill="none"/><path fill="#2874F0" d="M22 25h6l-4 6h4"/></svg>',
        'ibm': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 40"><text x="5" y="32" font-family="Impact, Arial Black, sans-serif" font-size="36" font-weight="900" fill="#052FAD" letter-spacing="4">IBM</text></svg>',
        'infosys': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 40"><text x="5" y="28" font-family="Arial, sans-serif" font-size="26" font-weight="bold" fill="#007CC3">Infosys</text></svg>',
        'tcs': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 40"><rect width="100" height="40" rx="6" fill="#005A9C"/><text x=\"20\" y=\"28\" font-family=\"Arial, sans-serif\" font-size=\"22\" font-weight=\"bold\" fill=\"#FFF\" letter-spacing=\"2\">TCS</text></svg>',
        'wipro': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 40"><text x="5" y="28" font-family="Arial, sans-serif" font-size="26" font-weight="bold" fill="#5F259F">wipro</text><circle cx="84" cy="22" r="4" fill="#FFA500"/><circle cx="92" cy="18" r="3" fill="#00A859"/><circle cx="94" cy="26" r="2.5" fill="#E5243B"/></svg>',
        'hcltech': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 40"><text x="5" y="28" font-family="Arial, sans-serif" font-size="24" font-weight="bold" fill="#004085">HCLTech</text></svg>',
        'techmahindra': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 40"><text x="5" y="20" font-family="Arial, sans-serif" font-size="15" font-weight="bold" fill="#333">Tech</text><text x="5" y="36" font-family="Arial, sans-serif" font-size="15" font-weight="bold" fill="#E31837">Mahindra</text></svg>',
        'oracle': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 40"><text x="5" y="28" font-family="Arial, sans-serif" font-size="24" font-weight="900" fill="#F80000" letter-spacing="3">ORACLE</text></svg>',
        'salesforce': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><path fill="#00A1E0" d="M19.4 11.2c2.2-2.3 5.4-3.7 8.8-3.7 5.6 0 10.3 3.8 11.7 8.9 2.5.8 4.3 3.2 4.3 6 0 3.5-2.8 6.3-6.3 6.3H10.5C6.9 28.7 4 25.8 4 22.2c0-3.3 2.5-6 5.7-6.4 1.3-4.5 5.5-7.8 10.4-7.8.6 0 1.2.1 1.8.2l-2.5 3z"/></svg>',
        'sap': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><path fill="#008FD3" d="M2 6h44v36H2z"/><text x="7" y="32" font-family="Arial, sans-serif" font-size="24" font-weight="900" fill="#FFF">SAP</text></svg>',
        'nvidia': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><path fill="#76B900" d="M24 10c-7.7 0-14 6.3-14 14s6.3 14 14 14c5.1 0 9.6-2.8 12.1-6.9l-4.5-2.6C29.8 30.6 27.1 32 24 32c-4.4 0-8-3.6-8-8s3.6-8 8-8c2.9 0 5.4 1.5 6.8 3.8l4.6-2.6C32.9 13.1 28.7 10 24 10z"/><circle cx="24" cy="24" r="3.5" fill="#76B900"/></svg>',
        'intel': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 40"><text x="5" y="28" font-family="Arial, sans-serif" font-size="28" font-weight="bold" fill="#0068B5">intel</text><circle cx="23" cy="12" r="2" fill="#00C7FD"/></svg>',
        'cisco': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><path fill="#1BA0D7" d="M8 20v12h3V20H8zm7-6v18h3V14h-3zm7-6v24h3V8h-3zm7 0v24h3V8h-3zm7 6v18h3V14h-3zm7 6v12h3V20h-3z"/></svg>',
        'walmart': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><path fill="#0071CE" d="M4 6h40v36H4z"/><path fill="#FFC220" d="M24 12v24m-12-12h24m-17-8.5l17 17m0-17l-17 17" stroke="#FFC220" stroke-width="4" stroke-linecap="round"/></svg>',
        'jpmorgan': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 40"><rect width="100" height="40" rx="6" fill="#117BBE"/><text x="10" y="26" font-family="Arial, sans-serif" font-size="15" font-weight="bold" fill="#FFF" letter-spacing="1">J.P.Morgan</text></svg>',
        'ey': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><rect width="48" height="48" rx="8" fill="#2E2E38"/><text x="8" y="32" font-family="Arial, sans-serif" font-size="24" font-weight="900" fill="#FFE600">EY</text></svg>',
        'kpmg': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 40"><rect width="100" height="40" rx="6" fill="#00338D"/><text x="12" y="28" font-family="Arial, sans-serif" font-size="22" font-weight="bold" fill="#FFF" letter-spacing="3">KPMG</text></svg>',
        'pwc': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 40"><rect width="100" height="40" rx="6" fill="#D04A02"/><text x="20" y="28" font-family="Georgia, serif" font-size="22" font-weight="bold" fill="#FFF">pwc</text></svg>',
        'goldmansachs': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 40"><rect width="100" height="40" rx="6" fill="#7399C6"/><text x="8" y="20" font-family="Arial, sans-serif" font-size="13" font-weight="bold" fill="#FFF">Goldman</text><text x="8" y="34" font-family="Arial, sans-serif" font-size="13" font-weight="bold" fill="#FFF">Sachs</text></svg>',
        'morganstanley': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 40"><rect width="100" height="40" rx="6" fill="#002B49"/><text x="6" y="20" font-family="Arial, sans-serif" font-size="12" font-weight="bold" fill="#FFF">Morgan</text><text x="6" y="34" font-family="Arial, sans-serif" font-size="12" font-weight="bold" fill="#FFF">Stanley</text></svg>',
        'cred': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><rect width="48" height="48" rx="8" fill="#000"/><path fill="#FFF" d="M16 12h16v8h-8v8h8v8H16V12z"/></svg>',
        'razorpay': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><rect width="48" height="48" rx="8" fill="#0C2340"/><path fill="#00BAF2" d="M14 36l12-24h8L22 36h-8z"/><path fill="#3395FF" d="M24 24l4-8h6l-4 8h-6z"/></svg>',
        'zepto': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><rect width="48" height="48" rx="8" fill="#800080"/><text x="12" y="34" font-family="Arial, sans-serif" font-size="28" font-weight="900" fill="#FFF">Z</text></svg>',
        'zerodha': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><rect width="48" height="48" rx="8" fill="#387ED1"/><polygon points="24,10 36,24 24,38 12,24" fill="#FFF"/></svg>',
        'postman': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><rect width="48" height="48" rx="8" fill="#FF6C37"/><circle cx="24" cy="24" r="10" fill="#FFF"/><path fill="#FF6C37" d="M22 18l8 6-8 6V18z"/></svg>',
        'browserstack': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><rect width="48" height="48" rx="8" fill="#0088CC"/><circle cx="20" cy="20" r="8" fill="#FFA000"/><circle cx="28" cy="28" r="8" fill="#00E676"/></svg>',
        'groww': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><rect width="48" height="48" rx="8" fill="#00D09C"/><circle cx="24" cy="24" r="12" stroke="#FFF" stroke-width="4" fill="none"/></svg>',
        'urbancompany': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><rect width="48" height="48" rx="8" fill="#000"/><text x="10" y="32" font-family="Arial, sans-serif" font-size="20" font-weight="900" fill="#FFF">UC</text></svg>',
        'polygon': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><rect width="48" height="48" rx="8" fill="#7B3FE4"/><polygon points="24,8 38,16 38,32 24,40 10,32 10,16" fill="#FFF"/></svg>',
        'sarvam': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><rect width="48" height="48" rx="8" fill="#FF5722"/><circle cx="24" cy="24" r="10" fill="#FFF"/><circle cx="24" cy="24" r="5" fill="#FF5722"/></svg>',
        'krutrim': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><rect width="48" height="48" rx="8" fill="#E53935"/><rect x="16" y="16" width="16" height="16" fill="#FFF"/></svg>',
        'default': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><rect width="48" height="48" rx="8" fill="#2563EB"/><path fill="#FFF" d="M16 16h16v16H16z" opacity="0.9"/><path fill="#FFF" d="M20 12h8v4h-8z"/></svg>'
    }

    count = 0
    for name, content in svgs.items():
        path = os.path.join(out_dir, f'{name}.svg')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content.strip())
        count += 1

    print(f'Successfully wrote {count} SVG logos into {out_dir}')

if __name__ == '__main__':
    create_logos()
