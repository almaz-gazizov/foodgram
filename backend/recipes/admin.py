from django.contrib import admin

from recipes.models import (
    Tag, Ingredient, Recipe, RecipeIngredient, ShoppingCart, Favorite
)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug')
    list_filter = ('name', 'color')
    search_fields = ('name',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ('measurement_unit',)
    search_fields = ('name',)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'pub_date', 'name', 'author',
        'text', 'image'
    )
    list_display_links = ('name',)
    list_filter = ('author', 'tags')
    search_fields = ('name', 'author')
    list_editable = ('author',)
    inlines = [RecipeIngredientInline]


@admin.register(ShoppingCart)
class ShoppingListAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    list_filter = ('user', 'recipe')
    list_display_links = ('user',)
    list_editable = ('recipe',)
    search_fields = ('user',)
    empty_value_display = 'Не задано'


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    list_filter = ('user', 'recipe')
    list_display_links = ('user',)
    list_editable = ('recipe',)
    search_fields = ('user',)
    empty_value_display = 'Не задано'
