# STC API 实现总结

## 已完成的工作

### 1. 创建的文件

#### `serializers.py` - API 序列化器
- **STCAnalysisSerializer**: 用于 STC 分析模型的序列化
- **STCAnalysisCreateSerializer**: 用于创建分析时的数据验证
- **STCResultSerializer**: 用于 STC 计算结果的序列化
- **STCAnalysisResultsSerializer**: 用于完整分析结果的序列化
- **STCComparisonSerializer**: 用于对比数据的序列化

#### `views.py` - API 视图
实现了以下功能：

**STCAnalysisViewSet** (ViewSet):
- `list()` - 列出所有分析（支持分页和筛选）
- `create()` - 创建新的分析
- `retrieve()` - 获取分析详情
- `update()` - 更新分析配置
- `destroy()` - 删除分析
- `start_analysis()` - 启动 STC 计算
- `results()` - 获取分析结果

**project_stc_comparison** (函数视图):
- 对比项目的 STC 值与贡献者统计数据

#### `urls.py` - URL 路由配置
配置了所有 STC API 的路由：
- `/api/stc/analyses/` - 分析的 CRUD 操作
- `/api/stc/analyses/{id}/start_analysis/` - 启动分析
- `/api/stc/analyses/{id}/results/` - 获取结果
- `/api/stc/projects/{project_id}/comparison/` - STC 对比

#### `README.md` - API 文档
完整的 API 使用文档，包括：
- 所有端点的详细说明
- 请求/响应示例
- 工作流程指南
- 错误码说明

#### `STC_API_Collection.json` - Postman 集合
可以直接导入 Postman 进行测试的 API 集合

### 2. 更新的文件

#### `backend/api/urls.py`
添加了 STC API 路由：
```python
path('stc/', include('stc_analysis.urls')),
```

#### `backend/secuflow/config/settings/base.py`
已添加 `stc_analysis` 到 `INSTALLED_APPS`

### 3. 创建的数据库迁移

- `stc_analysis/migrations/0001_initial.py` - STCAnalysis 模型的初始迁移

## API 端点总览

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/stc/analyses/` | 列出所有分析 |
| POST | `/api/stc/analyses/` | 创建新分析 |
| GET | `/api/stc/analyses/{id}/` | 获取分析详情 |
| PATCH | `/api/stc/analyses/{id}/` | 更新分析 |
| DELETE | `/api/stc/analyses/{id}/` | 删除分析 |
| POST | `/api/stc/analyses/{id}/start_analysis/` | 启动分析计算 |
| GET | `/api/stc/analyses/{id}/results/` | 获取分析结果 |
| GET | `/api/stc/projects/{project_id}/comparison/` | STC 对比数据 |

## 功能特性

### 1. 完整的 CRUD 操作
- 创建、读取、更新、删除 STC 分析记录
- 支持分页和多种筛选条件

### 2. STC 计算
- 基于 TNM 输出的 AssignmentMatrix.json 计算 STC
- 支持基本 STC 和 Monte Carlo STC 两种方法
- 自动保存结果到 JSON 文件

### 3. 结果管理
- 存储分析结果文件路径
- 提供 top_n 筛选功能
- 包含贡献者排名信息

### 4. 对比分析
- 将 STC 值与 TNM 分析的贡献者统计数据结合
- 支持按角色筛选
- 显示贡献者的多维度信息（STC、修改量、文件数等）

### 5. 错误处理
- 完整的错误处理和日志记录
- 统一的 API 响应格式
- 详细的错误码和错误信息

### 6. 权限控制
- 所有端点都需要 JWT 认证
- 遵循项目的权限体系

## 使用流程

### 快速开始

1. **获取 JWT Token**
   ```bash
   POST /api/token/
   Body: {"username": "user", "password": "pass"}
   ```

2. **创建 STC 分析**
   ```bash
   POST /api/stc/analyses/
   Headers: Authorization: Bearer {token}
   Body: {
     "project": "project-uuid",
     "use_monte_carlo": false
   }
   ```

3. **确保 TNM 分析已完成**
   ```bash
   # TNM 应该已经生成了 AssignmentMatrix.json
   ```

4. **启动 STC 计算**
   ```bash
   POST /api/stc/analyses/{id}/start_analysis/
   Body: {"branch": "main"}
   ```

5. **获取结果**
   ```bash
   GET /api/stc/analyses/{id}/results/
   ```

6. **查看对比数据**
   ```bash
   GET /api/stc/projects/{project_id}/comparison/
   ```

## 测试

### 单元测试
运行 STC 服务的测试：
```bash
docker-compose exec backend python manage.py test stc_analysis.test_stc
```

### API 测试
1. 导入 `STC_API_Collection.json` 到 Postman
2. 设置环境变量：
   - `base_url`: http://localhost:8000
   - `jwt_token`: 你的 JWT token
   - `project_id`: 项目 UUID
3. 按顺序执行请求

## 依赖关系

### 必需的数据
- **Project**: 必须有有效的项目记录
- **TNM Output**: 需要 TNM 分析生成的 AssignmentMatrix.json
- **Contributors**: 用于对比功能的贡献者统计数据

### 推荐工作流
1. 创建项目
2. 运行 TNM 分析
3. 分析 TNM 贡献者数据
4. 创建并运行 STC 分析
5. 查看对比结果

## 配置

### 环境变量
- `TNM_OUTPUT_DIR`: TNM 输出目录（默认: `/app/tnm_output`）

### 数据库
- `STCAnalysis` 模型已添加到数据库
- 运行迁移: `python manage.py migrate stc_analysis`

## 日志

所有 API 操作都会记录日志：
- INFO 级别：正常操作（创建、查询、计算完成）
- ERROR 级别：错误和异常
- 包含用户 ID、项目 ID、分析 ID 等上下文信息

## 未来改进

### 可能的增强功能
1. **异步计算**: 对大型项目使用 Celery 进行后台计算
2. **实时进度**: WebSocket 支持实时进度更新
3. **批量分析**: 支持一次分析多个项目
4. **可视化**: 提供图表和可视化端点
5. **导出功能**: 支持导出为 CSV、Excel 等格式
6. **缓存**: 使用 Redis 缓存分析结果
7. **版本对比**: 对比同一项目不同时间的 STC 值

### 性能优化
1. 数据库查询优化（select_related、prefetch_related）
2. 结果缓存
3. 分页优化
4. 异步任务队列

## 维护

### 常见问题

**Q: TNM 数据未找到？**
A: 确保先运行 TNM 分析，生成 AssignmentMatrix.json 文件

**Q: 分析失败？**
A: 检查 error_message 字段，通常是数据格式或文件路径问题

**Q: 结果为空？**
A: 确保 TNM 分析包含贡献者数据

### 故障排除
1. 检查 Docker 日志: `docker-compose logs backend`
2. 验证文件权限和路径
3. 确认数据库迁移已应用
4. 检查 TNM 输出文件完整性

## 相关文件

- `services.py`: STC 计算核心逻辑
- `models.py`: 数据库模型
- `test_stc.py`: 单元测试
- `apps.py`: 应用配置

## 贡献者

如需贡献代码或报告问题，请遵循项目的贡献指南。

---

**最后更新**: 2025-10-03
**版本**: 1.0.0

