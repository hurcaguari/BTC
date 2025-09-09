import Lib
import time

# 使用Config目录下的YAML配置文件
api = Lib.EtherscanAPI(config_path='Config/config.yaml')

# 显示缓存统计信息
print("=== 缓存状态 ===")
cache_stats = api.get_cache_stats()
for key, value in cache_stats.items():
    print(f"{key}: {value}")

# 清理过期缓存
api._clean_expired_cache()
print("\n=== 代币市场数据 ===\n")

# 测试获取代币信息
tokens = ['BTC', 'ETH', 'KAS', 'BNB']

for i, token in enumerate(tokens):
    start_time = time.time()
    info = api.get_token_info(token)
    end_time = time.time()
    
    print(f"代币: {info['symbol']}")
    print(f"  获取耗时: {end_time - start_time:.2f}秒")
    print(f"  数据来源: {'缓存' if info.get('cached', False) else 'API'}")
    
    if info['price_usd'] is not None:
        print(f"  美元价格: ${info['price_usd']:,.2f}")
    if info['price_cny'] is not None:
        print(f"  人民币价格: ¥{info['price_cny']:,.2f}")
    if info['supply'] is not None:
        print(f"  供应量: {info['supply']:,.0f} {info['supply_unit']}")
    if info['hashrate'] is not None:
        print(f"  算力: {info['hashrate']:,.2f} {info['hashrate_unit']}")
    else:
        print(f"  算力: {info['hashrate_unit']}")
    
    print("-" * 50)

# 再次显示缓存统计
print("\n=== 最终缓存状态 ===")
final_cache_stats = api.get_cache_stats()
for key, value in final_cache_stats.items():
    print(f"{key}: {value}")