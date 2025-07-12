#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
嵌入模型模式切换脚本
用于在本地模型和API模型之间切换
"""

import sys
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def update_config_file(use_api=True, api_provider='zhipu', api_model='embedding-2'):
    """
    更新配置文件中的嵌入模型设置
    """
    config_file = project_root / 'config.py'
    
    try:
        # 读取配置文件
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找嵌入配置部分
        lines = content.split('\n')
        new_lines = []
        in_embedding_section = False
        embedding_section_indent = ''
        
        for line in lines:
            if "'embedding': {" in line:
                in_embedding_section = True
                embedding_section_indent = line[:line.index("'embedding'")]
                new_lines.append(line)
                continue
            
            if in_embedding_section:
                if line.strip() == '}' and line.startswith(embedding_section_indent):
                    # 结束嵌入配置部分，写入新配置
                    indent = embedding_section_indent + '    '
                    new_lines.append(f"{indent}'model_name': 'bge-large-zh-v1.5',  # 本地模型名称（备用）")
                    new_lines.append(f"{indent}'device': 'cpu',")
                    new_lines.append(f"{indent}'use_api': {use_api},  # 是否使用API模式")
                    new_lines.append(f"{indent}'api_provider': '{api_provider}',  # API提供商: 'zhipu', 'tongyi', 'baichuan'")
                    new_lines.append(f"{indent}'api_model': '{api_model}',  # API模型名称")
                    new_lines.append(line)
                    in_embedding_section = False
                    continue
                else:
                    # 跳过原有的嵌入配置行
                    continue
            
            new_lines.append(line)
        
        # 写回配置文件
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))
        
        print(f"✅ 配置文件已更新")
        return True
        
    except Exception as e:
        print(f"❌ 更新配置文件失败: {e}")
        return False

def show_current_config():
    """
    显示当前配置
    """
    try:
        from config import MODEL_CONFIG
        embedding_config = MODEL_CONFIG.get('embedding', {})
        
        print("当前嵌入模型配置:")
        print(f"  使用API: {embedding_config.get('use_api', False)}")
        print(f"  本地模型: {embedding_config.get('model_name', 'N/A')}")
        print(f"  设备: {embedding_config.get('device', 'N/A')}")
        print(f"  API提供商: {embedding_config.get('api_provider', 'N/A')}")
        print(f"  API模型: {embedding_config.get('api_model', 'N/A')}")
        
        # 检查API密钥状态
        api_provider = embedding_config.get('api_provider', '')
        if api_provider:
            provider_config = MODEL_CONFIG.get(api_provider, {})
            api_key = provider_config.get('api_key', '')
            print(f"  API密钥状态: {'已配置' if api_key else '未配置'}")
        
    except Exception as e:
        print(f"❌ 读取配置失败: {e}")

def switch_to_api(provider='zhipu', model=None):
    """
    切换到API模式
    """
    print(f"切换到API模式: {provider}")
    
    # 设置默认模型
    if model is None:
        if provider == 'zhipu':
            model = 'embedding-2'
        elif provider == 'tongyi':
            model = 'text-embedding-v1'
        elif provider == 'baichuan':
            model = 'Baichuan-Text-Embedding'
        else:
            model = 'embedding-2'
    
    if update_config_file(use_api=True, api_provider=provider, api_model=model):
        print(f"✅ 已切换到 {provider} API模式")
        print(f"📝 使用模型: {model}")
        print("\n建议执行以下命令更新知识库:")
        print("python update_knowledge_base.py --mode all")
        return True
    return False

def switch_to_local():
    """
    切换到本地模式
    """
    print("切换到本地模式")
    
    if update_config_file(use_api=False):
        print("✅ 已切换到本地模式")
        print("📝 将使用本地模型: bge-large-zh-v1.5")
        print("\n建议执行以下命令更新知识库:")
        print("python update_knowledge_base.py --mode all")
        return True
    return False

def test_current_config():
    """
    测试当前配置
    """
    print("测试当前嵌入模型配置...")
    
    try:
        from models.embedding_model import EmbeddingModel
        
        model = EmbeddingModel()
        test_text = "这是一个测试文本"
        embedding = model.get_embedding(test_text)
        
        print(f"✅ 嵌入模型测试成功")
        print(f"📊 向量维度: {len(embedding)}")
        print(f"📝 测试文本: {test_text}")
        
        return True
        
    except Exception as e:
        print(f"❌ 嵌入模型测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    parser = argparse.ArgumentParser(description='嵌入模型模式切换脚本')
    parser.add_argument('--mode', choices=['api', 'local', 'status', 'test'], 
                       required=True, help='操作模式')
    parser.add_argument('--provider', choices=['zhipu', 'tongyi', 'baichuan'], 
                       default='zhipu', help='API提供商（仅在api模式下有效）')
    parser.add_argument('--model', type=str, help='API模型名称（可选）')
    
    args = parser.parse_args()
    
    print("嵌入模型模式切换工具")
    print("=" * 40)
    
    try:
        if args.mode == 'status':
            show_current_config()
        elif args.mode == 'test':
            test_current_config()
        elif args.mode == 'api':
            switch_to_api(args.provider, args.model)
        elif args.mode == 'local':
            switch_to_local()
        
    except Exception as e:
        print(f"❌ 操作失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()