from playwright.sync_api import sync_playwright

def scrape_company_site(base_url):
    pages_to_try = [
        base_url,
        base_url + "/about",
        base_url + "/about-us",
        base_url + "/company",
        base_url + "/who-we-are",
        base_url + "/products",
        base_url + "/solutions"
    ]

    all_text = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for url in pages_to_try:
            try:
                page.goto(url, timeout=15000)
                page.wait_for_load_state("networkidle")
                text = page.inner_text("body")
                all_text.append(f"\n--- PAGE: {url} ---\n{text}")
            except Exception as e:
                print(f"Skipped {url}: {e}")

        browser.close()

    return "\n".join(all_text)

if __name__ == "__main__":
    text = scrape_company_site("https://www.davisware.com")
    with open("scraped_text.txt", "w", encoding="utf-8") as f:
        f.write(text)

    print("Scraping complete. Output saved to scraped_text.txt")
