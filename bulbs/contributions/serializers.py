from collections import OrderedDict

from django.utils import timezone

from bulbs.content.models import Content
from bulbs.content.serializers import UserSerializer

from rest_framework import serializers

from .models import Contribution, ContributorRole, Rate, RATE_PAYMENT_TYPES, ROLE_PAYMENT_TYPES


class RolePaymentTypeField(serializers.Field):
    """
    payment type objects serialized to/from label/identifer
    """
    def to_representation(self, obj):
        if not isinstance(obj, int) and obj.isdigit():
            return dict(ROLE_PAYMENT_TYPES)[int(obj)]
        return dict(ROLE_PAYMENT_TYPES)[obj]

    def to_internal_value(self, data):
        if isinstance(data, int):
            return data
        return dict((label, value) for value, label in ROLE_PAYMENT_TYPES)[data]


class RatePaymentTypeField(serializers.Field):
    """
    rate object type serialized to/from label/identifier
    """
    def to_representation(self, obj):
        if not isinstance(obj, int) and obj.isdigit():
            return dict(ROLE_PAYMENT_TYPES)[int(obj)]
        return dict(ROLE_PAYMENT_TYPES)[obj]

    def to_internal_value(self, data):
        if isinstance(data, int):
            return data
        return dict((label, value) for value, label in RATE_PAYMENT_TYPES)[data]


class RateSerializer(serializers.ModelSerializer):

    name = RatePaymentTypeField()

    class Meta:
        model = Rate


class ContributorRoleSerializer(serializers.ModelSerializer):

    rates = RateSerializer(many=True, read_only=False)
    payment_type = RolePaymentTypeField()

    class Meta:
        model = ContributorRole
        # fields = ('id', 'name', 'description', 'payment_type', 'rates')


class ContributionListSerializer(serializers.ListSerializer):

    contributor = UserSerializer()

    def update(self, instance, validated_data):
        # Maps for id->instance and id->data item.
        contribution_mapping = {c.id: c for c in instance}
        data_mapping = {item['id']: item for item in validated_data if "id" in item}

        # Perform creations and updates.
        ret = []
        for data in validated_data:
            contribution = None
            if "id" in data:
                contribution = contribution_mapping.get(data["id"], None)

            if contribution is None:
                ret.append(self.child.create(data))
            else:
                ret.append(self.child.update(contribution, data))

        # Perform deletions.
        for contribution_id, contribution in contribution_mapping.items():
            if contribution_id not in data_mapping:
                contribution.delete()

        return ret


class ContributionSerializer(serializers.ModelSerializer):

    contributor = UserSerializer()
    rate = serializers.SerializerMethodField()
    content = serializers.PrimaryKeyRelatedField(queryset=Content.objects.all())

    class Meta:
        model = Contribution
        list_serializer_class = ContributionListSerializer

    def get_rate(self, obj):
        rate = obj.get_rate()
        if not rate:
            return None
        return {
            'id': rate.id,
            'name': rate.name,
            'rate': rate.rate,
        }        


class ContributionReportingSerializer(serializers.ModelSerializer):

    user = serializers.SerializerMethodField()
    content = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()

    class Meta:
        model = Contribution
        fields = ("id", "content", "user", "role", "notes")

    def get_content(self, obj):
        return OrderedDict([
            ("id", obj.content.id),
            ("title", obj.content.title),
            ("url", obj.content.get_absolute_url()),
            ("content_type", obj.content.__class__.__name__),
            ("feature_type", getattr(obj.content.feature_type, "name", None)),
            ("published", timezone.localtime(obj.content.published))
        ])

    def get_user(self, obj):
        return {
            "id": obj.contributor.id,
            "username": obj.contributor.username,
            "full_name": obj.contributor.get_full_name(),
        }

    def get_role(self, obj):
        return obj.role.name


class ContributorRoleField(serializers.Field):
    """This is fucking stupid, but it's basically a field that returns the the
    names of people who have contributed to this content under a certain role."""

    def __init__(self, role, *args, **kwargs):
        super(ContributorRoleField, self).__init__(*args, **kwargs)
        self.role = role
        self.source = "*"

    def to_representation(self, obj):
        qs = Contribution.objects.filter(content=obj, role=self.role).select_related("contributor")
        return ",".join([contribution.contributor.get_full_name() for contribution in qs])


class ContentReportingSerializer(serializers.ModelSerializer):

    content_type = serializers.SerializerMethodField()
    published = serializers.SerializerMethodField()
    feature_type = serializers.SerializerMethodField()
    url = serializers.URLField(source="get_absolute_url")
    authors = serializers.SerializerMethodField()

    class Meta:
        model = Content
        fields = ("id", "title", "url", "content_type", "feature_type", "published", "authors")

    def get_fields(self):

        fields = super(ContentReportingSerializer, self).get_fields()

        self._roles = {}
        for role in ContributorRole.objects.all():
            fields[role.name.lower()] = ContributorRoleField(role)

        return fields

    def get_contributors(self, obj, rolename):
        pass

    def get_content_type(self, obj):
        return obj.__class__.__name__

    def get_feature_type(self, obj):
        return getattr(obj.feature_type, "name", None)

    def get_published(self, obj):
        return timezone.localtime(obj.published)

    def get_authors(self, obj):
        return ",".join([author.get_full_name() for author in obj.authors.all()])
