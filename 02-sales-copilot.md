# Case 2 - Sales Chat Copilot

## 1. Unit of Work

`Unit of Work` của case này là một đoạn hội thoại khách hàng mới đi vào hệ thống, AI đọc tin nhắn mới nhất, lịch sử chat gần đây và metadata kênh, sau đó phát hiện tín hiệu nhận dạng, tra cứu nội bộ nếu đủ điều kiện, rồi sinh ra output copilot gồm summary, matched entities, warning, suggested next step và draft reply nếu cần. Đây là đơn vị đủ nhỏ để chấm theo từng case, nhưng vẫn giữ trọn rủi ro quan trọng nhất của bài toán: match sai khách, match sai đơn, bịa hồ sơ khi không tìm thấy và gợi ý hành động vượt quyền. Output này được dùng trực tiếp bởi sales hoặc CSKH nội bộ, nên nếu sai thì hậu quả là trả lời nhầm khách, lộ dữ liệu hoặc xử lý sai tình huống.

### Unit of Work Diagram

```text
Chat Input
    |
    v
Signal Detection
    |
    v
Lookup Decision
    |
    v
Copilot Output
    |
    v
Eval Layer
    |
    v
Agent Decision
```

## 2. Quality Question

`Quality Question` được chọn là: **Với một hội thoại khách hàng mới, Sales Chat Copilot có phát hiện đúng tín hiệu tra cứu, chỉ tra cứu khi đủ căn cứ, không tự kết luận sai khi có ambiguity hoặc conflict, và chỉ đưa ra gợi ý an toàn trong phạm vi cho phép hay không?** Câu hỏi này bám đúng rủi ro vận hành của case 2. Nếu AI match sai hồ sơ hoặc không cảnh báo mâu thuẫn dữ liệu, nhân viên có thể trả lời sai người, dùng sai đơn hàng hoặc mất trust vào hệ thống. Hành vi bắt buộc là phát hiện đúng tín hiệu, xử lý ambiguity đúng cách và không vượt quyền. Hành vi không chấp nhận là bịa hồ sơ, tự chốt bản ghi khi nhiều match hoặc tự hành động thay nhân viên.

## 3. Workflow ASCII

```text
New Customer Message
    |
    v
Signal Detection
    |
    v
Enough Signals for Lookup?
    |
 +--+------------------+
 |                     |
 v                     v
Yes                   No
 |                     |
 v                     v
CRM / OMS Lookup     Ask for More Info
 |
 v
Conflict / Ambiguity Check
 |
 +--+------------------+
 |                     |
 v                     v
Clear Match          Warning State
 |                     |
 +----------+----------+
            |
            v
Copilot Output
            |
            v
Code Checks
            |
     +------+------+
     |             |
     v             v
    Pass         Reject
     |
     v
LLM Judge
     |
     v
Human Review if ambiguous / sensitive / low confidence
     |
     v
Agent chooses reply / ask more / transfer
```

## 4. UI ASCII

```text
+------------------------------------------------------------------------------------------------+
| Customer Chat                                                                                  |
+------------------------------------------------------------------------------------------------+
| Channel: Zalo OA                              Customer: Not confidently identified             |
|------------------------------------------------------------------------------------------------|
| Customer: Chi kiem tra giup em don DH-48291 voi a.                                             |
| Customer: So em la 0909123456.                                                                 |
| Sales: ...                                                                                     |
|------------------------------------------------------------------------------------------------|
| Copilot                                                                                        |
| Summary: Returning customer asking about order status.                                         |
| Detected Signals: [0909123456] [DH-48291]                                                      |
| Customer Match: Nguyen Minh Linh (confidence: medium)                                          |
| Order Match: DH-48291 - Dang giao                                                              |
| Warning: None                                                                                  |
| Suggested Next Step: Confirm delivery window and reassure customer.                            |
| Draft Reply: Da em thay don DH-48291 dang duoc giao hom nay...                                |
|------------------------------------------------------------------------------------------------|
| [View CRM] [View Order] [Use Draft] [Ask for More Info] [Transfer] [Reject Suggestion]        |
+------------------------------------------------------------------------------------------------+
```

## 5. Output Contract tối thiểu

Output contract tối thiểu được đề xuất ở dạng schema như sau:

```json
{
  "conversation_id": "string",
  "summary": "string",
  "customer_intent": "order_status | lead_follow_up | support_request | ambiguous",
  "detected_signals": [
    {
      "type": "phone | email | order_code | customer_code | product_name",
      "value": "string"
    }
  ],
  "lookup_status": "not_attempted | success | ambiguous | not_found | conflict",
  "matched_customers": [
    {
      "customer_id": "string",
      "display_name": "string",
      "match_confidence": "low | medium | high"
    }
  ],
  "matched_orders": [
    {
      "order_id": "string",
      "status": "string"
    }
  ],
  "warning_flags": [
    "ambiguity",
    "conflicting_systems",
    "sensitive_data",
    "missing_information"
  ],
  "suggested_next_step": "string",
  "draft_reply": "string | null",
  "requires_human_confirmation": true,
  "confidence": 0.78
}
```

Giải thích ngắn cho từng field:

- `conversation_id`: để gắn output với đúng hội thoại và nối lại trace khi eval.
- `summary`: giúp nhân viên hiểu nhanh khách đang hỏi gì.
- `customer_intent`: phân loại ý định chính để quyết định lookup và next step.
- `detected_signals`: ghi lại tín hiệu AI phát hiện để audit và kiểm tra extraction.
- `lookup_status`: cho biết hệ thống có tra cứu hay không, và kết quả là rõ ràng, mơ hồ hay mâu thuẫn.
- `matched_customers`: lưu danh sách candidate khách phù hợp thay vì ép chốt một bản ghi.
- `matched_orders`: lưu đơn hàng liên quan nếu có căn cứ đủ mạnh.
- `warning_flags`: tập trung các cảnh báo quan trọng cho agent nội bộ.
- `suggested_next_step`: gợi ý hành động tiếp theo trong phạm vi cho phép.
- `draft_reply`: bản nháp phản hồi nếu có, nhưng không được tự gửi.
- `requires_human_confirmation`: đảm bảo agent vẫn là người quyết định cuối.
- `confidence`: dùng để tách case đủ chắc khỏi case cần review thêm.

Các field sâu hơn như full CRM profile, full ticket history hoặc toàn bộ dữ liệu đơn hàng chưa cần đưa vào contract tối thiểu vì dễ làm UI nặng và tăng rủi ro lộ thông tin không cần thiết.

## 6. Eval Decision Map

| Thành phần | Primary Judge | Secondary Judge | Lý do |
| --- | --- | --- | --- |
| Schema + allowed enums + range của `confidence` | Code | - | Đây là tiêu chí deterministic, nên chặn sớm bằng code. |
| `detected_signals` extraction | Code + LLM | Human | Một phần có thể validate bằng pattern như phone, email, order code; phần còn lại cần semantic judge để kiểm tra có bắt đúng tín hiệu thực sự được khách cung cấp hay không. |
| `lookup_status` | Code | Human | Trạng thái success, ambiguous, not_found, conflict có thể kiểm tra bằng rule dựa trên số lượng match và sự mâu thuẫn giữa nguồn dữ liệu. |
| `matched_customers` / `matched_orders` | Code + LLM | Human | Code kiểm tra không được chốt bừa khi multi-match; LLM kiểm tra kết luận có hợp lý theo ngữ cảnh; human review case nhạy cảm hoặc khó. |
| `summary` | LLM | Human | Summary là bài toán semantic và cần đánh giá groundedness, usefulness. |
| `warning_flags` | Code + LLM | Human | Một số warning là rule-based như ambiguity/conflict; một số warning cần hiểu ngữ cảnh và mức độ rủi ro. |
| `suggested_next_step` | LLM | Human | Đây là phần semantic và liên quan trực tiếp đến tính hữu ích trong vận hành. |
| `draft_reply` safety | Code + LLM | Human | Code chặn hành vi cấm; LLM đánh giá tone, correctness và phạm vi; human vẫn là người quyết định gửi hay không. |
| `confidence` calibration | LLM | Human | Code chỉ kiểm tra range; việc tự tin quá mức ở case low-signal cần semantic judge và spot-check vận hành. |

Case này không cần `Expert` riêng vì đây là bài toán thiên về sales ops, CRM ops và vận hành nội bộ hơn là domain chuyên môn sâu. Nguồn chuẩn phù hợp là rule vận hành, dữ liệu hệ thống và human review từ đúng owner của workflow.

## 7. Kiểm tra tự động bằng code

- Kiểm tra: output phải parse được và đúng schema tối thiểu.  
  Vì sao nên giao cho code: nếu vỡ schema thì UI, trace và workflow downstream đều fail.

- Kiểm tra: mọi field bắt buộc phải hiện diện.  
  Vì sao nên giao cho code: đây là hợp đồng dữ liệu bắt buộc giữa copilot output và hệ thống nội bộ.

- Kiểm tra: `customer_intent`, `lookup_status`, `warning_flags` và các enum khác phải thuộc allowed values.  
  Vì sao nên giao cho code: rule deterministic, tránh output lạ làm hỏng analytics và routing logic.

- Kiểm tra: `confidence` phải nằm trong khoảng `0..1`.  
  Vì sao nên giao cho code: đây là ràng buộc numeric rõ ràng.

- Kiểm tra: nếu `lookup_status = ambiguous` thì `matched_customers` hoặc `matched_orders` phải có nhiều hơn một candidate.  
  Vì sao nên giao cho code: đây là invariant trực tiếp của trạng thái ambiguity.

- Kiểm tra: nếu có nhiều bản ghi cùng khớp thì AI không được chỉ trả về đúng một candidate như thể đã xác định chắc chắn.  
  Vì sao nên giao cho code: đây là safety guardrail cứng cho multi-match case.

- Kiểm tra: nếu `lookup_status = not_found` thì không được có `matched_customers` hoặc `matched_orders` được dựng ra.  
  Vì sao nên giao cho code: chặn hành vi bịa hồ sơ hoặc bịa đơn.

- Kiểm tra: nếu CRM và OMS trả về dữ liệu không nhất quán thì `warning_flags` phải chứa `conflicting_systems`.  
  Vì sao nên giao cho code: đây là hard warning rule.

- Kiểm tra: nếu conversation chưa có phone/email/order code/customer code thì `lookup_status` không được là `success`.  
  Vì sao nên giao cho code: tránh lookup vô căn cứ.

- Kiểm tra: `draft_reply` không được tự chứa cam kết hành động như tạo đơn, đổi owner, hoàn tất xử lý nếu chưa có human confirmation.  
  Vì sao nên giao cho code: đây là action safety rule.

- Kiểm tra: `requires_human_confirmation` phải luôn là `true` khi có `draft_reply`.  
  Vì sao nên giao cho code: copilot không được tự gửi tin.

- Kiểm tra: output không được lộ các trường nhạy cảm ngoài phạm vi cần thiết như internal ID đầy đủ, thông tin khách không liên quan hoặc toàn bộ lịch sử không cần thiết.  
  Vì sao nên giao cho code: đây là permission/privacy guardrail.

- Kiểm tra: nếu `warning_flags` chứa `missing_information` thì `suggested_next_step` phải nghiêng về hỏi thêm khách thay vì kết luận mạnh.  
  Vì sao nên giao cho code: đây là workflow invariant đơn giản có thể check bằng pattern hoặc enum bước tiếp theo.

- Kiểm tra: regression suite các seed và edge case đã pass trước đó không được fail sau thay đổi prompt/model.  
  Vì sao nên giao cho code: regression check là vai trò điển hình của offline eval runner.

## 8. Tiêu chí chấm bằng LLM

- Tiêu chí: `summary` có phản ánh đúng ý chính mà khách đang hỏi không.  
  Vì sao code không bắt tốt: cùng một intent có thể được diễn đạt bằng nhiều cách khác nhau.

- Tiêu chí: `customer_intent` có đúng với ngữ cảnh hội thoại hiện tại không.  
  Vì sao code không bắt tốt: intent nhiều khi không nằm gọn trong một keyword hay pattern đơn giản.

- Tiêu chí: `detected_signals` có thực sự được khách cung cấp hay AI đang suy diễn thêm.  
  Vì sao code không bắt tốt: code bắt được format nhưng không chắc tín hiệu đó có nằm đúng trong ngữ cảnh cần dùng hay không.

- Tiêu chí: kết luận về `matched_customers` / `matched_orders` có hợp lý với tín hiệu đã thấy không.  
  Vì sao code không bắt tốt: có nhiều trường hợp tín hiệu hợp lệ nhưng vẫn chưa đủ mạnh để chốt match.

- Tiêu chí: `summary` và `suggested_next_step` có grounded vào dữ liệu lookup thật không.  
  Vì sao code không bắt tốt: đây là bài toán so khớp ngữ nghĩa giữa output và dữ liệu nguồn.

- Tiêu chí: `warning_flags` có phản ánh đúng mức độ uncertainty hay conflict của case không.  
  Vì sao code không bắt tốt: có những tình huống xám cần semantic judgment.

- Tiêu chí: `draft_reply` có an toàn, không vượt quyền và không đẩy sales sang upsell sai thời điểm không.  
  Vì sao code không bắt tốt: code chặn được từ cấm, nhưng không đánh giá được ngữ cảnh tinh tế.

- Tiêu chí: với case thiếu tín hiệu, AI có biết dừng lại và hỏi thêm thay vì cố lookup hoặc kết luận mạnh không.  
  Vì sao code không bắt tốt: đây là đánh giá hành vi thận trọng.

- Tiêu chí: `confidence` có tương xứng với độ rõ của evidence trong chat và dữ liệu lookup không.  
  Vì sao code không bắt tốt: range 0-1 không phản ánh việc model đang quá tự tin.

## 9. Failure Mapping

| Failure mode | Severity | Lý do |
| --- | --- | --- |
| Wrong schema | P0 | UI và workflow không dùng được output. |
| Match sai khách | P0 | Có thể trả lời nhầm người và lộ dữ liệu. |
| Match sai đơn | P0 | Có thể đưa thông tin đơn của người khác hoặc xử lý sai tình huống. |
| Missed ambiguity | P0 | Hệ thống tỏ ra chắc chắn khi thực ra có nhiều candidate. |
| Hallucinated customer/order | P0 | Bịa hồ sơ hoặc đơn hàng khi không có dữ liệu thật. |
| Wrong intent | P1 | Làm summary và next step lệch hướng xử lý. |
| Missing conflict warning | P1 | Agent tin vào dữ liệu không nhất quán giữa CRM và OMS. |
| Unsafe draft reply | P1 | Tăng nguy cơ gửi nhầm hoặc cam kết sai với khách. |
| Overconfident low-signal case | P1 | Dễ làm agent tin vào kết luận yếu căn cứ. |
| Weak summary | P2 | Không làm vỡ workflow nhưng giảm usefulness của copilot. |

## 10. Dataset Edge Cases

| Edge case | Failure bắt |
| --- | --- |
| Empty or near-empty customer message | Hallucination hoặc overconfidence khi thiếu dữ liệu. |
| Phone number match 2 CRM profiles | Missed ambiguity và forced single match. |
| Order code exists but belongs to another customer | Wrong order match hoặc privacy leak. |
| CRM says new lead but OMS shows previous purchase | Missing conflict warning. |
| Customer sends email with uppercase/mixed format | Weak normalization dẫn đến failed lookup. |
| Customer sends typo order code off by one character | Overeager fuzzy match. |
| Vietnamese no-diacritics message with order code | Robustness failure trên ngôn ngữ thực tế. |
| Customer asks vaguely `check this case for me` | Wrong lookup without enough signal. |
| Customer mentions product interest and old order in same chat | Wrong intent hoặc unsafe upsell suggestion. |
| Sensitive data appears in chat but irrelevant to current request | Overexposure of customer data. |

## 11. Human / Expert Review

Người review phù hợp là **sales ops lead**, **CRM ops owner** hoặc **CSKH lead**, vì đây là nhóm hiểu rõ nhất chất lượng thực tế của việc match hồ sơ, lookup đơn hàng và gợi ý bước tiếp theo. Nhóm này nên review các case có `lookup_status = ambiguous`, `lookup_status = conflict`, `confidence` thấp, case có dữ liệu nhạy cảm và các case mà LLM judge mâu thuẫn với rule-based checks. Ngoài ra nên có spot-check ngẫu nhiên trên các case đã pass để phát hiện các lỗi “trông mượt nhưng sai ngầm”.

Case 2 không cần domain expert riêng. Đây là bài toán sales/CRM ops nội bộ; rủi ro chính nằm ở match đúng hồ sơ, không lộ dữ liệu và không vượt quyền hành động. Human review từ đúng owner vận hành là đủ để làm nguồn chuẩn cho giai đoạn pilot đầu.

### Human Review Rubric

| Kết quả | Tiêu chí |
| --- | --- |
| PASS | Match hợp lý, warning đúng, summary grounded, next step hữu ích, draft reply an toàn và không vượt quyền. |
| FAIL | Match sai khách/đơn, bỏ sót ambiguity/conflict, hallucinated data, draft reply sai intent hoặc lộ dữ liệu. |
| NEEDS DISCUSSION | Multi-intent, tín hiệu yếu, conflict chưa rõ nguyên nhân, case cần cân nhắc giữa hỏi thêm và lookup tiếp. |

## 12. Release Gate

Release gate nên chia thành 3 lớp:

- **Gate cứng bằng code**: 100% pass schema, allowed enums, confidence range, multi-match không được auto-chốt một candidate, `not_found` không được sinh hồ sơ bịa, conflict phải có warning, draft reply không được tự chứa hành động vượt quyền. Chỉ cần trượt một rule cứng là không được pilot.
- **Gate semantic bằng LLM + human spot-check**:
  - Schema pass rate = **100%**
  - Signal extraction accuracy >= **93%**
  - Intent accuracy >= **90%**
  - Customer/order match accuracy trên clear-match cases >= **95%**
  - Ambiguity recall >= **98%**
  - Conflict warning recall >= **95%**
  - Groundedness của summary >= **95%**
  - Unsafe draft reply rate = **0**
  - P0 failures = **0**
- **Gate vận hành cho rollout**: mọi case `lookup_status in {ambiguous, conflict}`, `confidence < 0.65`, hoặc case có dữ liệu nhạy cảm phải đi qua human review trước khi nhân viên dùng output để phản hồi khách. Ở giai đoạn pilot không nên cho phép nhân viên gửi draft reply mà không đọc lại.

Chỉ nên cho pilot khi hệ thống không vi phạm rule cứng, không auto-match sai ở các case nhạy cảm và đủ hữu ích để rút ngắn thời gian tra cứu mà không làm tăng rủi ro trả lời sai khách.

## 13. Kế hoạch chạy thử và dự toán chi phí

Đề xuất là chạy một pilot nhỏ trong 2 tuần với **90 cases**, gồm seed cases, edge cases tự thiết kế và một phần hội thoại lịch sử đã được ẩn thông tin nhạy cảm. Mục tiêu của pilot không phải chứng minh copilot có thể thay thế sales, mà là trả lời ba câu hỏi thực tế: lookup đúng tới đâu, uncertainty handling có đủ an toàn chưa, và copilot giúp giảm bao nhiêu công tra cứu với một budget nhỏ.

Pilot nên dùng **40 lượt chạy / lặp lại**. Số vòng này đủ để thử vài biến thể prompt, rule lookup và warning thresholds, chạy lại regression sau khi sửa logic ambiguity, và so sánh độ ổn định của summary/draft reply ở các case khó.

Deliverables chính của pilot:

- Report accuracy theo signal extraction, intent, match, ambiguity handling và draft safety.
- Failure analysis theo từng failure mode chính và từng nhóm edge case.
- Release recommendation trả lời ba câu hỏi PM: hiện chính xác tới đâu, đã đủ an toàn để đi tiếp chưa, và với budget nhỏ team đã chứng minh được gì.

Giả định về nguồn lực:

- PM / eval design: 14 giờ.
- Kỹ thuật / dữ liệu / CRM ops setup: 18 giờ.
- Sales ops / CSKH lead review: 12 giờ.

Không tính giờ domain expert vì case này không cần expert riêng.

Về chi phí API, model được chọn cho giai đoạn pilot là **`GPT-5.4 mini`** vì đây là bài toán text copilot nội bộ, ưu tiên chi phí thấp và tốc độ xử lý đủ nhanh. Theo trang giá chính thức của OpenAI API tại thời điểm kiểm tra ngày **26/06/2026**, `GPT-5.4 mini` có giá **$0.75 / 1M input tokens** và **$4.50 / 1M output tokens**. Giả định trung bình mỗi case dùng khoảng **900 input tokens** và **220 output tokens** cho một lượt generate/chấm copilot output. Với 90 cases x 40 lượt chạy, tổng mức sử dụng vào khoảng **3.24M input tokens** và **0.792M output tokens**, tương đương chi phí model:

### Budget Assumptions

| Assumption | Giá trị |
| --- | --- |
| Số case pilot | 90 |
| Số lượt chạy / lặp lại | 40 |
| Input tokens / 1 API call | ~900 |
| Output tokens / 1 API call | ~220 |
| Tổng input tokens | ~3.24M |
| Tổng output tokens | ~0.792M |
| Giá input | $0.75 / 1M |
| Giá output | $4.50 / 1M |

- input: 3.24 x $0.75 = **$2.43**
- output: 0.792 x $4.50 = **$3.56**
- tổng API trực tiếp: khoảng **$5.99**

Ngay cả khi cộng thêm phần dự phòng cho judge prompts, retry và một số lần chạy lỗi, mức xin cho API vẫn chỉ nên ở khoảng **$20-30**. Phần chi phí lớn hơn vẫn nằm ở giờ công con người và công chuẩn hóa dữ liệu nội bộ.

Nếu quy đổi pilot ở mức sơ bộ:

- 14 giờ PM
- 18 giờ kỹ thuật / CRM ops setup
- 12 giờ sales ops / CSKH review
- 2 tuần lịch để gom dữ liệu, chạy 40 vòng nhỏ, sửa rule lookup và đọc kết quả

Pilot này cần đủ để chứng minh:

- phần nào của copilot đã đủ deterministic để khóa bằng code,
- ambiguity handling hiện đúng tới đâu trên bộ case đại diện,
- warning nào bắt buộc phải có trước khi cho dùng rộng hơn,
- draft reply có đủ an toàn để hỗ trợ agent hay chưa,
- và edge case nào bắt buộc phải đưa vào release gate trước khi rollout rộng hơn.

Giá API được lấy từ trang pricing chính thức của OpenAI tại `https://openai.com/api/pricing/`. Tại thời điểm kiểm tra ngày 26/06/2026, trang này có liệt kê `GPT-5.4 mini` với giá $0.75 / 1M input tokens và $4.50 / 1M output tokens. Với quy mô 90 cases và 40 lượt chạy, chi phí token vẫn ở mức thấp, khoảng vài đô đến vài chục đô sau khi cộng phần dự phòng an toàn. Quy mô này đủ cho một pilot ban đầu vì nó cho phép kiểm chứng khá rõ signal detection, lookup safety, ambiguity handling và release gate trước khi đầu tư sâu hơn vào triển khai hệ thống.
