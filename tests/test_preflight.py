"""tests/test_preflight.py — Unit tests for src/preflight.py"""

import pytest
from src.content import AccountType, Content, ContentStatus
from src.preflight import preflight_check


def make_content(**kwargs) -> Content:
    defaults = dict(
        id="1",
        account_type=AccountType.A,
        status=ContentStatus.PENDING_REVIEW,
        title="測試標題",
        body="短文內文",
        image_path=None,
    )
    defaults.update(kwargs)
    return Content(**defaults)


def test_preflight_passes_clean_content():
    content = make_content()
    assert preflight_check(content, ["x"]) == []


def test_preflight_warns_x_overlength():
    content = make_content(body="x" * 281)
    warnings = preflight_check(content, ["x"])
    assert any("X 字數超限" in w for w in warnings)


def test_preflight_warns_threads_overlength():
    content = make_content(body="t" * 501)
    warnings = preflight_check(content, ["threads"])
    assert any("Threads 字數超限" in w for w in warnings)


def test_preflight_warns_ig_no_image():
    content = make_content(image_path=None)
    warnings = preflight_check(content, ["instagram"])
    assert any("IG 需要圖片" in w for w in warnings)


def test_preflight_warns_ig_image_not_exists(tmp_path):
    content = make_content(image_path=str(tmp_path / "nonexistent.png"))
    warnings = preflight_check(content, ["instagram"])
    assert any("IG 圖片路徑不存在" in w for w in warnings)


def test_preflight_warns_empty_title():
    content = make_content(title="  ")
    warnings = preflight_check(content, ["x"])
    assert any("標題為空" in w for w in warnings)


def test_preflight_warns_empty_body():
    content = make_content(body="")
    warnings = preflight_check(content, ["x"])
    assert any("內文為空" in w for w in warnings)


def test_preflight_multiple_platforms_multiple_warnings():
    content = make_content(body="t" * 501, image_path=None)
    warnings = preflight_check(content, ["threads", "instagram", "x"])
    assert any("Threads 字數超限" in w for w in warnings)
    assert any("IG 需要圖片" in w for w in warnings)


def test_preflight_warns_linkedin_overlength():
    content = make_content(body="l" * 3001)
    warnings = preflight_check(content, ["linkedin"])
    assert any("LinkedIn 字數超限" in w for w in warnings)
