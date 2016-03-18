import logging
import pytz
import requests

from django.conf import settings
from django.db import models

from djbetty import ImageField

from bulbs.utils import vault

from .managers import PollManager
import sodahead

logger = logging.getLogger(__name__)


class PollMixin(models.Model):
    """Give a child object all Poll related fields and logic."""
    question_text = models.TextField(blank=True, default="")
    sodahead_id = models.CharField(max_length=20, blank=True, default="")
    last_answer_index = models.IntegerField(default=0)
    end_date = models.DateTimeField(null=True, default=None)
    poll_image = ImageField(null=True, blank=True)
    answer_type = models.TextField(blank=True, default="text")

    search_objects = PollManager()

    class Meta:
        abstract = True

    def get_sodahead_data(self):
        response = requests.get(sodahead.SODAHEAD_POLL_ENDPOINT.format(self.sodahead_id))

        if not response.ok:
            logger.error(
                'Poll(id: %s, sodahead_id: %s).get_sodahead_data status_code: %s error: %s',
                self.id,
                self.sodahead_id,
                response.text,
                response.status_code,
            )
            return {
                'poll': {
                    'totalVotes': 0,
                    'answers': [],
                },
            }
        else:
            return response.json()

    def get_sodahead_token(self):
        return vault.read(settings.SODAHEAD_TOKEN_VAULT_PATH)['value']

    def sodahead_payload(self):
        payload = {
            'access_token': self.get_sodahead_token(),
            'name': self.title,
            'title': self.question_text,
        }

        if self.sodahead_id:
            payload['id'] = self.sodahead_id

        if self.published:
            activation_date = self.published.astimezone(pytz.utc)
            payload['activationDate'] = activation_date.strftime(sodahead.SODAHEAD_DATE_FORMAT)
        else:
            payload['activationDate'] = None

        if self.end_date:
            end_date = self.end_date.astimezone(pytz.utc)
            payload['endDate'] = end_date.strftime(sodahead.SODAHEAD_DATE_FORMAT)
        else:
            payload['endDate'] = ''

        for answer in self.answers.all():
            if answer.answer_text and answer.answer_text is not u'':
                payload[answer.sodahead_answer_id] = answer.answer_text
            else:
                payload[answer.sodahead_answer_id] = sodahead.BLANK_ANSWER

        if 'answer_01' not in payload:
            payload['answer_01'] = sodahead.DEFAULT_ANSWER_1

        if 'answer_02' not in payload:
            payload['answer_02'] = sodahead.DEFAULT_ANSWER_2

        return payload

    def save(self, *args, **kwargs):
        if not self.sodahead_id:
            response = requests.post(sodahead.SODAHEAD_POLLS_ENDPOINT, self.sodahead_payload())

            if response.ok:
                self.sodahead_id = response.json()['poll']['id']
            elif response.status_code > 499:
                raise sodahead.SodaheadResponseError(response.text)
            else:
                raise sodahead.SodaheadResponseFailure(response.text)
        else:
            self.sync_sodahead()

        super(PollMixin, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        response = requests.delete(
            sodahead.SODAHEAD_DELETE_POLL_ENDPOINT.format(
                self.sodahead_id,
                self.get_sodahead_token(),
            )
        )
        if response.status_code > 499:
            raise sodahead.SodaheadResponseError(response.text)
        elif response.status_code > 399:
            raise sodahead.SodaheadResponseFailure(response.text)
        super(PollMixin, self).delete(*args, **kwargs)

    def sync_sodahead(self):
        response = requests.post(
            sodahead.SODAHEAD_POLL_ENDPOINT.format(self.sodahead_id),
            self.sodahead_payload()
        )

        if response.status_code > 499:
            raise sodahead.SodaheadResponseError(response.json())
        elif response.status_code > 399:
            raise sodahead.SodaheadResponseFailure(response.json())
