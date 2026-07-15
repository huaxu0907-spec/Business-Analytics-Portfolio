# 商业分析作品集（Business Analytics Portfolio）

这是一个围绕重点商家经营异常诊断、经营分析、SQL、Python、Dashboard 与自动经营周报构建的完整商业分析作品集。它展示的是从业务问题到分析交付的完整流程，而不只是代码实现。

## 项目背景

在电商经营场景中，重点商家 GMV 持续下滑时，业务需要先判断这是否属于平台或品类的共同趋势，再进一步定位商家自身的经营变化。仅看 GMV 无法说明问题，需要结合订单量、客单价、商品与 SKU 结构等指标进行拆解。

本项目基于公开匿名电商数据，围绕重点商家经营异常开展分析：通过统一 KPI 口径、SQL 数据提取与 Python 分析，形成 Dashboard、异常诊断和经营周报等交付物，为后续经营核查与决策支持提供分析依据。

## 核心业务问题

- GMV 是否存在异常下降？
- 变化是否属于平台整体或主营品类趋势？
- 订单量、客单价、商品结构等指标中，哪些影响更明显？
- 哪些高贡献 SKU 或经营信号需要重点核查？
- 如何建立持续监控、异常预警与复盘机制？

## 商业分析流程

业务理解

↓

KPI 指标设计

↓

SQL 数据提取

↓

Python 数据分析

↓

异常诊断

↓

业务洞察

↓

经营建议

↓

验证方案

## 项目成果

- **经营分析 Dashboard**：集中查看 GMV、订单量、客单价、活跃商家、趋势、贡献结构与商家诊断结果。
- **商家异常诊断**：基于经营和体验信号识别异常对象，输出处理等级、可观测证据与优先核查方向。
- **自动经营周报**：将当前筛选范围内的经营结果整理为管理层摘要、风险信号和建议动作，并支持 Word 下载。
- **Executive Summary**：用于展示项目背景、分析框架、关键发现、建议与技术栈的面试材料。
- **Resume**：提供面向商业分析与产品分析岗位的两份求职版本。

## 在线体验

### 经营分析 Dashboard

围绕经营规模、趋势变化、商家贡献和重点商家诊断，支持按时间、品类与商家范围查看分析结果。

【在线体验】

Streamlit 链接待补充

### 商家异常诊断

根据 GMV、订单量、延迟率和低评分率等可观测信号生成异常清单，并提供核查方向与建议动作。

【在线体验】

Streamlit 链接待补充

### 自动经营周报

将选定周期和范围内的指标、风险信号与建议动作整理为页面预览和可下载的 Word 周报。

【在线体验】

Streamlit 链接待补充

## 项目交付物

| 交付物 | 用途 | 文件 / 入口 |
| --- | --- | --- |
| Executive Summary | 项目背景、分析框架、关键发现与建议概览 | [Business Executive](executive/Executive_Business_Final.docx) / [Product Executive](executive/Executive_Product_Final.docx) |
| Business Analysis Report | 完整商业分析报告 | [Business Analysis Report](analysis/deliverables/Business_Analysis_Report.pdf) |
| Business Project Brief | 项目背景与分析任务说明 | [Business Project Brief](analysis/deliverables/Business_Project_Brief.docx) |
| SQL Scripts | 数据提取与分析逻辑 | [merchant_anomaly_analysis.sql](analysis/merchant_anomaly_analysis.sql) |
| Notebook | Python 分析过程与图表输出 | [merchant_anomaly_analysis.ipynb](analysis/merchant_anomaly_analysis.ipynb) |
| Dashboard | 经营分析与商家诊断 | [dashboard/app.py](dashboard/app.py) |
| 异常诊断 | 商家异常识别与优先级清单 | [anomaly_detection/app.py](anomaly_detection/app.py) |
| 经营周报 | 周报预览与 Word 生成 | [weekly_report/app.py](weekly_report/app.py) |
| Business Resume | 商业分析 / 经营分析 / 数据分析投递版本 | [Resume_Business_Final.docx](resume/Resume_Business_Final.docx) |
| Product Resume | 产品分析 / AI 产品 / 数据产品投递版本 | [Resume_Product_Final.docx](resume/Resume_Product_Final.docx) |

## 项目结构

```text
Business-Analytics-Portfolio/
├── dashboard/                 # 经营分析 Dashboard 独立入口
├── anomaly_detection/         # 商家异常诊断独立入口
├── weekly_report/             # 自动经营周报独立入口
├── executive/                 # Executive Summary 面试材料
├── resume/                    # 商业分析与产品分析简历
├── assets/screenshots/        # Dashboard、异常诊断、周报预览图片
├── analysis/                  # SQL、Notebook、分析结果与项目交付物
├── data/                      # 应用运行所需的公开匿名数据结果
├── shared/                    # 指标、图表、异常诊断与周报共用逻辑
├── scripts/                   # 数据准备脚本
├── app_core.py                # 三个 Streamlit 模块共用应用逻辑
├── requirements.txt           # Python 依赖
└── .gitignore                 # Git 忽略规则
```

## 技术栈

| 类别 | 工具与能力 |
| --- | --- |
| 商业分析 | Business Analysis、KPI Design、Root Cause Analysis、Dashboard、经营异常诊断 |
| 数据分析 | SQL、Python、Pandas、NumPy、Excel、DuckDB、数据清洗与指标分析 |
| 开发 | Streamlit、Plotly、python-docx、Git、GitHub |
| AI 辅助 | ChatGPT、Claude、Gemini、Codex、OpenCode |

## 本地运行

```bash
python -m pip install -r requirements.txt

streamlit run dashboard/app.py
streamlit run anomaly_detection/app.py
streamlit run weekly_report/app.py
```

## 项目截图

### Dashboard

![Dashboard 预览](assets/screenshots/dashboard.png)

### 异常诊断

![异常诊断预览](assets/screenshots/anomaly_detection.png)

### 经营周报

![经营周报预览](assets/screenshots/weekly_report.png)

## 适用岗位

商业分析、经营分析、数据分析、BI、商家分析、产品分析、数据产品、AI 产品。

## 说明

本项目基于公开匿名数据，用于展示商业分析、经营分析和数据产品相关能力。项目中的分析结论不代表真实企业经营结论，也不用于说明实际业务效果。

## 联系方式

- GitHub：待补充
- 邮箱：13080622230@163.com
