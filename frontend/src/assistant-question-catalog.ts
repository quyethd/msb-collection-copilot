export type AssistantQuestionGroup = 'Quyết định' | 'Dòng tiền & cam kết' | 'Mô phỏng tình huống' | 'Tuyến xử lý & ưu tiên';

export const assistantQuestionCatalog: { question: string; group: AssistantQuestionGroup }[] = [
  { question: 'Tại sao hôm nay chưa nên gọi khách hàng này?', group: 'Quyết định' },
  { question: 'Dòng tiền gần đây của khách hàng thế nào?', group: 'Dòng tiền & cam kết' },
  { question: 'Khách hàng có cam kết thanh toán nào đang mở không?', group: 'Dòng tiền & cam kết' },
  { question: 'Nếu dòng tiền 7 ngày bằng 0 thì quyết định có thay đổi không?', group: 'Mô phỏng tình huống' },
  { question: 'Vì sao khách hàng này được ưu tiên?', group: 'Quyết định' },
  { question: 'Yếu tố nào đang ảnh hưởng mạnh nhất đến quyết định?', group: 'Quyết định' },
  { question: 'Nếu cam kết thanh toán bị phá vỡ thì nên làm gì?', group: 'Mô phỏng tình huống' },
  { question: 'Khách hàng này đang thuộc CALL hay CBS?', group: 'Tuyến xử lý & ưu tiên' },
  { question: 'Tại sao hệ thống đề xuất chờ thay vì liên hệ?', group: 'Quyết định' },
  { question: 'Điều gì cần thay đổi để khách hàng được ưu tiên cao hơn?', group: 'Tuyến xử lý & ưu tiên' },
];

export const commonAssistantQuestions = assistantQuestionCatalog.slice(0, 4);
