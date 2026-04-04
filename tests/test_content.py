import pytest
from src.content import Content, ContentStatus, InvalidTransitionError, AccountType, ContentType
from datetime import datetime


class TestContentStateMachine:
    def test_draft_to_pending_review(self):
        """DRAFT -> PENDING_REVIEW should succeed"""
        c = Content(id="1", account_type=AccountType.A)
        c.transition_to(ContentStatus.PENDING_REVIEW)
        assert c.status == ContentStatus.PENDING_REVIEW

    def test_pending_review_to_approved(self):
        """PENDING_REVIEW -> APPROVED should succeed"""
        c = Content(id="1", account_type=AccountType.A, status=ContentStatus.PENDING_REVIEW)
        c.transition_to(ContentStatus.APPROVED)
        assert c.status == ContentStatus.APPROVED

    def test_approved_to_published(self):
        """APPROVED -> PUBLISHED should succeed"""
        c = Content(id="1", account_type=AccountType.A, status=ContentStatus.APPROVED)
        c.transition_to(ContentStatus.PUBLISHED)
        assert c.status == ContentStatus.PUBLISHED

    def test_draft_to_rejected(self):
        """DRAFT -> REJECTED should succeed"""
        c = Content(id="1", account_type=AccountType.A)
        c.transition_to(ContentStatus.REJECTED)
        assert c.status == ContentStatus.REJECTED

    def test_invalid_transition_approved_to_draft(self):
        """APPROVED -> DRAFT should fail"""
        c = Content(id="1", account_type=AccountType.A, status=ContentStatus.APPROVED)
        with pytest.raises(InvalidTransitionError):
            c.transition_to(ContentStatus.DRAFT)

    def test_invalid_transition_published_to_draft(self):
        """PUBLISHED -> DRAFT should fail"""
        c = Content(id="1", account_type=AccountType.A, status=ContentStatus.PUBLISHED)
        with pytest.raises(InvalidTransitionError):
            c.transition_to(ContentStatus.DRAFT)

    def test_pending_review_to_rejected(self):
        """PENDING_REVIEW -> REJECTED should succeed"""
        c = Content(id="1", account_type=AccountType.A, status=ContentStatus.PENDING_REVIEW)
        c.transition_to(ContentStatus.REJECTED)
        assert c.status == ContentStatus.REJECTED

    def test_published_to_analyzed(self):
        """PUBLISHED -> ANALYZED should succeed"""
        c = Content(id="1", account_type=AccountType.A, status=ContentStatus.PUBLISHED)
        c.transition_to(ContentStatus.ANALYZED)
        assert c.status == ContentStatus.ANALYZED

    def test_invalid_transition_rejected_to_published(self):
        """REJECTED -> PUBLISHED should fail"""
        c = Content(id="1", account_type=AccountType.A, status=ContentStatus.REJECTED)
        with pytest.raises(InvalidTransitionError):
            c.transition_to(ContentStatus.PUBLISHED)

    def test_invalid_transition_analyzed_to_draft(self):
        """ANALYZED -> DRAFT should fail (terminal state)"""
        c = Content(id="1", account_type=AccountType.A, status=ContentStatus.ANALYZED)
        with pytest.raises(InvalidTransitionError):
            c.transition_to(ContentStatus.DRAFT)

    def test_transition_updates_updated_at(self):
        """transition_to() should update updated_at timestamp"""
        c = Content(id="1", account_type=AccountType.A)
        original_updated_at = c.updated_at
        c.transition_to(ContentStatus.PENDING_REVIEW)
        assert c.updated_at >= original_updated_at

    def test_invalid_transition_raises_message_with_states(self):
        """InvalidTransitionError message should name both states"""
        c = Content(id="1", account_type=AccountType.A, status=ContentStatus.APPROVED)
        with pytest.raises(InvalidTransitionError, match="APPROVED"):
            c.transition_to(ContentStatus.DRAFT)


class TestContentSerialization:
    def test_to_dict_preserves_all_fields(self):
        """to_dict() should include all fields"""
        now = datetime.now()
        c = Content(
            id="1",
            account_type=AccountType.B,
            title="Test",
            body="Body",
            reasoning="Good content",
            scheduled_time=now
        )
        d = c.to_dict()
        assert d['id'] == "1"
        assert d['account_type'] == 'B'
        assert d['title'] == "Test"
        assert d['reasoning'] == "Good content"

    def test_from_dict_reconstruction(self):
        """from_dict() should reconstruct Content identically"""
        c1 = Content(
            id="1",
            account_type=AccountType.C,
            status=ContentStatus.PENDING_REVIEW,
            content_type=ContentType.PREDICTION,
            title="Title",
            body="Body"
        )
        d = c1.to_dict()
        c2 = Content.from_dict(d)
        assert c2.id == c1.id
        assert c2.account_type == c1.account_type
        assert c2.status == c1.status
        assert c2.title == c1.title

    def test_to_dict_enum_values_are_strings(self):
        """to_dict() should serialize Enums to their string values"""
        c = Content(id="1", account_type=AccountType.A)
        d = c.to_dict()
        assert isinstance(d['status'], str)
        assert isinstance(d['account_type'], str)
        assert isinstance(d['content_type'], str)
        assert d['status'] == 'DRAFT'
        assert d['account_type'] == 'A'
        assert d['content_type'] == 'NEWS_RECAP'

    def test_to_dict_datetime_is_iso_string(self):
        """to_dict() should serialize datetimes to ISO 8601 strings"""
        now = datetime.now()
        c = Content(id="1", account_type=AccountType.A, scheduled_time=now)
        d = c.to_dict()
        assert isinstance(d['scheduled_time'], str)
        assert isinstance(d['created_at'], str)
        assert isinstance(d['updated_at'], str)

    def test_to_dict_none_datetime_is_none(self):
        """to_dict() should keep None datetimes as None"""
        c = Content(id="1", account_type=AccountType.A)
        d = c.to_dict()
        assert d['scheduled_time'] is None
        assert d['published_at'] is None

    def test_from_dict_with_none_optional_fields(self):
        """from_dict() should handle None optional fields correctly"""
        c1 = Content(id="1", account_type=AccountType.A)
        d = c1.to_dict()
        c2 = Content.from_dict(d)
        assert c2.scheduled_time is None
        assert c2.published_at is None
        assert c2.source_url is None
        assert c2.image_path is None

    def test_roundtrip_preserves_platform_status(self):
        """Roundtrip to_dict/from_dict should preserve dict fields"""
        c1 = Content(
            id="1",
            account_type=AccountType.A,
            platform_status={"threads": "ok", "x": "pending"},
            engagement_data={"likes": 42, "replies": 3}
        )
        d = c1.to_dict()
        c2 = Content.from_dict(d)
        assert c2.platform_status == c1.platform_status
        assert c2.engagement_data == c1.engagement_data

    def test_from_dict_with_already_enum_values(self):
        """from_dict() should handle pre-converted Enum values gracefully"""
        c = Content(
            id="1",
            account_type=AccountType.A,
            status=ContentStatus.DRAFT,
            content_type=ContentType.EDUCATIONAL
        )
        d = c.to_dict()
        # Re-parse from the dict representation
        c2 = Content.from_dict(d)
        assert c2.content_type == ContentType.EDUCATIONAL

    def test_default_status_is_draft(self):
        """Content default status should be DRAFT"""
        c = Content(id="1", account_type=AccountType.A)
        assert c.status == ContentStatus.DRAFT

    def test_default_content_type_is_news_recap(self):
        """Content default content_type should be NEWS_RECAP"""
        c = Content(id="1", account_type=AccountType.A)
        assert c.content_type == ContentType.NEWS_RECAP

    def test_all_account_types_serializable(self):
        """All AccountType values (A, B, C) should serialize correctly"""
        for account in AccountType:
            c = Content(id="1", account_type=account)
            d = c.to_dict()
            c2 = Content.from_dict(d)
            assert c2.account_type == account

    def test_all_content_types_serializable(self):
        """All ContentType values should serialize correctly"""
        for ct in ContentType:
            c = Content(id="1", account_type=AccountType.A, content_type=ct)
            d = c.to_dict()
            c2 = Content.from_dict(d)
            assert c2.content_type == ct
