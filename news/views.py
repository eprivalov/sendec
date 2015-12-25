# -*-coding: utf-8 -*-

from django.shortcuts import render_to_response, RequestContext
from django.template.context_processors import csrf
from django.contrib.auth.decorators import login_required
from django.contrib import auth
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import User
from django.db.models import Q
from .models import News, NewsCategory, Companies, TopVideoContent, RssNews, RssPortals, NewsComments, NewsWatches, NewsCommentsReplies, RssSaveNews, RssNewsCovers
import datetime
import json
from userprofile.models import UserLikesNews, UserSettings, UserProfile, UserRssPortals
from .forms import NewsCommentsForm, NewsCommentsRepliesForm
from django.core.mail import send_mail


def main_page_load(request, template="index_new.html", page_template="page_template.html", extra_context=None):
    args = {
        "video_top": TopVideoContent.objects.all().values()[:3],
        "current_year": datetime.datetime.now().year,
        "title": "Home Page | ",
        "news_block": True,
        "breaking_news": render_news_by_sendec(request).order_by("-news_post_date")[0],
        "total_middle_news": render_news_by_sendec(request).order_by("-news_post_date")[1:4],
        "interest": get_interesting_news(request)[:3],
        "total_news": get_total_news,
        "page_template": page_template,
    }
    if render_news_by_sendec(request).order_by("-news_post_date")[4:13].count() > 0:
        args["total_bottom_news"] = render_news_by_sendec(request).order_by("-news_post_date")[4:13]

    if request.is_ajax():
        template = page_template

    if request.COOKIES.get("announce"):
        args["hide"] = False
    else:
        args["hide"] = True
    args["beta_announce"] = """<h5>Currently version is only for <i>beta testing</i>. We have hidden/disabled some functions and blocks.
<br>Beta test continues <b>till 21.12.15 17:00 GMT(UTC) +0300</b>
<br>If you found any problems or just want to tell us something else, you can <a href="/about/contacts/">write</a> to us
<br>We hope that next version(the last pre-release) will have all functions and design solutions which we build.</h5>
"""
    args.update(csrf(request))
    if auth.get_user(request).username:
        args["username"] = User.objects.get(username=auth.get_user(request).username)

    return render_to_response([template, "footer.html"], context=args, context_instance=RequestContext(request))




def get_total_news():
    return News.objects.all().values()


def render_news_by_sendec(request, **kwargs):
    if len(kwargs) > 0:
        return News.objects.all().filter(news_category_id=kwargs["category_id"]).exclude(id=kwargs["news_id"]).values()
    else:
        return News.objects.all().values()


def get_company_news(request, news_id, company_id):
    current_company_news = News.objects.filter(news_company_owner=
                                               company_id).exclude(id=news_id).order_by("-news_post_date")
    return current_company_news


def get_latest_news_total(request):
    latest_10_news = News.objects.all().order_by("-news_post_date")
    return latest_10_news


def render_current_news(request, category_id, news_id):
    current_news = News.objects.get(id=news_id)
    args = {
        "title": "%s | " % current_news.news_title,
        "current_news_values": current_news,
        "other_materials": render_news_by_sendec(request, news_id=news_id,
                                                 category_id=category_id).exclude(id=news_id)[:12],
        "latest_news": get_company_news(request, news_id, current_news.news_company_owner_id)[:5],
        "company_name": str(Companies.objects.get(id=current_news.news_company_owner_id)).capitalize(),
        "current_day": datetime.datetime.now().day,
        "comments_total": comments_load(request, news_id),
        "replies_total": replies_load(request, news_id),
        "liked": check_like(request, news_id),
        "disliked": check_dislike(request, news_id),
        "like_amount": UserLikesNews.objects.filter(news_id=news_id).filter(like=True).count(),
        "dislike_amount": UserLikesNews.objects.filter(news_id=news_id).filter(dislike=True).count(),
        "current_news_title": current_news.news_title,
        "external_link": shared_news_link(request, news_id),
    }
    if auth.get_user(request).username:
        args["username"] = User.objects.get(username=auth.get_user(request).username)
    addition_news_watches(request, news_id)
    args.update(csrf(request))

    if request.COOKIES.get("announce"):
        args["hide"] = False
    else:
        args["hide"] = True
    args["beta_announce"] = """<h5>Currently version is only for <i>beta testing</i>. We have hidden/disabled some functions and blocks.
<br>Beta test continues <b>till 21.12.15 17:00 GMT(UTC) +0300</b>
<br>If you found any problems or just want to tell us something else, you can <a href="/about/contacts/">write</a> to us
<br>We hope that next version(the last pre-release) will have all functions and design solutions which we build.</h5>
"""
    return render_to_response("current_news.html", args)


@login_required(login_url="/auth/login/")
def render_user_news(request, template="user_news.html", rss_template="rss_template.html", extra_context=None):
    user = User.objects.get(username=auth.get_user(request).username)
    user_rss_list = UserRssPortals.objects.filter(user_id=user.id).filter(check=True).values("id")
    args = {
        "title": "My news | ",
        "test": set_rss_for_user_test(request),
        "user_rss": get_user_rss_news(request, user_id=user.id).order_by("position"),
        "popular_rss": get_most_popular_rss_portals(request)[:9],
        "popular_rss_right": get_most_popular_rss_portals(request)[:3],
        "test_2": RssNews.objects.filter(portal_name_id__in=user_rss_list).values(),
        "rss_template": rss_template,
        "un_us_p": get_user_unselceted_portals(request, user_id=user.id),
        "new_user_news": get_rss_filterd(request, user.id),
    }
    args.update(csrf(request))
    if auth.get_user(request).username:
        args["username"] = User.objects.get(username=auth.get_user(request).username)
    args["rss_news"] = set_rss_for_user_test(request)
    if request.is_ajax():
        template = rss_template
    if request.COOKIES.get("announce"):
        args["hide"] = False
    else:
        args["hide"] = True
    args["beta_announce"] = """<h5>Currently version is only for <i>beta testing</i>. We have hidden/disabled some functions and blocks.
<br>Beta test continues <b>till 21.12.15 17:00 GMT(UTC) +0300</b>
<br>If you found any problems or just want to tell us something else, you can <a href="/about/contacts/">write</a> to us
<br>We hope that next version(the last pre-release) will have all functions and design solutions which we build.</h5>
"""
    if len(get_user_rss_news(request, user_id=user.id)) == 0:
        args["zero"] = True
    else:
        args["zero"] = False
    return render_to_response(template, context=args, context_instance=RequestContext(request))


def get_rss_filterd(request, user_id):
    user_portals_ids = UserRssPortals.objects.filter(user_id=user_id).filter(check=True).values("id")
    return RssNews.objects.filter(portal_name_id__in=user_portals_ids).order_by("-date_posted").order_by("-portal_name__userrssportals__rate").values()
    #return user_portals_ids


def get_user_unselceted_portals(request, user_id):
    return UserRssPortals.objects.filter(user_id=user_id).filter(check=False).values()


def get_user_rss_portals(request, user_id):
    return UserRssPortals.objects.filter(user_id=user_id).filter(check=True).values()


def get_most_popular_rss_portals(request):
    return RssPortals.objects.all().order_by("follows").values()


def get_user_chosen_portals(request):
    return UserSettings.objects.get(user_id=
                                    User.objects.get(username=
                                                     auth.get_user(request).username).id).portals_to_show.split(",")


def get_rss_news_pagination(request, current_page, next_page):
    data_rss_news = [current_new.get_json_rss() for current_new in RssNews.objects.all()[current_page:next_page]]
    response_data = {
        "rss": data_rss_news,
    }
    return HttpResponse(json.dumps(response_data), content_type="application/json")


def get_current_rss_news(request, news_id):
    return HttpResponse(json.dumps({"rss_news": RssNews.objects.get(id=news_id).get_json_rss()}),
                        content_type="application/json")


def get_rss_news(request):
    return RssNews.objects.all().values()


def render_top_news_page(request):
    args = {
        "top_news": get_top_news(request),
    }
    if auth.get_user(request).username:
        args["username"] = User.objects.get(username=auth.get_user(request).username)
    args.update(csrf(request))

    if request.COOKIES.get("announce"):
        args["hide"] = False
    else:
        args["hide"] = True
    args["beta_announce"] = """<h5>Currently version is only for <i>beta testing</i>. We have hidden/disabled some functions and blocks.
<br>Beta test continues <b>till 21.12.15 17:00 GMT(UTC) +0300</b>
<br>If you found any problems or just want to tell us something else, you can <a href="/about/contacts/">write</a> to us
<br>We hope that next version(the last pre-release) will have all functions and design solutions which we build.</h5>
"""
    return render_to_response("top_news.html", args)


def get_user_news_by_portals(request):
    inst = UserSettings.objects.get(user_id=
                                    User.objects.get(username=
                                                     auth.get_user(request).username).id).portals_to_show.split(",")
    total_news_2 = list(News.objects.filter(Q(news_portal_name_id=inst[cur_id])).order_by("-news_post_date") for cur_id
                        in range(len(inst)-1))
    return total_news_2


def test(request):
    from itertools import chain
    from operator import attrgetter

    inst_portals = UserSettings.objects.get(user_id=User.objects.get(username=auth.get_user(request).username).id).portals_to_show.split(",")
    inst_categories = UserSettings.objects.get(user_id=User.objects.get(username=auth.get_user(request).username).id).categories_to_show.split(",")
    check = False
    test_new = sorted(
        chain(
            News.objects.filter(news_category_id=1),
            News.objects.filter(news_category_id=6 if check == True else 0),
        ),
        key=attrgetter("news_post_date"),
        reverse=True
    )
    return test_new


def check_like(request, news_id):
    if auth.get_user(request).is_authenticated():
        if UserLikesNews.objects.filter(user_id=User.objects.get(username=auth.get_user(request).username).id).filter(news_id=news_id).filter(like=True).exists():
            return True
        else:
            return False
    else:
        pass


def check_dislike(request, news_id):
    if auth.get_user(request).is_authenticated():
        if UserLikesNews.objects.filter(user_id=User.objects.get(username=auth.get_user(request).username).id).filter(news_id=news_id).filter(dislike=True).exists():
            return True
        else:
            return False
    else:
        pass


def update_latest_news(request):
    latest_new = News.objects.filter(news_latest_shown=False).order_by("-news_post_date")[0]
    string = """<span class='time' style='color: blue;'>%s</span>
<span class='title' onclick="location.href='/news/%s/%s/';">%s</span><br>""" \
             % (latest_new.news_post_date.time().strftime("%H:%M"), latest_new.news_category_id, latest_new.id,
                latest_new.news_title)

    response_data = {
        "latest_news": [cur_new.get_json_news() for cur_new in News.objects.all().all().order_by("-news_post_date")[:1]],
        "string": [string]
    }

    latest_10 = News.objects.filter(news_currently_showing=True).order_by("-news_post_date")[:10]
    latest_10[10].news_currently_showing = False
    latest_10[10].save()

    latest_new.news_currently_showing = True
    latest_new.news_latest_shown = True
    latest_new.save()
    return HttpResponse(json.dumps(response_data), content_type="application/json")


def set_shown(request, news_id):
    instance = News.objects.get(id=int(news_id))
    instance.news_latest_shown = True
    instance.save()
    return HttpResponse()


@login_required(login_url="/auth/login/")
def addition_news_watches(request, news_id):
    if NewsWatches.objects.filter(news_id=news_id).exists():
        instance = NewsWatches.objects.get(news_id=news_id)
        instance.watches += 1
        instance.save()
    else:
        NewsWatches.objects.create(
            news_id=news_id,
            watches=1,
        )
    return HttpResponse()


def get_top_news(request):
    top_list_id = NewsWatches.objects.all()[:10].values()
    top_news = [News.objects.get(id=int(cur_news_id["news_id"])) for cur_news_id in top_list_id]
    return top_news


def render_current_news_comments(request, news_id):
    news_comments = NewsComments.objects.filter(news_attached=int(news_id))
    news_replies = NewsCommentsReplies.objects.filter(news_attached=int(news_id))
    response_data = {
        "content_comments": [data_comments.get_json_comments() for data_comments in news_comments.all()],
        "content_replies": [data_replies.get_json_replies() for data_replies in news_replies.all()]
    }
    return HttpResponse(json.dumps(response_data), content_type="application/json")


def render_current_category(request, category_name):
    args = {
        "title": "Politics | ",
        "latest_news": get_latest_news_total(request),
        "category_title": category_name.capitalize(),
    }
    if auth.get_user(request).username:
        args["username"] = User.objects.get(username=auth.get_user(request).username)
    args.update(csrf(request))

    if request.COOKIES.get("announce"):
        args["hide"] = False
    else:
        args["hide"] = True
    args["beta_announce"] = """<h5>Currently version is only for <i>beta testing</i>. We have hidden/disabled some functions and blocks.
<br>Beta test continues <b>till 21.12.15 17:00 GMT(UTC) +0300</b>
<br>If you found any problems or just want to tell us something else, you can <a href="/about/contacts/">write</a> to us
<br>We hope that next version(the last pre-release) will have all functions and design solutions which we build.</h5>
"""
    return render_to_response("current_category.html", args)

#   ###########################################################################
#   ############################# CATEGORIES ##################################
#   ###########################################################################


def render_technology_news(request):
    args = {
        "title": "Technology | ",
        "top_technology": get_technology_news(request)[0],
        "technology_news": get_technology_news(request)[1:],
        "category_title": "TECHNOLOGY",
    }
    if auth.get_user(request).username:
        args["username"] = User.objects.get(username=auth.get_user(request).username)
    args.update(csrf(request))

    if request.COOKIES.get("announce"):
        args["hide"] = False
    else:
        args["hide"] = True
    args["beta_announce"] = """<h5>Currently version is only for <i>beta testing</i>. We have hidden/disabled some functions and blocks.
<br>Beta test continues <b>till 21.12.15 17:00 GMT(UTC) +0300</b>
<br>If you found any problems or just want to tell us something else, you can <a href="/about/contacts/">write</a> to us
<br>We hope that next version(the last pre-release) will have all functions and design solutions which we build.</h5>
"""
    return render_to_response("technology.html", args)


def get_technology_news(request):
    return News.objects.all().filter(news_category_id=NewsCategory.objects.get(category_name="Technology").id)
#   #########3#################### END TECHNOLOGY #######################################


def render_auto_news(request):
    args = {
        "title": "Auto | ",
        "top_auto_news": get_auto_news(request)[0],
        "auto_news": get_auto_news(request)[1:],
        "category_title": "AUTO",
    }
    if auth.get_user(request).username:
        args["username"] = User.objects.get(username=auth.get_user(request).username)
    args.update(csrf(request))

    if request.COOKIES.get("announce"):
        args["hide"] = False
    else:
        args["hide"] = True
    args["beta_announce"] = """<h5>Currently version is only for <i>beta testing</i>. We have hidden/disabled some functions and blocks.
<br>Beta test continues <b>till 21.12.15 17:00 GMT(UTC) +0300</b>
<br>If you found any problems or just want to tell us something else, you can <a href="/about/contacts/">write</a> to us
<br>We hope that next version(the last pre-release) will have all functions and design solutions which we build.</h5>
"""
    return render_to_response("auto.html", args)


def get_auto_news(request):
    return News.objects.all().filter(news_category_id=NewsCategory.objects.get(category_name="Auto").id)
#   ################################## END AUTO #########################################


def render_bit_news(request):
    args = {
        "title": "Bio Technology | ",
        "top_bit_news": get_bit_news(request)[0],
        "bit_news": get_bit_news(request)[1:],
        "category_title": "Bio Technology",
    }
    if auth.get_user(request).username:
        args["username"] = User.objects.get(username=auth.get_user(request).username)
    args.update(csrf(request))

    if request.COOKIES.get("announce"):
        args["hide"] = False
    else:
        args["hide"] = True
    args["beta_announce"] = """<h5>Currently version is only for <i>beta testing</i>. We have hidden/disabled some functions and blocks.
<br>Beta test continues <b>till 21.12.15 17:00 GMT(UTC) +0300</b>
<br>If you found any problems or just want to tell us something else, you can <a href="/about/contacts/">write</a> to us
<br>We hope that next version(the last pre-release) will have all functions and design solutions which we build.</h5>
"""
    return render_to_response("bit.html", args)


def get_bit_news(request):
    return News.objects.all().filter(news_category_id=NewsCategory.objects.get(category_name="BIO").id)
#   ################################## END BIO #########################################


def render_companies_news(request):
    args = {
        "title": "Companies | ",
        "companies": get_companies(request),
        "category_title": "COMPANIES",
    }
    if auth.get_user(request).username:
        args["username"] = User.objects.get(username=auth.get_user(request).username)
    args.update(csrf(request))

    if request.COOKIES.get("announce"):
        args["hide"] = False
    else:
        args["hide"] = True
    args["beta_announce"] = """<h5>Currently version is only for <i>beta testing</i>. We have hidden/disabled some functions and blocks.
<br>Beta test continues <b>till 21.12.15 17:00 GMT(UTC) +0300</b>
<br>If you found any problems or just want to tell us something else, you can <a href="/about/contacts/">write</a> to us
<br>We hope that next version(the last pre-release) will have all functions and design solutions which we build.</h5>
"""
    return render_to_response("companies.html", args)


def get_companies(request):
    return Companies.objects.all().order_by("id")


def render_current_company(request, company_name):
    company = Companies.objects.get(verbose_name=company_name)
    args = {
        "title": company.name+" |",
        "company": company,
        "news": get_companies_news(request, Companies.objects.get(verbose_name=company_name).id),
    }
    args.update(csrf(request))
    if auth.get_user(request).username:
        args["username"] = User.objects.get(username=auth.get_user(request).username)
    if request.COOKIES.get("announce"):
        args["hide"] = False
    else:
        args["hide"] = True
    args["beta_announce"] = """<h5>Currently version is only for <i>beta testing</i>. We have hidden/disabled some functions and blocks.
<br>Beta test continues <b>till 21.12.15 17:00 GMT(UTC) +0300</b>
<br>If you found any problems or just want to tell us something else, you can <a href="/about/contacts/">write</a> to us
<br>We hope that next version(the last pre-release) will have all functions and design solutions which we build.</h5>
"""
    return render_to_response("current_company.html", args)


def get_companies_news(request, company_id):
    return News.objects.filter(news_company_owner_id=company_id).order_by("-news_post_date").values()


#   #############################END COMPANIES###################################


def render_entertainment_news(request):
    args = {
        "title": "Entertainment | ",
        "top_entertainment_news": get_entertainment_news(request)[0],
        "entertainment_news": get_entertainment_news(request)[1:],
        "category_title": "ENTERTAINMENT",
    }
    if auth.get_user(request).username:
        args["username"] = User.objects.get(username=auth.get_user(request).username)
    args.update(csrf(request))

    if request.COOKIES.get("announce"):
        args["hide"] = False
    else:
        args["hide"] = True
    args["beta_announce"] = """<h5>Currently version is only for <i>beta testing</i>. We have hidden/disabled some functions and blocks.
<br>Beta test continues <b>till 21.12.15 17:00 GMT(UTC) +0300</b>
<br>If you found any problems or just want to tell us something else, you can <a href="/about/contacts/">write</a> to us
<br>We hope that next version(the last pre-release) will have all functions and design solutions which we build.</h5>
"""
    return render_to_response("entertainment.html", args)


def get_entertainment_news(request):
    return News.objects.all().filter(news_category_id=NewsCategory.objects.get(category_name="Entertainment").id)

#   ################## END ENTERTAINMENT ######################################3333


def render_latest_news(request):
    args = {
        "title": "Latest | ",
        "top_latest_news": get_latest_news_total(request)[0],
        "latest_news": get_latest_news_total(request)[1:10],
        "category_title": "LATEST",
    }
    if auth.get_user(request).username:
        args["username"] = User.objects.get(username=auth.get_user(request).username)
    args.update(csrf(request))

    if request.COOKIES.get("announce"):
        args["hide"] = False
    else:
        args["hide"] = True
    args["beta_announce"] = """<h5>Currently version is only for <i>beta testing</i>. We have hidden/disabled some functions and blocks.
<br>Beta test continues <b>till 21.12.15 17:00 GMT(UTC) +0300</b>
<br>If you found any problems or just want to tell us something else, you can <a href="/about/contacts/">write</a> to us.\
<br>We hope that next version(the last pre-release) will have all functions and design solutions which we build.</h5>
"""
    return render_to_response("latest.html", args)


def render_reviews_news(request):
    args = {
        "title": "Reviews | ",
        "latest_news": get_latest_news_total(request),
        "category_title": "REVIEWS",
    }
    if auth.get_user(request).username:
        args["username"] = User.objects.get(username=auth.get_user(request).username)
    args.update(csrf(request))

    if request.COOKIES.get("announce"):
        args["hide"] = False
    else:
        args["hide"] = True
    args["beta_announce"] = """<h5>Currently version is only for <i>beta testing</i>. We have hidden/disabled some functions and blocks.
<br>Beta test continues <b>till 21.12.15 17:00 GMT(UTC) +0300</b>
<br>If you found any problems or just want to tell us something else, you can <a href="/about/contacts/">write</a> to us
<br>We hope that next version(the last pre-release) will have all functions and design solutions which we build.</h5>
"""
    return render_to_response("reviews.html", args)


def render_space_news(request):
    args = {
        "title": "Space | ",
        "top_space_news": get_space_news(request)[0],
        "space_news": get_space_news(request)[1:],
        "category_title": "SPACE",
    }
    if auth.get_user(request).username:
        args["username"] = User.objects.get(username=auth.get_user(request).username)
    args.update(csrf(request))

    if request.COOKIES.get("announce"):
        args["hide"] = False
    else:
        args["hide"] = True
    args["beta_announce"] = """<h5>Currently version is only for <i>beta testing</i>. We have hidden/disabled some functions and blocks.
<br>Beta test continues <b>till 21.12.15 17:00 GMT(UTC) +0300</b>
<br>If you found any problems or just want to tell us something else, you can <a href="/about/contacts/">write</a> to us
<br>We hope that next version(the last pre-release) will have all functions and design solutions which we build.</h5>
"""
    return render_to_response("space.html", args)


def get_space_news(request):
    return News.objects.all().filter(news_category_id=NewsCategory.objects.get(category_name="Space").id)


#   ################################### END SPACE ##############################3


@login_required(login_url="/auth/login")
def comment_send(request, category_id, news_id):
    user_instance = User.objects.get(username=auth.get_user(request).username)
    args = {
        "username": user_instance,
    }
    args.update(csrf(request))
    if request.POST:
        form = NewsCommentsForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.news_attached = News.objects.get(id=news_id)
            comment.comments_author = user_instance
            form.save()
    return HttpResponseRedirect("/news/%s/%s/" % (category_id, news_id), args)


def comments_load(request, news_id):
    return NewsComments.objects.filter(news_attached=news_id).order_by("-comments_post_date").values()


@login_required(login_url="/auth/login/")
def reply_send(request, news_id, comment_id):
    user_instance = User.objects.get(username=auth.get_user(request).username)
    news_instance = News.objects.get(id=news_id)
    args = {
        "username": user_instance,
    }
    args.update(csrf(request))
    if request.POST:
        form = NewsCommentsRepliesForm(request.POST)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.comment_attached = NewsComments.objects.get(id=comment_id)
            reply.news_attached = news_instance
            reply.reply_author = user_instance
            form.save()
    return HttpResponseRedirect("/news/%s/%s/" % (news_instance.news_category_id, news_id), args)


def replies_load(request, news_id):
    return NewsCommentsReplies.objects.filter(news_attached=news_id).order_by("reply_post_date").values()


@login_required(login_url="/auth/login/")
def add_like_news(request, news_id):
    user_instance = User.objects.get(username=auth.get_user(request).username)
    if UserLikesNews.objects.filter(user_id=user_instance.id).filter(news_id=news_id).exists():
        user_like_instance = UserLikesNews.objects.filter(user_id=user_instance.id).get(news_id=news_id)
        user_like_instance.dislike = False
        user_like_instance.like = True
        user_like_instance.save()
    else:
        instance = News.objects.get(id=news_id)
        instance.news_likes += 1
        instance.save()
        UserLikesNews.objects.create(
            like=True,
            dislike=False,
            news_id=news_id,
            user_id=user_instance.id
        )
    return HttpResponse()


@login_required(login_url="/auth/login/")
def add_dislike_news(request, news_id):
    user_instance = User.objects.get(username=auth.get_user(request).username)
    if UserLikesNews.objects.filter(user_id=user_instance.id).filter(news_id=news_id).exists():
        user_dislike_instance = UserLikesNews.objects.filter(user_id=user_instance.id).get(news_id=news_id)
        user_dislike_instance.dislike = True
        user_dislike_instance.like = False
        user_dislike_instance.save()
    else:
        instance = News.objects.get(id=news_id)
        instance.news_likes += 1
        instance.save()
        UserLikesNews.objects.create(
            like=False,
            dislike=True,
            news_id=news_id,
            user_id=user_instance.id
        )
    return HttpResponse()


def check_like_amount(request, news_id):
    return HttpResponse(json.dumps({"likes": UserLikesNews.objects.filter(news_id=news_id).filter(like=True).count()}),
                        content_type="application/json")


def check_dislike_amount(request, news_id):
    return HttpResponse(json.dumps({"dislikes": UserLikesNews.objects.filter(news_id=news_id).filter(dislike=True).count()}),
                        content_type="application/json")


def delete_comment(request, comment_id):
    args = {}
    args.update(csrf(request))
    news_instance = News.objects.get(id=NewsComments.objects.get(id=int(comment_id)).news_attached_id)
    if User.objects.get(username=auth.get_user(request).username).is_staff:
        instance = NewsComments.objects.get(id=int(comment_id))
        instance.delete()
    else:
        pass
    return HttpResponseRedirect("/news/%s/%s/" % (news_instance.news_category_id, news_instance.id), args)


def delete_reply(request, reply_id):
    args = {}
    args.update(csrf(request))
    news_instance = News.objects.get(id=NewsCommentsReplies.objects.get(id=int(reply_id)).news_attached_id)
    if User.objects.get(username=auth.get_user(request).username).is_staff:
        instance = NewsCommentsReplies.objects.get(id=int(reply_id))
        instance.delete()
    else:
        pass
    return HttpResponseRedirect("/news/%s/%s/" % (news_instance.news_category_id, news_instance.id), args)


def shared_news_link(request, news_id):
    news = News.objects.get(id=news_id)
    shared_link = "http://127.0.0.1:8000/ext/trans/{0}/{1}/".format(news.news_category_id, news.id)
    return shared_link


def external_transition(request, cat_id, news_id):
    news_instance = NewsWatches.objects.get(news_id=news_id)
    news_instance.external_transition += 1
    news_instance.save()
    return HttpResponseRedirect("/news/%s/%s/" % (cat_id, news_id))


def get_user_rss_news(request, user_id):
    return UserRssPortals.objects.filter(user_id=user_id).filter(check=True).values()


def get_updated_user_rss(request):
    user = User.objects.get(username=auth.get_user(request).username)
    portals = UserRssPortals.objects.filter(user_id=user.id).filter(check=True)
    data = [portal.get_json_portal() for portal in portals.all()]
    response_data = {
        "portals": data,
    }
    return HttpResponse(json.dumps(response_data), content_type="application/json")


def get_updated_rss(request):
    user = User.objects.get(username=auth.get_user(request).username)
    portals_user_list = get_user_rss_news(request, user_id=user.id)
    total_news = RssNews.objects.filter(portal_name_id__in=(portals_user_list[i]["portal_id"] for i
                                                            in range(len(portals_user_list))))
    news = [news.get_json_rss() for news in total_news]
    response_data = {
        "updated_news": news,
    }
    return HttpResponse(json.dumps(response_data), content_type="application/json; charset=utf-8")


def set_rss_for_user_test(request):
    user = User.objects.get(username=auth.get_user(request).username)
    portals_user_list = get_user_rss_news(request, user_id=user.id)
    test_new = RssNews.objects.filter(portal_name_id__in=(portals_user_list[i]["portal_id"] for i
                                                          in range(len(portals_user_list)))).values()
    return test_new


def remove_rss_portal_from_feed(request, uuid, pid):
    args = {}
    args.update(csrf(request))
    user = User.objects.get(id=UserProfile.objects.get(uuid=uuid).user_id)
    user_rss_instance = UserRssPortals.objects.get(portal_id=pid, user_id=user.id)
    user_rss_instance.check = False
    user_rss_instance.save()

    rss_portal_instance = RssPortals.objects.get(id=int(pid))
    rss_portal_instance.follows -= 1
    rss_portal_instance.save()
    return render_to_response("user_news.html", args, context_instance=RequestContext(request))


def save_rss_news(request, rss_id):
    user = User.objects.get(username=auth.get_user(request).username)
    if not RssSaveNews.objects.filter(user_id=user.id).filter(news_id=rss_id).exists():
        RssSaveNews.objects.create(
            user_id=user.id,
            news_id=rss_id
        )
    else:
        pass
    return HttpResponse()


def get_interesting_news(request):
    interest_news = NewsWatches.objects.all().order_by("-watches").values("news_id")
    return News.objects.filter(id__in=interest_news).values()


def test_rendering(request):
    user = User.objects.get(username=auth.get_user(request).username)
    user_rss_list = UserRssPortals.objects.filter(user_id=user.id).filter(check=True).values("id")
    args = {
        "title": "My news | ",
        "test": set_rss_for_user_test(request),
        "user_rss": get_user_rss_news(request, user_id=user.id),
        "popular_rss": get_most_popular_rss_portals(request)[:9],
        "popular_rss_right": get_most_popular_rss_portals(request)[:3],
        "test_2": RssNews.objects.filter(portal_name_id__in=user_rss_list).values(),
    }
    args.update(csrf(request))
    if request.COOKIES.get("announce"):
        args["hide"] = False
    else:
        args["hide"] = True
    args["beta_announce"] = """<h5>Currently version is only for <i>beta testing</i>. We have hidden/disabled some functions and blocks.
<br>Beta test continues <b>till 21.12.15 17:00 GMT(UTC) +0300</b>
<br>If you found any problems or just want to tell us something else, you can <a href="/about/contacts/">write</a> to us
<br>We hope that next version(the last pre-release) will have all functions and design solutions which we build.</h5>
"""
    return render_to_response("test_rss_news.html", args, context_instance=RequestContext(request))


def render_contacts_page(request):
    from news.forms import SendReportForm
    args = {
        "title": "Contacts |",
        "email": "insydia@yandex.ru",
        "phone": "+7-931-579-06-96",
        "cooperation": "saqel@yandex.ru",
        "form": SendReportForm,
    }
    args.update(csrf(request))
    if auth.get_user(request).username:
        args["username"] = User.objects.get(username=auth.get_user(request).username)
    if request.COOKIES.get("announce"):
        args["hide"] = False
    else:
        args["hide"] = True
    args["beta_announce"] = """<h5>Currently version is only for <i>beta testing</i>. We have hidden/disabled some functions and blocks.
<br>Beta test continues <b>till 21.12.15 17:00 GMT(UTC) +0300</b>
<br>If you found any problems or just want to tell us something else, you can <a href="/about/contacts/">write</a> to us
<br>We hope that next version(the last pre-release) will have all functions and design solutions which we build.</h5>
"""

    args["expression"] = """We express our gratitude for the financial and moral support to Afanasyev M.J.
(Associate Professor of "Instrumentation Technology")."""

    return render_to_response("contacts.html", args)


def set_user_portals(request):
    args = {}
    args.update(csrf(request))
    user = User.objects.get(username=auth.get_user(request).username)
    if request.POST:
        portals_list = request.POST.getlist("portals[]")
        for i in portals_list:
            rss_instance = UserRssPortals.objects.get(user_id=user.id, portal_id=int(i))
            rss_instance.check = True
            rss_instance.save()
    return HttpResponseRedirect("/news/usernews/")


def change_rates(request):
    args = {}
    args.update(csrf(request))
    if request.POST:# or request.is_ajax():
        dataArray = request.POST.getlist("dataArray")
        print(dataArray)
        a = json.loads(dataArray[0])
        for i in range(len(a["dict"])):
            print("a")
            current_id = int(a["dict"]["%s"%i]["id"][5:])
            current_position = a["dict"]["%s"%i]["pos"]
            print(i, ": {")
            print("\tid: ", current_id)
            print("\tpos: ", current_position)
            print("}")
            instance = UserRssPortals.objects.get(id=current_id)
            prev_position = instance.position
            instance.position = current_position
            #instance.rate = 1 + (1 * (abs(prev_position-instance.position)/100))
            if abs(instance.position-prev_position) != 0:
                instance.rate = (1 * (((100/instance.position)/abs(instance.position-prev_position))/100)) * (prev_position/instance.position)
            else:
                instance.rate = (1 * (((100/instance.position)/100)) * (prev_position/instance.position))
            instance.save()
    return HttpResponseRedirect("/news/usernews/")


def send_report(request):
    mail_subject = "[REPORT] I have found error"

    import requests
    from django.conf import settings
    response = {}
    data = request.POST
    captcha_rs = data.get('g-recaptcha-response')
    url = "https://www.google.com/recaptcha/api/siteverify"
    params = {
        'secret': settings.NORECAPTCHA_SECRET_KEY,
        'response': captcha_rs,
        #'remoteip': get_client_ip(request)
    }
    verify_rs = requests.get(url, params=params, verify=True)
    verify_rs = verify_rs.json()
    response["status"] = verify_rs.get("success", False)
    response['message'] = verify_rs.get('error-codes', None) or "Unspecified error."

    if response["status"]:
        if request.POST:
            text_content = request.POST["message"] + "\nE-mail: "+request.POST["email"]+"\nName: "+request.POST["username"]
            mail_from = "insydia@yandex.ru"
            mail_to = "insydia@yandex.ru"
            send_mail(mail_subject, text_content, mail_from, [mail_to])

    return HttpResponseRedirect("/about/contacts/")


def page_not_found(request):
    response = render_to_response("404.html", context_instance=RequestContext(request))
    response.status_code = 404
    return response