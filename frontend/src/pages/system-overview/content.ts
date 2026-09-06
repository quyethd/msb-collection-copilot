export const brand = {
  bank: 'MSB',
  product: 'Trợ lý Thu hồi Nợ',
  poweredBy: 'Powered by GreenNode AI',
};

export const hero = {
  headline: 'Trợ lý Thu hồi Nợ cho cán bộ và đội ngũ thu hồi nợ',
  value: 'Không chỉ tìm khách hàng nợ nhiều nhất. Hệ thống giúp xác định cơ hội thu hồi tốt nhất tiếp theo, hành động phù hợp và thời điểm nên thực hiện.',
  strong: 'Không tìm khách hàng nợ nhiều nhất. Tìm cơ hội thu hồi tốt nhất tiếp theo.',
  ctaPrimary: 'Khám phá giải pháp',
  ctaSecondary: 'Xem cách hệ thống hoạt động',
  disclaimer: 'Bản demo sử dụng dữ liệu mô phỏng, không sử dụng dữ liệu khách hàng thật.',
};

export const benefitChips = ['Đúng khách hàng', 'Đúng hành động', 'Đúng thời điểm', 'Lý do rõ ràng'];

export const audienceNav = [
  { label: 'Dành cho Tác nghiệp', href: '#audience-operations' },
  { label: 'Dành cho Quản lý', href: '#audience-management' },
  { label: 'Dành cho Kiến trúc / Công nghệ', href: '#architecture' },
];

export const problemSection = {
  title: 'Từ danh sách nợ đến quyết định hành động',
  intro: 'Cán bộ không thiếu dữ liệu. Cán bộ thiếu một quyết định rõ ràng và đáng tin cậy được tạo ra từ dữ liệu đó.',
};

export const pains: { title: string; body: string; notes?: { left: string; right: string }[] }[] = [
  {
    title: 'Nhiều khách hàng nhưng chưa rõ ai cần xử lý trước.',
    body: 'Danh sách nợ chỉ cho biết mức độ quá hạn, không cho biết cơ hội thu hồi tốt nhất tiếp theo.',
    notes: [
      { left: 'Quá hạn cao', right: 'cơ hội thu hồi tốt nhất' },
      { left: 'Dư nợ cao', right: 'cần gọi ngay' },
    ],
  },
  {
    title: 'Một quyết định cần tổng hợp nhiều tín hiệu.',
    body: 'Chưa có tín hiệu nào đơn lẻ đủ để ra quyết định.',
  },
  {
    title: 'Thuộc tuyến CALL không có nghĩa hôm nay nhất thiết phải gọi.',
    body: 'Tuyến xử lý là hướng vận hành. Hành động hôm nay phụ thuộc vào tín hiệu hiện tại.',
  },
  {
    title: 'Cán bộ và quản lý cần hiểu: quyết định vì sao như vậy?',
    body: '"Tại sao hệ thống lại đề xuất hành động này?" phải là câu trả lời được, trên cùng một màn hình.',
  },
];

export const benefitSection = {
  title: 'Ai trực tiếp hưởng lợi?',
  intro: 'Bốn nhóm người dùng nhận được giá trị khác nhau từ cùng một hệ thống quyết định.',
};

export const benefitCards: {
  id: string;
  group: 'operations' | 'management' | 'architecture';
  title: string;
  kicker: string;
  points: string[];
}[] = [
  {
    id: 'benefit-call',
    group: 'operations',
    title: 'Tác nghiệp CALL',
    kicker: 'Người gọi điện cho khách hàng',
    points: [
      'Biết khách hàng nào nên ưu tiên',
      'Biết trường hợp nào thuộc CALL nhưng chưa cần gọi ngay',
      'Xem hành động phù hợp',
      'Xem lý do trên cùng một màn hình',
      'Giảm việc tự tổng hợp nhiều nguồn dữ liệu',
    ],
  },
  {
    id: 'benefit-cbs',
    group: 'operations',
    title: 'Tác nghiệp CBS',
    kicker: 'Người nhắc thanh toán và theo dõi cam kết',
    points: [
      'Xác định khách cần nhắc thanh toán',
      'Khách phù hợp để chờ tự thanh toán',
      'Theo dõi tín hiệu dòng tiền',
      'Theo dõi cam kết thanh toán',
      'Hạn chế tác động không cần thiết',
    ],
  },
  {
    id: 'benefit-management',
    group: 'management',
    title: 'Trưởng nhóm / Quản lý thu hồi',
    kicker: 'Quản lý và phân bổ tác nghiệp',
    points: [
      'Nhìn tổng quan danh mục',
      'Phân bổ hành động',
      'Xem danh sách ưu tiên',
      'Phát hiện trường hợp cần chú ý',
      'Theo dõi tác động vận hành',
    ],
  },
  {
    id: 'benefit-architecture',
    group: 'architecture',
    title: 'Kiến trúc / Công nghệ',
    kicker: 'Chuyên gia xem xét tính bền vững',
    points: [
      'quyết định theo quy tắc xác định',
      'quy tắc có thể truy vết',
      'AI không thể thay đổi hành động đề xuất',
      'sử dụng công cụ dựa trên dữ liệu đã xác nhận',
      'kiến trúc có thể kiểm thử',
      'ranh giới module rõ ràng',
      'cơ chế an toàn',
      'khả năng kiểm toán',
    ],
  },
];

export const whoWhyWhatWhen = {
  title: 'Bốn câu hỏi vận hành, một luồng quyết định',
};

export const steps: { step: string; label: string; question: string; system: string }[] = [
  { step: 'WHO', label: 'Khách hàng nào nên ưu tiên?', question: 'Ai cần được xử lý trước trong danh mục?', system: 'Cơ hội thu hồi (Recovery Opportunity) + Xếp hạng' },
  { step: 'WHY', label: 'Vì sao khách hàng này được ưu tiên?', question: 'Tín hiệu nào dẫn tới mức ưu tiên này?', system: 'Bằng chứng + GreenNode Agent' },
  { step: 'WHAT', label: 'Hành động phù hợp là gì?', question: 'Cần làm gì với khách hàng này?', system: 'Hành động đề xuất tiếp theo (Next Best Action)' },
  { step: 'WHEN', label: 'Thực hiện ngay, chờ hay theo dõi?', question: 'Thời điểm thực hiện thế nào?', system: 'Dòng tiền + Cam kết thanh toán + lịch liên hệ + hành động tiếp theo' },
];

export const heroExample = {
  title: 'Ví dụ tác nghiệp: SYN002846',
  cif: 'SYN002846',
  disclaimer: 'Số liệu mô phỏng đã được chấp nhận trong bản demo.',
  rows: [
    { label: 'Số ngày quá hạn (DPD)', value: '11 ngày' },
    { label: 'Tiền vào 7 ngày', value: '48 triệu đồng' },
    { label: 'Dòng tiền ròng 30 ngày', value: '168 triệu đồng' },
    { label: 'Cam kết thanh toán (PTP)', value: 'Không có cam kết đang mở' },
    { label: 'Tuyến', value: 'CALL' },
  ],
  recommendation: 'Chờ khách hàng tự thanh toán',
  secondary: 'Chưa cần liên hệ',
  explanation:
    'Khách hàng thuộc tuyến CALL nhưng tín hiệu dòng tiền gần đây đáp ứng điều kiện để ưu tiên chờ tự thanh toán tại thời điểm hiện tại.',
};

export const whatIf = {
  title: 'Cùng một khách hàng. Khác tín hiệu. Khác hành động phù hợp.',
  disclaimer: 'Minh họa chạy trên bộ máy mô phỏng theo quy tắc.',
  rows: [
    { label: 'Tiền vào 7 ngày', before: '48 triệu', after: '0' },
    { label: 'Dòng tiền ròng 30 ngày', before: '168 triệu', after: '0' },
  ],
  before: 'Chờ khách hàng tự thanh toán',
  after: 'Liên hệ khách hàng',
  note: 'Tín hiệu được thay đổi chỉ trong kịch bản mô phỏng, không làm thay đổi dữ liệu gốc của khách hàng.',
};

export const pipeline = {
  title: 'Từ dữ liệu đến lời giải thích',
  stages: [
    { title: 'Dữ liệu khách hàng', detail: 'Khoản vay · Dư nợ · Số ngày quá hạn · Dòng tiền · Cam kết thanh toán · Lịch sử liên hệ' },
    { title: 'Chính sách bắt buộc (Hard Policy)', detail: 'Ràng buộc không thể thay đổi' },
    { title: 'Tuyến xử lý (Routing)', detail: 'Xác định tuyến CALL / CBS' },
    { title: 'Cơ hội thu hồi (Recovery Opportunity)', detail: 'Điểm cơ hội thu hồi' },
    { title: 'Hành động đề xuất tiếp theo (Next Best Action)', detail: 'Chọn hành động theo mức ưu tiên' },
    { title: 'Kênh và thời điểm', detail: 'Kênh và thời điểm thực hiện' },
    { title: 'GreenNode Agent', detail: 'Giải thích · Hỏi đáp · Điều tra · Mô phỏng · Tra cứu kiến thức (RAG)' },
  ],
  coreStatementTitle: 'Bộ máy quyết định (Decision Core)',
  coreStatement: 'theo quy tắc xác định là nguồn quyết định nghiệp vụ.',
  agentStatementTitle: 'GreenNode Agent',
  agentStatement: 'là lớp tương tác, điều phối công cụ nghiệp vụ, giải thích và tra cứu kiến thức hệ thống.',
};

export const ruleLayers = {
  title: 'Các lớp quyết định đang vận hành',
  intro: 'Sáu lớp độc lập. Mỗi lớp có trách nhiệm và thứ tự ưu tiên rõ ràng.',
};

export const routeCall = ['Mức cảnh báo = ĐỎ', 'Nhóm khách hàng thuộc ĐỎ / CAM / VÀNG', 'Số ngày quá hạn từ 5 ngày'];
export const routeCbs = ['Mức cảnh báo = ĐỎ', 'Nhóm khách hàng thuộc ĐỎ / CAM / VÀNG', 'Số ngày quá hạn dưới 5 ngày'];
export const routingNote = 'Tuyến xử lý là hướng vận hành. Tuyến xử lý không đồng nghĩa hành động phải thực hiện ngay.';

export const ptpPrecedence = [
  'Gọi lại theo lịch',
  'Xác minh thông tin liên hệ',
  'Cam kết thanh toán một phần',
  'Cam kết không thực hiện',
  'Cam kết đang mở',
  'Cam kết đã thực hiện',
  'Khả năng tự thanh toán (Self-cure)',
  'Chuyển mức xử lý khi từ chối',
  'Hành động mặc định của tuyến',
];

export const scoring = {
  components: [
    { name: 'Mức cấp thiết nghiệp vụ', weight: 20 },
    { name: 'Khả năng thanh toán', weight: 25 },
    { name: 'Mức sẵn sàng thanh toán', weight: 20 },
    { name: 'Khả năng liên hệ', weight: 15 },
    { name: 'Cơ hội theo thời điểm', weight: 15 },
    { name: 'Điều chỉnh chiến lược', weight: 5 },
  ],
  total: 100,
  disclaimer:
    'Điểm cơ hội thu hồi là điểm ưu tiên tương đối, không phải xác suất khách hàng chắc chắn thanh toán.',
};

export const nbaActions = [
  'Chờ',
  'Chờ khách hàng tự thanh toán',
  'Nhắc thanh toán',
  'Liên hệ',
  'Theo dõi cam kết',
  'Khôi phục cam kết',
  'Thanh toán một phần',
  'Gọi lại',
  'Xác minh liên hệ',
  'Chuyển mức xử lý',
];

export const architecture = {
  title: 'Kiến trúc hệ thống',
  intro:
    'Người dùng thao tác qua giao diện MSB và API ứng dụng. Quyết định nghiệp vụ được xử lý bởi Bộ máy quyết định (Decision Core) theo quy tắc xác định từ dữ liệu mô phỏng. Khi người dùng hỏi Trợ lý, GreenNode Agent hiểu câu hỏi tự nhiên, chọn đúng công cụ nghiệp vụ, lấy quyết định từ Bộ máy quyết định rồi giải thích dựa trên bằng chứng. GreenNode không phải yếu tố trang trí: Trợ lý dùng nó để tương tác tự nhiên, chọn công cụ, giải thích có căn cứ, điều tra và mô phỏng — còn quyết định thu hồi vẫn do bộ máy theo quy tắc nắm giữ.',
  coreLabel: 'Bộ máy quyết định (Decision Core) theo quy tắc xác định',
  coreState: '= Nguồn quyết định nghiệp vụ',
  agentLabel: 'Trợ lý GreenNode',
  agentState: '= Lớp tương tác và điều phối',
  frontend: { title: 'Giao diện người dùng', items: ['Tổng quan', 'Danh sách ưu tiên', 'Khách hàng', 'Tác động dự kiến'] },
  api: { title: 'Lớp API / bản demo', items: ['Thông tin khách hàng', 'Danh mục', 'Lịch sử thay đổi', 'Sự kiện', 'Tác động', 'Trợ lý (quyết định + kiến thức)'] },
  customerPath: {
    title: 'Luồng khách hàng / quyết định',
    intro: 'Câu hỏi về khách hàng đi qua AgentBase tới công cụ nghiệp vụ, lấy quyết định từ Bộ máy quyết định theo quy tắc.',
    items: ['GreenNode AgentBase (điều phối công cụ)', 'Công cụ nghiệp vụ mô phỏng', 'Bộ máy quyết định theo quy tắc', 'GLM 5.2 (giải thích có bằng chứng)'],
  },
  knowledgePath: {
    title: 'Luồng kiến thức hệ thống',
    intro: 'Câu hỏi khái niệm được tra cứu trong kho kiến thức GreenNode và trả lời có nguồn tham khảo.',
    items: ['GreenNode Vector Database', 'Kho kiến thức TASK-011H-V2', 'Qwen Flash (tổng hợp có nguồn)', 'Nhúng đa ngôn ngữ cục bộ'],
  },
  decisionPathLabel: 'LUỒNG KHÁCH HÀNG / QUYẾT ĐỊNH',
  knowledgePathLabel: 'LUỒNG KIẾN THỨC HỆ THỐNG',
  pathNote: 'Hai luồng tách biệt. Kiến thức hệ thống không quyết định nghiệp vụ và ngược lại.',
};

export const greenNodeStory = {
  title: 'Nền Tảng AI GreenNode',
  intro: 'GreenNode hỗ trợ cán bộ truy vấn, điều phối công cụ nghiệp vụ và tạo phần giải thích; Bộ máy quyết định giữ quyền xác định kết quả nghiệp vụ.',
  components: [
    { title: 'GreenNode AgentBase', detail: 'Điều phối Trợ lý với các công cụ nghiệp vụ. Đã được kiểm chứng kết nối công cụ quyết định và giữ nguyên kết quả nghiệp vụ.' },
    { title: 'Dịch vụ mô hình AI GreenNode (MaaS)', detail: 'Cung cấp GLM 5.2 cho phân tích và giải thích phức tạp, Qwen Flash cho câu trả lời kiến thức có nguồn.' },
    { title: 'GLM 5.2', detail: 'Hỗ trợ tạo phần giải thích dựa trên kết quả nghiệp vụ đã được xác nhận.' },
    { title: 'Qwen Flash', detail: 'Tổng hợp câu trả lời kiến thức hệ thống (RAG) dựa duy nhất trên các đoạn tài liệu được truy xuất.' },
    { title: 'GreenNode Vector Database', detail: 'Cơ sở dữ liệu véc-tơ lưu kho kiến thức phiên bản TASK-011H-V2 và truy xuất câu trả lời có nguồn tham khảo.' },
    { title: 'Nhúng đa ngôn ngữ cục bộ', detail: 'Mô hình nhúng véc-tơ đa ngôn ngữ chạy cục bộ (local multilingual embedding) để tra cứu theo nghĩa, véc-tơ không nằm trong đường quyết định.' },
    { title: 'Bộ máy quyết định (Decision Core)', detail: 'Không phải mô hình ngôn ngữ. Giữ quyền xác định tuyến, điểm, hành động và kênh xử lý.' },
  ],
};

export const knowledgeAssistant = {
  title: 'Trợ Lý Hiểu Cả Quyết Định Và Kiến Thức Hệ Thống',
  intro: 'Trợ lý trả lời theo hai luồng tách biệt. Luồng quyết định và khách hàng dùng công cụ nghiệp vụ truy vấn Bộ máy quyết định. Luồng kiến thức hệ thống tra cứu kho kiến thức GreenNode và tổng hợp đáp án có nguồn tham khảo.',
  trustMessage:
    'GreenNode AI hỗ trợ phân tích, giải thích và tra cứu kiến thức. Bộ máy quyết định giữ quyền xác định kết quả nghiệp vụ.',
  decision: {
    title: 'Luồng quyết định và khách hàng',
    body: 'Câu hỏi về một khách hàng (tuyến, điểm, hành động, dòng tiền, cam kết, mô phỏng) được điều phối qua AgentBase tới công cụ nghiệp vụ đã chấp nhận; kết quả lấy từ Bộ máy quyết định theo quy tắc và GLM 5.2 tạo phần giải thích.',
    examples: ['"Tại sao hôm nay chưa nên gọi khách hàng này?"', '"SYN002846 thuộc CALL hay CBS?"', '"Nếu dòng tiền 7 ngày bằng 0 thì sao?"'],
  },
  knowledge: {
    title: 'Luồng kiến thức hệ thống',
    body: 'Câu hỏi khái niệm (CALL/CBS, Điểm Cơ hội thu hồi, vai trò GreenNode, RAG...) được nhúng véc-tơ, tra cứu trong kho kiến thức TASK-011H-V2 vào GreenNode Vector Database, rồi Qwen Flash tổng hợp câu trả lời kèm nguồn tham khảo.',
    examples: ['"CALL và CBS khác nhau thế nào?"', '"Điểm Cơ hội thu hồi được tính như thế nào?"', '"Trợ lý có tự quyết định phương án xử lý không?"'],
  },
  sources: 'Kho kiến thức chỉ trả lời khi tìm thấy đoạn tài liệu đủ đáng tin. Trường hợp không đủ thông tin, Trợ lý nói rõ thay vì bịa dựng.',
};

export const modules = {
  title: 'Bên trong hệ thống',
  intro: 'Các module chính và trách nhiệm của từng phần.',
};

export const moduleCards: { name: string; role: string; checks?: string[] }[] = [
  { name: 'msb_policy', role: 'Chính sách bắt buộc, tuyến xử lý và ràng buộc nghiệp vụ.' },
  { name: 'msb_recovery', role: 'Điểm Cơ hội thu hồi.' },
  { name: 'msb_nba', role: 'Hành động đề xuất tiếp theo và thứ tự ưu tiên.' },
  { name: 'msb_simulation', role: 'Chạy mô phỏng theo quy tắc mà không làm thay đổi ngữ cảnh gốc.' },
  { name: 'msb_demo', role: 'Trạng thái, sự kiện và lịch sử bản demo.' },
  { name: 'msb_impact', role: 'Tác động vận hành và ước tính minh bạch theo giả định.' },
  { name: 'msb_agent', role: 'Môi trường Agent: điều phối công cụ, giải thích, điều tra và mô phỏng.' },
  {
    name: 'msb_agent_eval',
    role: 'Đánh giá độ tin cậy của Trợ lý.',
    checks: [
      'Kiểm tra Trợ lý dùng đúng công cụ nghiệp vụ',
      'So khớp quyết định Trợ lý với bộ máy theo quy tắc',
      'Kiểm tra khách hàng chưa biết không bị bịa dựng',
      'Kiểm tra yêu cầu can thiệp không phá vỡ cơ chế an toàn',
      'Kiểm tra không lộ lý do suy luận nội bộ',
    ],
  },
];

export const aiRole = {
  title: 'AI hỗ trợ hiểu quyết định, không thay đổi quyết định nghiệp vụ',
  safetyNote: 'Thiết kế giảm rủi ro AI tự suy diễn quyết định nghiệp vụ.',
  can: [
    'Hiểu câu hỏi tự nhiên',
    'Giải thích dựa trên bằng chứng',
    'Tổng hợp bằng chứng từ dữ liệu',
    'Chọn đúng công cụ nghiệp vụ',
    'Điều tra ngữ cảnh khách hàng',
    'Mô phỏng tình huống',
    'Tóm tắt trạng thái',
    'Tra cứu kho kiến thức hệ thống có nguồn tham khảo',
  ],
  cannot: [
    'Thay đổi quyết định của chính sách',
    'Thay đổi hành động đề xuất',
    'Tự tạo dữ liệu khách hàng',
    'Tự tạo cam kết thanh toán',
    'Bịa số liệu dòng tiền',
    'Dùng kho kiến thức để quyết định nghiệp vụ khách hàng',
    'Tiết lộ lý do suy luận nội bộ',
  ],
};

export const trust = {
  title: 'Quyết định và trả lời có thể kiểm chứng',
  badges: [
    'Quyết định Deterministic',
    'Truy vết quy tắc (Rule Trace)',
    'Dựa trên dữ liệu đã xác nhận (Grounding)',
    'AI không thay đổi quyết định',
    'CIF chưa biết an toàn',
    'Đã kiểm tra Prompt Injection',
    'Không lộ lý do suy luận',
    'Trả lời kiến thức có nguồn (RAG)',
  ],
  points: [
    'Quyết định nghiệp vụ đến từ các quy tắc deterministic.',
    'AgentBase truy xuất công cụ nghiệp vụ trước khi giải thích câu hỏi quyết định.',
    'Khách hàng chưa biết không bị bịa dựng thông tin.',
    'Yêu cầu can thiệp không làm thay đổi quyết định nghiệp vụ đã chấp nhận.',
    'Lý do suy luận nội bộ không được tiết lộ.',
    'Yêu cầu bí mật (API key, mật khẩu, nội dung kho nội bộ) bị chặn.',
    'Câu trả lời kiến thức chỉ xuất hiện khi truy xuất được đoạn tài liệu đủ đáng tin, kèm nguồn tham khảo.',
  ],
  status: 'Đã kiểm chứng kết nối GreenNode Vector Database và truy xuất kho kiến thức (RAG) trên môi trường demo / live proof.',
};

export const dayTimeline = {
  title: 'Một ngày tác nghiệp với Trợ lý Thu hồi Nợ',
  entries: [
    { time: '08:00', action: 'Mở Tổng quan', note: 'Xem danh mục, tuyến xử lý và các điểm cần chú ý.' },
    { time: '08:05', action: 'Mở Danh sách ưu tiên', note: 'Xác định khách hàng nên xử lý trước.' },
    { time: '08:10', action: 'Mở hồ sơ khách hàng', note: 'Xem dư nợ, số ngày quá hạn, dòng tiền, cam kết thanh toán, lịch sử liên hệ và hành động đề xuất.' },
    { time: '08:12', action: 'Hỏi Trợ lý', note: '"Tại sao hôm nay chưa nên gọi khách hàng này?"' },
    { time: '08:15', action: 'Thực hiện hành động', note: 'Liên hệ / nhắc / theo dõi cam kết / chờ tự thanh toán theo quyết định hiện tại.' },
  ],
};

export const sampleQuestions = {
  title: 'Bạn có thể hỏi Trợ lý điều gì?',
  note: 'Các câu hỏi dưới đây là ví dụ. Với khách hàng, Trợ lý trả lời dựa trên quyết định đã được xác định và dữ liệu hiện có. Với khái niệm hệ thống, Trợ lý tra cứu kho kiến thức GreenNode và trả lời có nguồn tham khảo.',
  questions: [
    ...assistantQuestionCatalog.map(({ question }) => question),
  ],
};

export const faqs: { question: string; answer: string }[] = [
  {
    question: 'AI có tự quyết định khách hàng nào phải gọi không?',
    answer:
      'Không. Quyết định nghiệp vụ do Bộ máy quyết định theo quy tắc tạo ra. AI sử dụng kết quả đã được xác định để hỗ trợ giải thích, truy vấn và mô phỏng.',
  },
  {
    question: 'Thuộc tuyến CALL có nghĩa là phải gọi ngay không?',
    answer:
      'Không. CALL là tuyến xử lý. Hành động đề xuất tiếp theo (Next Best Action) có thể đề xuất chờ khách hàng tự thanh toán nếu tín hiệu hiện tại đáp ứng điều kiện.',
  },
  {
    question: 'Điểm cơ hội thu hồi có phải xác suất khách hàng sẽ trả tiền không?',
    answer: 'Không. Đây là điểm ưu tiên tương đối được xây dựng từ các tín hiệu nghiệp vụ hiện có.',
  },
  {
    question: 'Nếu AI không hoạt động thì hệ thống có còn ra quyết định không?',
    answer:
      'Có. Chính sách, Cơ hội thu hồi và Hành động đề xuất tiếp theo được xử lý bởi Bộ máy quyết định theo quy tắc. AI là lớp hỗ trợ tương tác và giải thích.',
  },
  {
    question: 'Agent có thể tự thay đổi rule không?',
    answer: 'Không.',
  },
  {
    question: 'Bản demo có sử dụng dữ liệu khách hàng thật không?',
    answer: 'Không. Bản demo sử dụng dữ liệu mô phỏng.',
  },
  {
    question: 'Tại sao hệ thống cần GreenNode AI nếu đã có Rule Engine?',
    answer:
      'Bộ máy quy tắc đảm bảo quyết định nghiệp vụ nhất quán và kiểm soát được. GreenNode Agent giúp cán bộ truy vấn, điều tra, tổng hợp bằng chứng, giải thích và mô phỏng quyết định bằng ngôn ngữ tự nhiên mà không cần đọc thủ công nhiều trường dữ liệu.',
  },
  {
    question: 'Trợ lý có trả lời câu hỏi khái niệm như "CALL và CBS khác nhau thế nào?" không?',
    answer:
      'Có. Đây là câu hỏi kiến thức hệ thống. Trợ lý nhúng câu hỏi, tra cứu trong kho kiến thức GreenNode phiên bản TASK-011H-V2 và tổng hợp câu trả lời bằng Qwen Flash kèm nguồn tham khảo. Trường hợp không truy xuất được đoạn tài liệu đủ đáng tin, Trợ lý thừa nhận không đủ thông tin.',
  },
  {
    question: 'Trợ lý trả lời kiến thức hệ thống có quyết định nghiệp vụ không?',
    answer:
      'Không. Luồng kiến thức hệ thống và luồng quyết định khách hàng tách biệt. Quyết định nghiệp vụ chỉ đến từ Bộ máy quyết định theo quy tắc.',
  },
];

export const roadmap = {
  title: 'Lộ trình sản phẩm',
  current: {
    label: 'Đã có trong bản demo',
    items: ['Năng lực quyết định', 'CALL / CBS', 'Cơ hội thu hồi', 'Hành động đề xuất tiếp theo', 'Mô phỏng tình huống', 'Trợ lý GreenNode', 'Tra cứu kiến thức hệ thống (RAG) có nguồn'],
  },
  future: {
    label: 'Hướng phát triển tiếp theo',
    items: [
      'Phản hồi kết quả (Outcome feedback)',
      'Thử nghiệm / đánh giá A-B',
      'Học xếp hạng (Learning-to-rank)',
      'Tối ưu kênh xử lý',
      'Tối ưu hành động',
      'Theo dõi danh mục',
    ],
  },
  disclaimer: 'Những mục trong nhóm Hướng phát triển tiếp theo chưa phải tính năng đã triển khai.',
};

export const finalCta = {
  title: 'Từ dữ liệu phân tán đến quyết định tác nghiệp có thể giải thích',
};

export const team = {
  title: 'Debt Radar',
  subtitle: 'MSB AI Hackathon 2026',
  members: [
    { name: 'Hà Đức Quyết', org: 'DigiLenO', role: 'Trưởng nhóm' },
    { name: 'Phạm Huy Khánh', org: 'DigiLenO' },
    { name: 'Nguyễn Thị Phương', org: 'DC' },
  ],
};
import { assistantQuestionCatalog } from '../../assistant-question-catalog';
