export const brand = {
  bank: 'MSB',
  product: 'Trợ lý Thu hồi Nợ',
  poweredBy: 'Powered by GreenNode AI',
};

export const hero = {
  headline: 'Trợ lý quyết định thu hồi nợ cho tác nghiệp CALL/CBS',
  value: 'Giúp cán bộ xác định khách hàng nào nên xử lý trước, vì sao, hành động nào phù hợp và thời điểm nào nên thực hiện.',
  strong: 'Không tìm khách hàng nợ nhiều nhất. Tìm cơ hội thu hồi tốt nhất tiếp theo.',
  ctaPrimary: 'Xem cách hệ thống hoạt động',
  ctaSecondary: 'Xem kiến trúc',
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
      { left: 'DPD cao', right: 'cơ hội thu hồi tốt nhất' },
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
      'biết khách hàng nào nên ưu tiên',
      'biết trường hợp nào thuộc CALL nhưng chưa cần gọi ngay',
      'xem action phù hợp',
      'xem lý do trên cùng một màn hình',
      'giảm việc tự tổng hợp nhiều nguồn dữ liệu',
    ],
  },
  {
    id: 'benefit-cbs',
    group: 'operations',
    title: 'Tác nghiệp CBS',
    kicker: 'Người nhắc thanh toán và theo dõi cam kết',
    points: [
      'xác định khách cần nhắc thanh toán',
      'khách phù hợp để chờ tự thanh toán',
      'theo dõi tín hiệu dòng tiền',
      'theo dõi cam kết thanh toán',
      'hạn chế tác động không cần thiết',
    ],
  },
  {
    id: 'benefit-management',
    group: 'management',
    title: 'Team Leader / Collection Manager',
    kicker: 'Quản lý và phân bổ tác nghiệp',
    points: [
      'nhìn tổng quan danh mục',
      'phân bổ hành động',
      'xem danh sách ưu tiên',
      'phát hiện trường hợp cần chú ý',
      'theo dõi tác động vận hành',
    ],
  },
  {
    id: 'benefit-architecture',
    group: 'architecture',
    title: 'Architecture / Technology',
    kicker: 'Chuyên gia xem xét tính bền vững',
    points: [
      'deterministic decision',
      'traceable rules',
      'AI cannot override NBA',
      'grounded tool use',
      'testable architecture',
      'clear module boundaries',
      'guardrails',
      'auditability',
    ],
  },
];

export const whoWhyWhatWhen = {
  title: 'Bốn câu hỏi vận hành, một luồng quyết định',
};

export const steps: { step: string; label: string; question: string; system: string }[] = [
  { step: 'WHO', label: 'Khách hàng nào nên ưu tiên?', question: 'Ai cần được xử lý trước trong danh mục?', system: 'Recovery Opportunity + Ranking' },
  { step: 'WHY', label: 'Vì sao khách hàng này được ưu tiên?', question: 'Tín hiệu nào dẫn tới mức ưu tiên này?', system: 'Evidence + GreenNode Agent' },
  { step: 'WHAT', label: 'Hành động phù hợp là gì?', question: 'Cần làm gì với khách hàng này?', system: 'Next Best Action' },
  { step: 'WHEN', label: 'Thực hiện ngay, chờ hay theo dõi?', question: 'Thời điểm thực hiện thế nào?', system: 'Cashflow + PTP + callback + suppression + next action' },
];

export const heroExample = {
  title: 'Ví dụ tác nghiệp: SYN002846',
  cif: 'SYN002846',
  disclaimer: 'Số liệu mô phỏng đã được chấp nhận trong bản demo.',
  rows: [
    { label: 'DPD', value: '11 ngày' },
    { label: 'Tiền vào 7 ngày', value: '48 triệu đồng' },
    { label: 'Dòng tiền ròng 30 ngày', value: '168 triệu đồng' },
    { label: 'PTP', value: 'Không có cam kết đang mở' },
    { label: 'Tuyến', value: 'CALL' },
  ],
  recommendation: 'Chờ khách hàng tự thanh toán',
  secondary: 'Chưa cần liên hệ',
  explanation:
    'Khách hàng thuộc tuyến CALL nhưng tín hiệu dòng tiền gần đây đáp ứng điều kiện để ưu tiên chờ tự thanh toán tại thời điểm hiện tại.',
};

export const whatIf = {
  title: 'Cùng một khách hàng. Khác tín hiệu. Khác hành động phù hợp.',
  disclaimer: 'Minh họa chạy trên deterministic simulation engine.',
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
    { title: 'Dữ liệu khách hàng', detail: 'Loan / Debt · DPD · Cashflow · PTP · Call history · Next action' },
    { title: 'Hard Policy', detail: 'Ràng buộc không thể thay đổi' },
    { title: 'Routing', detail: 'Xác định tuyến CALL / CBS' },
    { title: 'Recovery Opportunity', detail: 'Điểm cơ hội thu hồi' },
    { title: 'Next Best Action', detail: 'Chọn hành động theo mức ưu tiên' },
    { title: 'Channel / Timing', detail: 'Kênh và thời điểm thực hiện' },
    { title: 'GreenNode Agent', detail: 'Giải thích · Hỏi đáp · Điều tra · Mô phỏng' },
  ],
  coreStatementTitle: 'Decision Core deterministic',
  coreStatement: 'là nguồn quyết định nghiệp vụ.',
  agentStatementTitle: 'GreenNode Agent',
  agentStatement: 'là lớp tương tác, điều phối tool và giải thích.',
};

export const ruleLayers = {
  title: 'Các lớp quyết định đang vận hành',
  intro: 'Sáu lớp độc lập. Mỗi lớp có trách nhiệm và thứ tự ưu tiên rõ ràng.',
};

export const routeCall = ['Heatmap = RED', 'Segment ∈ RED / ORANGE / YELLOW', 'DPD ≥ 5'];
export const routeCbs = ['Heatmap = RED', 'Segment ∈ RED / ORANGE / YELLOW', 'DPD < 5'];
export const routingNote = 'Routing là tuyến xử lý. Routing không đồng nghĩa action phải thực hiện ngay.';

export const ptpPrecedence = [
  'Callback',
  'Verify Contact',
  'Partial PTP',
  'Broken PTP',
  'Open PTP',
  'Kept PTP',
  'Self-cure',
  'RTP escalation',
  'Default route action',
];

export const scoring = {
  components: [
    { name: 'Business Urgency', weight: 20 },
    { name: 'Ability to Pay', weight: 25 },
    { name: 'Willingness to Pay', weight: 20 },
    { name: 'Contactability', weight: 15 },
    { name: 'Timing Opportunity', weight: 15 },
    { name: 'Strategic Adjustment', weight: 5 },
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
    'Người dùng thao tác qua giao diện MSB và API ứng dụng. Quyết định nghiệp vụ được xử lý bởi Decision Core deterministic từ dữ liệu mô phỏng. Khi người dùng hỏi Trợ lý, GreenNode Agent hiểu câu hỏi tự nhiên, chọn đúng công cụ nghiệp vụ, lấy quyết định từ Decision Core rồi giải thích dựa trên bằng chứng. GreenNode không phải yếu tố trang trí: Trợ lý dùng nó để tương tác tự nhiên, chọn công cụ, giải thích có căn cứ, điều tra và mô phỏng — còn quyết định thu hồi vẫn do engine deterministic nắm giữ.',
  coreLabel: 'Deterministic Decision Core',
  coreState: '= Source of Truth',
  agentLabel: 'GreenNode Agent',
  agentState: '= Interaction & Orchestration Layer',
  frontend: { title: 'FRONTEND', items: ['Tổng quan', 'Danh sách ưu tiên', 'Khách hàng', 'Tác động dự kiến'] },
  api: { title: 'API / DEMO LAYER', items: ['Customer 360', 'Portfolio', 'Timeline', 'Events', 'Impact'] },
  core: { title: 'DETERMINISTIC DECISION CORE', items: ['Policy', 'Recovery Score', 'NBA', 'Simulation'] },
  agent: { title: 'GRENNODE AGENT', items: ['Tool Use', 'Explain', 'Investigate', 'Simulate', 'Summary'] },
  data: { title: 'DATA / CONTEXT', items: ['Customer', 'Loan', 'Cashflow', 'PTP', 'Call history'] },
};

export const modules = {
  title: 'Bên trong hệ thống',
  intro: 'Các module chính và trách nhiệm của từng phần.',
};

export const moduleCards: { name: string; role: string; checks?: string[] }[] = [
  { name: 'msb_policy', role: 'Hard policy, routing, business constraints.' },
  { name: 'msb_recovery', role: 'Recovery Opportunity Score.' },
  { name: 'msb_nba', role: 'Next Best Action và thứ tự ưu tiên.' },
  { name: 'msb_simulation', role: 'Chạy tình huống deterministic mà không làm thay đổi context gốc.' },
  { name: 'msb_demo', role: 'Demo state, events và timeline.' },
  { name: 'msb_impact', role: 'Tác động vận hành và ước tính minh bạch theo giả định.' },
  { name: 'msb_agent', role: 'Agent runtime: điều phối tool, giải thích, điều tra và mô phỏng.' },
  {
    name: 'msb_agent_eval',
    role: 'Đánh giá độ tin cậy của Trợ lý.',
    checks: [
      'kiểm tra Agent dùng đúng công cụ nghiệp vụ',
      'so khớp quyết định Agent với deterministic engine',
      'kiểm tra khách hàng chưa biết không bị bịa dựng',
      'kiểm tra override guardrail',
      'kiểm tra không lộ lý do suy luận nội bộ',
    ],
  },
];

export const aiRole = {
  title: 'AI hỗ trợ hiểu quyết định, không thay đổi quyết định nghiệp vụ',
  safetyNote: 'Thiết kế giảm rủi ro AI tự suy diễn quyết định nghiệp vụ.',
  can: [
    'hiểu câu hỏi tự nhiên',
    'giải thích dựa trên bằng chứng',
    'tổng hợp bằng chứng từ dữ liệu',
    'chọn đúng công cụ nghiệp vụ',
    'điều tra ngữ cảnh khách hàng',
    'mô phỏng tình huống',
    'tóm tắt trạng thái',
  ],
  cannot: [
    'thay đổi quyết định của policy',
    'thay đổi hành động đề xuất (NBA)',
    'tự tạo dữ liệu khách hàng',
    'tự tạo cam kết thanh toán',
    'bịa số liệu dòng tiền',
    'tiết lộ lý do suy luận nội bộ',
  ],
};

export const trust = {
  title: 'Quyết định có thể kiểm chứng',
  badges: [
    'Quyết định Deterministic',
    'Truy vết quy tắc (Rule Trace)',
    'Grounded vào dữ liệu (Tool Grounding)',
    'AI không thay đổi quyết định',
    'CIF chưa biết an toàn',
    'Đã kiểm tra Prompt Injection',
    'Không lộ lý do suy luận',
  ],
  points: [
    'Quyết định nghiệp vụ đến từ các quy tắc deterministic.',
    'AgentBase truy xuất công cụ nghiệp vụ trước khi giải thích câu hỏi quyết định.',
    'Khách hàng chưa biết không bị bịa dựng thông tin.',
    'Yêu cầu can thiệp không làm thay đổi quyết định nghiệp vụ đã chấp nhận.',
    'Lý do suy luận nội bộ không được tiết lộ.',
  ],
  status: 'Đã kiểm chứng AgentBase kết nối công cụ quyết định và giữ nguyên kết quả nghiệp vụ.',
};

export const dayTimeline = {
  title: 'Một ngày tác nghiệp với Trợ lý Thu hồi Nợ',
  entries: [
    { time: '08:00', action: 'Mở Tổng quan', note: 'Xem danh mục, tuyến xử lý và các điểm cần chú ý.' },
    { time: '08:05', action: 'Mở Danh sách ưu tiên', note: 'Xác định khách hàng nên xử lý trước.' },
    { time: '08:10', action: 'Mở hồ sơ khách hàng', note: 'Xem dư nợ, DPD, dòng tiền, PTP, lịch sử liên hệ và hành động đề xuất.' },
    { time: '08:12', action: 'Hỏi Trợ lý', note: '"Tại sao hôm nay chưa nên gọi khách hàng này?"' },
    { time: '08:15', action: 'Thực hiện hành động', note: 'Liên hệ / nhắc / theo dõi PTP / chờ tự thanh toán theo quyết định hiện tại.' },
  ],
};

export const sampleQuestions = {
  title: 'Bạn có thể hỏi Trợ lý điều gì?',
  note: 'Các câu hỏi dưới đây là ví dụ. Từ trang Tổng quan, Trợ lý trả lời dựa trên quyết định đã được xác định và dữ liệu khách hàng hiện có.',
  questions: [
    'Tại sao hôm nay chưa nên gọi khách hàng này?',
    'Vì sao khách hàng này được ưu tiên?',
    'Yếu tố nào đang ảnh hưởng mạnh nhất đến quyết định?',
    'Khách hàng có cam kết thanh toán nào đang mở không?',
    'Dòng tiền gần đây của khách hàng thế nào?',
    'Nếu dòng tiền 7 ngày bằng 0 thì quyết định có thay đổi không?',
    'Nếu cam kết thanh toán bị phá vỡ thì nên làm gì?',
    'Khách hàng này đang thuộc CALL hay CBS?',
    'Tại sao hệ thống đề xuất chờ thay vì liên hệ?',
    'Điều gì cần thay đổi để khách hàng được ưu tiên cao hơn?',
  ],
};

export const faqs: { question: string; answer: string }[] = [
  {
    question: 'AI có tự quyết định khách hàng nào phải gọi không?',
    answer:
      'Không. Quyết định nghiệp vụ do Decision Engine deterministic tạo ra. AI sử dụng kết quả đã được xác định để hỗ trợ giải thích, truy vấn và mô phỏng.',
  },
  {
    question: 'Thuộc tuyến CALL có nghĩa là phải gọi ngay không?',
    answer:
      'Không. CALL là tuyến xử lý. Next Best Action có thể đề xuất chờ khách hàng tự thanh toán nếu tín hiệu hiện tại đáp ứng điều kiện.',
  },
  {
    question: 'Điểm cơ hội thu hồi có phải xác suất khách hàng sẽ trả tiền không?',
    answer: 'Không. Đây là điểm ưu tiên tương đối được xây dựng từ các tín hiệu nghiệp vụ hiện có.',
  },
  {
    question: 'Nếu AI không hoạt động thì hệ thống có còn ra quyết định không?',
    answer:
      'Có. Policy, Recovery Opportunity và Next Best Action được xử lý bởi Decision Core deterministic. AI là lớp hỗ trợ tương tác và giải thích.',
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
      'Rule Engine đảm bảo quyết định nghiệp vụ nhất quán và kiểm soát được. GreenNode Agent giúp cán bộ truy vấn, điều tra, tổng hợp evidence, giải thích và mô phỏng quyết định bằng ngôn ngữ tự nhiên mà không cần đọc thủ công nhiều trường dữ liệu.',
  },
];

export const roadmap = {
  title: 'Lộ trình sản phẩm',
  current: {
    label: 'Đã có trong bản demo',
    items: ['Decision Intelligence', 'CALL / CBS', 'Recovery Opportunity', 'Next Best Action', 'What-if Simulation', 'GreenNode Agent'],
  },
  future: {
    label: 'Hướng phát triển tiếp theo',
    items: [
      'Outcome feedback',
      'Pilot / A-B evaluation',
      'Learning-to-rank',
      'Channel optimization',
      'Treatment optimization',
      'Portfolio monitoring',
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