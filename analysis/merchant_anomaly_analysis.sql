-- 核心SQL（SQLite语法）
-- 目的：复现商家月度经营指标、同类商家比较和成交SKU迁移。
-- 表名假设：orders、order_items、products、category_translation。

DROP VIEW IF EXISTS delivered_items;
CREATE TEMP VIEW delivered_items AS
    SELECT
        i.order_id,
        i.seller_id,
        i.product_id,
        i.price,
        SUBSTR(o.order_purchase_timestamp, 1, 7) AS order_month,
        t.product_category_name_english AS category_en
    FROM order_items AS i
    INNER JOIN orders AS o USING (order_id)
    LEFT JOIN products AS p USING (product_id)
    LEFT JOIN category_translation AS t USING (product_category_name)
    WHERE o.order_status = 'delivered'
      AND o.order_purchase_timestamp >= '2017-01-01'
      AND o.order_purchase_timestamp < '2018-08-01'
;

DROP VIEW IF EXISTS seller_monthly;
CREATE TEMP VIEW seller_monthly AS
    SELECT
        seller_id,
        order_month,
        COUNT(DISTINCT order_id) AS orders,
        SUM(price) AS gmv_brl,
        SUM(price) / NULLIF(COUNT(DISTINCT order_id), 0) AS aov_brl,
        COUNT(DISTINCT product_id) AS transacting_skus
    FROM delivered_items
    GROUP BY seller_id, order_month
;

DROP VIEW IF EXISTS category_seller_monthly;
CREATE TEMP VIEW category_seller_monthly AS
    SELECT
        seller_id,
        category_en,
        order_month,
        COUNT(DISTINCT order_id) AS orders,
        SUM(price) AS gmv_brl
    FROM delivered_items
    GROUP BY seller_id, category_en, order_month
;

SELECT *
FROM seller_monthly
WHERE seller_id = 'da8622b14eb17ae2831f4ac5b9dab84a'
ORDER BY order_month;


-- 同类商家比较：主营品类首尾月份均至少5单。
WITH peer_base AS (
    SELECT
        seller_id,
        MAX(CASE WHEN order_month = '2018-04' THEN orders END) AS orders_apr,
        MAX(CASE WHEN order_month = '2018-07' THEN orders END) AS orders_jul,
        MAX(CASE WHEN order_month = '2018-04' THEN gmv_brl END) AS gmv_apr,
        MAX(CASE WHEN order_month = '2018-07' THEN gmv_brl END) AS gmv_jul
    FROM category_seller_monthly
    WHERE category_en = 'bed_bath_table'
      AND order_month IN ('2018-04', '2018-07')
    GROUP BY seller_id
)
SELECT
    seller_id,
    orders_apr,
    orders_jul,
    gmv_apr,
    gmv_jul,
    gmv_jul / NULLIF(gmv_apr, 0) - 1 AS gmv_change
FROM peer_base
WHERE orders_apr >= 5
  AND orders_jul >= 5
ORDER BY gmv_change;


-- 成交SKU迁移：未成交不等同于缺货或下架，只用于确定核查对象。
WITH target_skus AS (
    SELECT
        product_id,
        SUM(CASE WHEN order_month = '2018-04' THEN price ELSE 0 END) AS gmv_apr,
        SUM(CASE WHEN order_month = '2018-07' THEN price ELSE 0 END) AS gmv_jul
    FROM delivered_items
    WHERE seller_id = 'da8622b14eb17ae2831f4ac5b9dab84a'
      AND order_month IN ('2018-04', '2018-07')
    GROUP BY product_id
)
SELECT
    CASE
        WHEN gmv_apr > 0 AND gmv_jul > 0 THEN 'retained'
        WHEN gmv_apr > 0 AND gmv_jul = 0 THEN 'april_only'
        WHEN gmv_apr = 0 AND gmv_jul > 0 THEN 'july_new'
    END AS sku_group,
    COUNT(*) AS sku_count,
    SUM(gmv_apr) AS gmv_apr,
    SUM(gmv_jul) AS gmv_jul
FROM target_skus
GROUP BY sku_group
ORDER BY sku_group;
