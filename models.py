from django.db import models

import requests
import json
import datetime

class PublicVK(models.Model):
    public_id = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    subscribers = models.IntegerField(default=0)
    posts_per_week = models.IntegerField(default=0)
    likes_per_week = models.IntegerField(default=0)
    comments_per_week = models.IntegerField(default=0)
    views_per_week = models.IntegerField(default=0)
    wall_reposts_per_week = models.IntegerField(default=0)
    users_reposts_per_week = models.IntegerField(default=0)
    photos = models.IntegerField(default=0)
    albums = models.IntegerField(default=0)
    topics = models.IntegerField(default=0)
    videos = models.IntegerField(default=0)
    market = models.IntegerField(default=0)
    articles = models.IntegerField(default=0)
    history = models.JSONField(default=dir)
    category = models.CharField(max_length=100, default='')
    def __str__(self):
        return self.public_id



class UserProfileVk(models.Model):

    user_id = models.CharField(max_length=20)
    phone = models.CharField(max_length=20, blank=True)
    email = models.CharField(max_length=70, blank=True)
    name = models.CharField(max_length=35, blank=True)
    surname = models.CharField(max_length=40, blank=True)
    community_admin = models.ManyToManyField(PublicVK)

    def __str__(self):
        return self.user_id

    class Meta:
        db_table = ''
        managed = True
        verbose_name = 'UserProfileVk'
        verbose_name_plural = 'UserProfileVks'



class VKParser():
    last_response = {}
    last_url = ''
    def __init__(self, access_token, version):
        self.access_token = access_token
        self.version = version

    #timestamp_from, timestamp_to, interval, intervals_count, filters, stats_groups, extended, v
    def get_stats_group(self, group_id, params):
        if(str(group_id)[0] != '-'):
            raise IOError("id для сообществ должен содержать "-" в начале")
        params = {
            "group_id": group_id,
            "timestamp_from": params.get("timestamp_from", ''),
            "timestamp_to": params.get("timestamp_to",''),
            "v":self.version,
            "access_token":self.access_token
        }
        response = requests.get('https://api.vk.com/method/stats.get?', params=params)
        self.last_response.clear()
        self.last_response = json.loads(response.text)
        if "error" in response.text: 
            return False
        else:
            return response.text

    #
    #owner_id (for community -id), domain, offset, count, filter, extended, fields
    #После успешного выполнения возвращает объект, содержащий число результатов в поле count и массив объектов записей на стене в поле items.
    #Если был задан параметр extended=1, возвращает число результатов в поле count, отдельно массив объектов записей на стене в поле items, пользователей в поле profiles и сообществ в поле groups.
    #
    def get_post_from_wall_community(self, group_id, params):
        if(str(group_id)[0] != '-'):
            raise IOError("id для сообществ должен содержать "-" в начале")
        params = {
            "owner_id": group_id,
            "domain":params.get("domain", ''),
            "offset":params.get("offset", '1'),
            "count":params.get("count", 20),
            "filter":params.get("filter", ''),
            "extended":params.get("extended", 1),
            "fields":params.get("fields", ''),
            "v":self.version,
            "access_token":self.access_token
        }
        response = requests.get('https://api.vk.com/method/wall.get?', params=params)
        self.last_response.clear()
        self.last_response = json.loads(response.text)
        if "error" in response.text: 
            print(response.text)
            return False
        else:
            return response.text

    #
    #period - timestamp 
    #return count post per last period
    #
    def get_count_all_post_per_period_wall_community(self, group_id, period=86400, new_request=True):
        if(new_request):
            result = json.loads(self.get_post_from_wall_community(group_id, {}))
        else:
            result = self.last_response
        count = 0
        for item in result['response']['items']:
            if(datetime.datetime.now().timestamp() - period > item['date']):
                break
            count += 1
        return count

    

    def get_count_all_active_per_period_wall_community(self, group_id, period=86400, new_request=True):
        stats = {'posts':0, 'wall_reposts':0, 'likes':0, 'comments': 0, 'user_reposts':0, 'views':0}
        
        if(new_request):
            if(self.get_post_from_wall_community(group_id, {'count':30})):
                return stats
            else:
                return stats
            
        else:
            result = self.last_response
        
        for item in result['response']['items']:
            if(datetime.datetime.now().timestamp() - period > item['date']):
                break
            
            if(item.get('copy_history', 0)):
                stats['wall_reposts'] += 1
            else:
                stats['posts'] += 1
            
            stats['comments'] = item['comments']['count']
            stats['likes'] = item['likes']['count']
            stats['user_reposts'] = item['reposts']['count']
            try:
                stats['views'] = item['views']['count']        
            except KeyError:
                pass
        print(group_id)    
        return stats

    #
    #group_ids string max 500 ids, divide by comma ','
    #
    def get_community_info(self, group_ids, fields=''):
        params = {
            "group_ids": group_ids,
            "fields":fields,
            "v":self.version,
            "access_token":self.access_token
        }
        response = requests.get('https://api.vk.com/method/groups.getById?', params=params)
        self.last_response.clear()
        self.last_response = json.loads(response.text)
        self.last_url = response.url
        if "error" in response.text: 
            return False
        else:
            return response.text

    
   
    #
    #
    #I don't know what is the tag
    #
    def get_group_tags(self, group_id):
        params = {
            "group_id": group_id,
            "v":self.version,
            "access_token":self.access_token
        }
        response = requests.get('https://api.vk.com/method/groups.getTagList?', params=params)
        self.last_response.clear()
        self.last_response = json.loads(response.text)
        if "error" in response.text: 
            return False
        else:
            return response.text

    def group_search(self, q, type="", country_id = '', city_id = '', future = '', market = '', sort = 0, offset = 0, count = 20):
        params = {
            "q": q,
            "type":type,
            "country_id":country_id,
            "city_id":city_id,
            "future":future,
            "market":market,
            "sort":sort,
            "offset":offset,
            "count":count,
            "v":self.version,
            "access_token":self.access_token,

        }
        
        response = requests.get('https://api.vk.com/method/groups.search?', params=params)
        self.last_response.clear()
        self.last_response = json.loads(response.text)
        if "error" in response.text: 
            return False
        else:
            return response.text


    def get_user_via_id(self, user_ids, fileds='', nom_case='Nom'):
        params = {
            "user_ids":user_ids,
            "fields": fileds,
            "nom_case": nom_case,
            "v":self.version,
            "access_token":self.access_token,

        }
        response = requests.get('https://api.vk.com/method/users.get?', params=params)
        self.last_response.clear()
        self.last_response = json.loads(response.text)
        if "error" in response.text: 
            return False
        else:
            return response.text