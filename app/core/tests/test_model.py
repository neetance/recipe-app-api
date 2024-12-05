from django.contrib.auth import get_user_model
from django.test import TestCase

from unittest.mock import patch

from decimal import Decimal
from core import models

class ModelTest(TestCase):
    def test_user_with_email_created_successful(self):
        email = 'test@example.com'
        password = 'testpass123'
        user = get_user_model().objects.create_user(
            email = email,
            password = password
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_with_email_normalized(self):
        sample_emails = [
            ('TEST1@example.com', 'TEST1@example.com'),
            ('test2@Example.com', 'test2@example.com'),
            ('Test3@EXAMPLE.COM', 'Test3@example.com'),
            ('test4@example.COM', 'test4@example.com')
        ]

        for (email, expected) in sample_emails:
            user = get_user_model().objects.create_user(email, 'sample123')
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_raises_error(self):
        with self.assertRaises(ValueError):
            user = get_user_model().objects.create_user('', 'sample123')

    def test_create_superuser(self):
        user = get_user_model().objects.create_superuser(
            email = 'test123@example.com',
            password = 'sample123'
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_recipe(self):
        user = get_user_model().objects.create_user(
            'test@example.com',
            'testpass123'
        )

        recipe = models.Recipe.objects.create(
            user = user,
            title = 'sample title',
            time_minutes = 5,
            price = Decimal('5.50'),
            description = 'sample desc'
        )

        self.assertEqual(str(recipe), recipe.title)

    def test_create_tag(self):
        user = get_user_model().objects.create_user(
            email = 'test@example.com',
            password = 'testpass123'
        )

        tag = models.Tag.objects.create(
            user = user,
            name = 'test_tag'
        )

        self.assertEqual(str(tag), tag.name)

    @patch('core.models.uuid.uuid4')
    def test_recipe_file_name_uuid(self, mock_uuid):
        uuid = 'test_uuid'
        mock_uuid.return_value = uuid
        file_path = models.recipe_image_file_path(None, 'example.jpg')

        self.assertEqual(file_path, f'uploads/recipe/{uuid}.jpg')
