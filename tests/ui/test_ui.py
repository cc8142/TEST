from html.parser import HTMLParser

import allure
import pytest


class _DataTestParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.data_tests = []
        self.title_text = ""

    def handle_starttag(self, tag, attrs):
        attr_map = dict(attrs)
        if "data-test" in attr_map:
            self.data_tests.append(attr_map["data-test"])

    def handle_data(self, data):
        if "Demo Shop" in data and not self.title_text:
            self.title_text = data.strip()


def _get_html(client):
    resp = client.get("/")
    resp.raise_for_status()
    return resp.text


@pytest.mark.ui
@pytest.mark.smoke
@allure.epic("Storefront")
@allure.feature("Home Page")
@allure.story("Hero content")
@allure.severity(allure.severity_level.NORMAL)
@allure.label("layer", "ui")
@allure.label("component", "homepage")
def test_hero_title_present(api_client):
    with allure.step("Load home page HTML"):
        html = _get_html(api_client)
        allure.attach(html, name="home_html", attachment_type=allure.attachment_type.HTML)
    with allure.step("Parse hero title"):
        parser = _DataTestParser()
        parser.feed(html)
    with allure.step("Validate hero title text"):
        assert "hero-title" in parser.data_tests
        assert parser.title_text == "Demo Shop"


@pytest.mark.ui
@allure.epic("Storefront")
@allure.feature("Home Page")
@allure.story("CTA presence")
@allure.severity(allure.severity_level.MINOR)
@allure.label("layer", "ui")
@allure.label("component", "homepage")
def test_cta_button_present(api_client):
    with allure.step("Load home page HTML"):
        html = _get_html(api_client)
    with allure.step("Parse CTA button"):
        parser = _DataTestParser()
        parser.feed(html)
    with allure.step("Validate CTA button is present"):
        assert "cta-button" in parser.data_tests


@pytest.mark.ui
@allure.epic("Storefront")
@allure.feature("Home Page")
@allure.story("Feature list")
@allure.severity(allure.severity_level.MINOR)
@allure.label("layer", "ui")
@allure.label("component", "homepage")
def test_feature_items_present(api_client):
    with allure.step("Load home page HTML"):
        html = _get_html(api_client)
    with allure.step("Parse feature items"):
        parser = _DataTestParser()
        parser.feed(html)
    with allure.step("Validate feature list count"):
        assert parser.data_tests.count("feature-item") >= 3
