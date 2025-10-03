# Secuflow Backend Test Suite

这是Secuflow后端应用的统一测试套件。所有测试都组织在这个目录下，提供更好的结构和可维护性。

## 📁 目录结构

```
tests/
├── __init__.py              # 测试包初始化
├── conftest.py              # Pytest配置和共享fixtures
├── pytest.ini              # Pytest配置文件
├── test_runner.py           # 自定义测试运行器
├── README.md               # 本文件
├── unit/                   # 单元测试
│   ├── __init__.py
│   ├── test_accounts.py    # 账户模块单元测试
│   ├── test_stc_analysis.py # STC分析单元测试
│   └── ...
├── integration/            # 集成测试
│   ├── __init__.py
│   ├── test_stc_workflow.py # STC分析工作流测试
│   └── ...
├── api/                    # API测试
│   ├── __init__.py
│   ├── test_projects_api.py # 项目API测试
│   └── ...
├── fixtures/               # 测试数据和fixtures
│   ├── __init__.py
│   ├── sample_data.py      # 示例数据
│   └── ...
└── utils/                  # 测试工具和助手
    ├── __init__.py
    ├── test_helpers.py     # 测试助手函数
    └── ...
```

## 🚀 运行测试

### 基本用法

```bash
# 运行所有测试
python manage.py test tests

# 运行特定模块的测试
python manage.py test tests.unit.test_accounts

# 运行特定测试类
python manage.py test tests.unit.test_accounts.UserModelTests

# 运行特定测试方法
python manage.py test tests.unit.test_accounts.UserModelTests.test_create_user
```

### 按类型运行测试

```bash
# 运行单元测试
python manage.py test tests.unit

# 运行集成测试
python manage.py test tests.integration

# 运行API测试
python manage.py test tests.api
```

### 使用自定义测试运行器

```bash
# 使用自定义运行器
python tests/test_runner.py

# 运行特定测试
python tests/test_runner.py tests.unit.test_accounts

# 运行测试并生成覆盖率报告
python tests/test_runner.py --coverage
```

### 在Docker中运行

```bash
# 在Docker容器中运行所有测试
docker-compose exec backend python manage.py test tests

# 运行特定测试
docker-compose exec backend python manage.py test tests.unit
```

## 📊 测试覆盖率

### 安装覆盖率工具

```bash
pip install coverage
```

### 生成覆盖率报告

```bash
# 运行测试并收集覆盖率数据
coverage run --source='.' manage.py test tests

# 生成控制台报告
coverage report

# 生成HTML报告
coverage html

# 查看HTML报告
open htmlcov/index.html
```

## 🧪 测试类型说明

### 单元测试 (Unit Tests)
- 测试单个函数、方法或类
- 不依赖外部系统
- 运行速度快
- 位置：`tests/unit/`

### 集成测试 (Integration Tests)
- 测试模块之间的交互
- 可能涉及数据库操作
- 测试完整的工作流程
- 位置：`tests/integration/`

### API测试 (API Tests)
- 测试REST API端点
- 包括认证、权限、响应验证
- 使用APITestCase
- 位置：`tests/api/`

## 🛠️ 测试工具和助手

### BaseTestCase
所有测试的基类，提供常用的测试数据设置：

```python
from tests.conftest import BaseTestCase

class MyTests(BaseTestCase):
    def test_something(self):
        # self.user, self.project 等已经设置好
        pass
```

### APITestMixin
提供API测试的便利方法：

```python
from tests.utils.test_helpers import APITestMixin

class MyAPITests(APITestMixin, APITestCase):
    def test_api_endpoint(self):
        client = self.get_authenticated_client(self.user)
        response = client.get('/api/some-endpoint/')
        self.assert_api_success(response)
```

### SampleDataMixin
提供示例数据生成：

```python
from tests.fixtures.sample_data import SampleDataMixin

class MyTests(SampleDataMixin, TestCase):
    def test_with_sample_data(self):
        users = self.create_sample_users()
        projects = self.create_sample_projects(users[0][1])
```

## 📝 编写测试的最佳实践

### 1. 测试命名
- 测试文件：`test_<module_name>.py`
- 测试类：`<Module>Tests` 或 `Test<Module>`
- 测试方法：`test_<what_it_tests>`

### 2. 测试结构
```python
def test_something(self):
    # Arrange - 设置测试数据
    user = User.objects.create_user(...)
    
    # Act - 执行被测试的操作
    result = some_function(user)
    
    # Assert - 验证结果
    self.assertEqual(result, expected_value)
```

### 3. 使用fixtures和助手
```python
# 好的做法
class MyTests(BaseTestCase):
    def test_something(self):
        # 使用预设的self.user和self.project
        pass

# 避免重复设置
class MyTests(TestCase):
    def setUp(self):
        # 每个测试类都重复相同的设置
        pass
```

### 4. 测试隔离
- 每个测试应该独立运行
- 不依赖其他测试的结果
- 使用setUp和tearDown清理数据

### 5. 模拟外部依赖
```python
from unittest.mock import patch

@patch('some_module.external_service')
def test_with_mock(self, mock_service):
    mock_service.return_value = 'mocked_result'
    # 测试代码
```

## 🔧 配置和环境

### 测试设置
测试使用独立的设置文件和数据库：
- 设置文件：`secuflow.config.settings.local`
- 数据库：SQLite内存数据库（测试时）
- TNM目录：临时目录

### 环境变量
- `ENABLE_TEST_LOGGING`: 启用测试期间的日志输出
- `DJANGO_SETTINGS_MODULE`: Django设置模块

## 📈 持续集成

### GitHub Actions示例
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install coverage
      - name: Run tests
        run: |
          cd backend
          python tests/test_runner.py --coverage
```

## 🐛 调试测试

### 运行单个测试并查看详细输出
```bash
python manage.py test tests.unit.test_accounts.UserModelTests.test_create_user --verbosity=2
```

### 使用pdb调试
```python
def test_something(self):
    import pdb; pdb.set_trace()
    # 测试代码
```

### 保留测试数据库
```bash
python manage.py test tests --keepdb
```

## 📚 相关资源

- [Django测试文档](https://docs.djangoproject.com/en/4.2/topics/testing/)
- [Django REST Framework测试](https://www.django-rest-framework.org/api-guide/testing/)
- [Pytest文档](https://docs.pytest.org/)
- [Coverage.py文档](https://coverage.readthedocs.io/)

---

如有问题或建议，请联系开发团队。
