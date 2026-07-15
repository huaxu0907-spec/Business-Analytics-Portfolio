from __future__ import annotations

import json
import os
from datetime import date, timedelta

import pandas as pd
import streamlit as st

from shared.anomaly import anomaly_summary, detect_seller_anomalies

from shared.charts import (
    contribution_bar,
    diagnostic_trend,
    driver_waterfall,
    negative_merchants,
    overview_trend,
    peer_distribution,
    price_mix_chart,
    sku_migration_chart,
)
from shared.config import (
    CASE_SUMMARY_PATH,
    DEFAULT_END,
    DEFAULT_SELLER,
    DEFAULT_START,
    GMV_CURRENCY,
    seller_label,
)
from shared.data_loader import load_fact, load_metadata
from shared.metrics import (
    ALL_CATEGORIES,
    ALL_SELLERS,
    boundary_metrics,
    contribution,
    driver_decomposition,
    filter_fact,
    merchant_change_table,
    monthly_metrics,
    peer_benchmark,
    previous_period,
    price_mix,
    safe_change,
    sku_migration,
    summarize_kpis,
)
from shared.narratives import investigation_directions, is_default_case
from shared.reporting import build_weekly_report, create_weekly_report_docx


st.set_page_config(
    page_title="电商经营分析中心",
    page_icon=":material/analytics:",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data(show_spinner="正在读取经营数据…", max_entries=1)
def get_data() -> tuple[pd.DataFrame, dict]:
    return load_fact(), load_metadata()


def fmt_money(value: float) -> str:
    return f"{value:,.0f} {GMV_CURRENCY}"


def fmt_compact_money(value: float) -> str:
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.2f}M {GMV_CURRENCY}"
    if abs(value) >= 1_000:
        return f"{value / 1_000:.1f}K {GMV_CURRENCY}"
    return fmt_money(value)


def fmt_change(value: float | None) -> str:
    return "不可比" if value is None else f"{value:+.1%}"


def metric_delta(current: float, previous: float) -> str | None:
    change = safe_change(current, previous)
    return None if change is None else f"{change:+.1%} vs 前置期"


def show_scope(start: date, end: date, category: str, seller_scope: str) -> None:
    seller_text = seller_scope if seller_scope == ALL_SELLERS else seller_label(seller_scope)
    st.info(
        f"当前动态口径：{start} 至 {end}｜{category}｜{seller_text}｜"
        "GMV为已交付订单商品金额，不含运费",
        icon=":material/filter_alt:",
    )


def module_header(title: str, subtitle: str, icon: str, module: str, color: str) -> None:
    st.badge(module, icon=icon, color=color)
    st.title(title)
    st.write(subtitle)


def management_judgment(current, previous) -> tuple[str, str]:
    gmv_change = safe_change(current.gmv, previous.gmv)
    orders_change = safe_change(current.orders, previous.orders)
    aov_change = safe_change(current.aov, previous.aov)
    if gmv_change is None or orders_change is None or aov_change is None:
        return "当前缺少完整可比基准，暂不判断单一主导驱动。", "建议扩大分析周期，并继续观察指标趋势和结构变化。"
    if gmv_change < -0.05:
        if orders_change < aov_change - 0.03:
            return f"当前GMV较前置期下降{abs(gmv_change):.1%}，订单量收缩是更值得关注的驱动。", "建议优先进入异常对象清单，核查负向商家及高贡献SKU的成交变化。"
        if aov_change < orders_change - 0.03:
            return f"当前GMV较前置期下降{abs(gmv_change):.1%}，客单价下降是更值得关注的驱动。", "建议优先核查成交价格组合与SKU结构变化，并设置后续验证指标。"
        return f"当前GMV较前置期下降{abs(gmv_change):.1%}，未识别到订单量或客单价的单一主导驱动。", "建议继续观察指标趋势，并结合异常对象和经营结构进行复核。"
    if gmv_change > 0.05:
        return f"当前GMV较前置期增长{gmv_change:.1%}，经营规模整体改善。", "建议核查增长来源是否集中，并同步复核履约与评价等体验护栏。"
    return "当前GMV整体相对平稳，未识别到单一主导变化。", "建议保持当前监控口径，并继续观察核心指标和结构变化。"


def chart_card(question: str, figure) -> None:
    with st.container(border=True):
        st.caption(f"业务问题：{question}")
        st.plotly_chart(figure, width="stretch", config={"displayModeBar": False})


def render_home(metadata: dict) -> None:
    module_header("商业分析作品集", "围绕重点商家经营异常诊断，展示从经营分析到可视化、自动周报与标准化交付物的完整实践。", ":material/analytics:", "Business Analytics Portfolio", "blue")
    st.subheader("核心业务问题")
    st.markdown(
        "- GMV 是否出现异常下降，是否属于平台整体趋势？\n"
        "- 订单量、客单价与 SKU 结构中，哪些指标更值得优先关注？\n"
        "- 哪些高贡献未成交 SKU 需要优先核查？\n"
        "- 如何将一次诊断沉淀为持续监控与经营周报？"
    )

    st.subheader("三个交互模块")
    columns = st.columns(3, border=True)
    module_info = [
        ("01", "经营分析 Dashboard", "查看 GMV、订单、客单价与商家诊断。", "经营分析 Dashboard"),
        ("02", "商家异常诊断", "查看处理等级、可观测证据与优先核查方向。", "商家异常诊断"),
        ("03", "自动经营周报", "预览并导出标准化经营周报。", "自动经营周报"),
    ]
    for column, (number, title, description, target) in zip(columns, module_info):
        with column:
            st.caption(number)
            st.subheader(title)
            st.write(description)
            st.button(
                "进入模块",
                key=f"home_{number}",
                width="stretch",
                on_click=navigate_to,
                args=(target,),
            )

    st.subheader("数据范围")
    cards = st.columns(4)
    cards[0].metric("有效订单", f"{metadata['orders']:,}", border=True)
    cards[1].metric("活跃商家", f"{metadata['sellers']:,}", border=True)
    cards[2].metric("数据起始", metadata["start_date"], border=True)
    cards[3].metric("数据截止", metadata["end_date"], border=True)
    st.caption("公开 Olist 数据｜仅保留已交付订单｜金额单位 BRL｜不将公开数据结论表述为真实企业成果")
    st.subheader("项目交付物与源码")
    st.markdown(
        "- GitHub 源码链接：待补充\n"
        "- Gitee 源码链接：待补充\n"
        "- Executive Summary：仓库 `executive/` 目录\n"
        "- Resume：仓库 `resume/` 目录"
    )
    st.info(
        "证据边界：公开成交数据可用于识别经营变化与核查方向，但不能直接证明库存、曝光、流量、竞品价格或供应链机制；高贡献未成交 SKU 仅是优先核查对象。",
        icon=":material/warning:",
    )


def render_analysis_approach() -> None:
    module_header("分析思路", "将经营问题转化为可验证的指标、诊断与监控流程。", ":material/account_tree:", "Analysis Framework", "blue")
    st.subheader("商业分析流程")
    st.markdown(
        "业务背景\n\n↓\n\n业务问题\n\n↓\n\nKPI 指标设计\n\n↓\n\nSQL 数据提取\n\n↓\n\nPython 数据分析\n\n↓\n\n异常诊断\n\n↓\n\n业务洞察\n\n↓\n\n治理建议\n\n↓\n\n验证与监控"
    )
    st.subheader("分析判断逻辑")
    st.markdown(
        "- **先确认异常**：将重点商家与平台整体、主营品类的变化进行对比，避免把整体波动误判为单个商家问题。\n"
        "- **拆解 GMV**：GMV 由订单量与客单价共同构成，先拆分能够识别规模变化与价格/组合变化的不同方向。\n"
        "- **继续分析 SKU**：订单变化需要落到商品结构，才能定位高贡献商品的成交变化是否值得进一步核查。\n"
        "- **优先核查高贡献未成交 SKU**：它们对经营表现的潜在影响更大，但仅代表核查优先级，不直接证明缺货或供给收缩。"
    )
    st.subheader("证据边界与下一步")
    st.markdown(
        "公开数据不能证明库存、曝光、流量、竞品价格、促销触达或供应链等具体机制。若拥有真实企业数据，下一步应补充库存与可售状态、流量与曝光、商品价格与促销、营销触达、履约、供应商及商家运营记录等字段，用于验证假设并建立持续监控。"
    )


def render_project_notes() -> None:
    module_header("项目说明", "本作品集展示分析流程、可交互界面与标准化交付物，不扩展公开数据能够支持的结论。", ":material/folder_open:", "Project Notes", "blue")
    st.subheader("项目模块")
    st.markdown(
        "- **经营分析 Dashboard**：统一展示经营总览、指标趋势与商家诊断。\n"
        "- **商家异常诊断**：形成处理等级、可观测证据、核查方向与建议动作。\n"
        "- **自动经营周报**：将分析口径沉淀为页面预览与 Word 周报。"
    )
    st.subheader("仓库交付物")
    st.markdown(
        "分析报告、SQL Scripts 与 Notebook 位于 `analysis/`；Executive Summary 位于 `executive/`；Business Resume 与 Product Resume 位于 `resume/`。"
    )


def render_about() -> None:
    module_header("关于作者", "面向商业分析、经营分析、数据分析、产品分析与 AI 产品相关岗位的作品集。", ":material/person:", "About", "blue")
    st.markdown(
        "本项目基于公开匿名数据构建，用于展示商业分析与数据产品实践能力。分析结论不代表真实企业经营结论。\n\n"
        "GitHub：待补充  \\n"
        "Gitee：待补充  \\n"
        "邮箱：待补充"
    )


def navigate_to(target: str) -> None:
    st.session_state["requested_navigation"] = target


def render_anomaly_detection(fact: pd.DataFrame, metadata: dict) -> None:
    module_header("异常识别", "按月识别商家经营与体验信号，形成处理等级、优先核查方向和建议动作。", ":material/notification_important:", "程序2｜风险识别", "orange")

    minimum_date = pd.Timestamp(metadata["start_date"]).date()
    maximum_date = pd.Timestamp(metadata["end_date"]).date()
    st.sidebar.subheader("分析范围")
    selected_dates = st.sidebar.date_input(
        "监测日期",
        value=(pd.Timestamp(DEFAULT_START).date(), pd.Timestamp(DEFAULT_END).date()),
        min_value=minimum_date,
        max_value=maximum_date,
        key="anomaly_dates",
    )
    if not isinstance(selected_dates, (tuple, list)) or len(selected_dates) != 2:
        st.warning("请选择完整的开始日期和结束日期。", icon=":material/warning:")
        return
    start_date, end_date = selected_dates
    st.sidebar.subheader("分析对象")
    categories = [ALL_CATEGORIES] + sorted(fact["category"].dropna().unique().tolist())
    category = st.sidebar.selectbox("监测品类", categories, key="anomaly_category")
    st.sidebar.subheader("识别规则")
    minimum_orders = st.sidebar.slider("当前月与基准月最低订单量", 5, 50, 10, 5)
    decline_pct = st.sidebar.slider("GMV/订单量下降阈值", 10, 80, 30, 5)
    experience_pct = st.sidebar.slider("延迟率/低评分率阈值", 5, 60, 20, 5)

    scoped = filter_fact(fact, start_date, end_date, category=category)
    show_scope(start_date, end_date, category, ALL_SELLERS)
    st.caption(
        f"动态规则：相邻活跃月份对比｜双月均≥{minimum_orders}单｜"
        f"降幅≥{decline_pct}%或体验风险率≥{experience_pct}%"
    )
    anomalies = detect_seller_anomalies(
        scoped,
        minimum_orders=minimum_orders,
        decline_threshold=decline_pct / 100,
        late_rate_threshold=experience_pct / 100,
        low_review_threshold=experience_pct / 100,
    )
    summary = anomaly_summary(anomalies)
    cards = st.columns(4)
    cards[0].metric("异常事件", f"{summary['events']:,}", border=True)
    cards[1].metric("涉及商家", f"{summary['sellers']:,}", border=True)
    cards[2].metric("高严重度事件", f"{summary['high']:,}", border=True)
    cards[3].metric("异常期GMV", fmt_compact_money(summary["gmv"]), border=True)

    if anomalies.empty:
        st.success("当前口径下未识别到显著负向异常。建议保持现有监控口径，并在下一周期复核核心指标和体验护栏。", icon=":material/check_circle:")
        return

    left, right = st.columns(2)
    with left, st.container(border=True):
        st.caption("业务问题：异常事件主要处于什么严重度？")
        severity = (
            anomalies.groupby("severity", observed=True)
            .size()
            .reindex(["高", "中", "低"], fill_value=0)
            .rename_axis("严重度")
            .reset_index(name="事件数")
        )
        st.bar_chart(severity, x="严重度", y="事件数", color="#D95F59")
    with right, st.container(border=True):
        st.caption("业务问题：异常信号集中在哪些月份？")
        trend = anomalies.groupby("current_month", observed=True).size().reset_index(name="异常事件数")
        st.line_chart(trend, x="current_month", y="异常事件数", color="#3A6EA5")

    st.subheader("异常优先级清单")
    display = anomalies.copy()
    display["商家"] = display["seller_id"].map(seller_label)
    display = display.rename(
        columns={
            "current_month": "异常月份",
            "baseline_month": "基准月份",
            "orders": "订单量",
            "gmv": "GMV",
            "gmv_change": "GMV环比",
            "orders_change": "订单量环比",
            "late_rate": "延迟率",
            "low_review_rate": "低评分率",
            "severity": "严重度",
            "priority": "处理等级",
            "signals": "触发信号",
            "observable_evidence": "可观测证据",
            "investigation_direction": "优先核查方向",
            "recommended_action": "建议动作",
        }
    )
    display = display[
        ["商家", "异常月份", "基准月份", "处理等级", "严重度", "触发信号", "可观测证据", "优先核查方向", "建议动作", "订单量", "GMV", "GMV环比", "订单量环比", "延迟率", "低评分率"]
    ]
    st.dataframe(
        display,
        hide_index=True,
        column_config={
            "商家": st.column_config.TextColumn(pinned=True),
            "GMV": st.column_config.NumberColumn(format="%.0f BRL"),
            "GMV环比": st.column_config.NumberColumn(format="percent"),
            "订单量环比": st.column_config.NumberColumn(format="percent"),
            "延迟率": st.column_config.NumberColumn(format="percent"),
            "低评分率": st.column_config.NumberColumn(format="percent"),
        },
    )
    st.info(
        "处理方式：按P0、P1、P2确定核查顺序，再依据可观测证据和触发信号执行建议动作。",
        icon=":material/playlist_add_check:",
    )
    st.warning(
        "证据边界：规则识别的是相邻月份变化和体验信号，不等于已确认待验证原因；"
        "月份间隔可能受商家非连续经营影响，仍需结合业务信息复核。",
        icon=":material/warning:",
    )


def render_weekly_report(fact: pd.DataFrame, metadata: dict) -> None:
    module_header("自动经营周报", "将当前经营结果整理为管理层摘要、关键风险信号和下周期行动。", ":material/description:", "程序3｜管理汇报", "blue")
    minimum_date = pd.Timestamp(metadata["start_date"]).date()
    maximum_date = pd.Timestamp(metadata["end_date"]).date()
    default_end = pd.Timestamp(DEFAULT_END).date()
    default_start = pd.Timestamp(DEFAULT_END).date() - timedelta(days=6)
    st.sidebar.subheader("报告设置")
    selected_dates = st.sidebar.date_input(
        "报告周期",
        value=(default_start, default_end),
        min_value=minimum_date,
        max_value=maximum_date,
        key="report_dates",
    )
    if not isinstance(selected_dates, (tuple, list)) or len(selected_dates) != 2:
        st.warning("请选择完整的报告开始日期和结束日期。", icon=":material/warning:")
        return
    start_date, end_date = selected_dates
    if start_date > end_date:
        st.warning("报告开始日期不能晚于结束日期。", icon=":material/warning:")
        return
    st.sidebar.subheader("分析对象")
    categories = [ALL_CATEGORIES] + sorted(fact["category"].dropna().unique().tolist())
    category = st.sidebar.selectbox("报告品类", categories, key="report_category")
    report_title = st.sidebar.text_input("报告名称", value="电商经营周报", max_chars=40)

    current = filter_fact(fact, start_date, end_date, category=category)
    previous_start, previous_end = previous_period(start_date, end_date)
    previous = filter_fact(fact, previous_start, previous_end, category=category)
    if current.empty:
        st.warning("当前报告周期没有有效订单，请调整日期或品类。", icon=":material/warning:")
        return
    report = build_weekly_report(current, previous, start_date, end_date, category)
    show_scope(start_date, end_date, category, ALL_SELLERS)
    st.caption(f"对比期：{report.previous_start} 至 {report.previous_end}（与报告周期等长）")

    st.subheader("管理层预览")
    cards = st.columns(4)
    cards[0].metric("GMV", fmt_compact_money(report.current.gmv), fmt_change(report.changes["gmv"]), border=True)
    cards[1].metric("订单量", f"{report.current.orders:,}", fmt_change(report.changes["orders"]), border=True)
    cards[2].metric("客单价", fmt_money(report.current.aov), fmt_change(report.changes["aov"]), border=True)
    cards[3].metric("活跃商家", f"{report.current.active_sellers:,}", fmt_change(report.changes["sellers"]), border=True)
    st.caption("指标卡变化均相对于等长前置周期；前置期为零时显示不可比。")

    with st.container(border=True):
        st.subheader("核心判断")
        st.write(report.core_judgment)
    left, right = st.columns(2)
    with left, st.container(border=True, height="stretch"):
        st.subheader("关键风险信号")
        for signal in report.risk_signals:
            st.markdown(f"- {signal}")
    with right, st.container(border=True, height="stretch"):
        st.subheader("下周期行动")
        for index, action in enumerate(report.actions, start=1):
            st.markdown(f"{index}. {action}")

    st.subheader("主要经营贡献")
    sellers = report.top_sellers.head(5).copy()
    sellers["对象"] = sellers["seller_id"].map(seller_label)
    sellers["类型"] = "商家"
    categories_frame = report.top_categories.head(5).copy()
    categories_frame["对象"] = categories_frame["category"]
    categories_frame["类型"] = "品类"
    structure = pd.concat(
        [sellers[["类型", "对象", "gmv", "gmv_share", "orders"]], categories_frame[["类型", "对象", "gmv", "gmv_share", "orders"]]],
        ignore_index=True,
    ).rename(columns={"gmv": "GMV", "gmv_share": "GMV占比", "orders": "订单量"})
    st.dataframe(
        structure,
        hide_index=True,
        column_config={
            "GMV": st.column_config.NumberColumn(format="%.0f BRL"),
            "GMV占比": st.column_config.NumberColumn(format="percent"),
            "订单量": st.column_config.NumberColumn(format="%d"),
        },
    )

    try:
        docx_bytes = create_weekly_report_docx(report, report_title.strip() or "电商经营周报")
    except Exception:
        st.error("Word周报生成失败。请保持当前筛选条件并重新尝试；页面预览结果不受影响。", icon=":material/error:")
        return
    filename = f"经营周报_{start_date}_{end_date}.docx"
    st.download_button(
        "下载Word周报",
        data=docx_bytes,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        type="primary",
        icon=":material/download:",
    )
    st.info("页面预览和Word文件由同一计算结果生成；修改日期或品类后，两者会同步更新。", icon=":material/sync:")
    st.warning(
        "周报只汇总当前数据能够支持的经营与体验信号；异常信号不等于已确认待验证原因，建议效果仍需后续验证。",
        icon=":material/warning:",
    )


def open_diagnosis(seller_id: str) -> None:
    st.session_state["diag_seller"] = seller_id
    st.session_state["diag_selector"] = seller_id
    st.session_state["bi_view"] = "商家诊断"


def render_overview(
    fact: pd.DataFrame,
    start: date,
    end: date,
    category: str,
    seller_scope: str,
) -> None:
    seller_ids = None if seller_scope == ALL_SELLERS else [seller_scope]
    current = filter_fact(fact, start, end, seller_ids=seller_ids, category=category)
    previous_start, previous_end = previous_period(start, end)
    previous = filter_fact(fact, previous_start, previous_end, seller_ids=seller_ids, category=category)
    if current.empty:
        st.warning(
            "当前筛选范围没有有效订单。请扩大日期范围或调整商家、品类筛选。",
            icon=":material/warning:",
        )
        return

    current_kpi = summarize_kpis(current)
    previous_kpi = summarize_kpis(previous)
    cards = st.columns(4)
    cards[0].metric("GMV", fmt_compact_money(current_kpi.gmv), metric_delta(current_kpi.gmv, previous_kpi.gmv), border=True)
    cards[1].metric("订单量", f"{current_kpi.orders:,}", metric_delta(current_kpi.orders, previous_kpi.orders), border=True)
    cards[2].metric("客单价", fmt_money(current_kpi.aov), metric_delta(current_kpi.aov, previous_kpi.aov), border=True)
    cards[3].metric("活跃商家", f"{current_kpi.active_sellers:,}", metric_delta(current_kpi.active_sellers, previous_kpi.active_sellers), border=True)
    st.caption(f"指标卡对比期：{previous_start.date()} 至 {previous_end.date()}（与当前筛选等长）")
    judgment, action = management_judgment(current_kpi, previous_kpi)
    with st.container(border=True):
        st.markdown(f"**管理层判断：** {judgment}")
        st.markdown(f"**建议动作：** {action}")

    monthly = monthly_metrics(current)
    seller_contrib = contribution(current, "seller_id")
    category_contrib = contribution(current, "category")
    changes = merchant_change_table(current)

    left, right = st.columns(2)
    with left:
        chart_card("经营变化从何时开始，GMV与订单量是否同步？", overview_trend(monthly))
    with right:
        chart_card(
            "经营结果是否过度集中在少数商家？",
            contribution_bar(seller_contrib, "seller_id", "哪些商家贡献主要GMV？"),
        )
    left, right = st.columns(2)
    with left:
        chart_card(
            "哪些品类决定当前经营规模？",
            contribution_bar(category_contrib, "category", "哪些品类贡献主要GMV？"),
        )
    with right:
        if changes.empty:
            st.info("当前范围不足以比较首尾月份。请扩大日期范围后再生成异常对象清单。", icon=":material/info:")
        else:
            chart_card("哪些达到最低规模的商家需要进入诊断？", negative_merchants(changes))

    if not changes.empty:
        with st.container(border=True):
            st.subheader("进入商家诊断")
            candidates = changes.nsmallest(min(20, len(changes)), "gmv_change")["seller_id"].tolist()
            selected = st.selectbox(
                "选择需要进一步核查的商家",
                candidates,
                format_func=seller_label,
                key="candidate_seller",
            )
            st.button(
                "查看商家诊断",
                type="primary",
                icon=":material/manage_search:",
                on_click=open_diagnosis,
                args=(selected,),
            )
    st.caption(
        "异常对象清单采用首尾月GMV变化，并要求首尾月订单量均不少于5单；"
        "它用于确定核查对象，不直接证明潜在机制。"
    )


def render_diagnosis(
    fact: pd.DataFrame,
    start: date,
    end: date,
    category: str,
    seller_scope: str,
) -> None:
    scoped = filter_fact(fact, start, end, category=category)
    if scoped.empty:
        st.warning("当前日期与品类范围没有可诊断数据。", icon=":material/warning:")
        return

    sellers = contribution(scoped, "seller_id", limit=scoped["seller_id"].nunique())["seller_id"].tolist()
    preferred = seller_scope if seller_scope != ALL_SELLERS else st.session_state.get("diag_seller", DEFAULT_SELLER)
    if preferred not in sellers:
        preferred = sellers[0]
    if seller_scope != ALL_SELLERS or st.session_state.get("diag_selector") not in sellers:
        st.session_state["diag_selector"] = preferred
    selected_seller = st.selectbox("诊断商家", sellers, format_func=seller_label, key="diag_selector")
    st.session_state["diag_seller"] = selected_seller
    seller_frame = scoped.loc[scoped["seller_id"].eq(selected_seller)].copy()
    boundary = boundary_metrics(seller_frame)
    if boundary["last_month"] is None:
        st.warning("当前筛选范围不足两个成交月份，无法进行首尾月诊断。请扩大日期范围。", icon=":material/warning:")
        return

    st.info(
        f"商家诊断口径：{seller_label(selected_seller)}｜{boundary['first_month']} 对比 "
        f"{boundary['last_month']}｜当前筛选数据实时计算",
        icon=":material/manage_search:",
    )
    cards = st.columns(3)
    cards[0].metric(
        "GMV首尾月变化",
        fmt_change(boundary["gmv_change"]),
        f"{boundary['base'].gmv:,.0f} → {boundary['end'].gmv:,.0f} BRL",
        border=True,
        delta_color="off",
    )
    cards[1].metric(
        "订单量首尾月变化",
        fmt_change(boundary["orders_change"]),
        f"{boundary['base'].orders:,} → {boundary['end'].orders:,} 单",
        border=True,
        delta_color="off",
    )
    cards[2].metric(
        "客单价首尾月变化",
        fmt_change(boundary["aov_change"]),
        f"{boundary['base'].aov:,.1f} → {boundary['end'].aov:,.1f} BRL",
        border=True,
        delta_color="off",
    )

    default_case = is_default_case(selected_seller, start, end, category)
    if default_case and CASE_SUMMARY_PATH.exists():
        summary = json.loads(CASE_SUMMARY_PATH.read_text(encoding="utf-8"))
        st.success(
            "默认案例基准：报告与Notebook确认GMV变化"
            f" {summary['gmv_change']:.1%}、订单量变化 {summary['orders_change']:.1%}、"
            f"客单价变化 {summary['aov_change']:.1%}。以下图表仍由当前数据重新计算。",
            icon=":material/check_circle:",
        )
    else:
        st.info(
            "当前不是默认案例口径；页面不会沿用报告中的固定数字，所有判断均基于当前筛选结果。",
            icon=":material/calculate:",
        )

    monthly = monthly_metrics(seller_frame)
    peer = peer_benchmark(scoped, selected_seller)
    driver = driver_decomposition(boundary)
    migration, sku_summary = sku_migration(seller_frame)
    price = price_mix(seller_frame)

    left, right = st.columns(2)
    with left:
        chart_card("指标下降发生在何时，三个指标是否同步？", diagnostic_trend(monthly))
    with right:
        if peer.get("target") is None:
            st.info("当前同类样本不足：目标商家或同类商家未同时满足首尾月各5单。", icon=":material/info:")
        else:
            chart_card("该变化是商家特有，还是同类普遍波动？", peer_distribution(peer, selected_seller))
            st.caption(f"同类口径：主营品类 {peer['category']}，有效同类 {len(peer['peers'])} 家。")
    left, right = st.columns(2)
    with left:
        delta_gmv = boundary["end"].gmv - boundary["base"].gmv
        chart_card("GMV变化主要由订单量还是客单价驱动？", driver_waterfall(driver, delta_gmv))
    with right:
        chart_card("哪些SKU成交结构变化应进入核查清单？", sku_migration_chart(migration))
    chart_card("客单价变化是否伴随成交价格组合变化？", price_mix_chart(price))

    st.subheader("优先核查方向")
    st.caption("以下内容根据当前筛选结果生成核查优先级，不代表已确认待验证原因。")
    for index, item in enumerate(investigation_directions(boundary, peer, sku_summary), start=1):
        with st.expander(
            f"{index}. {item['direction']}｜{item['signal']}",
            expanded=index == 1,
            icon=":material/fact_check:",
        ):
            st.markdown(f"**行动建议：** {item['action']}")
            st.markdown(f"**验证指标：** {item['validation']}")
    st.warning(
        "证据边界：公开成交数据不能直接证明库存、曝光、竞争价格或流量机制；"
        "成交SKU减少不等于供给收缩。",
        icon=":material/warning:",
    )


fact, metadata = get_data()
st.session_state.setdefault("bi_view", "经营总览")
st.session_state.setdefault("diag_seller", DEFAULT_SELLER)
st.session_state.setdefault("diag_selector", DEFAULT_SELLER)
st.session_state.setdefault("portfolio_navigation", "首页")

if "requested_navigation" in st.session_state:
    st.session_state["portfolio_navigation"] = st.session_state.pop("requested_navigation")

app_mode = os.getenv("STREAMLIT_APP_MODE")
navigation_options = ["首页", "经营分析 Dashboard", "商家异常诊断", "自动经营周报", "分析思路", "项目说明", "关于作者"]
navigation = app_mode or st.sidebar.radio(
    "作品集导航",
    navigation_options,
    key="portfolio_navigation",
)
st.sidebar.caption("独立部署模式" if app_mode else "统一作品集入口")

if navigation == "首页":
    render_home(metadata)
    st.stop()

if navigation == "商家异常诊断":
    render_anomaly_detection(fact, metadata)
    st.stop()

if navigation == "自动经营周报":
    render_weekly_report(fact, metadata)
    st.stop()

if navigation == "分析思路":
    render_analysis_approach()
    st.stop()

if navigation == "项目说明":
    render_project_notes()
    st.stop()

if navigation == "关于作者":
    render_about()
    st.stop()

module_header("经营分析 Dashboard", "从经营总览识别关注指标，再进入商家诊断形成优先核查方向、行动建议和验证指标。", ":material/monitoring:", "程序1｜经营监控", "blue")

minimum_date = pd.Timestamp(metadata["start_date"]).date()
maximum_date = pd.Timestamp(metadata["end_date"]).date()
st.sidebar.subheader("分析范围")
selected_dates = st.sidebar.date_input(
    "分析日期",
    value=(pd.Timestamp(DEFAULT_START).date(), pd.Timestamp(DEFAULT_END).date()),
    min_value=minimum_date,
    max_value=maximum_date,
)
if not isinstance(selected_dates, (tuple, list)) or len(selected_dates) != 2:
    st.warning("请选择完整的开始日期和结束日期。", icon=":material/warning:")
    st.stop()
start_date, end_date = selected_dates
if start_date > end_date:
    st.warning("开始日期不能晚于结束日期。", icon=":material/warning:")
    st.stop()

st.sidebar.subheader("分析对象")
categories = [ALL_CATEGORIES] + sorted(fact["category"].dropna().unique().tolist())
category = st.sidebar.selectbox("品类", categories, index=0)
top_sellers = contribution(fact, "seller_id", limit=200)["seller_id"].tolist()
if DEFAULT_SELLER not in top_sellers:
    top_sellers.insert(0, DEFAULT_SELLER)
seller_options = [ALL_SELLERS] + top_sellers
seller_scope = st.sidebar.selectbox(
    "商家范围",
    seller_options,
    format_func=lambda value: value if value == ALL_SELLERS else seller_label(value),
)
st.sidebar.caption("商家列表保留GMV贡献前200名，并固定包含默认案例商家。")

show_scope(start_date, end_date, category, seller_scope)
view = st.segmented_control(
    "业务视图",
    ["经营总览", "商家诊断"],
    key="bi_view",
    width="content",
)
if view == "经营总览":
    render_overview(fact, start_date, end_date, category, seller_scope)
else:
    render_diagnosis(fact, start_date, end_date, category, seller_scope)
