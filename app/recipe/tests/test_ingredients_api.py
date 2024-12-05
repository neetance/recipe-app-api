from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status # type: ignore
from rest_framework.test import APIClient # type: ignore

from core.models import Ingredient

from recipe.serializers import IngredientSerializer

INGREDIENTS_URL = reverse('recipe:ingredient-list')

def detail_url(ingredient_id):
    return reverse('recipe:ingredient-detail', args = [ingredient_id])

class PublicIngredientsApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class PublicIngredientAPiTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email = 'test@example.com',
            password = 'testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients(self):
        Ingredient.objects.create(user = self.user, name = 'sample name 1')
        Ingredient.objects.create(user = self.user, name = 'sample name 2')

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many = True)

        self.assertEqual(res.data, serializer.data)

    def test_results_limited_to_user(self):
        user2 = get_user_model().objects.create_user(
            email = 'newuser@example.com',
            password = 'passw123'
        )

        Ingredient.objects.create(user = self.user, name = 'sample name 1')
        Ingredient.objects.create(user = user2, name = 'sample name 2')

        res = self.client.get(INGREDIENTS_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        ing1 = Ingredient.objects.filter(user = self.user)
        ing2 = Ingredient.objects.filter(user = user2)

        serializer1 = IngredientSerializer(ing1, many = True)
        serializer2 = IngredientSerializer(ing2, many = True)

        self.assertEqual(res.data, serializer1.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_update_ingredient(self):
        ingredient = Ingredient.objects.create(user = self.user, name = 'cilantro')
        payload = {'name': 'coriander'}

        url = detail_url(ingredient.id)

        res = self.client.patch(url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        ingredient.refresh_from_db()

        self.assertEqual(ingredient.name, payload['name'])

    def test_delete_ingredient(self):
        ingredient = Ingredient.objects.create(user = self.user, name = 'breakfast')
        url = detail_url(ingredient.id)

        res = self.client.delete(url)
        ingredients = Ingredient.objects.filter(user = self.user)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ingredients.exists())


