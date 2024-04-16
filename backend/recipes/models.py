from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator

from users.models import CustomUser

MAX_LEN_STR = 20
MAX_LEN_COLOR = 7
MIN_COOKING_TIME = AMOUNT_MIN_VALUE = 1
MAX_COOKING_TIME = AMOUNT_MAХ_VALUE = 32000
MAX_LEN_RECIPE_TEXT = 2000
(
    MAX_LEN_TAG_NAME,
    MAX_LEN_TAG_SLUG,
    MAX_LEN_INGREGIENT,
    MAX_LEN_UNIT,
    MAX_LEN_RECIPE_NAME
) = [200 for _ in range(5)]


class Tag(models.Model):
    name = models.CharField(
        'Название',
        max_length=MAX_LEN_TAG_NAME,
        unique=True
    )
    color = models.CharField(
        'Цвет',
        unique=True,
        max_length=MAX_LEN_COLOR
    )
    slug = models.SlugField(
        'Слаг',
        max_length=MAX_LEN_TAG_SLUG,
        unique=True
    )

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'
        ordering = ('id',)

    def __str__(self):
        return self.name[:MAX_LEN_STR]


class Ingredient(models.Model):
    name = models.CharField(
        'Название ингредиента',
        max_length=MAX_LEN_INGREGIENT
    )
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=MAX_LEN_UNIT
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('id',)
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'], name='unique_ingredient'
            ),
        ]

    def __str__(self):
        return (
            f'{self.name[:MAX_LEN_STR]}, '
            f'{self.measurement_unit[:MAX_LEN_STR]}'
        )


class Recipe(models.Model):
    author = models.ForeignKey(
        CustomUser,
        verbose_name='Автор рецепта',
        on_delete=models.CASCADE,
        related_name='recipes'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Список игредиентов',
        through='RecipeIngredient',
        related_name='recipes'
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Тэги',
        related_name='recipes'
    )
    image = models.ImageField(
        'Изображение',
        upload_to='recipes/'
    )
    name = models.CharField(
        'Название',
        max_length=MAX_LEN_RECIPE_NAME
    )
    text = models.CharField(
        'Описание',
        max_length=MAX_LEN_RECIPE_TEXT
    )
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления (мин)',
        validators=[
            MinValueValidator(MIN_COOKING_TIME),
            MaxValueValidator(MAX_COOKING_TIME),
        ],
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.name[:MAX_LEN_STR]


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=models.CASCADE,
        related_name='ingredient_list'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        verbose_name='Ингредиент',
        on_delete=models.CASCADE,
        related_name='ingredient'
    )
    amount = models.PositiveSmallIntegerField(
        'Количество',
        validators=[
            MinValueValidator(AMOUNT_MIN_VALUE),
            MaxValueValidator(AMOUNT_MAХ_VALUE),
        ],
    )

    class Meta:
        verbose_name = 'Ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецепта'
        ordering = ('id',)

    def __str__(self):
        return f'{self.ingredient}: {self.amount}'


class ShoppingFavoriteModel(models.Model):
    user = models.ForeignKey(
        CustomUser,
        verbose_name='Пользователь',
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=models.CASCADE
    )

    class Meta:
        abstract = True
        ordering = ('id',)
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_user_recipe'
            )
        ]


class ShoppingCart(ShoppingFavoriteModel):

    class Meta:
        verbose_name = 'Корзина покупок'
        verbose_name_plural = 'Корзины покупок'
        default_related_name = 'shopping_carts'

    def __str__(self):
        return (
            f'{self.user[:MAX_LEN_STR]}: '
            f'{self.recipe[:MAX_LEN_STR]}'
        )


class Favorite(ShoppingFavoriteModel):

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'
        default_related_name = 'favorite_recipes'

    def __str__(self):
        return (
            f'{self.user[:MAX_LEN_STR]}: '
            f'{self.recipe[:MAX_LEN_STR]}'
        )
