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
        
        # 初始化链映射（先用硬编码的备用映射，然后尝试从chainlist API更新）
        self._init_chain_mappings()
        
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
            'SOL': 'solana',
            'BASE': 'base',
            'BLAST': 'blast',
            'SCROLL': 'scroll',
            'LINEA': 'linea'
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
                if 'rates' in data and 'CNY' in data['rates']:
                    rate = data['rates']['CNY']
                    # 只有成功获取汇率时才缓存
                    self._set_cached_data(cache_key, rate)
                    return rate
        except Exception as e:
            print(f"获取汇率失败: {e}")
            
        # 失败时返回默认汇率，不缓存
        return 7.2
    
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
                if coingecko_id in data and 'usd' in data[coingecko_id]:
                    usd_price = data[coingecko_id]['usd']
                    
                    # 获取汇率并计算人民币价格
                    usd_to_cny = self.get_usd_to_cny_rate()
                    cny_price = usd_price * usd_to_cny
                    
                    result = (usd_price, cny_price)
                    # 只有成功获取价格数据时才缓存
                    self._set_cached_data(cache_key, result)
                    return result
        except Exception as e:
            print(f"获取{token_symbol}价格失败: {e}")
            
        # 失败时不缓存，直接返回
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
        success = False
        
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
                        success = True
            except Exception as e:
                print(f"获取BTC算力失败: {e}")
                
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
                        success = True
            except Exception as e:
                print(f"获取KAS算力失败: {e}")
        else:
            # 对于POS币种或其他非POW币种，直接返回并缓存
            success = True
        
        # 只有成功获取数据时才缓存
        if success:
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
    
    def _init_chain_mappings(self):
        """初始化链映射，必须从chainlist API获取"""
        # 尝试从chainlist API获取
        try:
            chainlist_data = self._get_chainlist_data()
            if chainlist_data:
                dynamic_chains = self._parse_chainlist_data(chainlist_data)
                if dynamic_chains:
                    self.chains = dynamic_chains
                    print(f"📋 从chainlist API加载了 {len(dynamic_chains)} 个链配置")
                    return
                else:
                    print("❌ chainlist数据解析失败")
            else:
                print("❌ 无法获取chainlist数据")
        except Exception as e:
            print(f"❌ chainlist初始化失败: {e}")
        
        # 如果所有尝试都失败了，抛出异常
        raise RuntimeError("❌ 无法初始化链映射：chainlist API不可用且不允许使用备用映射")

    def _get_chainlist_data(self):
        """获取chainlist数据（带缓存）"""
        cache_key = "chainlist_data"
        
        # 尝试从缓存获取
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            print("📦 使用缓存的chainlist数据")
            return cached_data
        
        # 缓存未命中，从API获取
        try:
            print("🌐 从API获取chainlist数据...")
            self._wait_for_rate_limit()
            
            url = "https://api.etherscan.io/v2/chainlist"
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('result'):
                # 缓存数据
                self._set_cached_data(cache_key, data)
                print(f"✅ 获取到 {len(data['result'])} 条链配置数据")
                return data
            else:
                print("❌ API返回数据格式异常")
                return None
                
        except Exception as e:
            print(f"❌ 获取chainlist数据失败: {e}")
            return None
    
    def _parse_chainlist_data(self, data):
        """解析chainlist数据并构建映射"""
        try:
            chains_result = data.get('result', [])
            
            # 解析链信息，优先保留主网链
            mainnet_priority = {}  # 用于存储每个符号的最佳链选择
            
            for chain_info in chains_result:
                chain_id = int(chain_info.get('chainid', 0))
                chain_name = chain_info.get('chainname', '')
                api_url = chain_info.get('apiurl', '')
                block_explorer = chain_info.get('blockexplorer', '')
                status = chain_info.get('status', 0)
                
                # 只处理状态为1（正常）的链
                if status != 1:
                    continue
                
                # 提取代币符号
                token_symbol = self._extract_token_symbol(chain_name, chain_id)
                if not token_symbol:
                    continue
                
                # 构建链信息
                chain_data = {
                    'chain_id': chain_id,
                    'name': chain_name,
                    'api_url': api_url,
                    'explorer': block_explorer
                }
                
                # 优先级选择逻辑：主网 > 测试网
                is_mainnet = not self._is_testnet(chain_name)
                
                if token_symbol not in mainnet_priority:
                    mainnet_priority[token_symbol] = (chain_data, is_mainnet, chain_id)
                else:
                    current_data, current_is_mainnet, current_id = mainnet_priority[token_symbol]
                    
                    # 如果当前是主网而存储的是测试网，则替换
                    if is_mainnet and not current_is_mainnet:
                        mainnet_priority[token_symbol] = (chain_data, is_mainnet, chain_id)
                    # 如果都是主网，选择较小的chain_id（通常是原生链）
                    elif is_mainnet and current_is_mainnet and chain_id < current_id:
                        mainnet_priority[token_symbol] = (chain_data, is_mainnet, chain_id)
            
            # 构建最终映射
            result_chains = {}
            for symbol, (chain_data, is_mainnet, _) in mainnet_priority.items():
                result_chains[symbol] = chain_data
            
            print(f"📋 解析到 {len(result_chains)} 个链配置（优先选择主网）")
            for symbol, data in list(result_chains.items())[:10]:  # 显示前10个
                print(f"   {symbol}: {data['name']} (ID: {data['chain_id']})")
            
            return result_chains
            
        except Exception as e:
            print(f"❌ 解析chainlist数据失败: {e}")
            return {}
    
    def _extract_token_symbol(self, chain_name, chain_id):
        """从链名称中提取代币符号"""
        chain_name = chain_name.lower()
        
        # 特殊映射规则
        symbol_mappings = {
            # Ethereum生态
            'ethereum': 'ETH',
            'sepolia': 'ETH_SEPOLIA' if 'sepolia' in chain_name else 'ETH',
            'holesky': 'ETH_HOLESKY',
            
            # BSC生态  
            'bnb smart chain': 'BNB',
            'bsc': 'BNB',
            'binance': 'BNB',
            
            # Polygon生态
            'polygon': 'MATIC',
            'matic': 'MATIC',
            'zkevm': 'ZKEVM',
            
            # Layer 2
            'arbitrum': 'ARB',
            'optimism': 'OP', 
            'base': 'BASE',
            'blast': 'BLAST',
            'scroll': 'SCROLL',
            'linea': 'LINEA',
            
            # 其他主要链
            'avalanche': 'AVAX',
            'cronos': 'CRO',
            'celo': 'CELO',
            'gnosis': 'GNOSIS',
            'mantle': 'MNT',
            'moonbeam': 'GLMR',
            'moonriver': 'MOVR',
            'bittorrent': 'BTT',
            'fraxtal': 'FRAX',
            'zksync': 'ZK'
        }
        
        # 遍历映射规则
        for pattern, symbol in symbol_mappings.items():
            if pattern in chain_name:
                # 处理测试网后缀
                if any(test in chain_name for test in ['testnet', 'sepolia', 'holesky', 'fuji', 'amoy']):
                    if not symbol.endswith('_TEST') and not symbol.endswith('_SEPOLIA') and not symbol.endswith('_HOLESKY'):
                        if 'sepolia' in chain_name:
                            return f"{symbol.split('_')[0]}_SEPOLIA"
                        elif 'holesky' in chain_name:
                            return f"{symbol.split('_')[0]}_HOLESKY"  
                        else:
                            return f"{symbol.split('_')[0]}_TEST"
                return symbol
        
        return None
    
    def _is_testnet(self, chain_name):
        """判断是否为测试网"""
        testnet_indicators = ['testnet', 'sepolia', 'holesky', 'test', 'fuji', 'amoy', 'goerli']
        chain_name_lower = chain_name.lower()
        return any(indicator in chain_name_lower for indicator in testnet_indicators)


# 模块测试代码
if __name__ == '__main__':
    api = EtherscanAPI()
    
    # 测试API状态
    print("API状态:", api.get_api_status())
    
    # 测试代币信息
    btc_info = api.get_token_info('BTC')
    print("BTC信息:", btc_info)
