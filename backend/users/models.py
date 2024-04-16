from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models

MAX_LEN_STR = 15
MAX_LEN_USER = 150


class CustomUser(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    email = models.EmailField(
        'Почта',
        unique=True,
    )
    username = models.CharField(
        'Пользователь',
        max_length=MAX_LEN_USER,
        unique=True,
        validators=[
            UnicodeUsernameValidator()
        ],
    )
    first_name = models.CharField('Имя', max_length=MAX_LEN_USER)
    last_name = models.CharField('Фамилия', max_length=MAX_LEN_USER)
    password = models.CharField(
        'Пароль',
        max_length=MAX_LEN_USER,
        blank=False,
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username[:MAX_LEN_STR]


class Subscription(models.Model):
    user = models.ForeignKey(
        CustomUser,
        verbose_name='Подписчик',
        on_delete=models.CASCADE,
        related_name='subscribers'
    )
    author = models.ForeignKey(
        CustomUser,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='author'
    )

    class Meta:
        verbose_name = 'Подписчик'
        verbose_name_plural = 'Подписчики'
        ordering = ('user',)
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'], name='unique_subscription'
            ),
        ]

    def __str__(self):
        return (
            f'{self.user[:MAX_LEN_STR]} подписан '
            f'на {self.author[:MAX_LEN_STR]}'
        )
