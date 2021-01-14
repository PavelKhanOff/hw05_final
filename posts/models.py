from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models   .SlugField(max_length=20, unique=True, default='slug')
    description = models.TextField()

    def __str__(self):
        return self.title


class Post(models.Model):
    title = models.CharField(max_length=200, default='title_post')
    text = models.TextField(verbose_name='Твой лучший текст!',
                            help_text='Пиши без ошибок плз')
    pub_date = models.DateTimeField(verbose_name='date published',
                                    auto_now_add=True)
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='posts'
    )
    group = models.ForeignKey(
        Group, verbose_name='Группа!',
        help_text='Выбери группу!',
        on_delete=models.SET_NULL, blank=True,
        null=True, related_name='group_posts'
    )
    image = models.ImageField(upload_to='posts/', blank=True, null=True,
                              verbose_name='Изображение',
                              help_text='Добавьте изображение '
                                        'для своего поста!')

    class Meta:
        ordering = ['-pub_date']

    def __str__(self):
        return self.text[:15]


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE,
                             related_name='comment')
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='comment')
    text = models.TextField(verbose_name='Комментарий',
                            help_text='Напиши свой комментарий')
    created = models.DateTimeField(verbose_name='Comment date',
                                   auto_now_add=True)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return self.text


class Follow(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='follower')
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='following')
