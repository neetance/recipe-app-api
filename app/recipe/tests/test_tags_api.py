from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status # type: ignore
from rest_framework.test import APIClient # type: ignore

from core.models import Tag

from recipe.serializers import TagSerializer

TAGS_URL = reverse('recipe:tag-list')

def detail_url(tag_id):
    return reverse('recipe:tag-detail', args = [tag_id])

class PublicApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateApiTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email = 'test@example.com',
            password = 'testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        Tag.objects.create(user = self.user, name = 'vegan')
        Tag.objects.create(user = self.user, name = 'dessert')

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many = True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        user2 = get_user_model().objects.create_user(
            email = 'testmail@example.com',
            password = 'testpassbruh'
        )
        Tag.objects.create(user = user2, name = 'nonveg')
        tag = Tag.objects.create(user = self.user, name = 'thai')

        res = self.client.get(TAGS_URL)

        serializer = TagSerializer(tag)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data[0], serializer.data)

    def test_update_tag(self):
        tag = Tag.objects.create(user = self.user, name = 'after dinner')
        payload = {'name': 'dessert'}

        url = detail_url(tag.id)

        res = self.client.patch(url, payload)
        tag.refresh_from_db()

        self.assertEqual(tag.name, payload['name'])

    def test_delete_tag(self):
        tag = Tag.objects.create(user = self.user, name = 'breakfast')
        url = detail_url(tag.id)

        res = self.client.delete(url)
        tags = Tag.objects.filter(user = self.user)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(tags.exists())