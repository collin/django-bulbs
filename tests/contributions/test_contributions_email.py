"""Tests for bulbs.contributions.email."""
import mock
import random

from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from django.utils import timezone

from bulbs.contributions.email import EmailReport
from bulbs.contributions.models import ContributorRole
from bulbs.utils.test import make_content, BaseAPITestCase

from example.testcontent.models import TestContentObj


User = get_user_model()


# class EmailReportTestCase(BaseIndexableTestCase):
class EmailReportTestCase(BaseAPITestCase):
    """TestCase for bulbs.contributions.email.EmailReport."""

    def setUp(self):
        super(EmailReportTestCase, self).setUp()
        # Define relevant variables.
        self.endpoint = reverse("contributor-email-list")
        self.last_month = (self.now.month - 1) % 12
        self.next_month = (self.now.month + 1) % 12

        # Add Users.
        self.tony_sarpino = User.objects.create(
            first_name="Tony",
            last_name="Sarpino",
            username="Tone",
            email="admin@theonion.com"
        )
        self.buddy_sarpino = User.objects.create(
            first_name="Buddy", last_name="Sarpino", username="Buddy"
        )

        # Add Roles.
        self.draft_writer = ContributorRole.objects.create(name="Draft Writer", payment_type=0)

        # Add Rates.
        self.draft_writer.flat_rates.create(rate=60)

        # Make Content with contributions.
        make_content(
            TestContentObj,
            authors=[self.tony_sarpino],
            published=timezone.datetime(
                day=random.randrange(1, 28), month=self.now.month, year=self.now.year
            ),
            _quantity=25
        )
        make_content(
            TestContentObj,
            authors=[self.tony_sarpino, self.buddy_sarpino],
            published=timezone.datetime(
                day=random.randrange(1, 28), month=self.last_month, year=self.now.year
            ),
            _quantity=25
        )
        make_content(
            TestContentObj,
            authors=[self.tony_sarpino],
            published=timezone.datetime(
                day=random.randrange(1, 28), month=self.next_month, year=self.now.year
            ),
            _quantity=25
        )

        # Refresh the index.
        TestContentObj.search_objects.refresh()

    def test_get_contributors_default(self):
        report = EmailReport()
        contributors = report.get_contributors()
        self.assertEqual(contributors.count(), 1)

    def test_get_contributors_last_month(self):
        report = EmailReport(month=self.last_month)
        contributors = report.get_contributors()
        self.assertEqual(contributors.count(), 2)

    def test_get_contributor_contributions_default(self):
        report = EmailReport()
        contributions = report.get_contributions_by_contributor(self.tony_sarpino)
        self.assertEqual(contributions.count(), 25)

    def test_get_contributor_contributions_next_month(self):
        report = EmailReport(month=self.next_month)
        contributions = report.get_contributions_by_contributor(self.tony_sarpino)
        self.assertEqual(contributions.count(), 25)

    def test_email_body(self):
        report = EmailReport(month=self.next_month)
        body = report.get_email_body(self.tony_sarpino)
        self.assertTrue(body)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend')
    def test_email_api(self):
        with mock.patch("django.core.mail.EmailMultiAlternatives.send") as mock_send:
            mock_send.return_value = None
            data = {
                "deadline": self.now + timezone.timedelta(days=5),
                "start": timezone.datetime(day=1, month=self.last_month, year=self.now.year)
            }
            resp = self.api_client.post(self.endpoint, data=data)
            self.assertEqual(resp.status_code, 200)
            self.assertTrue(mock_send.called)
