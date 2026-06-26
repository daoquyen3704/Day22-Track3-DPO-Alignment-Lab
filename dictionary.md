# Dictionary

Tài liệu này gom các thuật ngữ tiếng Anh và các identifier kỹ thuật có nghĩa xuất hiện trong repo, sắp theo thứ tự từ điển A-Z.

Phạm vi:
- Có giữ các thuật ngữ sản phẩm, eval, AI, workflow, field name, tên kỹ thuật và acronym có nghĩa.
- Không liệt kê các mã ví dụ thuần định danh như `T-001`, `SC-01`, `MC-01`, số điện thoại, email mẫu, tên người hay tên công ty mẫu.

## A

- **account_name**: Tên tài khoản hoặc tên tổ chức gắn với ticket/hồ sơ trong dữ liệu đầu vào.
- **action**: Hành động mà hệ thống hoặc người dùng dự kiến thực hiện tiếp theo.
- **Agent**: Tác nhân AI hoặc hệ thống AI thực hiện một nhóm nhiệm vụ thay mặt người dùng.
- **Agent Success Rate**: Tỷ lệ tác nhân AI hoàn thành đúng công việc mong muốn; thường là chỉ số chất lượng tổng quát quan trọng.
- **AI**: Artificial Intelligence; trí tuệ nhân tạo.
- **AI Flywheel**: Vòng lặp cải tiến liên tục của hệ thống AI, thường đi từ trace -> dataset -> eval -> cải tiến -> monitoring.
- **ambiguity**: Tình huống mơ hồ, không đủ chắc chắn để kết luận một nghĩa, một bản ghi hoặc một route duy nhất.
- **Ambiguous**: Mơ hồ; thường dùng để mô tả case hoặc tín hiệu không đủ rõ.
- **API**: Application Programming Interface; giao diện cho phép hệ thống gọi dịch vụ hoặc chức năng của hệ thống khác.
- **application eval**: Đánh giá AI trong ngữ cảnh một ứng dụng cụ thể, thay vì đánh giá năng lực chung của model.
- **ASCII**: Bộ ký tự cơ bản thường dùng để vẽ giao diện hoặc workflow dạng text.
- **assertion**: Kiểm tra khẳng định bằng code; nếu điều kiện không đúng thì xem như fail.

## B

- **B2B**: Business-to-Business; mô hình doanh nghiệp bán cho doanh nghiệp.
- **backend**: Phần xử lý phía máy chủ hoặc hệ thống nội bộ phía sau giao diện người dùng.
- **behavior**: Hành vi mà AI thể hiện khi xử lý một case.
- **benchmark**: Bộ chuẩn hoặc bộ bài kiểm tra dùng để so sánh chất lượng.
- **bias**: Thiên lệch trong đánh giá hoặc trong kết quả do con người, dữ liệu, rubric hoặc model gây ra.
- **billing**: Liên quan đến thanh toán, hóa đơn, tính phí.
- **billing_ops**: Nhóm vận hành xử lý các vấn đề về billing.
- **boundary**: Ranh giới hệ thống không được vượt qua, ví dụ ranh giới giữa gợi ý và chẩn đoán.
- **brief**: Mô tả ngắn về bài toán hoặc yêu cầu.
- **budget**: Ngân sách; khoản chi phí dự kiến để chạy pilot, eval hoặc vận hành.
- **business rule**: Quy tắc nghiệp vụ do công ty đặt ra để hệ thống phải tuân theo.

## C

- **calibration**: Hiệu chỉnh cách chấm của LLM hoặc rubric sao cho gần với đánh giá của con người.
- **call center**: Trung tâm tổng đài tiếp nhận cuộc gọi của khách hàng hoặc bệnh nhân.
- **case**: Một tình huống, mẫu dữ liệu hoặc đơn vị thử nghiệm cụ thể.
- **category**: Nhãn phân loại chính của ticket, câu hỏi hoặc yêu cầu.
- **checkpoint**: Điểm kiểm tra trong workflow, nơi hệ thống cần dừng lại để review hoặc xác nhận.
- **CI**: Continuous Integration; quy trình chạy kiểm tra tự động khi có thay đổi.
- **citation**: Trích dẫn nguồn hoặc tài liệu dùng làm căn cứ cho câu trả lời.
- **classification**: Bài toán phân loại đầu vào vào một hoặc nhiều nhóm.
- **click-through**: Chỉ số cho biết người dùng có nhấp qua một bước hoặc nội dung nào đó không.
- **code**: Mã nguồn hoặc logic lập trình dùng để kiểm tra, xử lý và tự động hóa.
- **codebase**: Toàn bộ mã nguồn của hệ thống hoặc repo.
- **confidence**: Mức độ tự tin mà hệ thống gán cho kết quả của nó, thường ở dạng số.
- **Conflicting systems**: Tình huống nhiều hệ thống trả về dữ liệu mâu thuẫn nhau.
- **connector**: Thành phần kết nối AI với hệ thống dữ liệu hoặc dịch vụ bên ngoài.
- **constraint**: Ràng buộc mà AI hoặc workflow phải tuân theo.
- **context**: Ngữ cảnh kèm theo đầu vào, ví dụ lịch sử hội thoại, metadata, hồ sơ liên quan.
- **contract**: Cam kết cấu trúc hoặc nghĩa của dữ liệu đầu ra giữa các phần của hệ thống.
- **conversion**: Chỉ số cho biết người dùng có hoàn tất một hành động mong muốn hay không.
- **Copilot**: Công cụ AI hỗ trợ người dùng trong quá trình làm việc, nhưng không tự toàn quyền hành động.
- **coverage**: Mức độ bao phủ của dataset, test hoặc eval đối với các tình huống quan trọng.
- **critique**: Phần nhận xét/phê bình chất lượng đầu ra, thường do judge hoặc reviewer đưa ra.
- **CRM**: Customer Relationship Management; hệ thống quản lý thông tin và tương tác với khách hàng.
- **customer_tier**: Trường dữ liệu chỉ phân hạng khách hàng, ví dụ thường hay enterprise.

## D

- **Data correctness**: Mức độ đúng của dữ liệu so với nguồn chuẩn như DB hoặc hệ thống nội bộ.
- **dataset**: Tập hợp các case dùng để huấn luyện, tham chiếu hoặc đánh giá.
- **DB**: Database; cơ sở dữ liệu.
- **decision**: Quyết định mà AI hoặc hệ thống đưa ra ở một bước xử lý.
- **Decision Map / Eval Decision Map**: Bản đồ quyết định phần nào nên chấm bằng code, LLM, human hay expert.
- **deliverable**: Đầu ra cần nộp hoặc sản phẩm cần bàn giao.
- **deterministic**: Tính xác định; cùng đầu vào thì phải cho cùng kết quả theo rule rõ ràng.
- **deterministic checks**: Các kiểm tra bằng code/rule có kết quả đúng sai rõ ràng.
- **domain**: Miền nghiệp vụ cụ thể như support, sales, y tế.
- **domain expert**: Người có chuyên môn sâu trong domain và có quyền xác nhận các case rủi ro hoặc policy.
- **draft reply**: Bản nháp câu trả lời do AI gợi ý, vẫn cần người duyệt trước khi gửi.
- **drift**: Sự lệch dần của hành vi hoặc dữ liệu so với trạng thái ban đầu khi hệ thống đi vào production.

## E

- **edge case**: Tình huống biên, hiếm hoặc khó, thường dễ làm hệ thống sai.
- **email**: Địa chỉ thư điện tử; trong repo thường là tín hiệu để lookup khách hàng.
- **empathy**: Mức độ đồng cảm trong cách AI diễn đạt.
- **engineer / engineering**: Vai trò kỹ thuật phụ trách xây dựng hoặc vận hành hệ thống.
- **enterprise**: Nhóm khách hàng doanh nghiệp lớn, thường có mức ưu tiên và yêu cầu xử lý cao hơn.
- **enum**: Danh sách giá trị cho phép của một field.
- **escalate**: Nâng mức xử lý lên người hoặc quy trình ưu tiên cao hơn.
- **escalation**: Hành động hoặc nhánh xử lý nâng cấp khi case có rủi ro hoặc cần chuyên môn cao hơn.
- **eval**: Viết tắt của evaluation; hoạt động đánh giá chất lượng hệ thống AI.
- **evidence**: Dữ kiện hoặc đoạn nguồn làm căn cứ cho kết luận của AI hoặc reviewer.
- **expected behavior**: Hành vi mong đợi của hệ thống ở một case cụ thể.
- **expert review**: Bước đánh giá của chuyên gia domain trước khi chấp nhận đầu ra hoặc release.

## F

- **fail**: Trượt một kiểm tra, một tiêu chí hoặc một gate.
- **failure**: Lỗi hoặc tình huống AI xử lý sai.
- **failure mode**: Kiểu lỗi lặp lại có mẫu hình nhất định.
- **feature request**: Yêu cầu tính năng mới từ người dùng.
- **field**: Một trường dữ liệu trong input, output hoặc schema.
- **flow**: Luồng đi của dữ liệu và quyết định trong hệ thống.
- **format**: Định dạng dữ liệu hoặc cách biểu diễn đầu ra.
- **full system**: Toàn bộ hệ thống hoàn chỉnh; README nói không cần xây phần này.
- **funnel completion**: Chỉ số theo dõi người dùng có đi hết một chuỗi bước hay không.

## G

- **gate**: Cổng kiểm soát chất lượng; không đạt thì không được đi tiếp.
- **golden output**: Đầu ra chuẩn tham chiếu dùng để so sánh trong eval.
- **good**: Chất lượng “đủ tốt”; trong repo thường nhấn mạnh phải định nghĩa cụ thể chứ không nói chung chung.
- **grounded**: Có bám vào nguồn dữ liệu hoặc bằng chứng thật.
- **grounding**: Việc ràng buộc đầu ra của AI vào source hoặc evidence có thật.
- **guardrail**: Cơ chế bảo vệ nhằm chặn hành vi nguy hiểm hoặc vượt quyền.

## H

- **happy path**: Tình huống chuẩn, trơn tru, ít mơ hồ nhất.
- **hard rule**: Quy tắc cứng bắt buộc đúng 100%.
- **high-risk**: Tình huống có rủi ro cao nếu AI xử lý sai.
- **history**: Lịch sử hội thoại, ticket hoặc tương tác trước đó.
- **human**: Con người tham gia review, gán nhãn hoặc vận hành.
- **human evaluation**: Đánh giá bởi con người.
- **human review**: Bước để người thật kiểm tra lại đầu ra AI.
- **human_escalation**: Trường hoặc logic đánh dấu cần escalte sang người thật xử lý.

## I

- **ID**: Identifier; mã định danh của bản ghi, ticket, user, order hoặc trace.
- **implementation**: Cách hiện thực một ý tưởng bằng hệ thống hoặc code.
- **inbox**: Hộp thư/hộp nhận ticket hoặc hội thoại nội bộ.
- **inconsistency**: Sự không nhất quán giữa các lần chấm, các reviewer hoặc các nguồn dữ liệu.
- **input**: Dữ liệu đầu vào mà AI nhận để xử lý.
- **instruction-following**: Khả năng model làm theo đúng chỉ dẫn.
- **intent**: Ý định hoặc mục đích mà người dùng đang muốn giải quyết.
- **internal ID**: Mã định danh nội bộ không nên lộ ra ngoài.
- **invariant**: Điều kiện phải luôn đúng trong hệ thống.

## J

- **JSON**: JavaScript Object Notation; định dạng dữ liệu có cấu trúc thường dùng cho input/output.
- **JSON schema**: Định nghĩa hình dạng, kiểu dữ liệu và field bắt buộc của một đối tượng JSON.
- **judge**: Thành phần hoặc vai trò dùng để chấm đầu ra.
- **judgment**: Sự đánh giá theo ngữ nghĩa hoặc chuyên môn, không chỉ là kiểm tra đúng/sai máy móc.

## L

- **labeling**: Gán nhãn dữ liệu để làm dataset tham chiếu hoặc calibration.
- **language robustness**: Khả năng hệ thống vẫn hoạt động tốt khi input thay đổi kiểu ngôn ngữ, ví dụ không dấu hoặc transcript nhiễu.
- **latency**: Độ trễ; thời gian hệ thống phản hồi.
- **lead**: Khách hàng tiềm năng trong CRM/sales.
- **legal**: Liên quan pháp lý; trong tài liệu tham khảo thường được nêu như domain cần cẩn trọng.
- **live chat**: Kênh chat trực tiếp với khách hàng.
- **LLM**: Large Language Model; mô hình ngôn ngữ lớn.
- **LLM-as-judge**: Dùng một LLM khác để chấm đầu ra AI theo rubric.
- **log**: Nhật ký hệ thống ghi lại sự kiện, quyết định và lỗi.
- **logic**: Quy tắc hoặc cách suy diễn mà hệ thống dùng để đi từ input đến output.
- **lookup**: Tra cứu dữ liệu trong hệ thống nội bộ dựa trên tín hiệu như số điện thoại, email, mã đơn.

## M

- **match**: Ghép đúng tín hiệu đầu vào với bản ghi phù hợp.
- **math**: Năng lực toán học; trong reference guide được nhắc như một năng lực chung của model.
- **medical**: Liên quan y khoa hoặc sức khỏe.
- **metadata**: Dữ liệu mô tả đi kèm, ví dụ kênh, thời gian, nguồn, loại khách hàng.
- **metric**: Chỉ số đo chất lượng hoặc vận hành.
- **Missing information**: Tình huống thiếu dữ liệu để kết luận chắc chắn.
- **mock outcome**: Đầu ra giả định được dùng để soi lỗi hoặc phân tích sai.
- **mockup**: Bản phác giao diện; README nói chỉ cần ASCII chứ không cần mockup đẹp.
- **model**: Mô hình AI được dùng để sinh đầu ra hoặc chấm.
- **model-based evaluation**: Đánh giá bằng model, thường là LLM judge.
- **monitoring**: Giám sát hệ thống khi chạy thật.
- **multi-intent**: Một input chứa nhiều ý định cùng lúc.

## N

- **needs_human**: Field cho biết case cần con người xem tiếp.
- **next step**: Bước xử lý tiếp theo được AI hoặc workflow gợi ý.
- **normalization**: Chuẩn hóa dữ liệu đầu vào về cùng định dạng để dễ parse hoặc match.
- **north star metric**: Chỉ số chính đại diện cho thành công tổng thể của hệ thống.

## O

- **OA**: Official Account; thường dùng trong Zalo OA.
- **offline evals**: Bộ đánh giá chạy ngoài môi trường production, thường trước khi release.
- **OMS**: Order Management System; hệ thống quản lý đơn hàng.
- **online monitoring**: Giám sát chất lượng và hành vi khi hệ thống đang chạy thật.
- **ops**: Operations; bộ phận vận hành.
- **operational rule**: Quy tắc vận hành áp lên workflow, ngoài logic AI thuần túy.
- **order**: Đơn hàng.
- **output**: Dữ liệu đầu ra AI sinh ra sau khi xử lý.
- **Output Contract**: Bộ field tối thiểu mà đầu ra phải có để UI, workflow và eval hoạt động được.
- **owner**: Người hoặc nhóm chịu trách nhiệm chính cho một khách, case hoặc hệ thống.

## P

- **parser**: Thành phần đọc và bóc tách cấu trúc từ text hoặc trace.
- **pattern**: Mẫu lặp lại; có thể là failure pattern hoặc regex pattern.
- **permission**: Quyền truy cập hoặc hành động mà user/agent được phép làm.
- **pilot**: Giai đoạn thử nghiệm nhỏ để chứng minh hướng làm có khả thi hay không.
- **plan**: Kế hoạch triển khai, chạy eval hoặc pilot.
- **PM**: Product Manager hoặc Project Manager; trong repo dùng theo vai trò người đề xuất eval strategy.
- **policy**: Chính sách hoặc quy định mà hệ thống phải tuân theo.
- **precision**: Trong đánh giá phân loại, tỷ lệ các dự đoán dương tính là đúng.
- **PRD**: Product Requirements Document; tài liệu yêu cầu sản phẩm.
- **pre-release**: Giai đoạn trước khi đưa bản mới ra sử dụng.
- **privacy**: Quyền riêng tư; đặc biệt quan trọng với dữ liệu khách hàng và y tế.
- **production**: Môi trường chạy thật cho người dùng thật.
- **production trace**: Dấu vết/log sinh ra từ hệ thống đang chạy thật.
- **Product**: Bộ phận sản phẩm hoặc ngữ cảnh sản phẩm.
- **product_team**: Team sản phẩm; trong case 1 có rule billing không được route sang team này.
- **prompt**: Chỉ dẫn đầu vào cho model.
- **provider**: Bên cung cấp model hoặc dịch vụ kỹ thuật.
- **Pydantic**: Thư viện Python thường dùng để khai báo schema và validate dữ liệu.

## Q

- **Quality Question**: Câu hỏi chất lượng cốt lõi mà bộ eval phải trả lời.
- **queue**: Hàng chờ xử lý nội bộ.

## R

- **RAG**: Retrieval-Augmented Generation; mô hình sinh câu trả lời có dùng tài liệu tra cứu kèm theo.
- **RBAC**: Role-Based Access Control; mô hình phân quyền theo vai trò.
- **reason**: Lý do hoặc diễn giải ngắn giải thích tại sao AI đưa ra quyết định.
- **reason_codes**: Các mã lý do cấu trúc hóa để giải thích quyết định của AI.
- **reasoning**: Quá trình suy luận của model hoặc người đánh giá.
- **recall**: Trong đánh giá phân loại, tỷ lệ các trường hợp dương tính thật được bắt đúng.
- **record**: Bản ghi trong CRM, OMS, hồ sơ bệnh nhân hoặc database.
- **reference dataset**: Bộ case tham chiếu dùng để test, regression và calibration.
- **regex**: Regular Expression; mẫu ký tự dùng để tìm kiếm, kiểm tra format hoặc trích xuất tín hiệu.
- **regression**: Tình huống tính năng từng đúng nhưng trở nên sai sau thay đổi model/prompt/code.
- **Release Gate**: Bộ điều kiện tối thiểu phải đạt trước khi cho phép release hoặc pilot bước tiếp theo.
- **render**: Hiển thị dữ liệu lên giao diện.
- **repository**: Kho mã nguồn hoặc thư mục bài nộp.
- **retention**: Chỉ số giữ chân người dùng quay lại tiếp tục sử dụng.
- **retrieval**: Bước lấy tài liệu, hồ sơ hoặc dữ liệu liên quan từ hệ thống.
- **review**: Bước xem xét và xác nhận chất lượng bởi con người hoặc chuyên gia.
- **risk**: Rủi ro nếu hệ thống sai hoặc vượt quyền.
- **risk level**: Mức độ rủi ro của một case hoặc một lỗi.
- **robustness**: Độ bền của hệ thống trước input xấu, nhiễu, thiếu dấu, typo hoặc ngữ cảnh khó.
- **route**: Chuyển case sang đúng nhánh, team hoặc người xử lý.
- **route_to**: Field chỉ đích đến mà case cần được chuyển tới.
- **routing**: Quá trình quyết định route.
- **rubric**: Bộ tiêu chí chấm có cấu trúc để reviewer hoặc judge dùng thống nhất.
- **runner / eval runner**: Công cụ tự động chạy cả bộ eval; README nói không cần xây phần này.

## S

- **SaaS**: Software as a Service; phần mềm cung cấp dưới dạng dịch vụ.
- **safety**: Tính an toàn của hành vi AI.
- **safety hard rule**: Quy tắc an toàn cứng, vi phạm là fail ngay.
- **sales**: Bộ phận bán hàng.
- **sales ops**: Nhóm vận hành hỗ trợ quy trình sales.
- **scaffold**: Mức độ khung sẵn mà đề bài đã chuẩn bị; cao nghĩa là gợi ý nhiều, thấp nghĩa là phải tự thiết kế nhiều.
- **schema**: Cấu trúc bắt buộc của dữ liệu.
- **schema validator**: Công cụ kiểm tra dữ liệu có đúng schema hay không.
- **scenario**: Kịch bản tình huống dùng trong thiết kế hoặc test.
- **seed case**: Một vài case mẫu ban đầu để giúp hình dung phạm vi bài toán.
- **semantic**: Thuộc về ngữ nghĩa, nghĩa là phải hiểu nội dung chứ không chỉ nhìn pattern bề mặt.
- **semantic quality**: Chất lượng ngữ nghĩa của câu trả lời, summary hoặc route.
- **sentiment**: Cảm xúc/tông cảm xúc thể hiện trong ticket hoặc hội thoại.
- **session**: Phiên làm việc hoặc chuỗi tương tác liên tiếp.
- **severity**: Mức độ nghiêm trọng của lỗi hoặc tình huống.
- **ship**: Đưa tính năng ra dùng thật.
- **signal**: Tín hiệu có ích để ra quyết định, ví dụ email, mã đơn, từ khóa red flag.
- **source**: Nguồn dữ liệu gốc dùng để hỗ trợ kết luận.
- **source metadata**: Metadata đi kèm tài liệu hoặc dữ liệu nguồn.
- **speech-to-text**: Chuyển tiếng nói thành văn bản.
- **state machine**: Cách mô hình hóa hệ thống theo trạng thái và các chuyển trạng thái hợp lệ.
- **status**: Trạng thái hiện tại của một bản ghi, order, ticket hoặc case.
- **style**: Phong cách diễn đạt của câu trả lời.
- **suggestion**: Gợi ý mà AI đưa ra cho người dùng nội bộ.
- **summary**: Tóm tắt nội dung chính từ ticket, chat hoặc cuộc gọi.
- **support**: Hỗ trợ khách hàng.
- **Support Triage / support triage**: Luồng AI đọc ticket support và gợi ý phân loại, urgency, route.
- **synthetic**: Dữ liệu nhân tạo được tạo ra có chủ đích để test một kiểu lỗi hay tình huống.

## T

- **task**: Công việc cụ thể mà AI hoặc hệ thống được giao.
- **task success**: Mức độ hoàn thành đúng task.
- **task understanding**: Mức độ AI hiểu đúng mình đang phải làm gì.
- **taxonomy**: Hệ thống phân loại chính thức của domain, ví dụ các loại route y tế nội bộ.
- **team**: Nhóm xử lý hoặc nhóm sở hữu một phần workflow.
- **Technical**: Nhãn thường dùng cho vấn đề kỹ thuật.
- **technical_support**: Team hỗ trợ kỹ thuật nhận các ticket technical.
- **template**: Mẫu cấu trúc có thể tái sử dụng.
- **test**: Bài kiểm tra đơn lẻ hoặc bộ kiểm tra.
- **threshold**: Ngưỡng định lượng dùng để pass/fail hoặc cảnh báo.
- **ticket**: Phiếu/yêu cầu hỗ trợ của khách hàng.
- **ticket_id**: Mã định danh của ticket.
- **timeline**: Mốc thời gian dự kiến cho pilot hoặc release.
- **token**: Đơn vị tính đầu vào/đầu ra của model; thường dùng để tính cost.
- **tool**: Công cụ mà agent hoặc workflow có thể gọi để lấy dữ liệu hoặc hành động.
- **tool call**: Lần gọi một tool cụ thể.
- **tool usage**: Cách và mức độ dùng tool trong workflow.
- **trace**: Dấu vết chi tiết của một lần chạy hệ thống.
- **trace analysis**: Phân tích log/trace để tìm lỗi, pattern và edge case.
- **trace parser**: Thành phần đọc trace để trích dữ liệu phục vụ eval.
- **triage**: Sàng lọc hoặc phân loại ban đầu để quyết định hướng xử lý.
- **TriageOutput**: Tên mẫu cho object đầu ra triage trong ví dụ code.
- **trust**: Mức độ người dùng tin vào hệ thống AI.
- **TypeScript**: Ngôn ngữ lập trình mở rộng từ JavaScript có kiểu dữ liệu tĩnh.

## U

- **UI**: User Interface; giao diện người dùng.
- **uncertainty**: Mức độ không chắc chắn của hệ thống khi kết luận.
- **Unit of Work**: Đơn vị công việc đủ nhỏ để eval, nhưng vẫn đủ ý nghĩa vận hành.
- **unknown**: Không xác định được; thường dùng khi thiếu dữ liệu để kết luận.
- **unsupported claim**: Khẳng định không được nguồn dữ liệu hỗ trợ.
- **urgency**: Mức độ khẩn cấp của case.
- **usage**: Mức độ sử dụng hệ thống hoặc tính năng.
- **usability**: Mức độ dễ dùng và hữu ích của hệ thống.
- **user**: Người dùng cuối hoặc người dùng nội bộ.
- **User Input Grid**: Cụm trong tài liệu tham khảo chỉ bảng hệ thống hóa các kiểu input người dùng.
- **UX**: User Experience; trải nghiệm tổng thể khi người dùng tương tác với hệ thống.
- **UUID**: Universally Unique Identifier; mã định danh duy nhất toàn cục, thường không nên lộ ra ngoài.

## V

- **v0 / v1**: Các phiên bản ban đầu hoặc các vòng lặp cải tiến theo version.
- **valid**: Hợp lệ theo schema, enum, rule hoặc policy.
- **validation / validate**: Quá trình kiểm tra dữ liệu hoặc output có hợp lệ không.
- **validator**: Công cụ hoặc hàm dùng để kiểm tra tính hợp lệ.
- **variant**: Biến thể của một prompt, model, flow hoặc test case.
- **verbosity**: Độ dài và mức độ lan man của câu trả lời.
- **version**: Phiên bản của dataset, prompt, model, rubric hoặc release.
- **versioning**: Cách quản lý các phiên bản thay đổi theo thời gian.

## W

- **warning**: Cảnh báo hiển thị cho người dùng nội bộ khi có ambiguity, conflict hoặc risk.
- **web chat**: Kênh chat trên website.
- **weak reason**: Lý do giải thích quá ngắn, quá yếu hoặc không đủ căn cứ.
- **workbook**: Bộ câu hỏi/bản mẫu để người học điền câu trả lời.
- **workflow**: Chuỗi bước xử lý từ input đến output và các checkpoint review.

## Z

- **Zalo OA**: Zalo Official Account; kênh nhắn tin doanh nghiệp trên Zalo.
- **Zod**: Thư viện JavaScript/TypeScript dùng để mô tả schema và validate dữ liệu.
