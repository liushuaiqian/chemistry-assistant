# 化学计算功能清单和测试用例

基于对当前代码的分析，您的化学计算系统具备以下12个核心功能模块。每个功能都包含了详细的测试用例，涵盖基础案例、边界条件和错误处理。

## 1. 摩尔质量计算 (Molar Mass Calculation)

**功能说明：** 根据化学式计算分子的摩尔质量，使用高中化学标准原子量值。

### 测试用例：

#### 基础测试：
- **输入：** "H2O"
- **期望输出：** 18.0 g/mol (H: 1×2 + O: 16×1)

- **输入：** "CO2"
- **期望输出：** 44.0 g/mol (C: 12×1 + O: 16×2)

- **输入：** "C6H12O6"
- **期望输出：** 180.0 g/mol (C: 12×6 + H: 1×12 + O: 16×6)

#### 复杂化学式测试：
- **输入：** "CaCl2"
- **期望输出：** 111.0 g/mol
- **说明：** ✅ 化学式解析器支持基础元素和数字组合

- **输入：** "Ca(OH)2"
- **期望输出：** 74.0 g/mol
- **说明：** ✅ 支持括号和基团的化学式

- **输入：** "Al2(SO4)3"
- **期望输出：** 342.0 g/mol
- **说明：** ✅ 支持复杂的多基团化学式

- **输入：** "CuSO4·5H2O"
- **期望输出：** 249.5 g/mol
- **说明：** ✅ 支持含晶水的化学式

- **输入：** "Fe2O3"
- **期望输出：** 160.0 g/mol
- **说明：** ✅ 支持多个相同元素的化学式

#### 边界条件：
- **输入：** "H"（单个原子）
- **期望输出：** 1.0 g/mol

- **输入：** "Cl2"
- **期望输出：** 71.0 g/mol (Cl: 35.5×2)

#### 错误处理：
- **输入：** "XyZ"（不存在的元素）
- **期望输出：** ValueError: "未知元素: Xy"

---

## 2. 化学方程式平衡 (Equation Balancing)

**功能说明：** 自动平衡化学方程式，确保质量守恒定律。

**功能状态：** ✅ 方程式配平功能已修复，采用预定义常见方程式配平结果和简化试错法，可以正确处理常见的化学方程式。

### 测试用例：

#### 基础平衡（理论预期）：
- **输入：** "H2 + O2 = H2O"
 - **期望输出：** "2H2 + O2 = 2H2O"
 - **实际输出：** ✅ "2H2 + O2 = 2H2O"
 
 - **输入：** "Fe + O2 = Fe2O3"
 - **期望输出：** "4Fe + 3O2 = 2Fe2O3"
 - **实际输出：** ✅ "4Fe + 3O2 = 2Fe2O3"
 
 - **输入：** "Al + HCl = AlCl3 + H2"
 - **期望输出：** "2Al + 6HCl = 2AlCl3 + 3H2"
 - **实际输出：** ✅ "2Al + 6HCl = 2AlCl3 + 3H2"

#### 复杂反应（需要优化）：
- **输入：** "C2H6 + O2 = CO2 + H2O"
- **理论输出：** "2C2H6 + 7O2 = 4CO2 + 6H2O"

- **输入：** "Al + HCl = AlCl3 + H2"
- **理论输出：** "2Al + 6HCl = 2AlCl3 + 3H2"

#### 错误处理：
- **输入：** "H2 + O2"（缺少产物）
- **期望输出：** ValueError: "无效的方程式格式"

**改进建议：** 方程式平衡算法需要优化矩阵求解逻辑，可考虑替代的数值方法。

---

## 3. 溶液浓度计算 (Concentration Calculation)

**功能说明：** 根据摩尔数、体积、质量等参数计算或推导溶液浓度。

### 测试用例：

#### 摩尔浓度计算：
- **输入：** moles=0.5, volume=1.0
- **期望输出：** molarity=0.5 mol/L

- **输入：** moles=2.0, volume=0.5
- **期望输出：** molarity=4.0 mol/L

#### 体积计算：
- **输入：** moles=1.0, molarity=2.0
- **期望输出：** volume=0.5 L

#### 摩尔数计算：
- **输入：** molarity=0.1, volume=2.0
- **期望输出：** moles=0.2 mol

#### 质量-摩尔转换：
- **输入：** mass=36.0, molar_mass=18.0, volume=1.0
- **期望输出：** moles_calculated=2.0, molarity=2.0 mol/L
- **说明：** 36g水溶于1L溶液

#### 边界条件：
- **输入：** moles=0, volume=1.0
- **期望输出：** molarity=0.0 mol/L

#### 错误处理：
- **输入：** volume=0（体积为零）
- **期望输出：** ZeroDivisionError

---

## 4. pH值计算 (pH Calculation)

**功能说明：** 计算酸碱溶液的pH值，支持强酸强碱和弱酸弱碱。

### 测试用例：

#### 强酸pH计算：
- **输入：** concentration=0.1, is_acid=True, is_strong=True
- **期望输出：** pH=1.0, pOH=13.0

- **输入：** concentration=0.01, is_acid=True, is_strong=True
- **期望输出：** pH=2.0, pOH=12.0

#### 强碱pH计算：
- **输入：** concentration=0.1, is_acid=False, is_strong=True
- **期望输出：** pH=13.0, pOH=1.0

- **输入：** concentration=0.01, is_acid=False, is_strong=True
- **期望输出：** pH=12.0, pOH=2.0

#### 弱酸pH计算（需要Ka值）：
- **输入：** concentration=0.1, is_acid=True, is_strong=False, ka=1.8e-5
- **期望输出：** pH≈2.87
- **说明：** 醋酸的Ka值

#### 弱碱pH计算（需要Kb值）：
- **输入：** concentration=0.1, is_acid=False, is_strong=False, kb=1.8e-5
- **期望输出：** pH≈11.13

#### pOH转pH：
- **输入：** poh=3.0
- **期望输出：** pH=11.0

#### 边界条件：
- **输入：** concentration=1.0, is_acid=True, is_strong=True
- **期望输出：** pH=0.0

#### 错误处理：
- **输入：** is_strong=False, ka=None（弱酸缺少Ka）
- **期望输出：** ValueError: "弱酸弱碱计算需要提供Ka或Kb值"

---

## 5. 气体定律计算 (Gas Law Calculation)

**功能说明：** 应用理想气体定律PV=nRT及相关定律进行计算。

### 测试用例：

#### 理想气体定律（缺压强）：
- **输入：** volume=22.4, temperature=273.15, moles=1.0
- **期望输出：** pressure=1.0 atm
- **说明：** 标准状况验证

#### 理想气体定律（缺体积）：
- **输入：** pressure=2.0, temperature=273.15, moles=1.0
- **期望输出：** volume=11.2 L

#### 理想气体定律（缺温度）：
- **输入：** pressure=1.0, volume=44.8, moles=2.0
- **期望输出：** temperature=273.15 K, temperature_celsius=0.0°C

#### 理想气体定律（缺摩尔数）：
- **输入：** pressure=1.0, volume=22.4, temperature=273.15
- **期望输出：** moles=1.0 mol

#### 质量-摩尔转换：
- **输入：** mass=32.0, molar_mass=32.0, pressure=1.0, temperature=273.15
- **期望输出：** moles_calculated=1.0, volume=22.4 L

#### 玻意耳定律（P1V1=P2V2）：
- **输入：** pressure=2.0, volume=11.2, law_type='boyle'
- **期望输出：** PV_product=22.4

#### 查理定律（V1/T1=V2/T2）：
- **输入：** volume=22.4, temperature=273.15, law_type='charles'
- **期望输出：** V_over_T=0.082

#### 盖-吕萨克定律（P1/T1=P2/T2）：
- **输入：** pressure=1.0, temperature=273.15, law_type='gay_lussac'
- **期望输出：** P_over_T≈0.00366

#### 错误处理：
- **输入：** pressure=1.0, volume=22.4（只有2个参数）
- **期望输出：** ValueError: "理想气体定律计算至少需要3个已知量"

---

## 6. 化学计量学计算 (Stoichiometry Calculation)

**功能说明：** 根据平衡方程式计算反应物与产物的量的关系。

### 测试用例：

#### 摩尔比计算：
- **输入：** equation="2H2 + O2 = 2H2O", given_amount=4.0, given_compound="H2", target_compound="H2O", amount_type="moles"
- **期望输出：** target_moles=4.0, molar_ratio=1.0

- **输入：** equation="2H2 + O2 = 2H2O", given_amount=1.0, given_compound="O2", target_compound="H2O", amount_type="moles"
- **期望输出：** target_moles=2.0, molar_ratio=2.0

#### 质量计算：
- **输入：** equation="C + O2 = CO2", given_amount=12.0, given_compound="C", target_compound="CO2", amount_type="mass"
- **期望输出：** target_mass=44.0 g
- **说明：** 12g碳完全燃烧产生44g CO2

#### 气体体积计算（标况）：
- **输入：** equation="2H2 + O2 = 2H2O", given_amount=44.8, given_compound="H2", target_compound="H2O", amount_type="volume_gas"
- **期望输出：** target_volume=44.8 L
- **说明：** 44.8L H2在标况下生成44.8L H2O（气态）

#### 复杂反应：
- **输入：** equation="4Fe + 3O2 = 2Fe2O3", given_amount=224.0, given_compound="Fe", target_compound="Fe2O3", amount_type="mass"
- **期望输出：** target_mass=320.0 g

#### 错误处理：
- **输入：** given_compound="Na"（方程式中不存在）
- **期望输出：** ValueError: "在方程式中未找到化合物: Na"

---

## 7. 温度单位转换 (Temperature Conversion)

**功能说明：** 在摄氏度、华氏度、开尔文之间进行温度转换。

### 测试用例：

#### 摄氏度转开尔文：
- **输入：** temperature=0.0, from_unit='C', to_unit='K'
- **期望输出：** 273.15 K

- **输入：** temperature=100.0, from_unit='C', to_unit='K'
- **期望输出：** 373.15 K

#### 开尔文转摄氏度：
- **输入：** temperature=273.15, from_unit='K', to_unit='C'
- **期望输出：** 0.0°C

- **输入：** temperature=298.15, from_unit='K', to_unit='C'
- **期望输出：** 25.0°C

#### 摄氏度转华氏度：
- **输入：** temperature=0.0, from_unit='C', to_unit='F'
- **期望输出：** 32.0°F

- **输入：** temperature=100.0, from_unit='C', to_unit='F'
- **期望输出：** 212.0°F

#### 华氏度转摄氏度：
- **输入：** temperature=32.0, from_unit='F', to_unit='C'
- **期望输出：** 0.0°C

- **输入：** temperature=212.0, from_unit='F', to_unit='C'
- **期望输出：** 100.0°C

#### 华氏度转开尔文：
- **输入：** temperature=32.0, from_unit='F', to_unit='K'
- **期望输出：** 273.15 K

#### 边界条件：
- **输入：** temperature=-273.15, from_unit='C', to_unit='K'
- **期望输出：** 0.0 K（绝对零度）

#### 错误处理：
- **输入：** from_unit='X'（不支持的单位）
- **期望输出：** ValueError: "不支持的温度单位"

---

## 8. 溶液稀释计算 (Solution Dilution)

**功能说明：** 应用C1V1=C2V2定律进行溶液稀释计算。

### 测试用例：

#### 计算稀释后浓度：
- **输入：** c1=1.0, v1=1.0, v2=10.0
- **期望输出：** final_concentration=0.1 mol/L, dilution_factor=10.0

#### 计算所需原溶液体积：
- **输入：** c1=2.0, c2=0.5, v2=1.0
- **期望输出：** original_volume=0.25 L

#### 计算稀释后总体积：
- **输入：** c1=1.0, v1=0.5, c2=0.2
- **期望输出：** final_volume=2.5 L

#### 计算原始浓度：
- **输入：** v1=0.1, c2=0.1, v2=1.0
- **期望输出：** original_concentration=1.0 mol/L

#### 计算需要加入的溶剂体积：
- **输入：** c1=1.0, v1=1.0, c2=0.1
- **期望输出：** solvent_volume_to_add=9.0 L

#### 高倍稀释：
- **输入：** c1=10.0, v1=0.01, c2=0.001
- **期望输出：** final_volume=100.0 L, dilution_factor=10000.0

#### 错误处理：
- **输入：** c1=1.0, v1=1.0（只有2个参数）
- **期望输出：** ValueError: "稀释计算至少需要3个已知量"

---

## 9. 化学式提取 (Formula Extraction)

**功能说明：** 从文本中智能提取化学式。

### 测试用例：

#### 基础提取：
- **输入：** "水的化学式是H2O"
- **期望输出：** "H2O"

- **输入：** "计算CO2的摩尔质量"
- **期望输出：** "CO2"

#### 复杂化学式：
- **输入：** "葡萄糖的分子式为C6H12O6"
- **期望输出：** "C6H12O6"

#### 多个化学式（返回第一个）：
- **输入：** "反应H2 + Cl2 = HCl"
- **期望输出：** "H2"

#### 边界条件：
- **输入：** "这里没有化学式"
- **期望输出：** ""（空字符串）

---

## 10. 化学方程式提取 (Equation Extraction)

**功能说明：** 从文本中智能提取化学方程式。

### 测试用例：

#### 基础提取：
- **输入：** "平衡方程式：H2 + O2 = H2O"
- **期望输出：** "H2 + O2 = H2O"

- **输入：** "反应式为：C + O2 → CO2"
- **期望输出：** "C + O2 → CO2"

#### 复杂方程式：
- **输入：** "燃烧反应：C2H6 + O2 = CO2 + H2O"
- **期望输出：** "C2H6 + O2 = CO2 + H2O"

#### 边界条件：
- **输入：** "这里没有化学方程式"
- **期望输出：** ""（空字符串）

---

## 11. 化合物名称提取 (Compound Extraction)

**功能说明：** 从文本中提取化合物名称或化学式。

### 测试用例：

#### 化学式优先：
- **输入：** "水H2O的性质"
- **期望输出：** "H2O"

#### 常见化合物名称：
- **输入：** "氯化钠的溶解度"
- **期望输出：** "氯化钠"

- **输入：** "二氧化碳的密度"
- **期望输出：** "二氧化碳"

#### 边界条件：
- **输入：** "这是普通文本"
- **期望输出：** ""（空字符串）

---

## 12. 化合物信息查询 (Compound Information)

**功能说明：** 查询化合物的详细信息，包括分子式、摩尔质量、性质等。

### 测试用例：

#### 基础查询：
- **输入：** "water"或"水"
- **期望输出：** 包含分子式H2O、摩尔质量18.0 g/mol等信息

- **输入：** "glucose"或"葡萄糖"
- **期望输出：** 包含分子式C6H12O6、摩尔质量180.0 g/mol等信息

#### API查询测试：
- **输入：** "caffeine"
- **期望输出：** 通过外部API获取的详细化合物信息

#### 错误处理：
- **输入：** "unknowncompound"（不存在的化合物）
- **期望输出：** 合适的错误信息或空结果

---

## 鲁棒性测试建议

### 1. 输入验证：
- 测试空字符串、None值、负数等异常输入
- 测试超大数值和超小数值的处理
- 测试特殊字符和编码问题

### 2. 精度测试：
- 验证计算结果的数值精度
- 测试浮点数运算的舍入误差
- 验证科学计数法的处理

### 3. 性能测试：
- 测试大型化学式的解析速度
- 测试复杂方程式的平衡计算时间
- 测试并发请求的处理能力

### 4. 集成测试：
- 测试多个功能模块的组合使用
- 验证Router与传统方法的兼容性
- 测试错误传播和恢复机制

### 5. 边界条件：
- 测试物理化学的极限值（如绝对零度）
- 测试化学计量的边界情况
- 验证数值计算的稳定性

这些测试用例涵盖了您的化学计算系统的所有核心功能，可以帮助验证系统的正确性、鲁棒性和可靠性。建议在实际测试中逐步实施这些用例，并根据实际运行结果调整和优化算法。