import requests
s = requests.session()
required_args = {
        'name':'sessionid ',
        'value':'b2s4fxoff6kur2lmox88c3jplgvt9xe5'
    }

optional_args = {
    'domain':'pepper.ninja',
    'path':'/',
}

my_cookie = requests.cookies.create_cookie(**required_args,**optional_args)
s.cookies.set_cookie(my_cookie)
r = s.get('https://pepper.ninja/api/search/items/?start=333331&stop=333333&query=%7B%22q":"а+",%22trending%22:false,%22search_in_status%22:true,%22simple_search%22:false,%22can_message%22:false,%22vk_search%22:false,%22market%22:false,%22description%22:true,%22search_sex%22:[],%22search_age%22:[],%22country_id%22:1,%22city%22:[],%22min_members%22:%22%22,%22max_members%22:%22%22,%22search_type%22:%7B%22group%22:false,%22event%22:false,%22page%22:false%7D,%22minus_word%22:%22%22,%22sort%22:%22%22,%22search_country%22:[],%22search_rus_regions%22:[],%22search_interest%22:[],%22results_limit%22:1000000%7D')
print(r.text)
