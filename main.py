import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
import time

def extract_emails_phones_addresses(text):
    # Extract emails
    emails = set(re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text))

    # Extract Indian & general phone numbers
    phones = set(re.findall(r"\+91[-\s]?[6-9]\d{9}|\b\d{3,5}[-.\s]?\d{5,7}\b", text))

    # Extract address-like text
    address_pattern = r'\b[#\d\w\s,-]{5,100}(Street|location|Address)\b.*?[.,]'
    addresses = set(re.findall(address_pattern, text, flags=re.IGNORECASE))

    return emails, phones, addresses

def extract_profit_marketing(text):
    profit_info = []
    marketing_info = []

    sentences = re.split(r'(?<=[.!?])\s+', text)
    for sentence in sentences:
        if re.search(r'\bprofit\b', sentence, re.I):
            profit_info.append(sentence.strip())
        if re.search(r'\bmarketing budget\b', sentence, re.I):
            marketing_info.append(sentence.strip())

    return profit_info, marketing_info

def crawl_website(start_url, max_pages=20):
    visited = set()
    to_visit = [start_url]
    emails, phones, addresses = set(), set(), set()
    profits, marketing = [], []

    while to_visit and len(visited) < max_pages:
        url = to_visit.pop(0)
        if url in visited:
            continue
        visited.add(url)
        st.write(f"Crawling: {url}")

        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Get visible text only
            text = soup.get_text(separator=' ', strip=True)

            e, p, a = extract_emails_phones_addresses(text)
            emails.update(e)
            phones.update(p)
            addresses.update(a)

            p_info, m_info = extract_profit_marketing(text)
            profits.extend(p_info)
            marketing.extend(m_info)

            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(url, href)
                parsed = urlparse(full_url)

                # Filter unwanted domains (optional)
                if full_url.startswith(('http', 'https')) and parsed.netloc.endswith(urlparse(start_url).netloc):
                    if full_url not in visited:
                        to_visit.append(full_url)

            time.sleep(0.5)  # Polite delay

        except Exception as e:
            st.warning(f"Failed to crawl {url}: {e}")

    return emails, phones, addresses, profits, marketing

def main():
    st.title("🌐 Company Contact & Business Info Crawler")

    company_url = st.text_input("Enter Company Website URL (e.g., https://example.com)")

    max_pages = st.slider("Max pages to crawl", 5, 50, 15)

    if st.button("Start Crawling") and company_url:
        with st.spinner("Crawling the website..."):
            emails, phones, addresses, profits, marketing = crawl_website(company_url, max_pages)

        st.success("✅ Crawling Complete!")

        st.subheader("📧 Emails Found:")
        st.json(list(emails) if emails else ["No emails found."])

        st.subheader("📞 Phone Numbers Found:")
        st.json(list(phones) if phones else ["No phone numbers found."])

        st.subheader("📍 Addresses Found:")
        st.json(list(addresses) if addresses else ["No addresses found."])

        st.subheader("📈 Profitability Information:")
        st.write(profits if profits else "No profitability info found.")

        st.subheader("💰 Marketing Budget Information:")
        st.write(marketing if marketing else "No marketing budget info found.")

if __name__ == "__main__":
    main()
