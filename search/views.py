from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import auth
from django.contrib.auth.models import User
from django.template.context_processors import csrf
from django.shortcuts import render_to_response, render, HttpResponseRedirect
from django.db.models import Q


from news.models import NewsWatches, News

# Create your views here.

#@login_required(login_url="/auth/login/")
def render_search_page(request):
    args = {
        #"username": User.objects.get(username=auth.get_user(request).username),
        "latest_news": get_latest_news_total(request),
    }

    if "q" in request.GET and request.GET["q"]:
        search_word = request.GET["q"]
        if search_word is "":
            args["erorr_empty_field"] = True
        elif len(get_search_result_text(request,search_word)) < 1 and len(get_search_result_text(request, search_word)) < 1:
            args["empty_result"] = True
            args["popular_news"] = get_popular_news(request)
        else:
            args["results"] = get_search_result(request, search_word)
            args["matches_amount"] = get_matches_amount(request, search_word)

    args.update(csrf(request))
    return render_to_response("search.html", args)


def get_latest_news_total(request):
    from news.models import News
    latest_10_news = News.objects.all().order_by("-news_post_date")[:10]
    return latest_10_news


#@login_required(login_url="/auth/login/")
def get_search_result(request, search_word):
    from news.models import News
    return News.objects.filter(Q(news_title__contains=search_word) | Q(news_post_text__contains=search_word)).values()


#@login_required(login_url="/auth/login/")
def get_search_result_text(request, search_word):
    from news.models import News
    return News.objects.filter(news_post_text__contains=search_word).order_by("-news_post_date").values()

#@login_required(login_url="/auth/login/")
def get_matches_amount(request, search_word):
    from news.models import News
    return News.objects.filter(Q(news_title__contains=search_word) | Q(news_post_text__contains=search_word)).count()


def get_popular_news(request):
    popular_news_id_list = NewsWatches.objects.all().order_by("watches")[:10].values("news_id")
    news_list = []
    for i in popular_news_id_list:
        news_list.append(News.objects.get(id=int(i["news_id"])))
    return news_list