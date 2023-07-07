import datetime

from rediscluster import RedisCluster

from readConfig import ReadConfig


def get_msg(env, phone):
    red_items = ReadConfig().get_iterm(f"redis-{env}")
    host_list = eval(red_items['host'])
    red = RedisCluster(startup_nodes=host_list, decode_responses=True)
    # red = redis.Redis(host='127.0.0.1', port=server.local_bind_port, decode_responses=True)
    msg = "没有查询到！"
    key = f"captcha_{phone}"
    cur_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    ttl_time = red.ttl(key)
    if red.exists(key) == 1:
        text = red.get(key)
        msg = f"env: {env}, phone: {phone}, Login_code: {text}, {cur_time}, {ttl_time}\n"
    print(msg)
    return msg


if __name__ == '__main__':
    get_msg('alpha', '13716610001')
    get_msg('pre', '13716610001')
