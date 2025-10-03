# 测试迁移指南

## 📋 概述

我们已经成功创建了统一的测试文件夹结构，将所有测试集中管理。这个指南说明了如何从旧的分散测试结构迁移到新的统一结构。

## 🏗️ 新的测试结构

```
backend/tests/
├── __init__.py              # 测试包初始化
├── conftest.py              # 共享fixtures和配置
├── pytest.ini              # Pytest配置
├── test_runner.py           # 自定义测试运行器
├── README.md               # 使用文档
├── MIGRATION_GUIDE.md      # 本迁移指南
├── unit/                   # 单元测试
│   ├── test_accounts.py    # ✅ 已完成
│   ├── test_stc_analysis.py # ✅ 已完成
│   ├── test_projects.py    # 待迁移
│   ├── test_contributors.py # 待迁移
│   └── test_project_monitoring.py # 待迁移
├── integration/            # 集成测试
│   ├── test_stc_workflow.py # ✅ 已完成
│   └── test_full_workflow.py # 待创建
├── api/                    # API测试
│   ├── test_projects_api.py # ✅ 已完成
│   ├── test_stc_api.py     # 待迁移
│   ├── test_contributors_api.py # 待迁移
│   └── test_monitoring_api.py # 待迁移
├── fixtures/               # 测试数据
│   ├── sample_data.py      # ✅ 已完成
│   └── tnm_samples.py      # 待创建
└── utils/                  # 测试工具
    ├── test_helpers.py     # ✅ 已完成
    └── mock_helpers.py     # 待创建
```

## 📊 迁移状态

### ✅ 已完成的迁移

| 原文件位置 | 新文件位置 | 状态 | 测试通过 |
|-----------|-----------|------|----------|
| - | `tests/unit/test_accounts.py` | ✅ 新建 | ✅ 6/6 |
| - | `tests/unit/test_stc_analysis.py` | ✅ 新建 | ✅ 8/8 |
| - | `tests/api/test_projects_api.py` | ✅ 新建 | ⚠️ 部分失败 |
| - | `tests/integration/test_stc_workflow.py` | ✅ 新建 | ⚠️ 部分失败 |

### 🔄 待迁移的文件

| 原文件位置 | 新文件位置 | 优先级 |
|-----------|-----------|--------|
| `accounts/tests.py` | `tests/unit/test_accounts.py` | 🔄 已部分迁移 |
| `stc_analysis/test_*.py` | `tests/unit/test_stc_analysis.py` | 🔄 已部分迁移 |
| `project_monitoring/tests.py` | `tests/unit/test_project_monitoring.py` | 🔴 高 |
| `projects/test_cleanup.py` | `tests/unit/test_projects.py` | 🔴 高 |
| `stc_analysis/test_views.py` | `tests/api/test_stc_api.py` | 🟡 中 |
| `contributors/` 相关测试 | `tests/unit/test_contributors.py` | 🟡 中 |

## 🚀 迁移步骤

### 1. 迁移现有测试文件

```bash
# 示例：迁移 project_monitoring 测试
# 1. 复制现有测试内容
cp backend/project_monitoring/tests.py backend/tests/unit/test_project_monitoring.py

# 2. 更新导入语句
# 将 from tests.conftest import BaseTestCase 添加到新文件
# 更新其他相对导入

# 3. 继承 BaseTestCase
# 将 TestCase 改为 BaseTestCase

# 4. 运行测试验证
docker-compose exec backend python manage.py test tests.unit.test_project_monitoring
```

### 2. 更新导入语句

**旧的导入方式：**
```python
from django.test import TestCase
from accounts.models import User, UserProfile
from projects.models import Project
```

**新的导入方式：**
```python
from tests.conftest import BaseTestCase
from tests.fixtures.sample_data import SampleDataMixin
from tests.utils.test_helpers import APITestMixin
```

### 3. 使用共享的测试基类

**旧的测试类：**
```python
class MyTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(...)
        self.project = Project.objects.create(...)
```

**新的测试类：**
```python
class MyTests(BaseTestCase):
    # setUp 已在 BaseTestCase 中完成
    # self.user, self.project 等已可用
    def test_something(self):
        # 直接使用 self.user, self.project
        pass
```

## 🛠️ 迁移工具和助手

### BaseTestCase
提供常用的测试数据设置：
- `self.admin_user` / `self.admin_profile`
- `self.user` / `self.user_profile` 
- `self.other_user` / `self.other_profile`
- `self.project`

### APITestMixin
提供API测试便利方法：
- `get_authenticated_client(user)`
- `assert_api_success(response)`
- `assert_api_error(response)`

### SampleDataMixin
提供示例数据生成：
- `create_sample_users()`
- `create_sample_projects()`
- `get_sample_tnm_files()`

## 📝 迁移检查清单

### 对于每个迁移的测试文件：

- [ ] 更新导入语句
- [ ] 继承适当的基类（BaseTestCase, APITestMixin等）
- [ ] 移除重复的setUp代码
- [ ] 使用共享的fixtures和助手
- [ ] 运行测试确保通过
- [ ] 更新测试文档

### 对于API测试：

- [ ] 使用 `APITestMixin`
- [ ] 使用 `get_authenticated_client()`
- [ ] 使用 `assert_api_success()` / `assert_api_error()`
- [ ] 检查响应格式（JSON vs DRF分页）

### 对于集成测试：

- [ ] 使用 `MockTNMOutputMixin` 模拟TNM输出
- [ ] 使用 `FileSystemTestMixin` 处理临时文件
- [ ] 测试完整的工作流程

## 🔧 常见问题和解决方案

### 1. 导入错误
**问题：** `ModuleNotFoundError: No module named 'tests.conftest'`
**解决：** 确保在 `backend/` 目录下运行测试

### 2. 测试数据冲突
**问题：** `IntegrityError: Duplicate entry`
**解决：** 使用 BaseTestCase 提供的共享数据，或创建新的测试用户

### 3. API响应格式不匹配
**问题：** `KeyError: 'data'` 或 `AttributeError: 'JsonResponse' object has no attribute 'data'`
**解决：** 
- DRF分页响应：使用 `response.json()['results']`
- ApiResponse格式：使用 `response.json()['data']`

### 4. 文件路径问题
**问题：** 测试中的文件路径不正确
**解决：** 使用 `FileSystemTestMixin` 和临时目录

## 📈 迁移后的好处

### 1. 统一管理
- 所有测试集中在 `tests/` 目录
- 清晰的分类结构（unit/integration/api）
- 统一的运行方式

### 2. 代码复用
- 共享的测试基类和fixtures
- 减少重复的setUp代码
- 统一的测试工具和助手

### 3. 更好的维护性
- 清晰的测试组织
- 更容易找到和修改测试
- 更好的测试覆盖率跟踪

### 4. CI/CD友好
- 统一的测试运行命令
- 更好的测试报告
- 更容易的覆盖率统计

## 🎯 下一步计划

1. **完成核心模块迁移**
   - project_monitoring 测试
   - projects 测试
   - contributors 测试

2. **创建更多集成测试**
   - 完整的STC分析工作流
   - 项目监控工作流
   - 用户权限测试

3. **优化测试工具**
   - 更多的测试助手函数
   - 更好的模拟工具
   - 性能测试工具

4. **文档完善**
   - 更详细的使用示例
   - 最佳实践指南
   - 故障排除指南

---

## 📞 需要帮助？

如果在迁移过程中遇到问题，请参考：
1. `tests/README.md` - 详细使用文档
2. `tests/unit/test_accounts.py` - 单元测试示例
3. `tests/api/test_projects_api.py` - API测试示例
4. `tests/integration/test_stc_workflow.py` - 集成测试示例
