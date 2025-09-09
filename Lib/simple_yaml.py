"""
简单的YAML解析器 - 作为PyYAML的后备方案
仅支持基本的YAML语法，足以解析我们的配置文件
"""
import re

def simple_yaml_load(yaml_content):
    """
    简单的YAML解析器，支持基本语法：
    - 键值对 (key: value)
    - 嵌套对象
    - 列表
    - 注释 (# 开头的行)
    """
    lines = yaml_content.split('\n')
    result = {}
    current_dict = result
    dict_stack = [result]
    current_indent = 0
    
    for line in lines:
        # 去除注释
        if '#' in line:
            line = line[:line.index('#')]
        
        line = line.rstrip()
        if not line.strip():
            continue
            
        # 计算缩进
        indent = len(line) - len(line.lstrip())
        
        # 处理缩进变化
        if indent < current_indent:
            # 回退到对应的缩进层级
            levels_back = (current_indent - indent) // 2
            for _ in range(levels_back):
                if len(dict_stack) > 1:
                    dict_stack.pop()
            current_dict = dict_stack[-1]
            current_indent = indent
        elif indent > current_indent:
            current_indent = indent
        
        line = line.strip()
        
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            
            if not value:  # 嵌套对象
                new_dict = {}
                current_dict[key] = new_dict
                dict_stack.append(new_dict)
                current_dict = new_dict
            else:
                # 处理不同类型的值
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]  # 移除引号
                elif value.lower() == 'true':
                    value = True
                elif value.lower() == 'false':
                    value = False
                elif value.isdigit():
                    value = int(value)
                elif '.' in value and value.replace('.', '').isdigit():
                    value = float(value)
                    
                current_dict[key] = value
        elif line.startswith('-'):
            # 处理列表项
            item = line[1:].strip()
            if item.startswith('"') and item.endswith('"'):
                item = item[1:-1]
                
            # 如果当前字典的最后一个键没有值，将其设为列表
            if current_dict and list(current_dict.keys()):
                last_key = list(current_dict.keys())[-1]
                if not isinstance(current_dict[last_key], list):
                    current_dict[last_key] = []
                current_dict[last_key].append(item)
    
    return result

def safe_load(stream):
    """兼容PyYAML的接口"""
    if hasattr(stream, 'read'):
        content = stream.read()
    else:
        content = stream
    return simple_yaml_load(content)

# 测试函数
if __name__ == '__main__':
    test_yaml = """
    # 测试配置
    api_keys:
      etherscan: "test_key"
    
    cache:
      enabled: true
      duration_minutes: 5
    
    tokens:
      - BTC
      - ETH
    """
    result = simple_yaml_load(test_yaml)
    print("解析结果:", result)
