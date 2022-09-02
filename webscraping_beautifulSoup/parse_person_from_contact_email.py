import requests
from bs4 import BeautifulSoup
import re
import json

session = requests.Session()

static = 'https://www.grubhub.com/eat/static-content?contentOnly=1'
soup = BeautifulSoup(session.get(static).text, 'html.parser')
client = re.findall("beta_[a-zA-Z0-9]+",str(soup.find('script', {'type': 'text/javascript'})))
print(client)

# client='beta_UmWlpstzQSFmocLy3h1UieYcVST'

# define and add a proper header
headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36',
        'authorization': 'Bearer',
        'content-type': 'application/json;charset=UTF-8'
          }
session.headers.update(headers)

# straight from networking tools. Device ID appears to accept any 10-digit value
data = '{"brand":"GRUBHUB","client_id":"' + client[0] + '","device_id":-708763761,"scope":"anonymous"}'
resp = session.post('https://api-gtm.grubhub.com/auth', data=data)

# refresh = json.loads(resp.text)['session_handle']['refresh_token']
access = json.loads(resp.text)['session_handle']['access_token']

# update header with new token
session.headers.update({'authorization': 'Bearer ' + access})

restaurants_links = [
    'https://www.grubhub.com/restaurant/dosa-love-893-e-el-camino-real-sunnyvale/3024935',
    'https://www.grubhub.com/restaurant/beaus-breakfast-burritos-1404-madison-ave-new-york/3235140',
    'https://www.grubhub.com/restaurant/impeckable-wings-901-nw-24th-st-san-antonio/3159434',
    'https://www.grubhub.com/restaurant/the-vegan-grill-5155-3rd-st-san-francisco/2994242'
]

restaurants_details = []
category_products_details = []
products_topping_details = []

for restaurant_link in restaurants_links:

    if restaurant_link[-1] == '/':
        restaurant_id = restaurant_link.split('/')[-2]
    else:
        restaurant_id = restaurant_link.split('/')[-1]

    # restaurant and products api
    res_pro_api = "https://api-gtm.grubhub.com/restaurants/{}?hideChoiceCategories=true&version=4&variationId=rtpFreeItems&orderType=standard&hideUnavailableMenuItems=true&hideMenuItems=false".format(restaurant_id)

    grub = session.get(res_pro_api)
    if grub.status_code == 200:
        restaurants_response = json.loads(grub.text)
        if 'restaurant' in restaurants_response:
            restaurant = restaurants_response.get('restaurant', {})

            # getting restaurant details
            address = ''
            city = ''
            country = ''
            review = 0
            stars = 0
            restaurant_name = restaurant.get('name', '')

            if 'address' in restaurant:
                address_line = restaurant['address']
                address = address_line.get('street_address', '')
                country = address_line.get('country', '')
                city = address_line.get('locality', '')
            if 'rating' in restaurant:
                review = restaurant['rating'].get('rating_count', 0)
                stars = restaurant['rating'].get('rating_value', 0)

            restaurants_details.append([restaurant_name, address, city, country, review, stars])

            if 'menu_category_list' in restaurant and restaurant['menu_category_list']:
                menu_categories = restaurant['menu_category_list']
                for menu_category in menu_categories:
                    if 'menu_item_list' in menu_category and menu_category['menu_item_list']:
                        category_products = menu_category['menu_item_list']
                        for category_product in category_products:
                            category_name = category_product.get('menu_category_name', '')
                            product_name = category_product.get('name', '')
                            product_description = category_product.get('description','')
                            product_price = category_product['price']['amount']/10
                            category_products_details.append([category_name, product_name, product_description, product_price])

                            product_id = category_product['id']

                            # getting restaurant products details
                            # products detail api
                            pro_api = "https://api-gtm.grubhub.com/restaurants/{}/menu_items/{}?time=1662059755411&hideUnavailableMenuItems=true&orderType=standard&version=4".format(restaurant_id, product_id)

                            product_topping_response = session.get(pro_api)
                            if product_topping_response.status_code == 200:
                                toppings = json.loads(product_topping_response.text)
                                if 'choice_category_list' in toppings and toppings['choice_category_list']:
                                    for modifier in toppings['choice_category_list']:
                                        modifier_name = modifier.get('name', '')
                                        choices_list = modifier.get('choice_option_list', [])
                                        modifier_min = modifier.get('min_choice_options', 0)
                                        modifier_max = modifier.get('max_choice_options', len(choices_list))
                                        for choice in choices_list:
                                            choice_name = choice.get('description', '')
                                            choice_price = choice['price']['amount']/10
                                            products_topping_details.append([modifier_name, modifier_min, modifier_max,
                                                                             choice_name, choice_price])

                            else:
                                # get new token
                                pass

                            # recommendation api
                            recommendation_api = "https://api-gtm.grubhub.com/recommendations/menuitem/crosssell?restaurantId={}&menuItemIdsInCart={}&variationId=0.2_PriceCeiling%3D0.50".format(restaurant_id, product_id)

                            product_recommendation = session.get(recommendation_api)
                            if product_recommendation.status_code == 200:
                                extra_toppings = json.loads(product_recommendation.text)
                                if 'menu_item_recommendations_result' in extra_toppings and extra_toppings['menu_item_recommendations_result']:
                                    extra_topping_list = extra_toppings['menu_item_recommendations_result']
                                    for extra_topping in extra_topping_list:
                                        if 'menu_item_recommendation_list' in extra_topping and extra_topping['menu_item_recommendation_list']:
                                            for recommended_item in extra_topping['menu_item_recommendation_list']:
                                                choice_name = recommended_item.get('menu_item_name', '')
                                                choice_price = recommended_item['menu_item_price']['amount'] / 10
                                                products_topping_details.append(
                                                    ["Complete your meal", 0, 1,
                                                     choice_name, choice_price])
                            else:
                                # get new token
                                pass
    else:
        pass


