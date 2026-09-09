import asyncio

from api.index import MeetSpotRequest
from app.i18n import get_translations
from app.tool.meetspot_recommender import CafeRecommender


def _sample_locations():
    return [
        {
            "name": "Peking University",
            "formatted_address": "No. 5 Yiheyuan Road, Haidian, Beijing",
            "location": "116.3100,39.9920",
            "lng": 116.3100,
            "lat": 39.9920,
            "city": "Beijing",
        },
        {
            "name": "Tsinghua University",
            "formatted_address": "Qinghua Yuan, Haidian, Beijing",
            "location": "116.3260,40.0030",
            "lng": 116.3260,
            "lat": 40.0030,
            "city": "Beijing",
        },
    ]


def _sample_places():
    return [
        {
            "name": "Manner Coffee",
            "location": "116.3180,39.9970",
            "address": "B1, Zhongguancun Plaza, Beijing",
            "business_hours": "08:00-21:00",
            "tel": "010-12345678",
            "tag": ["咖啡馆", "WiFi", "安静"],
            "biz_ext": {"rating": "4.7"},
            "_matched_requirements": ["安静", "WiFi"],
            "_requirement_confidence": {"安静": "high", "WiFi": "medium"},
            "_recommendation_reason": "Closest option, only 420m away · Matches your quiet, Wi-Fi needs",
            "_score": 91,
            "_score_breakdown": {
                "base": 28,
                "distance": 24,
                "popularity": 18,
                "scenario": 13,
                "requirement": 8,
            },
        }
    ]


def _make_recommender(monkeypatch):
    recommender = CafeRecommender(api_key="test-key")

    async def _fake_transport_tips(*args, **kwargs):
        return "<li><i class='bx bx-train'></i>Take Metro Line 4 and arrive 10 minutes early</li>"

    monkeypatch.setattr(recommender, "_llm_generate_transport_tips", _fake_transport_tips)
    return recommender


def test_generate_html_content_english(monkeypatch):
    recommender = _make_recommender(monkeypatch)

    html = asyncio.run(
        recommender._generate_html_content(
            locations=_sample_locations(),
            places=_sample_places(),
            center_point=(116.3180, 39.9975),
            user_requirements="quiet with Wi-Fi",
            keywords="咖啡馆",
            participant_locations=["Peking University", "Tsinghua University"],
            language="en",
        )
    )

    assert '<html lang="en">' in html
    assert "Recommendation Summary" in html
    assert "Participant Locations" in html
    assert "Map Overview" in html
    assert "Travel & Parking Tips" in html
    assert "AI Search Process" in html
    assert "Step 4: POI Search" in html
    assert "Search Again" in html
    assert "Copy Link" in html
    assert "Navigate" in html
    assert "Closest option" in html
    assert "quiet" in html
    assert "推荐摘要" not in html


def test_generate_html_content_chinese(monkeypatch):
    recommender = _make_recommender(monkeypatch)

    html = asyncio.run(
        recommender._generate_html_content(
            locations=_sample_locations(),
            places=_sample_places(),
            center_point=(116.3180, 39.9975),
            user_requirements="环境安静 有WiFi",
            keywords="咖啡馆",
            participant_locations=["北京大学", "清华大学"],
            language="zh",
        )
    )

    assert '<html lang="zh-CN">' in html
    assert "推荐摘要" in html
    assert "交通与停车建议" in html
    assert "AI 搜索过程" in html


def test_format_result_text_english(monkeypatch):
    recommender = _make_recommender(monkeypatch)

    result_text = recommender._format_result_text(
        locations=_sample_locations(),
        places=_sample_places(),
        html_path="workspace/js_src/place_recommendation_test.html",
        keywords="咖啡馆",
        language="en",
    )

    assert "Recommended cafes" in result_text
    assert "Rating: 4.7" in result_text
    assert "HTML page: place_recommendation_test.html" in result_text


def test_result_translation_keys_exist():
    zh = get_translations("zh")
    en = get_translations("en")
    required_keys = [
        "result.nav.research",
        "result.summary.title",
        "result.section.locations",
        "result.section.map",
        "result.section.venues",
        "result.transport.title",
        "result.place.rating_label",
        "result.empty.title",
        "result.footer.text",
    ]

    for key in required_keys:
        assert key in zh
        assert key in en


def test_meetspot_request_accepts_language():
    request = MeetSpotRequest(locations=["A", "B"], language="en")
    assert request.language == "en"
