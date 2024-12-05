from rest_framework import serializers  # type: ignore

from core.models import Recipe, Tag, Ingredient


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ['id', 'name']
        read_only_fields = ['id']

class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, required=False)
    ingredients = IngredientSerializer(many=True, required=False)

    class Meta:
        model = Recipe
        fields = ['id', 'title', 'time_minutes', 'price', 'link', 'tags', 'ingredients']
        read_only_fields = ['id']

    def create(self, validated_data):
        # print(validated_data)
        tags = validated_data.pop('tags', [])
        ings = validated_data.pop('ingredients', [])
        # print(validated_data)
        recipe = Recipe.objects.create(**validated_data)
        auth_user = self.context['request'].user

        for tag in tags:
            tag_obj, created = Tag.objects.get_or_create(
                user=auth_user,
                **tag
            )
            recipe.tags.add(tag_obj)

        for ing in ings:
            ing_obj, created = Ingredient.objects.get_or_create(
                user=auth_user,
                **ing
            )
            recipe.ingredients.add(ing_obj)

        return recipe

    def update(self, instance, validated_data):
        # print(instance)
        # print(validated_data)
        tags = validated_data.pop('tags', [])
        ingredients = validated_data.pop('ingredients', [])

        instance.ingredients.clear()
        instance.tags.clear()

        auth_user = self.context['request'].user

        recipe = super().update(instance, validated_data)

        for tag in tags:
            tag_obj, created = Tag.objects.get_or_create(
                user=auth_user,
                **tag
            )
            recipe.tags.add(tag_obj)

        for ingredient in ingredients:
            ing_obj, created = Ingredient.objects.get_or_create(
                user=auth_user,
                **ingredient
            )
            recipe.ingredients.add(ing_obj)

        return recipe


class RecipeDetailSerializer(RecipeSerializer):
    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ['description']
