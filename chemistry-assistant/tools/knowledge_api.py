#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
知识API
封装外部知识库API（如PubChem）
"""

import requests
import json
from config import EXTERNAL_API_CONFIG

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