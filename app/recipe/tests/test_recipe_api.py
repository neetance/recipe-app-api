from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status # type: ignore
from rest_framework.test import APIClient # type: ignore

from core.models import Recipe, Tag, Ingredient

from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPE_URL = reverse('recipe:recipe-list')

def detail_url(recipe_id):
    return reverse('recipe:recipe-detail', args = [recipe_id])

def create_recipe(user, **params):
    defaults = {
        'title': 'sample title',
        'time_minutes': 22,
        'price': Decimal('5.25'),
        'description': 'sample desc',
        'link': 'http://example.com/recipe.pdf'
    }
    defaults.update(params)

    recipe = Recipe.objects.create(user = user, **defaults)
    return recipe

class PublicRecipeApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(RECIPE_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateRecipeApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'test@example.com',
            'testpass123'
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        create_recipe(user = self.user)
        create_recipe(user = self.user)

        res = self.client.get(RECIPE_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many = True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_list_limited_to_user(self):
        other_user = get_user_model().objects.create_user(
            'other@example.com',
            'otherpass12'
        )

        create_recipe(user = other_user)
        create_recipe(user = self.user)

        res = self.client.get(RECIPE_URL)

        recipes = Recipe.objects.filter(user = self.user)
        serializer = RecipeSerializer(recipes, many = True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_recipe_detail(self):
        create_recipe(user = self.user, title = 't1')
        create_recipe(user = self.user, title = 't2')

        recipe = Recipe.objects.get(title = 't1')
        recipe_id = recipe.id

        res = self.client.get(detail_url(recipe_id = recipe_id))
        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(res.data, serializer.data)

    def test_create_recipe(self):
        payload = {
            'title': 'sample title',
            'time_minutes': 22,
            'price': Decimal('6.99')
        }

        res = self.client.post(RECIPE_URL, payload)

        recipe = Recipe.objects.get(id = res.data['id'])

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_partial_update(self):
        original_link = 'https://example.com/recipe.pdf'
        recipe = create_recipe(
            user = self.user,
            title = 'sample title',
            link = original_link
        )

        payload = {
            'title': 'new title'
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)

    def test_full_update(self):
        recipe = create_recipe(
            user = self.user,
            title = 'sample title',
            link = 'https://example.com/recipe.pdf',
            description = 'sample desc'
        )

        payload = {
            'title': 'new title',
            'link': 'https://example.com/new-recipe.pdf',
            'description': 'new desc',
            'time_minutes': 10,
            'price': Decimal('5.99')
        }

        url = detail_url(recipe.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()

        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        recipe = create_recipe(user = self.user)
        url = detail_url(recipe.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id = recipe.id).exists())

    def test_delete_other_users_recipe_fails(self):
        new_user = get_user_model().objects.create_user(
            email = 'newmail@example.com',
            password = 'newpass12'
        )
        recipe = create_recipe(user = new_user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id = recipe.id).exists())

    def test_recipe_created_with_new_tags(self):
        payload = {
            'title': 'sample name',
            'time_minutes': 30,
            'price': Decimal('7.99'),
            'tags': [
                {'name': 'thai'}, {'name': 'dessert'}
            ]
        }

        res = self.client.post(RECIPE_URL, payload, format = 'json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.filter(user = self.user)[0]

        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name = tag['name'],
                user = self.user
            ).exists()

            self.assertTrue(exists)

    def test_recipe_created_with_exisitng_tags(self):
        tag = Tag.objects.create(name = 'Indian', user = self.user)
        payload = {
            'title': 'pongal',
            'time_minutes': '35',
            'price': Decimal('4.50'),
            'tags': [
                {'name': 'Indian'}, {'name': 'breakfast'}
            ]
        }

        res = self.client.post(RECIPE_URL, payload, format = 'json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.filter(user = self.user)[0]
        # print(recipe.__dict__)
        # print(recipe.tags)

        self.assertIn(tag, recipe.tags.all())
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name = tag['name'],
                user = self.user
            ).exists()

            self.assertTrue(exists)

    def test_create_tag_on_update(self):
        recipe = create_recipe(user = self.user)
        payload = {
            'tags': [{'name': 'dinner'}]
        }

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format = 'json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag = Tag.objects.get(user = self.user, name = 'dinner')
        self.assertIn(tag, recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        tag_breakf = Tag.objects.create(user = self.user, name = 'breakfast')
        recipe = create_recipe(user = self.user)
        recipe.tags.add(tag_breakf)

        payload = {
            'tags': [{'name': 'lunch'}]
        }

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format = 'json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        tag = Tag.objects.get(user = self.user, name = 'lunch')
        self.assertIn(tag, recipe.tags.all())
        self.assertNotIn(tag_breakf, recipe.tags.all())

    def test_clear_tags_from_recipe(self):
        tag_breakf = Tag.objects.create(user = self.user, name = 'breakfast')
        recipe = create_recipe(user = self.user)
        recipe.tags.add(tag_breakf)

        payload = {
            'tags': []
        }

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format = 'json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)

    def test_recipe_created_with_new_ingredients(self):
        payload = {
            'title': 'cauliflower toast',
            'time_minutes': 40,
            'price': Decimal('7.25'),
            'ingredients': [{'name': 'cauliflower'}, {'name': 'salt'}]
        }

        res = self.client.post(RECIPE_URL, payload, format = 'json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        exist = Recipe.objects.filter(user = self.user, title = payload['title']).exists()
        #exist = recipe.exists()
        self.assertTrue(exist)

        recipe = Recipe.objects.get(title = payload['title'])
        for ingredient in payload['ingredients']:
            exists = recipe.ingredients.filter(
                name = ingredient['name'],
                user = self.user
            ).exists()
            self.assertTrue(exists)

    def test_recipe_created_with_existing_ingredients(self):
        ing = Ingredient.objects.create(user = self.user, name = 'lemon')
        payload = {
            'title': 'soup',
            'time_minutes': 25,
            'price': Decimal('2.99'),
            'ingredients': [{'name': 'lemon'}, {'name': 'fish sauce'}]
        }

        res = self.client.post(RECIPE_URL, payload, format = 'json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(title = payload['title'])
        self.assertEqual(recipe.ingredients.count(), 2)
        self.assertIn(ing, recipe.ingredients.all())

        for ingredient in payload['ingredients']:
            exists = recipe.ingredients.filter(
                user = self.user,
                name = ingredient['name']
            ).exists()

            self.assertTrue(exists)

    def test_create_ingredient_on_update(self):
        recipe = create_recipe(user = self.user)
        payload = {
            'ingredients': [{'name': 'chili'}]
        }

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format = 'json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ing = Ingredient.objects.get(user = self.user, name = payload['ingredients'][0]['name'])
        self.assertIn(ing, recipe.ingredients.all())

    def test_assign_ingredient_on_update(self):
        recipe = create_recipe(user = self.user)
        ing1 = Ingredient.objects.create(user = self.user, name = 'butter')
        recipe.ingredients.add(ing1)

        ing2 = Ingredient.objects.create(user = self.user, name = 'chili')
        payload = {
            'ingredients': [{'name': 'chili'}]
        }

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format = 'json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(ing2, recipe.ingredients.all())
        self.assertNotIn(ing1, recipe.ingredients.all())

    def test_clear_ingredients(self):
        recipe = create_recipe(user = self.user)
        ing1 = Ingredient.objects.create(user = self.user, name = 'butter')
        recipe.ingredients.add(ing1)

        payload = {
            'ingredients': []
        }

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format = 'json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(), 0)
