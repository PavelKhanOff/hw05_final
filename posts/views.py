

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post

User = get_user_model()


def index(request):
    post_list = Post.objects.select_related('group')
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'index.html', {'page': page,
                                          'paginator': paginator})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.group_posts.all()
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
    if request.method == 'POST':
        if form.is_valid():
            post = form.instance
            post.author = request.user
            form.save()
            return redirect('index')
        return render(request, 'new_post.html', {'form': form})
    return render(request, 'new_post.html', {'form': form})


def profile(request, username):
    author = get_object_or_404(User, username=username)
    author_followers = author.follower.all().count()
    author_following = author.following.all().count()
    profile_posts = author.posts.all()
    profile_posts_count = profile_posts.count()
    paginator = Paginator(profile_posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    following = False
    if request.user.is_authenticated:
        following = Follow.objects.filter(user=request.user, author=author)
    context = {
        'author': author,
        'page': page,
        'post_count': profile_posts_count,
        'paginator': paginator,
        'following': following,
        'author_followers': author_followers,
        'author_following': author_following,
    }

    return render(request, 'profile.html', context)


def post_view(request, username, post_id):
    form = CommentForm()
    post = get_object_or_404(Post,
                             author__username=username,
                             pk=post_id)
    comments = Comment.objects.filter(post=post)
    post_author = post.author.posts.all()
    post_count = post_author.count()
    context = {
        'post': post,
        'post_count': post_count,
        'author': post.author,
        'post_id': post_id,
        'comments': comments,
        'form': form,
        'current_action': True
    }

    return render(request, 'post.html', context)


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    form = PostForm(request.POST or None, instance=post)
    if request.user == post.author:
        if request.method == 'POST':
            if form.is_valid():
                post = form.save()
                post.save()
                return redirect('post', username=username, post_id=post_id)
    else:
        return redirect('post', username=username, post_id=post_id)

    return render(request, 'new_post.html', {'form': form,
                                             'post': post,
                                             'update': True,
                                             })


@login_required
def add_comment(request, username, post_id):
    form = CommentForm(request.POST)
    if request.method == 'POST':
        if form.is_valid():
            comment = form.instance
            comment.author = request.user
            comment.post = Post.objects.get(id=post_id)
            form.save()
            return redirect(f'/{username}/{post_id}')
        return render(request, 'comments.html', {'form': form})
    else:
        form = CommentForm()
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
    user = request.user
    author = get_object_or_404(User, username=username)
    follow_check = Follow.objects.filter(author=author, user=user)
    if follow_check.exists() is False and author != user:
        Follow.objects.create(user=user, author=author)
    return redirect('profile', username=username)


@login_required
def profile_unfollow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=user, author=author).delete()
    return redirect('profile', username=username)
