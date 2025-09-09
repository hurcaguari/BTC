#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件管理工具
支持环境变量和模板配置
"""

import os
import yaml
import shutil
from pathlib import Path

class ConfigManager:
    """配置管理器，支持环境变量替换"""
    
    @staticmethod
    def create_config_from_template():
        """从模板创建配置文件"""
        template_path = Path("Config/config.template.yaml")
        config_path = Path("Config/config.yaml")
        
        if not template_path.exists():
            raise FileNotFoundError("配置模板文件不存在")
        
        if config_path.exists():
            response = input(f"配置文件 {config_path} 已存在，是否覆盖？ (y/N): ")
            if response.lower() != 'y':
                print("操作已取消")
                return
        
        # 复制模板文件
        shutil.copy2(template_path, config_path)
        print(f"✅ 已从模板创建配置文件: {config_path}")
        print("⚠️  请编辑配置文件，将 YOUR_API_KEY_HERE 替换为您的真实API密钥")
        
        return config_path
    
    @staticmethod
    def load_config_with_env(config_path="Config/config.yaml"):
        """
        加载配置文件，支持环境变量替换
        
        环境变量格式：
        - ETHERSCAN_API_KEY
        - COINGECKO_API_KEY
        """
        
        config_path = Path(config_path)
        
        if not config_path.exists():
            print("❌ 配置文件不存在，正在从模板创建...")
            ConfigManager.create_config_from_template()
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
        except Exception as e:
            print(f"❌ 配置文件加载失败: {e}")
            return {}
        
        # 环境变量替换
        if 'api_keys' in config:
            # Etherscan API密钥
            env_etherscan = os.getenv('ETHERSCAN_API_KEY')
            if env_etherscan:
                config['api_keys']['etherscan'] = env_etherscan
                print("✅ 使用环境变量 ETHERSCAN_API_KEY")
            
            # 其他API密钥
            env_coingecko = os.getenv('COINGECKO_API_KEY')
            if env_coingecko and 'coingecko' in config['api_keys']:
                config['api_keys']['coingecko'] = env_coingecko
                print("✅ 使用环境变量 COINGECKO_API_KEY")
        
        return config
    
    @staticmethod
    def check_api_keys(config):
        """检查API密钥是否已配置"""
        issues = []
        
        if 'api_keys' not in config:
            issues.append("❌ 缺少 api_keys 配置")
            return issues
        
        api_keys = config['api_keys']
        
        # 检查 Etherscan API密钥
        etherscan_key = api_keys.get('etherscan', '')
        if not etherscan_key or etherscan_key == 'YOUR_ETHERSCAN_API_KEY_HERE':
            issues.append("⚠️  Etherscan API密钥未配置")
            issues.append("   获取地址: https://etherscan.io/apis")
            issues.append("   设置环境变量: set ETHERSCAN_API_KEY=your_key_here")
        
        if not issues:
            issues.append("✅ API密钥配置检查通过")
        
        return issues

def main():
    """配置管理主函数"""
    print("🔧 配置文件管理工具")
    print("=" * 50)
    
    while True:
        print("\n选择操作:")
        print("1. 从模板创建配置文件")
        print("2. 检查API密钥配置")
        print("3. 加载配置测试")
        print("4. 设置环境变量指导")
        print("0. 退出")
        
        choice = input("\n请选择 (0-4): ").strip()
        
        if choice == '0':
            print("👋 再见！")
            break
        elif choice == '1':
            ConfigManager.create_config_from_template()
        elif choice == '2':
            config = ConfigManager.load_config_with_env()
            issues = ConfigManager.check_api_keys(config)
            for issue in issues:
                print(issue)
        elif choice == '3':
            config = ConfigManager.load_config_with_env()
            print(f"✅ 配置加载成功，包含 {len(config)} 个配置项")
        elif choice == '4':
            print("\n🔐 环境变量设置指导:")
            print("Windows (PowerShell):")
            print("  $env:ETHERSCAN_API_KEY='your_api_key_here'")
            print("Windows (命令提示符):")
            print("  set ETHERSCAN_API_KEY=your_api_key_here")
            print("Linux/Mac:")
            print("  export ETHERSCAN_API_KEY='your_api_key_here'")
            print("\n建议将环境变量添加到系统配置中以便永久生效")
        else:
            print("❌ 无效选项")

if __name__ == '__main__':
    main()
