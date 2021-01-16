from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User


def index(request):
    post_list = Post.objects.select_related('group')
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'index.html', {'page': page,
                                          'paginator': paginator})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {
        'group': group,
        'page': page,
        'paginator': paginator,
    }
    return render(request, 'group.html', context)


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('index')
    return render(request, 'new_post.html', {'form': form})


def profile(request, username):
    author = get_object_or_404(User, username=username)
    profile_posts = author.posts.all()
    paginator = Paginator(profile_posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    following = False
    if request.user.is_authenticated:
        following = request.user.follower.filter(author=author).exists()
    context = {
        'author': author,
        'page': page,
        'paginator': paginator,
        'following': following,
    }

    return render(request, 'profile.html', context)


def post_view(request, username, post_id):
    form = CommentForm()
    post = get_object_or_404(Post,
                             author__username=username,
                             pk=post_id)
    comments = post.author.comments.all()
    context = {
        'post': post,
        'author': post.author,
        'comments': comments,
        'form': form,
    }

    return render(request, 'post.html', context)


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    if request.user != post.author:
        return redirect('post', username=username, post_id=post_id)
    form = PostForm(request.POST or None, instance=post)
    if form.is_valid():
        form.save()
        return redirect('post', username=username, post_id=post_id)
    return render(request, 'new_post.html', {'form': form,
                                             'post': post,
                                             })


@login_required
def add_comment(request, username, post_id):
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.instance
        comment.author = request.user
        comment.post = Post.objects.get(id=post_id)
        form.save()
        return redirect("post", username=username, post_id=post_id)
    return render(request, 'comments.html', {'form': form})


def page_not_found(request, exception):
    return render(request, "misc/404.html", {'path': request.path},
                  status=404)


def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request, 'follow.html',
        {
            'page': page,
            'paginator': paginator
        })


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    follow_check = Follow.objects.filter(author=author, user=request.user)
    if not follow_check.exists() and author != request.user:
        Follow.objects.create(user=request.user, author=author)
    return redirect('profile', username=username)

# Пытался сделать вот так сначала, но тесты не проходили
# @login_required
# def profile_unfollow(request, username):
#     get_object_or_404(Follow,
#                       user=request.user, author__username=username).delete()
#
#     return redirect('profile', username=username)


# Сделал вот так, по итогу все ок, вроде проверка происходит
@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follow_check = Follow.objects.filter(user=request.user, author=author)
    if follow_check:
        Follow.objects.filter(user=request.user, author=author).exists()
        follow_check.delete()
    return redirect('profile', username=username)
