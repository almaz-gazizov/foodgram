import base64

from django.core.files.base import ContentFile
from django.core.validators import MinValueValidator, MaxValueValidator
from rest_framework import serializers

from recipes.models import (
    Favorite, Ingredient, Recipe, RecipeIngredient, ShoppingCart, Tag
)
from users.models import CustomUser, Subscription

MIN_AMOUNT = 1
MAX_AMOUNT = 32000


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeMinifiedSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class CustomUserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CustomUser
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return user.subscribers.filter(author=obj).exists()


class SubscriptionSerializer(CustomUserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField(source='recipes.count')

    class Meta(CustomUserSerializer.Meta):
        fields = CustomUserSerializer.Meta.fields + (
            'recipes',
            'recipes_count'
        )

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes = obj.recipes.all()
        recipes_limit = request.query_params.get('recipes_limit')
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        return RecipeMinifiedSerializer(recipes, many=True).data


class SubscriptionCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Subscription
        fields = ('user', 'author')

    def validate(self, attrs):
        user = attrs['user']
        author = attrs['author']
        if user == author:
            raise serializers.ValidationError(
                'Нельзя подписаться на себя.'
            )
        if user.subscribers.filter(author=author).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого пользователя.'
            )
        return attrs

    def to_representation(self, instance):
        return SubscriptionSerializer(
            instance.author,
            context={'request': self.context.get('request')}
        ).data


class FavoriteCreateSerializer(serializers.Serializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')

    def validate(self, data):
        user = self.context['request'].user
        recipe = data['recipe']
        if self.context['request'].method == 'POST':
            if user.favorite_recipes.filter(recipe=recipe).exists():
                raise serializers.ValidationError(
                    'Рецепт есть в избранных.'
                )
        elif self.context['request'].method == 'DELETE':
            if not user.favorite_recipes.filter(recipe=recipe).exists():
                raise serializers.ValidationError(
                    'Рецепта нет в избранных.'
                )
        return data

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return Favorite.objects.create(**validated_data)

    def to_representation(self, instance):
        return RecipeMinifiedSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data


class ShoppingCartCreateSerializer(serializers.Serializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')

    def validate(self, attrs):
        user = self.context['request'].user
        recipe = attrs['recipe']
        if self.context['request'].method == 'POST':
            if user.shopping_carts.filter(recipe=recipe).exists():
                raise serializers.ValidationError(
                    'Рецепт находится в корзине.'
                )
        elif self.context['request'].method == 'DELETE':
            if user.shopping_carts.filter(recipe=recipe).exists():
                raise serializers.ValidationError('Рецепта нет в корзине.')
        return attrs

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return ShoppingCart.objects.create(**validated_data)

    def to_representation(self, instance):
        return RecipeMinifiedSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField(
        validators=[
            MinValueValidator(MIN_AMOUNT),
            MaxValueValidator(MAX_AMOUNT)
        ]
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    ingredients = RecipeIngredientSerializer(
        many=True, source='ingredient_list'
    )
    image = Base64ImageField()
    author = CustomUserSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        exclude = ('pub_date',)

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if not user.is_authenticated:
            return False
        return user.favorite_recipes.filter(recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if not user.is_authenticated:
            return False
        return user.shopping_carts.filter(recipe=obj).exists()


class RecipeCreateSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientCreateSerializer(many=True)
    image = Base64ImageField(use_url=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all(), required=True
    )
    author = CustomUserSerializer(
        read_only=True
    )
    cooking_time = serializers.IntegerField(
        validators=[
            MinValueValidator(MIN_AMOUNT),
            MaxValueValidator(MAX_AMOUNT)
        ]
    )

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'cooking_time', 'text',
            'author', 'tags', 'ingredients', 'image'
        )

    def to_representation(self, instance):
        return RecipeSerializer(
            instance,
            context={'request': self.context.get('request')}
        ).data

    def validate(self, attrs):
        tags = attrs.get('tags')
        ingredients = attrs.get('ingredients')
        if not tags:
            raise serializers.ValidationError(
                'Укажите теги рецепта.'
            )
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError(
                'Теги не должны повторяться.'
            )
        if not ingredients:
            raise serializers.ValidationError(
                'Должен быть хотя бы 1 ингредиент.'
            )
        unique_ing = {item['id'] for item in ingredients}
        if len(unique_ing) != len(ingredients):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться.'
            )
        return attrs

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        request = self.context.get('request')
        recipe = Recipe.objects.create(
            author=request.user,
            **validated_data
        )
        recipe.tags.set(tags)
        return self._add_ingredients(ingredients, recipe)

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        instance.tags.clear()
        instance.tags.set(tags)
        instance.ingredients.clear()
        super().update(instance, validated_data)
        return self._add_ingredients(ingredients, instance)

    @staticmethod
    def _add_ingredients(ingredients, recipe):
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient['id'],
                amount=ingredient['amount'],
            )
            for ingredient in ingredients
        )
        return recipe
