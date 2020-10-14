import logging
import time, json

from communityparser.celery import app
from .models import PublicVK, UserProfileVk, VKParser

@app.task
def parse_vk():
    parser = VKParser("", '5.86')
    
    hot_keys_all = {
        'городские активисты': 'горожане,городские активисты,городской проект,активные горожане,события город',
        'антикафе, свободные пространства, коворкинги, кластеры':'антикафе,пространство,свободное пространство,лофт,кластер,арт кластер,коворкинг,тайм кафе,арт кафе,котокафе',
        'культурные и творческие проекты':"образовательный проект,культурный проект,творческое сообщество,сообщество художников",
        'образовательные проекты':'образовательный проект,лекторий,лекции,курсы,образование,вебинар,семинар',
        'мастера':"мастерская,художественная мастерская,handmade,хендмейд,ремесло,своими руками,авторский,ручной работы,рукоделие"
        }
    for hot_keys in hot_keys_all:
        for search_str in hot_keys_all[hot_keys].split(','):
            search = parser.group_search(search_str, city_id=104, count=1000)
            for group_id in json.loads(search)['response']['items']:
                group = parser.get_community_info(group_id['id'], fields='members_count,addresses,contacts,counters,description,links,site,trending')
                group = json.loads(group)
                
                try:
                    photos = group['response'][0]['counters']['photos']
                except KeyError:
                    photos = 0
                
                try:
                    albums = group['response'][0]['counters']['albums']
                except KeyError:
                    albums = 0
                
                try:
                    topics = group['response'][0]['counters']['topics']
                except KeyError:
                    topics = 0
                
                try:
                    videos = group['response'][0]['counters']['videos']
                except KeyError:
                    videos = 0
                
                try:
                    articles = group['response'][0]['counters']['articles']
                except KeyError:
                    articles = 0
                
                try:
                    market = group['response'][0]['counters']['market']
                except KeyError:
                    market = 0
                
                time.sleep(0.05)
                stats = parser.get_count_all_active_per_period_wall_community(-group_id['id'], period=604800)
                publ, public = PublicVK.objects.update_or_create(
                    public_id=group_id['id'], 
                    defaults={
                        'subscribers':group['response'][0]['members_count'], 
                        'category':hot_keys,
                        'photos':photos,
                        'albums':albums,
                        'topics':topics,
                        'videos':videos,
                        'articles':articles,
                        'market':market,
                        'posts_per_week':stats['posts'],
                        'wall_reposts_per_week':stats['wall_reposts'],
                        'likes_per_week':stats['likes'],
                        'comments_per_week':stats['comments'],
                        'views_per_week':stats['views'],
                        'users_reposts_per_week':stats['user_reposts'],
                        }
                    )
                publ.history.append({
                    time.time():
                        {
                        'subscribers':publ.subscribers, 
                        'category':publ.category,
                        'photos':publ.photos,
                        'albums':publ.albums,
                        'topics':publ.topics,
                        'videos':publ.videos,
                        'articles':publ.articles,
                        'market':publ.market,
                        'posts_per_week':publ.posts_per_week,
                        'wall_reposts_per_week':publ.wall_reposts_per_week,
                        'likes_per_week':publ.likes_per_week,
                        'comments_per_week':publ.comments_per_week,
                        'views_per_week':publ.views_per_week
                        }
                    })

                try:
                    contacts = group['response'][0]['contacts']
                except KeyError:
                    contacts = {}

                for contact in contacts:
                    user_id = contact.get('user_id', '')
                    if (user_id):
                        user = json.loads(parser.get_user_via_id(user_id))
                        name = user['response'][0]['first_name']
                        surname = user['response'][0]['last_name']
                    # todo create subqueries to get name and last_name via user id 
                    obj, created = UserProfileVk.objects.get_or_create(user_id=user_id,
                        defaults={
                        'name':name, 
                        'surname':surname, 
                        'phone':contact.get('phone', ''), 
                        'email':contact.get('email', ''),
                        },
                    )
                    obj.community_admin.add(publ)
                    time.sleep(0.3)
                time.sleep(0.03)
        time.sleep(3600)