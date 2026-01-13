class HomePage:
    def __init__(self, page):
        self.page = page

    def open(self, base_url):
        self.page.goto(base_url, wait_until="domcontentloaded")

    def hero_title_text(self):
        return self.page.locator("[data-test='hero-title']").inner_text().strip()

    def cta_text(self):
        return self.page.locator("[data-test='cta-button']").inner_text().strip()
