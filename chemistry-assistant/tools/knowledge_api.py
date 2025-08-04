#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
知识API
封装外部知识库API（如PubChem）
"""

import requests
import json
import time
from typing import Dict, Any, List, Optional
from http import HTTPStatus
from config import EXTERNAL_API_CONFIG
from utils.logger import get_logger

try:
    from dashscope import Application
    DASHSCOPE_AVAILABLE = True
except ImportError:
    DASHSCOPE_AVAILABLE = False
    logger = get_logger(__name__)
    logger.warning("dashscope库未安装，通义百炼知识检索功能将不可用")

logger = get_logger(__name__)

class KnowledgeAPI:
    """
    知识API类
    负责调用外部知识库API获取化学信息
    """
    
    def __init__(self):
        """
        初始化知识API
        """
        self.pubchem_base_url = EXTERNAL_API_CONFIG['pubchem']['base_url']
        
        # Metaso知识库API配置
        self.metaso_config = EXTERNAL_API_CONFIG.get('metaso', {})
        self.metaso_url = self.metaso_config.get('base_url', '')
        self.metaso_api_key = self.metaso_config.get('api_key', '')
        self.metaso_topic_id = self.metaso_config.get('search_topic_id', '')
        self.metaso_timeout = self.metaso_config.get('timeout', 30)
        
        # 通义百炼知识检索智能体API配置
        self.tongyi_app_config = EXTERNAL_API_CONFIG.get('tongyi_knowledge_app', {})
        self.tongyi_api_key = self.tongyi_app_config.get('api_key', '')
        self.tongyi_app_id = self.tongyi_app_config.get('app_id', '')
        self.tongyi_pipeline_ids = self.tongyi_app_config.get('pipeline_ids', [])
        self.tongyi_timeout = self.tongyi_app_config.get('timeout', 30)
    
    def get_compound_info(self, compound):
        """
        获取化合物信息
        
        Args:
            compound (str): 化合物名称或化学式
            
        Returns:
            dict: 化合物信息
        """
        # 首先尝试通过PubChem API获取信息
        pubchem_info = self._query_pubchem(compound)
        if pubchem_info:
            return pubchem_info
        
        # 如果PubChem没有结果，返回基本信息或错误信息
        return {
            'name': compound,
            'error': '未找到化合物信息'
        }
    
    def _query_pubchem(self, compound):
        """
        查询PubChem API获取化合物信息
        
        Args:
            compound (str): 化合物名称或化学式
            
        Returns:
            dict: 化合物信息
        """
        try:
            # 尝试通过名称搜索
            url = f"{self.pubchem_base_url}/compound/name/{compound}/JSON"
            response = requests.get(url)
            
            # 如果名称搜索失败，尝试通过化学式搜索
            if response.status_code != 200:
                url = f"{self.pubchem_base_url}/compound/formula/{compound}/JSON"
                response = requests.get(url)
            
            # 如果仍然失败，返回空结果
            if response.status_code != 200:
                return {}
            
            # 解析响应
            data = response.json()
            
            # 提取化合物信息
            compound_info = {}
            
            # 获取基本信息
            if 'PC_Compounds' in data and len(data['PC_Compounds']) > 0:
                compound_data = data['PC_Compounds'][0]
                
                # 获取化合物ID
                compound_info['cid'] = compound_data.get('id', {}).get('id', {}).get('cid', '')
                
                # 获取分子式
                for prop in compound_data.get('props', []):
                    if prop.get('urn', {}).get('label') == 'Molecular Formula':
                        compound_info['molecular_formula'] = prop.get('value', {}).get('sval', '')
                    elif prop.get('urn', {}).get('label') == 'IUPAC Name':
                        compound_info['iupac_name'] = prop.get('value', {}).get('sval', '')
                    elif prop.get('urn', {}).get('label') == 'Molecular Weight':
                        compound_info['molar_mass'] = prop.get('value', {}).get('fval', 0)
                    elif prop.get('urn', {}).get('label') == 'Melting Point':
                        compound_info['melting_point'] = prop.get('value', {}).get('fval', 0)
                    elif prop.get('urn', {}).get('label') == 'Boiling Point':
                        compound_info['boiling_point'] = prop.get('value', {}).get('fval', 0)
                    elif prop.get('urn', {}).get('label') == 'Density':
                        compound_info['density'] = prop.get('value', {}).get('fval', 0)
            
            # 如果获取到了CID，尝试获取更多信息
            if 'cid' in compound_info and compound_info['cid']:
                # 获取溶解性和危险性信息
                self._enrich_compound_info(compound_info)
            
            return compound_info
            
        except Exception as e:
            print(f"查询PubChem API出错: {e}")
            return {}
    
    def _enrich_compound_info(self, compound_info):
        """
        丰富化合物信息
        
        Args:
            compound_info (dict): 基本化合物信息
            
        Returns:
            dict: 丰富后的化合物信息
        """
        try:
            cid = compound_info['cid']
            
            # 获取溶解性信息
            url = f"{self.pubchem_base_url}/compound/cid/{cid}/property/Solubility/JSON"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                if 'PropertyTable' in data and 'Properties' in data['PropertyTable'] and len(data['PropertyTable']['Properties']) > 0:
                    compound_info['solubility'] = data['PropertyTable']['Properties'][0].get('Solubility', '未知')
            
            # 获取危险性信息
            url = f"{self.pubchem_base_url}/compound/cid/{cid}/property/GHS-Classification/JSON"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                if 'PropertyTable' in data and 'Properties' in data['PropertyTable'] and len(data['PropertyTable']['Properties']) > 0:
                    compound_info['hazards'] = data['PropertyTable']['Properties'][0].get('GHS-Classification', '未知')
            
            return compound_info
            
        except Exception as e:
            print(f"丰富化合物信息出错: {e}")
            return compound_info
    
    def search_reaction(self, reactants=None, products=None):
        """
        搜索化学反应
        
        Args:
            reactants (list, optional): 反应物列表
            products (list, optional): 生成物列表
            
        Returns:
            list: 相关反应列表
        """
        # 这个功能需要更复杂的API调用，这里只是一个示例框架
        # 实际实现可能需要调用专业的反应数据库API
        
        return [{
            'reaction_id': '示例ID',
            'reaction_equation': '示例反应方程式',
            'conditions': '示例反应条件',
            'reference': '示例参考文献'
        }]
    
    def get_element_info(self, element):
        """
        获取元素信息
        
        Args:
            element (str): 元素符号或名称
            
        Returns:
            dict: 元素信息
        """
        try:
            # 尝试通过PubChem API获取元素信息
            url = f"{self.pubchem_base_url}/element/name/{element}/JSON"
            response = requests.get(url)
            
            # 如果名称搜索失败，尝试通过符号搜索
            if response.status_code != 200:
                url = f"{self.pubchem_base_url}/element/symbol/{element}/JSON"
                response = requests.get(url)
            
            # 如果仍然失败，返回空结果
            if response.status_code != 200:
                return {
                    'name': element,
                    'error': '未找到元素信息'
                }
            
            # 解析响应
            data = response.json()
            
            # 提取元素信息
            element_info = {}
            
            # 获取基本信息
            if 'Elements' in data and len(data['Elements']) > 0:
                element_data = data['Elements'][0]
                
                element_info['name'] = element_data.get('Name', '')
                element_info['symbol'] = element_data.get('Symbol', '')
                element_info['atomic_number'] = element_data.get('AtomicNumber', 0)
                element_info['atomic_weight'] = element_data.get('AtomicWeight', 0)
                element_info['electron_configuration'] = element_data.get('ElectronConfiguration', '')
                element_info['oxidation_states'] = element_data.get('OxidationStates', '')
                element_info['group'] = element_data.get('Group', 0)
                element_info['period'] = element_data.get('Period', 0)
                element_info['block'] = element_data.get('Block', '')
                element_info['description'] = element_data.get('Description', '')
            
            return element_info
            
        except Exception as e:
            print(f"获取元素信息出错: {e}")
            return {
                'name': element,
                'error': f'获取信息时出错: {str(e)}'
            }
    
    def search_knowledge_base(self, question: str) -> Dict[str, Any]:
        """
        搜索Metaso知识库
        
        Args:
            question (str): 要搜索的问题
            
        Returns:
            dict: 搜索结果，包含答案和参考文献
        """
        if not self.metaso_url or not self.metaso_api_key or not self.metaso_topic_id:
            logger.warning("Metaso API配置不完整，无法进行知识库搜索")
            return {
                'success': False,
                'error': 'Metaso API配置不完整',
                'answer': '',
                'references': []
            }
        
        try:
            # 准备请求参数
            params = {
                'question': question,
                'searchTopicId': self.metaso_topic_id
            }
            
            # 准备请求头
            headers = {
                'Authorization': f'Bearer {self.metaso_api_key}',
                'Content-Type': 'application/json',
                'Connection': 'keep-alive'
            }
            
            logger.info(f"正在搜索Metaso知识库: {question[:50]}...")
            
            # 发送POST请求
            response = requests.post(
                self.metaso_url,
                data=json.dumps(params),
                headers=headers,
                timeout=self.metaso_timeout
            )
            
            # 检查响应状态
            if response.status_code != 200:
                logger.error(f"Metaso API请求失败，状态码: {response.status_code}")
                return {
                    'success': False,
                    'error': f'API请求失败，状态码: {response.status_code}',
                    'answer': '',
                    'references': []
                }
            
            # 解析响应
            result = response.json()
            
            # 检查API返回的错误码
            if result.get('errCode', 0) != 0:
                error_msg = result.get('errMsg', '未知错误')
                logger.error(f"Metaso API返回错误: {error_msg}")
                return {
                    'success': False,
                    'error': f'API返回错误: {error_msg}',
                    'answer': '',
                    'references': []
                }
            
            # 提取数据
            data = result.get('data', {})
            answer = data.get('text', '')
            references = data.get('references', [])
            result_id = data.get('resultId', '')
            session_id = data.get('sessionId', '')
            balance = data.get('balance', 0)
            
            logger.info(f"Metaso知识库搜索成功，获得{len(references)}个参考文献")
            
            # 格式化参考文献
            formatted_references = []
            for ref in references:
                formatted_ref = {
                    'title': ref.get('title', ''),
                    'author': ref.get('author', ''),
                    'article_type': ref.get('article_type', ''),
                    'page': ref.get('page', 0),
                    'total_page': ref.get('total_page', 0),
                    'publish_date': ref.get('publish_date', ''),
                    'file_type': ref.get('file_meta', {}).get('type', ''),
                    'file_url': ref.get('file_meta', {}).get('url', ''),
                    'refer_id': ref.get('display', {}).get('refer_id', 0)
                }
                formatted_references.append(formatted_ref)
            
            return {
                'success': True,
                'answer': answer,
                'references': formatted_references,
                'result_id': result_id,
                'session_id': session_id,
                'balance': balance,
                'question': question
            }
            
        except requests.exceptions.Timeout:
            logger.error(f"Metaso API请求超时（{self.metaso_timeout}秒）")
            return {
                'success': False,
                'error': f'请求超时（{self.metaso_timeout}秒）',
                'answer': '',
                'references': []
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Metaso API请求异常: {str(e)}")
            return {
                'success': False,
                'error': f'请求异常: {str(e)}',
                'answer': '',
                'references': []
            }
        except json.JSONDecodeError as e:
            logger.error(f"Metaso API响应解析失败: {str(e)}")
            return {
                'success': False,
                'error': f'响应解析失败: {str(e)}',
                'answer': '',
                'references': []
            }
        except Exception as e:
            logger.error(f"Metaso知识库搜索出错: {str(e)}")
            return {
                'success': False,
                'error': f'搜索出错: {str(e)}',
                'answer': '',
                'references': []
            }
    
    def get_comprehensive_info(self, query: str) -> Dict[str, Any]:
        """
        获取综合信息，结合多个知识源
        
        Args:
            query (str): 查询内容
            
        Returns:
            dict: 综合信息结果
        """
        result = {
            'query': query,
            'metaso_result': None,
            'pubchem_result': None,
            'combined_answer': '',
            'all_references': []
        }
        
        # 首先尝试Metaso知识库搜索
        metaso_result = self.search_knowledge_base(query)
        result['metaso_result'] = metaso_result
        
        if metaso_result.get('success'):
            result['combined_answer'] = metaso_result.get('answer', '')
            result['all_references'].extend(metaso_result.get('references', []))
        
        # 如果查询看起来像化合物名称，也尝试PubChem
        if any(keyword in query.lower() for keyword in ['化合物', '分子', '化学式', '摩尔质量', '分子量']):
            # 尝试提取化合物名称
            compound_keywords = ['甲烷', '乙烷', '苯', '水', 'H2O', 'CH4', 'C2H6', 'C6H6']
            for keyword in compound_keywords:
                if keyword in query:
                    pubchem_result = self.get_compound_info(keyword)
                    if pubchem_result and 'error' not in pubchem_result:
                        result['pubchem_result'] = pubchem_result
                        # 将PubChem信息添加到综合答案中
                        if result['combined_answer']:
                            result['combined_answer'] += '\n\n### 补充化合物信息（来自PubChem）:\n'
                        else:
                            result['combined_answer'] = '### 化合物信息（来自PubChem）:\n'
                        
                        if 'molecular_formula' in pubchem_result:
                            result['combined_answer'] += f"分子式: {pubchem_result['molecular_formula']}\n"
                        if 'molar_mass' in pubchem_result:
                            result['combined_answer'] += f"摩尔质量: {pubchem_result['molar_mass']} g/mol\n"
                        if 'iupac_name' in pubchem_result:
                            result['combined_answer'] += f"IUPAC名称: {pubchem_result['iupac_name']}\n"
                    break
        
        return result
    
    def search_tongyi_knowledge(self, prompt: str) -> Dict[str, Any]:
        """
        搜索通义百炼知识检索智能体
        
        Args:
            prompt (str): 搜索提示词/问题
            
        Returns:
            dict: 搜索结果，包含答案和相关信息
        """
        if not DASHSCOPE_AVAILABLE:
            logger.error("dashscope库未安装，无法使用通义百炼知识检索功能")
            return {
                'success': False,
                'error': 'dashscope库未安装',
                'answer': '',
                'usage': None
            }
        
        if not self.tongyi_api_key or not self.tongyi_app_id:
            logger.warning("通义百炼知识检索API配置不完整，无法进行搜索")
            return {
                'success': False,
                'error': '通义百炼API配置不完整',
                'answer': '',
                'usage': None
            }
        
        try:
            logger.info(f"正在搜索通义百炼知识库: {prompt[:50]}...")
            
            # 构建rag_options
            rag_options = {}
            if self.tongyi_pipeline_ids:
                rag_options['pipeline_ids'] = self.tongyi_pipeline_ids
            
            # 调用通义百炼知识检索智能体API
            response = Application.call(
                api_key=self.tongyi_api_key,
                app_id=self.tongyi_app_id,
                prompt=prompt,
                rag_options=rag_options
            )
            
            # 检查响应状态
            if response.status_code != HTTPStatus.OK:
                error_msg = f"请求失败: {response.status_code} - {response.message}"
                logger.error(f"通义百炼API请求失败: {error_msg}")
                logger.error(f"request_id={response.request_id}")
                return {
                    'success': False,
                    'error': error_msg,
                    'answer': '',
                    'usage': None,
                    'request_id': getattr(response, 'request_id', '')
                }
            
            # 提取响应数据
            answer = response.output.text if hasattr(response.output, 'text') else str(response.output)
            usage = getattr(response, 'usage', None)
            request_id = getattr(response, 'request_id', '')
            
            logger.info(f"通义百炼知识库搜索成功，获得答案长度: {len(answer)}字符")
            
            return {
                'success': True,
                'answer': answer,
                'usage': usage,
                'request_id': request_id,
                'prompt': prompt
            }
            
        except Exception as e:
            logger.error(f"通义百炼知识库搜索出错: {str(e)}")
            return {
                'success': False,
                'error': f'搜索出错: {str(e)}',
                'answer': '',
                'usage': None
            }
    
    def get_enhanced_comprehensive_info(self, query: str) -> Dict[str, Any]:
        """
        获取增强的综合信息，结合通义百炼、Metaso和PubChem多个知识源
        
        Args:
            query (str): 查询内容
            
        Returns:
            dict: 综合信息结果
        """
        result = {
            'query': query,
            'tongyi_result': None,
            'metaso_result': None,
            'pubchem_result': None,
            'combined_answer': '',
            'all_sources': []
        }
        
        # 首先尝试通义百炼知识检索智能体
        tongyi_result = self.search_tongyi_knowledge(query)
        result['tongyi_result'] = tongyi_result
        
        if tongyi_result.get('success'):
            result['combined_answer'] = f"### 通义百炼知识库检索结果:\n{tongyi_result.get('answer', '')}\n\n"
            result['all_sources'].append({
                'source': '通义百炼知识库',
                'content': tongyi_result.get('answer', ''),
                'success': True
            })
        
        # 尝试Metaso知识库搜索作为补充
        metaso_result = self.search_knowledge_base(query)
        result['metaso_result'] = metaso_result
        
        if metaso_result.get('success'):
            metaso_answer = metaso_result.get('answer', '')
            if metaso_answer and metaso_answer not in result['combined_answer']:
                result['combined_answer'] += f"### Metaso知识库补充信息:\n{metaso_answer}\n\n"
                result['all_sources'].append({
                    'source': 'Metaso知识库',
                    'content': metaso_answer,
                    'references': metaso_result.get('references', []),
                    'success': True
                })
        
        # 如果查询看起来像化合物名称，也尝试PubChem
        if any(keyword in query.lower() for keyword in ['化合物', '分子', '化学式', '摩尔质量', '分子量', '甲烷', '乙烷', '苯', '水']):
            # 尝试提取化合物名称
            compound_keywords = ['甲烷', '乙烷', '苯', '水', 'H2O', 'CH4', 'C2H6', 'C6H6', '乙醇', 'C2H5OH']
            for keyword in compound_keywords:
                if keyword in query:
                    pubchem_result = self.get_compound_info(keyword)
                    if pubchem_result and 'error' not in pubchem_result:
                        result['pubchem_result'] = pubchem_result
                        
                        pubchem_info = "### PubChem化合物数据库信息:\n"
                        if 'molecular_formula' in pubchem_result:
                            pubchem_info += f"分子式: {pubchem_result['molecular_formula']}\n"
                        if 'molar_mass' in pubchem_result:
                            pubchem_info += f"摩尔质量: {pubchem_result['molar_mass']} g/mol\n"
                        if 'iupac_name' in pubchem_result:
                            pubchem_info += f"IUPAC名称: {pubchem_result['iupac_name']}\n"
                        
                        result['combined_answer'] += pubchem_info + "\n"
                        result['all_sources'].append({
                            'source': 'PubChem数据库',
                            'content': pubchem_info,
                            'success': True
                        })
                    break
        
        # 如果没有获得任何结果，提供默认信息
        if not result['combined_answer']:
            result['combined_answer'] = "抱歉，未能从知识库中找到相关信息。请尝试重新表述您的问题或使用更具体的关键词。"
        
        return result