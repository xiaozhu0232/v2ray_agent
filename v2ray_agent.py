import os
import json
from urllib.parse import urljoin
import requests
import settings
from v2ray_api.client import Client
from v2ray_api.errors import EmailExistsError, EmailNotFoundError
from apscheduler.schedulers.blocking import BlockingScheduler
import logging

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
V2RAY_CONFIG = os.path.join(BASE_DIR, 'v2ray_config', 'config.json')

REQUEST_HEADERS = {'user-agent': 'v2ray-agent',
                   'Nodeid': settings.NODE_ID,
                   'Apikey': settings.API_KEY}

LAST_TRAFFIC_RECORD = None

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)


def get_enable_users():
    users = []
    r = requests.get(urljoin(settings.V2RAYUI_URL, 'userapi'), headers=REQUEST_HEADERS)
    if r.status_code == 200:
        try:
            user_dict = r.json()
            users = user_dict['users']
        except Exception as e:
            log.error(e)
            raise e
    else:
        log.error('Can not get users info from v2rayui API.')
        raise ValueError('Can not get users info from v2rayui API.')
    return users


def get_v2ray_users(inbound_tag):
    users = []
    try:
        with open(V2RAY_CONFIG, 'r') as f:
            config_dict = json.load(f)
        for inbound in config_dict['inbounds']:
            if inbound['tag'] == inbound_tag:
                for user in inbound['settings']['clients']:
                    users.append(user['id'])
                break
    except Exception as e:
        log.error(e)
        return []
    return users


def loop_check_users():
    if settings.V2RAY_API_HOST and settings.V2RAY_API_PORT:
        v2ray_client = Client(address=settings.V2RAY_API_HOST, port=int(settings.V2RAY_API_PORT))
    else:
        return None
    try:
        enable_users = get_enable_users()
    except Exception as e:
        log.error(e)
        return None
    v2ray_users = get_v2ray_users(settings.V2RAY_INBOUND_TAG)
    with open(V2RAY_CONFIG, 'r') as f:
        v2ray_config_dict = json.load(f)
    config_changed = False
    for user in enable_users:
        if user['user_id'] in v2ray_users:
            v2ray_users.remove(user['user_id'])
        else:
            try:
                log.info('Add new user: %s' % user['user_id'])
                v2ray_client.add_user(inbound_tag=settings.V2RAY_INBOUND_TAG,
                                      user_id=user['user_id'],
                                      email=user['user_id'],
                                      level=user['level'],
                                      alter_id=user['alter_id'])
            except EmailExistsError:
                log.error('User %s exists, skip adding...' % user['user_id'])
            except Exception as e:
                log.error(e)
                continue
            for inbound in v2ray_config_dict['inbounds']:
                if inbound['tag'] == settings.V2RAY_INBOUND_TAG:
                    inbound['settings']['clients'].append({
                        'id': user['user_id'],
                        'email': user['user_id'],
                        'level': user['level'],
                        'alterId': user['alter_id']
                    })
                    config_changed = True
                    log.info('Add new user %s to config.json' % user['user_id'])
                    break
    if len(v2ray_users):
        for user_id in v2ray_users:
            try:
                log.info('Delete user: %s' % user['user_id'])
                v2ray_client.remove_user(inbound_tag=settings.V2RAY_INBOUND_TAG, email=user_id)
            except EmailNotFoundError:
                log.error('User %s not exists, skip deleting...' % user['user_id'])
            except Exception as e:
                log.error(e)
                continue
            for inbound in v2ray_config_dict['inbounds']:
                if inbound['tag'] == settings.V2RAY_INBOUND_TAG:
                    for i, client_item in enumerate(inbound['settings']['clients']):
                        if client_item['id'] == user_id:
                            inbound['settings']['clients'].pop(i)
                            config_changed = True
                            log.info('Delete user %s from config.json' % user['user_id'])
                            break
                    break
    if config_changed:
        with open(V2RAY_CONFIG, 'w') as f:
            f.write(json.dumps(v2ray_config_dict, ensure_ascii=False, sort_keys=True, indent=2))
            log.info('The changes were written to file config.json successfully.')


def loop_update_traffic():
    global LAST_TRAFFIC_RECORD
    if settings.V2RAY_API_HOST and settings.V2RAY_API_PORT:
        v2ray_client = Client(address=settings.V2RAY_API_HOST, port=int(settings.V2RAY_API_PORT))
    else:
        return None
    traffic = v2ray_client.get_all_traffic(reset=True)
    result = {'users': traffic['users'], 'node': {'uplink': 0, 'downlink': 0}}
    for inbound in traffic['inbound']:
        if inbound == settings.V2RAY_INBOUND_TAG:
            result['node'] = {
                'uplink': traffic['inbound'][inbound].get('uplink', 0),
                'downlink': traffic['inbound'][inbound].get('downlink', 0)
            }
    if LAST_TRAFFIC_RECORD:
        result['node']['uplink'] += LAST_TRAFFIC_RECORD['node']['uplink']
        result['node']['downlink'] += LAST_TRAFFIC_RECORD['node']['downlink']
        for user_id in result['users']:
            result['users'][user_id] = {
                'uplink': result['users'][user_id].get('uplink', 0) + LAST_TRAFFIC_RECORD['users'][user_id].get('uplink', 0),
                'downlink': result['users'][user_id].get('downlink', 0) + LAST_TRAFFIC_RECORD['users'][user_id].get('downlink', 0)
            }
    r = requests.post(urljoin(settings.V2RAYUI_URL, 'trafficapi'), json=result, headers=REQUEST_HEADERS)
    if r.status_code == 200 or r.status_code == 202:
        LAST_TRAFFIC_RECORD = None
    else:
        log.warning('Update traffic failed...')
        LAST_TRAFFIC_RECORD = result


scheduler = BlockingScheduler()
scheduler.add_job(loop_check_users, 'interval', seconds=int(settings.CHECK_USER_INTERVAL))
scheduler.add_job(loop_update_traffic, 'interval', seconds=int(settings.UPDATE_TRAFFIC_INTERVAL))
logging.getLogger('apscheduler.executors.default').setLevel(logging.WARNING)
scheduler.start()
