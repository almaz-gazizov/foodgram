from django_filters.rest_framework import CharFilter, FilterSet
from django_filters.rest_framework import filters as djangofilters

from recipes.models import Ingredient, Recipe, Tag


class IngredientFilter(FilterSet):
    name = CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name', )


class RecipeFilter(FilterSet):
    tags = djangofilters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        field_name='tags__slug',
        to_field_name='slug')
    is_favorited = djangofilters.NumberFilter(
        method='get_favorite_recipes'
    )
    is_in_shopping_cart = djangofilters.NumberFilter(
        method='get_is_in_shopping_cart'
    )

    def get_favorite_recipes(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(
                favorite_recipes__user=self.request.user
            )
        return queryset

    def get_is_in_shopping_cart(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(
                shopping_carts__user=self.request.user
            )
        return queryset

    class Meta:
        model = Recipe
        fields = (
            'tags',
            'author',
            'is_favorited',
            'is_in_shopping_cart'
        )
