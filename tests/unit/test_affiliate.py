from desiquip.adapters.affiliate import amazon_search_link
from desiquip.services.affiliate import AffiliateService


def test_amazon_link_is_a_tagged_search_never_an_invented_product():
    assert amazon_search_link("smart plug wifi", "desiquip-21") == \
        "https://www.amazon.in/s?k=smart+plug+wifi&tag=desiquip-21"


class FakeShortener:
    def shorten(self, url):
        return "https://bit.ly/x" + str(len(url))


class TestAffiliateService:
    def test_builds_tagged_links_and_deals_page(self, store, job, tmp_path):
        svc = AffiliateService(store, amazon_tag="desiquip-21", shortener=FakeShortener(), deals_page=tmp_path / "deals.md")
        svc.run(job)
        links = store.read_json(job, "links.json")["links"]
        assert links[0]["ref"] == "p1" and "tag=desiquip-21" in links[0]["url"]
        assert links[0]["short_url"].startswith("https://bit.ly/")
        assert "mini chopper" in (tmp_path / "deals.md").read_text(encoding="utf-8")

    def test_without_amazon_tag_writes_no_links(self, store, job, tmp_path):
        AffiliateService(store, amazon_tag="", shortener=None, deals_page=tmp_path / "deals.md").run(job)
        assert store.read_json(job, "links.json") == {"links": [], "note": "AMZ_TAG not set"}
