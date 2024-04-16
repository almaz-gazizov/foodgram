from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response

from api.filters import IngredientFilter, RecipeFilter
from api.paginators import CustomPagination
from api.permissions import IsAuthorAdminOrReadOnly
from api.serializers import (
    CustomUserSerializer, FavoriteCreateSerializer,
    IngredientSerializer, RecipeCreateSerializer,
    RecipeSerializer, ShoppingCartCreateSerializer,
    SubscriptionCreateSerializer, SubscriptionSerializer, TagSerializer
)
from recipes.models import (
    Ingredient, Recipe, RecipeIngredient, Tag
)
from users.models import CustomUser


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    search_fields = ('^name',)
    pagination_class = None


class CustomUserViewSet(UserViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [AllowAny]
    pagination_class = CustomPagination

    def get_permissions(self):
        if self.action == 'me':
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=[IsAuthenticated],
        pagination_class=CustomPagination
    )
    def subscriptions(self, request):
        # queryset = request.user.author.all() Не может отобразить на сайте(
        queryset = CustomUser.objects.filter(author__user=self.request.user)
        pages = self.paginate_queryset(queryset)
        serializer = SubscriptionSerializer(
            pages, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, id):
        author = get_object_or_404(CustomUser, pk=id)

        if request.method == 'POST':
            serializer = SubscriptionCreateSerializer(
                data={'user': request.user.id, 'author': author.id},
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            delete_subscription, _ = (
                request.user.subscribers.filter(author=author).delete()
            )
            if not delete_subscription:
                return Response(
                    'Нет подписки.',
                    status=status.HTTP_400_BAD_REQUEST)
            return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthorAdminOrReadOnly]
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeSerializer
        return RecipeCreateSerializer

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk):
        if request.method == 'POST':
            serializer = FavoriteCreateSerializer(
                data={'user': request.user.id, 'recipe': pk},
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            recipe = get_object_or_404(Recipe, id=pk)
            user = request.user
            delete_favorite = user.favorite_recipes.filter(recipe=recipe)
            if not delete_favorite.exists():
                return Response(
                    'Нет избранного.',
                    status=status.HTTP_400_BAD_REQUEST
                )
            delete_favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk):
        if request.method == 'POST':
            user = request.user
            serializer = ShoppingCartCreateSerializer(
                data={'user': user.id, 'recipe': pk},
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            recipe = get_object_or_404(Recipe, id=pk)
            user = request.user
            delete_shopping_cart = user.shopping_carts.filter(recipe=recipe)
            if not delete_shopping_cart.exists():
                return Response(
                    'Нет покупок.',
                    status=status.HTTP_400_BAD_REQUEST
                )
            delete_shopping_cart.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @staticmethod
    def ingredients_txt(ingredients):
        shopping_list = ''
        for ingredient in ingredients:
            shopping_list += (
                f'{ingredient["ingredient__name"]}  - '
                f'{ingredient["sum"]}'
                f'({ingredient["ingredient__measurement_unit"]})\n'
            )
        return shopping_list

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_carts__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(sum=Sum('amount'))
        shopping_list = self.ingredients_txt(ingredients)
        return HttpResponse(shopping_list, content_type='text/plain')
