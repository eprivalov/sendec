from django import template
from django.utils.importlib import import_module
from django.contrib.auth.models import User
from news.models import News, NewsWatches, NewsPortal, NewsCategory, RssPortals, RssNewsCovers, Companies, \
    UserRssNewsReading, RssNews
from userprofile.models import UserSettings
from django.contrib.auth.models import User
from favourite.models import RssSaveNews

register = template.Library()


@register.filter(name="get_username")
def get_username(value):
    return User.objects.get(id=int(value)).username

@register.filter(name="get_news_title")
def get_news_title(value):
    return News.objects.get(id=int(value)).news_title


@register.filter(name="get_news_text")
def get_news_text(value):
    return News.objects.get(id=int(value)).news_post_text


@register.filter(name="get_news_date")
def get_news_date(value):
    return News.objects.get(id=int(value)).news_post_date


@register.filter(name="get_news_portal")
def get_news_portal(value):
    return NewsPortal.objects.get(id=News.objects.get(id=int(value)).news_portal_name_id).portal_name


@register.filter(name="get_news_category")
def get_news_category(value, get_id=False):
    if get_id == False:
        return NewsCategory.objects.get(id=News.objects.get(id=int(value)).news_category_id).category_name.lower()
    else:
        return News.objects.get(id=int(value)).news_category_id

@register.filter(name="check_reading_category")
def check_reading_category(value_cid, value_username):
    user_settings_categories = UserSettings.objects.get(user_id=User.objects.get(username=value_username).id).categories_to_show.split(",")
    if str(value_cid) in user_settings_categories:
        return True
    else:
        return False


@register.filter(name="get_article_author")
def get_article_author(value):
    first_name = User.objects.get(id=value).first_name
    second_name = User.objects.get(id=value).last_name
    if first_name and second_name:
        return first_name.capitalize()+" "+second_name.capitalize()
    else:
        return User.objects.get(id=value).username


@register.filter(name="get_portal_name")
def get_portal_name(value):
    return NewsPortal.objects.get(id=int(value)).portal_name


@register.filter(name="get_company_owner_name")
def get_company_owner_name(value):
    return Companies.objects.get(id=int(value)).verbose_name


@register.filter(name="get_rss_portal_name")
def get_rss_portal_name(value):
    return RssPortals.objects.get(id=int(value)).portal


@register.filter(name="get_rss_portal_favicon")
def get_rss_portal_favicon(value):
    return RssPortals.objects.get(id=int(value)).favicon

@register.filter(name="get_rss_verbose_name")
def get_rss_verbose_name(value):
    return RssPortals.objects.get(id=int(value)).verbose_name



@register.filter(name="get_user_photo")
def get_user_photo(value):
    return User.objects.get(id=int(value)).profile.user_photo


@register.filter(name="get_rss_news_cover")
def get_rss_news_cover(value):
    try:
        return RssNewsCovers.objects.get(rss_news_id=int(value)).main_cover
    except RssNewsCovers.DoesNotExist:
        return False



@register.filter(name="get_rss_news_title")
def get_rss_news_title(value):
    return RssNews.objects.get(id=int(value)).title


@register.filter(name="get_rss_news_date")
def get_rss_news_date(value):
    return RssNews.objects.get(id=int(value)).date_posted


@register.filter(name="get_portal_link")
def get_portal_link(value):
    return NewsPortal.objects.get(id=int(value)).portal_base_link


@register.filter(name="company_articles_amount")
def company_articles_amount(value):
    return News.objects.filter(news_company_owner_id=int(value)).count()


@register.filter(name="rss_articles_amount")
def rss_articles_amount(value):
    return RssNews.objects.filter(portal_name_id=int(value)).count()


@register.filter(name="devide")
def devide(value):
    if int(value) % 2 == 0:
        return True
    else:
        return False


@register.filter(name="count_watches")
def count_watches(value):
    try:
        return NewsWatches.objects.get(news_id=int(value)).watches
    except NewsWatches.DoesNotExist:
        return 0


@register.filter(name="check_format")
def check_format(value):
    if str(value).lower()[-4:] in ['.jpg', '.png', 'jpeg']:
        return True
    elif str(value).lower()[-4:] in ['.mp4']:
        return False


@register.filter(name="get_unread_news")
def get_unread_news(value, user):
    return UserRssNewsReading.objects.filter(user_id=user).filter(rss_portal_id=int(value)).filter(read=False).count()


@register.filter(name="check_read_rss")
def check_read_rss(value, user):
    return UserRssNewsReading.objects.get(rss_news_id=int(value), user_id=int(user)).read


@register.filter(name="get_cover_last_article")
def get_cover_last_article(value):
    rss_instance = RssNews.objects.filter(portal_name_id=int(value))[0]
    # rss_instance = RssNews.objects.get(id=157)
    return RssNewsCovers.objects.get(rss_news_id=rss_instance.id).main_cover


@register.filter(name="get_description")
def get_description(value):
    return RssPortals.objects.get(id=int(value)).description


@register.filter(name="divide")
def divide(value, arg):
    return (int(value) / int(arg)) if int(arg) != 0 else 0


@register.filter(name="get_news_cover")
def get_news_cover(value):
    return 1

@register.filter(name="check_saved_rss")
def check_saved_rss(value, user):
    if RssSaveNews.objects.filter(rss_id=int(value), user_id=user).exists():
        return True
    else:
        return False