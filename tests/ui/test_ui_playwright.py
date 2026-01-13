import allure
import pytest

from tests.ui.pages.home_page import HomePage

pytest.importorskip("playwright.sync_api")


@allure.epic("Storefront")
@allure.feature("Home Page")
@allure.story("Hero content (browser)")
@allure.severity(allure.severity_level.CRITICAL)
@allure.label("layer", "ui")
@allure.label("component", "homepage")
@pytest.mark.ui
@pytest.mark.e2e
def test_hero_title_visible(ui_page, base_url):
    home = HomePage(ui_page)
    with allure.step("Open home page"):
        home.open(base_url)
    with allure.step("Validate hero title"):
        assert home.hero_title_text() == "Demo Shop"


@allure.epic("Storefront")
@allure.feature("Home Page")
@allure.story("CTA text (browser)")
@allure.severity(allure.severity_level.CRITICAL)
@allure.label("layer", "ui")
@allure.label("component", "homepage")
@pytest.mark.ui
@pytest.mark.e2e
def test_cta_button_text(ui_page, base_url):
    home = HomePage(ui_page)
    with allure.step("Open home page"):
        home.open(base_url)
    with allure.step("Validate CTA text"):
        assert home.cta_text() == "Buy Now"
