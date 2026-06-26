# Case 1 - Support Ticket Triage

## 1. Unit of Work

`Unit of Work` của case này là một ticket support mới đi vào hệ thống, AI đọc `subject`, `message`, `customer_tier` và sinh ra output triage gồm category, urgency, route, requires_human, queue_priority, confidence và reason. Đây là đơn vị đủ nhỏ để chấm độc lập theo từng case, nhưng vẫn giữ trọn các rủi ro vận hành quan trọng nhất: route sai team, bỏ sót escalation và làm chậm xử lý ticket enterprise. Output này được dùng trực tiếp trong inbox nội bộ, nên nếu sai thì hậu quả là sai quyết định vận hành chứ không chỉ sai nhãn phân loại.

### Unit of Work Diagram

```text
Ticket Input
    |
    v
AI Triage
    |
    v
Triage Output
    |
    v
Eval Layer
    |
    v
Queue Decision
```

## 2. Quality Question

`Quality Question` được chọn là: **Với một ticket support mới, AI có tạo ra triage output đủ đúng để ticket vào đúng hàng xử lý, không bỏ sót case cần escalation, và không kết luận quá mức khi thông tin còn mơ hồ hay không?** Câu hỏi này bám sát rủi ro vận hành của bài toán. Nếu AI route sai hoặc đánh urgency quá thấp, ticket có thể đi sai đội, chậm SLA và làm giảm trust của team support. Hành vi bắt buộc là đúng route, đúng escalation logic và đúng schema. Hành vi không chấp nhận là bỏ sót tín hiệu high-risk hoặc đưa ra reason không bám input.

## 3. Workflow ASCII

```text
New Ticket
    |
    v
AI Triage
    |
    v
Code Checks
    |
 +--+------------------+
 |                     |
 v                     v
Pass                 Reject
 |
 v
LLM Judge
 |
 v
Confidence < 0.6 ?
 |
 +-----------+------------------+
 |                              |
 v                              v
Yes                            No
 |                              |
 v                              v
Human Review                Queue Assignment
 |
 v
Approve / Edit / Escalate
```

## 4. UI ASCII

```text
+--------------------------------------------------------------+
| Ticket Triage Inbox                                          |
+--------------------------------------------------------------+
| Ticket ID: T-002                                             |
| Customer Tier: Enterprise                                    |
| Subject: URGENT: payment failed and account disabled         |
|--------------------------------------------------------------|
| Message                                                      |
| Our team is locked out because your billing system failed.   |
| Fix this now.                                                |
|--------------------------------------------------------------|
| AI Suggestion                                                |
| Category: Billing                                            |
| Urgency: Critical                                            |
| Route: Billing Ops                                           |
| Requires Human: YES                                          |
| Queue Priority: High Priority                                |
| Confidence: 0.81                                             |
| Reason: Billing failure caused account lockout for an        |
| enterprise customer and is blocking work.                    |
|--------------------------------------------------------------|
| [Approve] [Edit] [Reject] [Escalate] [Comment]               |
+--------------------------------------------------------------+
```

## 5. Output Contract tối thiểu

Output contract tối thiểu được đề xuất ở dạng schema như sau:

```json
{
  "ticket_id": "string",
  "category": "technical | billing | feature_request | unknown",
  "urgency": "low | medium | high | critical",
  "route_to": "technical_support | billing_ops | product_team | support_l1 | human_escalation",
  "requires_human": true,
  "queue_priority": "normal | high_priority",
  "reason_summary": "string",
  "reason_codes": [
    "login_issue",
    "billing_failure",
    "blocked_work",
    "locked_out",
    "account_disabled"
  ],
  "confidence": 0.82
}
```

Giải thích ngắn cho từng field:

- `ticket_id`: để gắn output với đúng ticket và nối lại trace khi eval.
- `category`: quyết định phân loại chính hiển thị trên UI và ảnh hưởng trực tiếp đến routing.
- `urgency`: quyết định mức độ khẩn và tác động đến hàng chờ xử lý.
- `route_to`: đích vận hành thực tế của ticket.
- `requires_human`: cờ xác định case có cần người xử lý ngay hay không.
- `queue_priority`: cho biết ticket vào hàng bình thường hay ưu tiên cao.
- `reason_summary`: giải thích ngắn để nhân viên support hiểu vì sao hệ thống đưa ra gợi ý đó.
- `reason_codes`: phục vụ audit và eval, giúp kiểm tra output có bám đúng tín hiệu trong ticket hay không.
- `confidence`: dùng để tách case đủ chắc khỏi case cần review thêm.

Các field như sentiment, account history hay previous ticket stats chưa cần đưa vào contract tối thiểu vì không quyết định trực tiếp UI hiện tại, route hay release gate của case này.

## 6. Eval Decision Map

| Thành phần | Primary Judge | Secondary Judge | Lý do |
| --- | --- | --- | --- |
| Schema + allowed enums + range của `confidence` | Code | - | Đây là tiêu chí deterministic, có thể fail/pass rõ ràng và nên chặn sớm bằng code. |
| `category` | LLM | Human | Category phụ thuộc vào hiểu nghĩa ticket; human dùng để calibration và review disagreement. |
| `urgency` | LLM | Human | Có lower-bound hard rule, nhưng mức high hay critical vẫn cần semantic judgment và kiểm tra vận hành. |
| `route_to` | Code + LLM | Human | Code chặn các hard rule như billing không vào `product_team`; LLM quyết định route theo ngữ nghĩa; human review case khó. |
| `requires_human` | Code | Human | Rule enterprise + high/critical là deterministic, nhưng human cần xem lại các case mơ hồ và threshold review. |
| `reason_summary` và `reason_codes` groundedness | LLM | Human | Code khó xác minh chất lượng giải thích; cần judge xem reason có bám ticket, có thiếu tín hiệu quan trọng hay bịa thêm không. |
| `confidence` calibration | LLM | Human | Code chỉ check được range 0-1; việc tự tin quá mức ở case low-info phải nhờ semantic judge và review vận hành. |

Case này không cần `Expert` riêng vì support triage trong bối cảnh này chưa chạm domain đòi hỏi chuyên môn sâu như y khoa hay pháp lý. Nguồn chuẩn phù hợp hơn là rule vận hành kết hợp với human review của support ops.

## 7. Kiểm tra tự động bằng code

- Kiểm tra: output phải parse được và đúng schema tối thiểu.  
  Vì sao nên giao cho code: pass/fail rõ ràng; nếu vỡ schema thì UI và downstream workflow đều fail.

- Kiểm tra: mọi field bắt buộc (`ticket_id`, `category`, `urgency`, `route_to`, `requires_human`, `queue_priority`, `reason_summary`, `reason_codes`, `confidence`) phải hiện diện.  
  Vì sao nên giao cho code: đây là hợp đồng dữ liệu bắt buộc giữa AI output và hệ thống nội bộ.

- Kiểm tra: `category`, `urgency`, `route_to`, `queue_priority` phải thuộc allowed enums.  
  Vì sao nên giao cho code: rule deterministic, tránh output lạ làm hỏng routing hoặc analytics.

- Kiểm tra: `confidence` phải nằm trong khoảng `0..1`.  
  Vì sao nên giao cho code: đây là ràng buộc numeric rõ ràng.

- Kiểm tra: nếu `customer_tier = enterprise` và `urgency in {high, critical}` thì `requires_human = true`.  
  Vì sao nên giao cho code: business rule cứng của bài toán.

- Kiểm tra: ticket billing không được route sang `product_team`.  
  Vì sao nên giao cho code: đây là hard routing guardrail.

- Kiểm tra: nếu ticket chứa các dấu hiệu `blocking work`, `locked out`, `account disabled` thì `urgency` không được là `low`.  
  Vì sao nên giao cho code: đây là lower-bound safety rule dễ biểu diễn bằng pattern/rule.

- Kiểm tra: nếu `requires_human = true` thì `queue_priority` không được là `normal`.  
  Vì sao nên giao cho code: đây là invariant vận hành để tránh cờ escalation nhưng vẫn nằm sai hàng chờ.

- Kiểm tra: nếu `urgency = critical` thì `queue_priority` phải là `high_priority`.  
  Vì sao nên giao cho code: quan hệ này đủ deterministic cho v1 của triage.

- Kiểm tra: `reason_summary` không được rỗng và phải vượt độ dài tối thiểu, ví dụ >= 12 ký tự.  
  Vì sao nên giao cho code: không đánh giá được chất lượng giải thích, nhưng loại được output trống hoặc quá yếu.

- Kiểm tra: `reason_codes` phải là mảng không rỗng và tất cả phần tử thuộc enum cho phép.  
  Vì sao nên giao cho code: giúp giữ trace giải thích ở dạng chuẩn hóa và dễ audit.

- Kiểm tra: với case `unknown` hoặc low-info, `confidence` không được vượt ngưỡng quá cao, ví dụ > 0.85.  
  Vì sao nên giao cho code: đây là guardrail đơn giản để bắt lỗi tự tin quá mức ở các case mơ hồ.

- Kiểm tra: nếu `route_to = human_escalation` thì `requires_human` phải là `true`.  
  Vì sao nên giao cho code: invariant trực tiếp của workflow.

- Kiểm tra: output không được sinh field lạ làm thay đổi contract downstream ngoài danh sách cho phép.  
  Vì sao nên giao cho code: giúp contract ổn định qua các lần iterate.

- Kiểm tra: regression suite các seed và edge case đã pass trước đó không được fail sau thay đổi prompt/model.  
  Vì sao nên giao cho code: regression check là vai trò điển hình của offline eval runner về sau.

## 8. Tiêu chí chấm bằng LLM

- Tiêu chí: `category` có phản ánh đúng bản chất vấn đề mà ticket đang nêu không.  
  Vì sao code không bắt tốt: cùng một vấn đề có thể được diễn đạt bằng nhiều cách khác nhau, không thể dựa hết vào keyword.

- Tiêu chí: `urgency` có hợp lý với mức độ ảnh hưởng vận hành được mô tả trong ticket không.  
  Vì sao code không bắt tốt: rule chỉ cho biết lower bound, còn phân biệt medium với high hay high với critical cần hiểu ngữ cảnh.

- Tiêu chí: `route_to` có hợp lý với nội dung ticket và category đã gán không.  
  Vì sao code không bắt tốt: nhiều ticket vừa chạm technical vừa chạm billing, cần semantic judgment để biết đội nào nên nhận đầu tiên.

- Tiêu chí: `reason_summary` có tóm tắt đúng tín hiệu chính khiến AI đưa ra route/urgency không.  
  Vì sao code không bắt tốt: code khó đánh giá chất lượng tóm tắt và độ hữu ích thực tế với agent.

- Tiêu chí: `reason_summary` và `reason_codes` có grounded vào input, không bịa thêm sự thật không có trong subject/message không.  
  Vì sao code không bắt tốt: đây là bài toán so khớp ngữ nghĩa giữa explanation và nội dung ticket.

- Tiêu chí: output có bỏ sót tín hiệu quan trọng như blocked work, locked out, payment failed hay không.  
  Vì sao code không bắt tốt: có thể ticket diễn đạt gián tiếp hoặc không dùng đúng keyword mẫu.

- Tiêu chí: với case low-info, AI có biết giữ `unknown` hoặc confidence thấp thay vì ép gán category mạnh không.  
  Vì sao code không bắt tốt: đây là đánh giá hành vi thận trọng, không chỉ là validate schema.

- Tiêu chí: `confidence` có tương xứng với độ rõ ràng của bằng chứng trong ticket không.  
  Vì sao code không bắt tốt: range 0-1 không phản ánh việc model đang quá tự tin.

## 9. Failure Mapping

| Failure mode | Severity | Lý do |
| --- | --- | --- |
| Wrong schema | P0 | Output không parse được thì UI và queue không dùng được. |
| Missed escalation | P0 | Ticket bị giữ ở hàng thường dù đáng lẽ phải có người xử lý ngay. |
| Wrong route | P1 | Ticket đi sai đội và làm chậm xử lý. |
| Wrong urgency | P1 | Làm lệch hàng chờ, ảnh hưởng SLA và thứ tự ưu tiên. |
| Hallucinated reason | P1 | Agent nội bộ nhận giải thích sai và dễ tin nhầm quyết định. |
| Overconfident on low-info case | P1 | Hệ thống kết luận quá mạnh ở case mơ hồ, làm tăng sai routing. |
| Missing reason codes | P2 | Giảm khả năng audit và khó phân tích lỗi về sau. |
| Weak reason summary | P2 | Không làm vỡ workflow nhưng giảm khả năng review của agent. |

## 10. Dataset Edge Cases

| Edge case | Failure bắt |
| --- | --- |
| Empty ticket hoặc message gần như trống | Hallucination hoặc overconfidence khi thiếu dữ liệu. |
| Billing + technical trong cùng một ticket | Wrong routing khi AI chỉ chọn một ý nổi bật bề mặt. |
| Angry enterprise customer nhưng mô tả chưa rõ | Missed escalation do bỏ qua tín hiệu mức độ ảnh hưởng. |
| Duplicate ticket gửi lại trong ngày | Wrong priority hoặc route không nhất quán. |
| Very short ticket như `Help ASAP` | Overconfidence ở low-info case. |
| Sarcasm hoặc câu viết cảm tính | Wrong urgency vì hiểu sai tone. |
| Subject và message mâu thuẫn nhau | Wrong category hoặc wrong route do chọn sai nguồn tín hiệu. |
| Ticket có từ `payment` nhưng thực ra là hỏi tính năng hoàn tiền | Keyword trap dẫn đến wrong category. |
| Ticket nói `cannot login` nhưng nguyên nhân là billing lockout | Route technical thay vì billing ops. |
| Enterprise ticket có blocked work nhưng ngôn ngữ gián tiếp | Missed escalation khi rule keyword không đủ bao phủ. |

## 11. Human / Expert Review

Người review phù hợp là **support ops lead** hoặc **triage owner** của team support, vì đây là nhóm hiểu SLA, queue thực tế và hậu quả của route sai tốt hơn reviewer thuần kỹ thuật. Nhóm này nên review các case có `confidence` thấp, `category = unknown`, ticket nhiều ý cùng lúc, ticket enterprise có dấu hiệu blocked work, và các case mà LLM judge mâu thuẫn với rule-based checks. Ngoài ra nên có spot-check ngẫu nhiên trên các case đã pass để phát hiện failure pattern mà rule chưa bắt được.

Case 1 không cần domain expert. Đây là bài toán support triage nội bộ trong domain SaaS phổ thông; rủi ro chính nằm ở vận hành, SLA và queue routing, chưa phải kết luận chuyên môn sâu. Human review từ đúng owner vận hành là đủ để làm nguồn chuẩn cho giai đoạn pilot đầu.

### Human Review Rubric

| Kết quả | Tiêu chí |
| --- | --- |
| PASS | Route đúng, urgency hợp lý, requires_human đúng, reason grounded, không bỏ sót tín hiệu quan trọng. |
| FAIL | Wrong team, missing escalation, hallucinated reason, urgency quá thấp, output mâu thuẫn với business rule. |
| NEEDS DISCUSSION | Multi-intent, ambiguity cao, subject/message mâu thuẫn, case quá ít dữ liệu để kết luận chắc chắn. |

## 12. Release Gate

Release gate nên chia thành 3 lớp:

- **Gate cứng bằng code**: 100% pass schema, allowed enums, confidence range, enterprise high/critical => requires_human, billing không route sang `product_team`, blocked-work signals không bị gán `low`. Chỉ cần trượt một rule cứng là không được pilot.
- **Gate semantic bằng LLM + human spot-check**:
  - Schema pass rate = **100%**
  - Category accuracy >= **92%**
  - Urgency accuracy >= **90%**
  - Route accuracy >= **92%**
  - Critical recall >= **98%**
  - Groundedness của `reason_summary`/`reason_codes` >= **95%**
  - P0 failures = **0**
- **Gate vận hành cho rollout**: mọi case `confidence < 0.6`, `category = unknown`, hoặc enterprise có tín hiệu blocked work phải đi qua human review trước khi ticket vào queue cuối cùng. Ở giai đoạn pilot chưa nên cho phép auto-triage âm thầm cho toàn bộ ticket.

Chỉ nên cho pilot khi hệ thống không vi phạm rule cứng, không bỏ sót escalation nguy hiểm và đủ hữu ích để giảm tải cho support triage mà không làm tăng tỷ lệ sai queue.

## 13. Kế hoạch chạy thử và dự toán chi phí

Đề xuất là chạy một pilot nhỏ trong 2 tuần với **80 cases**, gồm seed cases, edge cases tự thiết kế và một phần ticket lịch sử đã được ẩn thông tin nhạy cảm. Mục tiêu của pilot không phải chứng minh hệ thống có thể ship ngay, mà là trả lời ba câu hỏi thực tế: triage đúng tới đâu, lỗi nào còn lặp lại và cần thêm guardrail nào trước khi mở rộng.

Pilot nên dùng **40 lượt chạy / lặp lại**. Số vòng này đủ để thử một vài biến thể prompt/rule, chạy lại regression sau khi sửa route mapping và đo độ ổn định của confidence ở các case mơ hồ, trong khi vẫn phù hợp với quy mô của một case có nhiều phần deterministic.

Deliverables chính của pilot:

- Report accuracy theo category, urgency, route và escalation.
- Failure analysis theo từng failure mode chính và từng nhóm edge case.
- Release recommendation trả lời ba câu hỏi PM: hiện chính xác tới đâu, đã đủ an toàn để đi tiếp chưa, và với budget nhỏ team đã chứng minh được gì.

Giả định về nguồn lực:

- PM / eval design: 12 giờ.
- Kỹ thuật / vận hành dữ liệu: 14 giờ.
- Support ops lead / human review: 10 giờ.

Không tính giờ domain expert vì case này không cần expert riêng.

Về chi phí API, model được chọn cho giai đoạn pilot là **`GPT-5.4 mini`** vì đây là bài toán text triage nội bộ, ưu tiên chi phí thấp và tốc độ xử lý đủ nhanh. Theo trang giá chính thức của OpenAI API tại thời điểm tra cứu ngày **26/06/2026**, `GPT-5.4 mini` có giá **$0.75 / 1M input tokens** và **$4.50 / 1M output tokens**. Giả định trung bình mỗi case dùng khoảng **700 input tokens** và **180 output tokens** cho một lượt generate/chấm triage. Với 80 cases x 40 lượt chạy, tổng mức sử dụng vào khoảng **2.24M input tokens** và **0.576M output tokens**, tương đương chi phí model:

### Budget Assumptions

| Assumption | Giá trị |
| --- | --- |
| Số case pilot | 80 |
| Số lượt chạy / lặp lại | 40 |
| Input tokens / 1 API call | ~700 |
| Output tokens / 1 API call | ~180 |
| Tổng input tokens | ~2.24M |
| Tổng output tokens | ~0.576M |
| Giá input | $0.75 / 1M |
| Giá output | $4.50 / 1M |

- input: 2.24 x $0.75 = **$1.68**
- output: 0.576 x $4.50 = **$2.59**
- tổng API trực tiếp: khoảng **$4.27**

Ngay cả khi cộng thêm phần dự phòng cho judge prompts, retry và một số lần chạy lỗi, mức xin cho API vẫn chỉ nên ở khoảng **$15-25**. Phần chi phí lớn hơn vẫn nằm ở giờ công con người.

Nếu quy đổi pilot ở mức sơ bộ:

- 12 giờ PM
- 14 giờ kỹ thuật/vận hành
- 10 giờ support ops review
- 2 tuần lịch để gom dữ liệu, chạy 40 vòng nhỏ, sửa guardrail và đọc kết quả

Pilot này cần đủ để chứng minh:

- phần nào của triage đã đủ deterministic để khóa bằng code,
- route và escalation hiện đúng tới đâu trên bộ case đại diện,
- confidence threshold nào hợp lý để bật human review,
- edge case nào bắt buộc phải đưa vào release gate trước khi đề xuất rollout rộng hơn.

Giá API được lấy từ trang pricing chính thức của OpenAI tại `https://openai.com/api/pricing/`. Tại thời điểm kiểm tra ngày 26/06/2026, trang này có liệt kê `GPT-5.4 mini` với giá $0.75 / 1M input tokens và $4.50 / 1M output tokens. Với quy mô 80 cases và 40 lượt chạy, chi phí token vẫn ở mức thấp, khoảng vài đô đến vài chục đô sau khi cộng phần dự phòng an toàn. Quy mô này đủ cho một pilot ban đầu vì nó cho phép kiểm chứng khá rõ route, escalation behavior và chốt release gate trước khi đầu tư sâu hơn vào triển khai hệ thống.
