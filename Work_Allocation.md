# Work Allocation

```text
目前的文件內容為AI複製貼上，待修改。
```

## 👨‍💻 隊員 A（建議由 Team Lead 或 SQL 較熟的人擔任）

### 主導核心：PostgreSQL 關係型資料庫實作 (Task 1 + 基礎建設)

* **負責檔案**：
* databases/relational/schema.sql (設計 DDL 綱要)
* skeleton/seed_postgres.py (實作大部份的 SQL 資料匯入)

* **對應 JSON**：`registered_users.json`、`bookings.json`、`payments.json`、`feedback.json`。
* **職責描述**：

1. 負責搞定基礎建設（Docker、環境變數與 AI 模型切換測試）。
2. 研究使用者、訂票、付款與回饋這四個欄位重複性高、具備嚴格外部鍵（Foreign Key）關係的資料。
3. 設計 PostgreSQL 綱要，並撰寫大量邏輯較複雜的 SQL 批次灌資料腳本（Seeding）。

---

## 👩‍💻 隊員 B

### 主導核心：Neo4j 圖形資料庫與鐵路網拓撲 (Task 2)

* **負責檔案**：
* databases/graph/seed.cypher (定義圖形節點與關係)
* skeleton/seed_neo4j.py (實作 Cypher 匯入邏輯)
* databases/graph/queries.py (圖形演算法查詢，如最短路徑、轉乘)

* **對應 JSON/HTML**：`metro_stations.json`、`national_rail_stations.json`、`metro_schedules.json`、`national_rail_schedules.json`、`network_map.html`。
* **職責描述**：

1. 研究捷運線、鐵路網的實體連接關係（哪些站跟哪些站相鄰、轉乘時間多少）。
2. 在 Neo4j 建立 MetroStation 與 NationalRailStation 節點，並拉出 METRO_LINK 和 INTERCHANGE_TO 的關係線。
3. 確保 AI 助理能回答「最快路線怎麼走？」或「某站封閉時的替代方案」等圖形網絡圖問題。

---

## 👨‍💻 隊員 C

### 主導核心：pgvector 向量資料庫與 RAG 政策庫延伸 (Task 3 + 4 擴充)

* **負責檔案**：
* train-mock-data/ 裡所有的 Policy JSON 檔案擴充（Task 3）
* databases/relational/queries.py 或特定功能延伸（Task 4）
* 負責幫忙串接新工具（Advanced 部分）。

* **對應 JSON**：`booking_rules.json`、`refund_policy.json`、`ticket_types.json`、`travel_policies.json`。
* **職責描述**：

1. 負責 RAG（檢索增強生成）的政策文本部分。研究如何擴充鐵路的營運規章（如：寵物規定、腳踏車攜帶、遺失物處理等），將它們整理進 JSON。
2. 配合執行 `seed_vectors.py`，確保向量模型的維度與 .env 的 AI 供應商（Ollama 的 768 或 Gemini 的 3072）完美匹配。
3. 與隊員 A、B 合作，撰寫 AI Agent 需要呼叫的查詢 Function（`queries.py`），並按照 Advanced 步驟將新功能註冊為 AI 的「工具（Tools）」。
