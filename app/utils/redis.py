import os
import redis
from config import REDIS_CONFIG, APP_ENV

# Kết nối Redis
app_env = APP_ENV
if app_env == "develop":
    redis_client = redis.Redis(
        host=REDIS_CONFIG['host'],  
        port=REDIS_CONFIG['port'],       
        db=REDIS_CONFIG['db'],        
        username=REDIS_CONFIG['username'], 
        password=REDIS_CONFIG['password'], 
        ssl=True,
        ssl_cert_reqs="none"
    )
elif app_env == "local":
    redis_client = redis.StrictRedis(host=os.getenv('REDIS_HOST', 'localhost'),
                                 port=os.getenv('REDIS_PORT', '6379'),
                                 db=os.getenv('REDIS_DB', '0'),
                                 decode_responses=True )