# STC Analysis API Documentation

## Overview

STC (Spanning Tree Centrality) Analysis API 提供了基于生成树中心性的贡献者重要性分析功能。

## API Endpoints

### 1. 创建 STC 分析

**POST** `/api/stc/analyses/`

创建一个新的 STC 分析任务。

**Request Body:**
```json
{
  "project": "uuid-of-project",
  "use_monte_carlo": false,
  "monte_carlo_iterations": 1000
}
```

**Response:**
```json
{
  "success": true,
  "message": "Analysis created successfully",
  "data": {
    "id": 1,
    "project": "uuid-of-project",
    "project_name": "Project Name",
    "analysis_date": "2025-10-03T10:00:00Z",
    "is_completed": false,
    "use_monte_carlo": false,
    "monte_carlo_iterations": 1000
  }
}
```

### 2. 列出所有分析

**GET** `/api/stc/analyses/`

获取所有 STC 分析记录。

**Query Parameters:**
- `project_id` (optional): 按项目 ID 筛选
- `is_completed` (optional): 按完成状态筛选 (true/false)
- `page` (optional): 页码
- `page_size` (optional): 每页数量

**Response:**
```json
{
  "success": true,
  "message": "Data retrieved successfully",
  "data": {
    "count": 10,
    "next": "http://api/stc/analyses/?page=2",
    "previous": null,
    "results": [
      {
        "id": 1,
        "project": "uuid",
        "project_name": "Project Name",
        "analysis_date": "2025-10-03T10:00:00Z",
        "is_completed": true,
        "use_monte_carlo": false
      }
    ]
  }
}
```

### 3. 获取分析详情

**GET** `/api/stc/analyses/{id}/`

获取特定分析的详细信息。

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "project": "uuid",
    "project_name": "Project Name",
    "analysis_date": "2025-10-03T10:00:00Z",
    "is_completed": true,
    "use_monte_carlo": false,
    "results_file": "/path/to/results.json",
    "error_message": null
  }
}
```

### 4. 开始分析

**POST** `/api/stc/analyses/{id}/start_analysis/`

启动 STC 计算。需要先运行 TNM 分析以生成所需的数据。

**Request Body:**
```json
{
  "branch": "main",
  "tnm_output_dir": "/app/tnm_output/project_uuid_main"
}
```

**Response:**
```json
{
  "success": true,
  "message": "STC analysis completed successfully",
  "data": {
    "analysis_id": 1,
    "total_nodes": 15,
    "results_file": "stc_results_1_20251003_100000.json",
    "top_contributors": [
      {
        "node_id": "0",
        "contributor_login": "john_doe",
        "stc_value": 0.85,
        "rank": 1
      },
      {
        "node_id": "1",
        "contributor_login": "jane_smith",
        "stc_value": 0.72,
        "rank": 2
      }
    ]
  }
}
```

### 5. 获取分析结果

**GET** `/api/stc/analyses/{id}/results/`

获取完整的 STC 分析结果。

**Query Parameters:**
- `top_n` (optional): 只返回前 N 个结果

**Response:**
```json
{
  "success": true,
  "message": "STC analysis results retrieved successfully",
  "data": {
    "analysis_id": 1,
    "project_id": "uuid",
    "analysis_date": "2025-10-03T10:00:00Z",
    "use_monte_carlo": false,
    "total_nodes": 15,
    "results": [
      {
        "node_id": "0",
        "contributor_login": "john_doe",
        "stc_value": 0.85,
        "rank": 1
      },
      {
        "node_id": "1",
        "contributor_login": "jane_smith",
        "stc_value": 0.72,
        "rank": 2
      }
    ]
  }
}
```

### 6. STC 与贡献者统计对比

**GET** `/api/stc/projects/{project_id}/comparison/`

对比项目的 STC 值与贡献者统计数据。

**Query Parameters:**
- `analysis_id` (optional): 指定分析 ID（默认使用最新的已完成分析）
- `role` (optional): 按功能角色筛选
- `top_n` (optional): 只返回前 N 个结果

**Response:**
```json
{
  "success": true,
  "message": "STC comparison data retrieved successfully",
  "data": {
    "analysis_id": 1,
    "project_id": "uuid",
    "project_name": "Project Name",
    "analysis_date": "2025-10-03T10:00:00Z",
    "total_contributors": 10,
    "contributors": [
      {
        "contributor_login": "john_doe",
        "contributor_id": 1,
        "stc_value": 0.85,
        "stc_rank": 1,
        "total_modifications": 5000,
        "files_modified": 150,
        "functional_role": "coder",
        "is_core_contributor": true
      }
    ]
  }
}
```

## 工作流程

1. **创建分析任务**
   ```bash
   POST /api/stc/analyses/
   ```

2. **确保 TNM 分析已完成**
   - STC 分析依赖于 TNM 输出的 AssignmentMatrix.json 文件

3. **启动 STC 计算**
   ```bash
   POST /api/stc/analyses/{id}/start_analysis/
   ```

4. **获取结果**
   ```bash
   GET /api/stc/analyses/{id}/results/
   ```

5. **查看对比数据**
   ```bash
   GET /api/stc/projects/{project_id}/comparison/
   ```

## 错误码

- `STC_LIST_ERROR`: 获取分析列表失败
- `STC_CREATE_ERROR`: 创建分析失败
- `ANALYSIS_ALREADY_COMPLETED`: 分析已完成
- `TNM_DATA_NOT_FOUND`: TNM 数据未找到
- `INVALID_DATA`: 数据验证失败
- `STC_ANALYSIS_ERROR`: STC 分析计算失败
- `ANALYSIS_NOT_COMPLETED`: 分析未完成
- `RESULTS_NOT_FOUND`: 结果文件未找到
- `NO_ANALYSIS_FOUND`: 未找到已完成的分析
- `STC_COMPARISON_ERROR`: 对比数据获取失败

## 认证

所有 API 端点都需要 JWT 认证。在请求头中包含：

```
Authorization: Bearer <your-jwt-token>
```

