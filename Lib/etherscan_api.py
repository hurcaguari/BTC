import requests
import json
import os
import time
import sqlite3
from datetime import datetime, timedelta

# YAML支持（如果没有安装pyyaml，使用内置简单解析器）
try:
    import yaml
    YAML_AVAILABLE = True
    print("使用PyYAML解析器")
except ImportError:
    try:
        from . import simple_yaml as yaml
        YAML_AVAILABLE = True
        print("使用内置简单YAML解析器")
    except ImportError:
        import simple_yaml as yaml
        YAML_AVAILABLE = True
        print("使用内置简单YAML解析器")

class EtherscanAPI:
    """
    通用的Etherscan API类，支持多链查询和数据缓存
    功能：传入代币缩写返回当前价格（美元和人民币）以及算力总量/代币供应量
    """
    
    def __init__(self, config_path='Config/config.yaml'):
        self.config = self._load_config(config_path)
        
        # 从YAML配置中获取API密钥
        api_keys = self.config.get('api_keys', {})
        self.api_key = api_keys.get('etherscan', '')
        
        # 缓存配置
        cache_config = self.config.get('cache', {})
        self.enable_cache = cache_config.get('enabled', True)
        self.cache_duration = cache_config.get('duration_minutes', 5)
        self.cache_db = cache_config.get('database', 'cache/token_cache.db')
        
        # API配置
        api_config = self.config.get('api', {})
        self.request_delay = api_config.get('request_delay', 2)
        self.timeout = api_config.get('timeout', 10)
        
        # 确保缓存目录存在并初始化数据库
        os.makedirs(os.path.dirname(self.cache_db), exist_ok=True)
        self._init_cache_db()
        
        # 最后一次请求时间
        self._last_request_time = 0
        
        # 支持的主流链和对应的Chain ID
        self.chains = {
            # 主网
            'ETH': {'chain_id': 1, 'name': 'Ethereum Mainnet'},
            'BNB': {'chain_id': 97, 'name': 'BNB Smart Chain Mainnet'},
            'MATIC': {'chain_id': 137, 'name': 'Polygon Mainnet'},
            'ARB': {'chain_id': 42161, 'name': 'Arbitrum One Mainnet'},
            'OP': {'chain_id': 10, 'name': 'OP Mainnet'},
            'BASE': {'chain_id': 8453, 'name': 'Base Mainnet'},
            'AVAX': {'chain_id': 43114, 'name': 'Avalanche C-Chain'},
            'BLAST': {'chain_id': 81457, 'name': 'Blast Mainnet'},
            'SCROLL': {'chain_id': 534352, 'name': 'Scroll Mainnet'},
            'LINEA': {'chain_id': 59144, 'name': 'Linea Mainnet'},
            # 测试网
            'ETH_SEPOLIA': {'chain_id': 11155111, 'name': 'Sepolia Testnet'},
            'BNB_TEST': {'chain_id': 97, 'name': 'BNB Smart Chain Testnet'},
        }
        
        # 代币到CoinGecko ID的映射
        self.coingecko_ids = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum', 
            'BNB': 'binancecoin',
            'KAS': 'kaspa',
            'MATIC': 'matic-network',
            'AVAX': 'avalanche-2',
            'LTC': 'litecoin',
            'DOGE': 'dogecoin',
            'ARB': 'arbitrum',
            'OP': 'optimism',
            'SOL': 'solana'
        }
        
    def _load_config(self, path):
        """加载配置文件（支持YAML和JSON格式）"""
        if not os.path.exists(path):
            # 如果指定路径不存在，尝试查找其他格式
            base_path = os.path.splitext(path)[0]
            for ext in ['.yaml', '.yml', '.json']:
                alt_path = base_path + ext
                if os.path.exists(alt_path):
                    path = alt_path
                    break
            else:
                raise FileNotFoundError(f'配置文件 {path} 不存在')
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                if path.endswith(('.yaml', '.yml')) and YAML_AVAILABLE:
                    return yaml.safe_load(f)
                else:
                    return json.load(f)
        except Exception as e:
            raise ValueError(f'配置文件格式错误: {e}')
    
    def _init_cache_db(self):
        """初始化缓存数据库"""
        if not self.enable_cache:
            return
        try:
            with sqlite3.connect(self.cache_db) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cache_data (
                        cache_key TEXT PRIMARY KEY,
                        data TEXT NOT NULL,
                        timestamp DATETIME NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 创建索引
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_timestamp ON cache_data(timestamp)
                ''')
                conn.commit()
        except Exception as e:
            print(f"初始化缓存数据库失败: {e}")
    
    def _is_cache_valid(self, timestamp):
        """检查缓存是否有效"""
        if not self.enable_cache:
            return False
        try:
            cache_time = datetime.fromisoformat(timestamp)
            now = datetime.now()
            return now - cache_time < timedelta(minutes=self.cache_duration)
        except:
            return False
    
    def _get_cached_data(self, key):
        """从数据库获取缓存数据"""
        if not self.enable_cache:
            return None
        
        try:
            with sqlite3.connect(self.cache_db) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT data, timestamp FROM cache_data WHERE cache_key = ?',
                    (key,)
                )
                result = cursor.fetchone()
                
                if result and self._is_cache_valid(result[1]):
                    return json.loads(result[0])
                elif result:
                    # 缓存过期，删除
                    cursor.execute('DELETE FROM cache_data WHERE cache_key = ?', (key,))
                    conn.commit()
        except Exception as e:
            print(f"获取缓存数据失败: {e}")
        
        return None
    
    def _set_cached_data(self, key, data):
        """将数据保存到数据库缓存"""
        if not self.enable_cache:
            return
        
        try:
            with sqlite3.connect(self.cache_db) as conn:
                cursor = conn.cursor()
                timestamp = datetime.now().isoformat()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO cache_data (cache_key, data, timestamp)
                    VALUES (?, ?, ?)
                ''', (key, json.dumps(data, ensure_ascii=False), timestamp))
                
                conn.commit()
        except Exception as e:
            print(f"保存缓存数据失败: {e}")
    
    def _clean_expired_cache(self):
        """清理过期的缓存数据"""
        if not self.enable_cache:
            return
        
        try:
            with sqlite3.connect(self.cache_db) as conn:
                cursor = conn.cursor()
                cutoff_time = datetime.now() - timedelta(minutes=self.cache_duration)
                
                cursor.execute(
                    'DELETE FROM cache_data WHERE timestamp < ?',
                    (cutoff_time.isoformat(),)
                )
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                if deleted_count > 0:
                    print(f"清理了 {deleted_count} 条过期缓存")
                    
        except Exception as e:
            print(f"清理缓存失败: {e}")
    
    def get_cache_stats(self):
        """获取缓存统计信息"""
        if not self.enable_cache:
            return {'cache_enabled': False}
        
        try:
            with sqlite3.connect(self.cache_db) as conn:
                cursor = conn.cursor()
                
                # 总缓存条数
                cursor.execute('SELECT COUNT(*) FROM cache_data')
                total_count = cursor.fetchone()[0]
                
                # 有效缓存条数
                cutoff_time = datetime.now() - timedelta(minutes=self.cache_duration)
                cursor.execute(
                    'SELECT COUNT(*) FROM cache_data WHERE timestamp >= ?',
                    (cutoff_time.isoformat(),)
                )
                valid_count = cursor.fetchone()[0]
                
                return {
                    'cache_enabled': True,
                    'total_cache_entries': total_count,
                    'valid_cache_entries': valid_count,
                    'expired_cache_entries': total_count - valid_count,
                    'cache_duration_minutes': self.cache_duration
                }
        except Exception as e:
            return {'cache_enabled': True, 'error': str(e)}
    
    def _wait_for_rate_limit(self):
        """等待API调用间隔"""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < self.request_delay:
            time.sleep(self.request_delay - time_since_last)
        self._last_request_time = time.time()
    
    def get_usd_to_cny_rate(self):
        """获取美元对人民币汇率"""
        cache_key = 'usd_cny_rate'
        cached = self._get_cached_data(cache_key)
        if cached is not None:
            return cached
        
        self._wait_for_rate_limit()
        try:
            url = 'https://api.exchangerate-api.com/v4/latest/USD'
            resp = requests.get(url, timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                rate = data['rates'].get('CNY', 7.2)
                self._set_cached_data(cache_key, rate)
                return rate
        except:
            pass
        return 7.2  # 默认汇率
    
    def get_token_price(self, token_symbol):
        """获取代币价格（美元和人民币）"""
        token_symbol = token_symbol.upper()
        cache_key = f'price_{token_symbol}'
        cached = self._get_cached_data(cache_key)
        if cached is not None:
            return cached
        
        coingecko_id = self.coingecko_ids.get(token_symbol)
        if not coingecko_id:
            return None, None
        
        self._wait_for_rate_limit()
        try:
            url = f'https://api.coingecko.com/api/v3/simple/price?ids={coingecko_id}&vs_currencies=usd'
            resp = requests.get(url, timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                usd_price = data[coingecko_id]['usd']
                
                # 获取汇率并计算人民币价格
                usd_to_cny = self.get_usd_to_cny_rate()
                cny_price = usd_price * usd_to_cny
                
                result = (usd_price, cny_price)
                self._set_cached_data(cache_key, result)
                return result
        except:
            pass
        return None, None
    
    def get_token_supply(self, token_symbol):
        """获取代币供应量"""
        token_symbol = token_symbol.upper()
        cache_key = f'supply_{token_symbol}'
        cached = self._get_cached_data(cache_key)
        if cached is not None:
            return cached
        
        result = None, token_symbol
        
        if token_symbol == 'ETH':
            self._wait_for_rate_limit()
            try:
                url = f'https://api.etherscan.io/api?module=stats&action=ethsupply&apikey={self.api_key}'
                resp = requests.get(url, timeout=self.timeout)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get('status') == '1':
                        supply_wei = int(data['result'])
                        supply_eth = supply_wei / (10**18)
                        result = (supply_eth, 'ETH')
            except:
                pass
        
        # 备选方案：使用CoinGecko获取供应量
        if result[0] is None:
            coingecko_id = self.coingecko_ids.get(token_symbol)
            if coingecko_id:
                self._wait_for_rate_limit()
                try:
                    url = f'https://api.coingecko.com/api/v3/coins/{coingecko_id}'
                    resp = requests.get(url, timeout=self.timeout)
                    if resp.status_code == 200:
                        data = resp.json()
                        supply = data.get('market_data', {}).get('circulating_supply')
                        if supply:
                            result = (supply, token_symbol)
                except:
                    pass
        
        self._set_cached_data(cache_key, result)
        return result
    
    def get_token_hashrate(self, token_symbol):
        """获取代币算力（仅适用于POW币种）"""
        token_symbol = token_symbol.upper()
        cache_key = f'hashrate_{token_symbol}'
        cached = self._get_cached_data(cache_key)
        if cached is not None:
            return cached
        
        result = None, 'N/A (POS)'
        
        if token_symbol == 'BTC':
            self._wait_for_rate_limit()
            try:
                url = 'https://api.blockchain.info/stats'
                resp = requests.get(url, timeout=self.timeout)
                if resp.status_code == 200:
                    data = resp.json()
                    hashrate = data.get('hash_rate')  # GH/s
                    if hashrate:
                        result = (hashrate, 'GH/s')
            except:
                pass
                
        elif token_symbol == 'KAS':
            self._wait_for_rate_limit()
            try:
                url = 'https://api.kaspa.org/info/hashrate'
                resp = requests.get(url, timeout=self.timeout)
                if resp.status_code == 200:
                    data = resp.json()
                    hashrate = data.get('hashrate')
                    if hashrate:
                        result = (hashrate, 'H/s')
            except:
                pass
        
        self._set_cached_data(cache_key, result)
        return result
    
    def get_chain_info(self, chain_symbol):
        """获取链信息"""
        return self.chains.get(chain_symbol.upper())
    
    def get_multichain_balance(self, address, chains=['ETH', 'BNB', 'MATIC']):
        """
        获取指定地址在多条链上的余额
        使用Etherscan V2 API的多链功能
        """
        cache_key = f'balance_{address}_{"_".join(chains)}'
        cached = self._get_cached_data(cache_key)
        if cached is not None:
            return cached
        
        results = {}
        for chain in chains:
            chain_info = self.get_chain_info(chain)
            if not chain_info:
                results[chain] = {'error': 'Chain not supported'}
                continue
            
            self._wait_for_rate_limit()
            try:
                url = f'https://api.etherscan.io/v2/api?chainid={chain_info["chain_id"]}&module=account&action=balance&address={address}&tag=latest&apikey={self.api_key}'
                resp = requests.get(url, timeout=self.timeout)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get('status') == '1':
                        balance_wei = int(data['result'])
                        balance_eth = balance_wei / (10**18)
                        results[chain] = {
                            'balance': balance_eth,
                            'balance_wei': balance_wei,
                            'chain_name': chain_info['name']
                        }
                    else:
                        results[chain] = {'error': data.get('message', 'API Error')}
                else:
                    results[chain] = {'error': f'HTTP {resp.status_code}'}
            except Exception as e:
                results[chain] = {'error': str(e)}
        
        self._set_cached_data(cache_key, results)        
        return results
    
    def get_token_info(self, token_symbol):
        """
        获取代币完整信息
        返回: {
            'symbol': 代币符号,
            'price_usd': 美元价格,
            'price_cny': 人民币价格,
            'supply': 供应量,
            'supply_unit': 供应量单位,
            'hashrate': 算力,
            'hashrate_unit': 算力单位,
            'cached': 是否来自缓存,
            'cache_time': 缓存时间
        }
        """
        token_symbol = token_symbol.upper()
        cache_key = f'token_info_{token_symbol}'
        
        # 检查完整缓存
        cached = self._get_cached_data(cache_key)
        if cached is not None:
            cached['cached'] = True
            return cached
        
        # 获取各项数据
        price_usd, price_cny = self.get_token_price(token_symbol)
        supply, supply_unit = self.get_token_supply(token_symbol)
        hashrate, hashrate_unit = self.get_token_hashrate(token_symbol)
        
        result = {
            'symbol': token_symbol,
            'price_usd': price_usd,
            'price_cny': price_cny,
            'supply': supply,
            'supply_unit': supply_unit,
            'hashrate': hashrate,
            'hashrate_unit': hashrate_unit,
            'cached': False,
            'cache_time': datetime.now().isoformat()
        }
        
        # 缓存完整结果
        self._set_cached_data(cache_key, result)
        return result

    def list_supported_chains(self):
        """列出所有支持的链"""
        return {
            'chains': self.chains,
            'total_count': len(self.chains)
        }
        
    def list_supported_tokens(self):
        """列出所有支持的代币"""
        return {
            'tokens': list(self.coingecko_ids.keys()),
            'total_count': len(self.coingecko_ids)
        }

    def get_api_status(self):
        """获取API状态信息"""
        return {
            'api_key_configured': bool(self.api_key),
            'supported_chains_count': len(self.chains),
            'supported_tokens_count': len(self.coingecko_ids),
            'cache_enabled': self.enable_cache,
            'cache_duration_minutes': self.cache_duration,
            'request_delay_seconds': self.request_delay
        }
    
    def clear_cache(self):
        """清除所有缓存数据"""
        if not self.enable_cache:
            return False
        
        try:
            with sqlite3.connect(self.cache_db) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM cache_data')
                deleted_count = cursor.rowcount
                conn.commit()
                
                print(f"清除了 {deleted_count} 条缓存数据")
                return True
        except Exception as e:
            print(f"清除缓存失败: {e}")
            return False


# 模块测试代码
if __name__ == '__main__':
    api = EtherscanAPI()
    
    # 测试API状态
    print("API状态:", api.get_api_status())
    
    # 测试代币信息
    btc_info = api.get_token_info('BTC')
    print("BTC信息:", btc_info)
