import requests
import json
from loguru import logger
import json
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from loguru import logger
import os

cookies = {
    'auth_token': '5f7ef41a982e6593d3f7f905b0fb85ecc7a88366',
    'ct0': '0fd9927295d02d17c9793c22d1616682601a637010f4cfb0c0577ac8ce327bc8276bd4557a40ef89cc9652645776921f7dcd4684ae0deeb103d2f2bb62ea34a75d594d24000bec5b754e859c3a680cd9',
}
headers = {
    'authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA',
    'x-csrf-token': '0fd9927295d02d17c9793c22d1616682601a637010f4cfb0c0577ac8ce327bc8276bd4557a40ef89cc9652645776921f7dcd4684ae0deeb103d2f2bb62ea34a75d594d24000bec5b754e859c3a680cd9',
}
list_id = '1464058952732184580'

tweet_cache = dict()
msg_box = []
logger.add(f"log/{list_id}.log") 


def send_msg(msg: str):
    # 自定义个性化推送方式 这里用飞书作为例子
    url = f'https://open.feishu.cn/open-apis/bot/v2/hook/{os.getenv("bot_token")}'
    headers = {'Content-Type': 'application/json'}
    data = {'msg_type': 'text', 'content': { 'text': msg }}
    requests.post(url, headers=headers, json=data).json()


def list_params(listId):
    # https://github.com/fa0311/TwitterInternalAPIDocument
    return {
        'variables': json.dumps({
            "listId": listId,
            "count" : 20
        }),
        'features': json.dumps({
            "responsive_web_graphql_exclude_directive_enabled": False,
            "verified_phone_label_enabled": False,
            "responsive_web_home_pinned_timelines_enabled": False,
            "creator_subscriptions_tweet_preview_api_enabled": False,
            "responsive_web_graphql_timeline_navigation_enabled": False,
            "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
            "c9s_tweet_anatomy_moderator_badge_enabled": False,
            "tweetypie_unmention_optimization_enabled": False,
            "responsive_web_edit_tweet_api_enabled": False,
            "graphql_is_translatable_rweb_tweet_is_translatable_enabled": False,
            "view_counts_everywhere_api_enabled": False,
            "longform_notetweets_consumption_enabled": False,
            "responsive_web_twitter_article_tweet_consumption_enabled": False,
            "tweet_awards_web_tipping_enabled": False,
            "freedom_of_speech_not_reach_fetch_enabled": False,
            "standardized_nudges_misinfo": False,
            "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": False,
            "longform_notetweets_rich_text_read_enabled": False,
            "longform_notetweets_inline_media_enabled": False,
            "responsive_web_media_download_video_enabled": False,
            "responsive_web_enhance_cards_enabled": False
        }),
    }

def find_full_text(data):
    if isinstance(data, dict):
        for key, value in data.items():
            if key == "full_text":
                return value
            elif isinstance(value, (dict, list)):
                result = find_full_text(value)
                if result:
                    return result
    elif isinstance(data, list):
        for item in data:
            result = find_full_text(item)
            if result:
                return result

def get_tweets():
    logger.debug('get tweets...')
    res = requests.get(
        'https://twitter.com/i/api/graphql/d1mUZHaqFMxe0xHI3rVc-w/ListLatestTweetsTimeline',
        params=list_params(list_id),
        cookies=cookies,
        headers=headers,
    ).json()
    if 'errors' in res:
        raise Exception(res['errors'])
    return res


def get_entries():
    data = get_tweets()['data']['list']['tweets_timeline']['timeline']['instructions'][0]['entries']
    entries = []
    for i in data:
        if not find_full_text(i): continue

        if 'items' in i['content']:
            result = i['content']['items'][-1]['item']['itemContent']['tweet_results']['result']
        else:
            try:
                result = i['content']['itemContent']['tweet_results']['result']['tweet']
            except:
                result = i['content']['itemContent']['tweet_results']['result']
        entries.append(result)
    return entries

def init():
    logger.debug('init...')
    global msg_box, tweet_cache
    try:
        entries = get_entries()
        for i in entries:
            tweet_id = i['rest_id']
            logger.debug(f'init tweet: {tweet_id} {i["legacy"]["full_text"][:5]}')
            tweet_cache[tweet_id] = True
    except Exception as e:
        logger.error(e)

def job_function():
    try:
        entries = get_entries()
        global msg_box
        tweet_list = [result['rest_id'] for result in entries]
        for result in entries:
            tweet_id = result['rest_id']
            author = result['core']['user_results']['result']['legacy']['name']
            screen_name = result['core']['user_results']['result']['legacy']['screen_name']
            created_at = datetime.strptime(result['legacy']['created_at'], '%a %b %d %H:%M:%S %z %Y').strftime('%Y-%m-%d %H:%M:%S')
            full_text = result['legacy']['full_text']

            if tweet_id in tweet_cache: break
            logger.success(f'new tweet {tweet_id}')
            tweet_cache[tweet_id] = True

            if 'quoted_status_result' in result:
                quoted_text = find_full_text(result['quoted_status_result'])
                full_text = full_text + '\n=====转推=====\n' + quoted_text

            # TODO: fix format and add pic parse
            
            msg = f'''
    {full_text}

    https://twitter.com/{screen_name}/status/{tweet_id}
    {created_at}'''
            if full_text.startswith('RT '):
                msg = f'{author} 转推:' + msg
            else:
                msg = f'{author}:' + msg

            msg_box.append(msg)

        for i in msg_box:
            # send_msg(i)
            logger.info(i)
        msg_box = []
        return tweet_list
    except Exception as e:
        logger.error(e)
        


def sweep():
    logger.debug('sweep...')
    global tweet_cache
    tweet_list = job_function()
    tweet_cache.clear()
    for i in tweet_list:
        tweet_cache[i] = True
    

if __name__ == '__main__':   
    
    scheduler = BlockingScheduler()
    scheduler.add_job(job_function, 'interval', seconds=30)
    scheduler.add_job(sweep, 'interval', days=3)
    init()
    scheduler.start()