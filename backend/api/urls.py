from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (
    CustomUserViewSet, IngredientViewSet,
    RecipeViewSet, TagViewSet
)

router = DefaultRouter()
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('users', CustomUserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
    path('auth/', include('djoser.urls')),
]
