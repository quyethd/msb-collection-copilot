// @vitest-environment jsdom
import { describe, expect, it, beforeEach, afterEach } from 'vitest';
import { createRoot, type Root } from 'react-dom/client';
import { act } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { SystemOverviewPage } from './SystemOverviewPage';
import {
  aiRole,
  architecture,
  benefitCards,
  brand,
  faqs,
  greenNodeStory,
  hero,
  heroExample,
  knowledgeAssistant,
  moduleCards,
  modules,
  nbaActions,
  pains,
  pipeline,
  ptpPrecedence,
  recoveryExample,
  routingNote,
  ruleLayers,
  sampleQuestions,
  scoring,
  steps,
  team,
  whatIf,
} from './content';

const page = () =>
  renderToStaticMarkup(
    <SystemOverviewPage onOpenOverview={() => undefined} onOpenCustomer={() => undefined} />,
  );

const html = page();

describe('TASK-011F system overview page', () => {
  it('renders hero product message and brand', () => {
    expect(html).toContain(brand.bank);
    expect(html).toContain(brand.product);
    expect(html).toContain(brand.poweredBy);
    expect(html).toContain('Trợ lý Thu hồi Nợ cho cán bộ và đội ngũ thu hồi nợ');
    expect(html).toContain('Không tìm khách hàng nợ nhiều nhất.');
    expect(html).toContain('Tìm cơ hội thu hồi tốt nhất tiếp theo.');
    for (const chip of ['Đúng khách hàng', 'Đúng hành động', 'Đúng thời điểm', 'Lý do rõ ràng']) {
      expect(html).toContain(chip);
    }
    for (const cta of [hero.ctaPrimary, hero.ctaSecondary]) {
      expect(html).toContain(cta);
    }
    expect(html).not.toMatch(/<div class="so-hero">[\s\S]*?<div class="so-brand">/);
    expect(html).toContain('so-footer-brand');
  });

  it('shows the synthetic-data disclaimer', () => {
    expect(html).toContain(hero.disclaimer);
  });

  it('shows audience shortcuts for operations, management and architecture', () => {
    expect(html).toContain('Dành cho Tác nghiệp');
    expect(html).toContain('Dành cho Quản lý');
    expect(html).toContain('Dành cho Kiến trúc / Công nghệ');
    expect(html).toContain('#audience-operations');
    expect(html).toContain('#audience-management');
    expect(html).toContain('#architecture');
  });

  it('explains the four core pains', () => {
    expect(html).toContain('Từ danh sách nợ đến quyết định hành động');
    expect(pains).toHaveLength(4);
    expect(html).toContain('Quá hạn cao');
    expect(html).toContain('Dư nợ cao');
    expect(html).toContain('cơ hội thu hồi tốt nhất');
    expect(html).toContain('cần gọi ngay');
    expect(html).toContain('Thuộc tuyến CALL không có nghĩa hôm nay nhất thiết phải gọi.');
    expect(html).toContain('Tại sao hệ thống lại đề xuất hành động này?');
    for (const signal of ['Số ngày quá hạn (DPD)', 'Dòng tiền', 'Cam kết thanh toán', 'Tuyến CALL / CBS']) {
      expect(html).toContain(signal);
    }
  });

  it('covers CALL and CBS audiences', () => {
    expect(benefitCards.some((c) => c.title.includes('CALL'))).toBe(true);
    expect(benefitCards.some((c) => c.title.includes('CBS'))).toBe(true);
    expect(html).toContain('Tác nghiệp CALL');
    expect(html).toContain('Tác nghiệp CBS');
    expect(html).toContain('Trưởng nhóm / Quản lý thu hồi');
    expect(html).toContain('Kiến trúc / Công nghệ');
  });

  it('maps WHO / WHY / WHAT / WHEN to actual system stages', () => {
    expect(html).toContain('WHO');
    expect(html).toContain('WHY');
    expect(html).toContain('WHAT');
    expect(html).toContain('WHEN');
    expect(steps).toHaveLength(4);
    expect(html).toContain('Cơ hội thu hồi (Recovery Opportunity) + Xếp hạng');
    expect(html).toContain('Bằng chứng + GreenNode Agent');
    expect(html).toContain('Hành động đề xuất tiếp theo (Next Best Action)');
    expect(html).toContain('Dòng tiền + Cam kết thanh toán + lịch liên hệ + hành động tiếp theo');
  });

  it('shows the accepted SYN002846 hero facts', () => {
    expect(heroExample.cif).toBe('SYN002846');
    expect(html).toContain('SYN002846');
    expect(html).toContain('11 ngày');
    expect(html).toContain('48 triệu đồng');
    expect(html).toContain('168 triệu đồng');
    expect(html).toContain('Không có cam kết đang mở');
    expect(html).toContain('CALL');
    expect(html).toContain('Chờ khách hàng tự thanh toán');
    expect(html).toContain('Chưa cần liên hệ');
    expect(html).toContain(heroExample.explanation);
    expect(html).not.toContain('khách chắc chắn sẽ trả');
  });

  it('shows the what-if example with the deterministic simulation note', () => {
    expect(html).toContain(whatIf.title);
    expect(html).toContain('Cùng một khách hàng. Khác tín hiệu. Khác hành động phù hợp.');
    expect(html).toContain('48 triệu');
    expect(html).toContain('168 triệu');
    expect(html).toContain('Liên hệ khách hàng');
    expect(html).toContain(whatIf.disclaimer);
  });

  it('keeps decision responsibility separated: deterministic core vs GreenNode Agent', () => {
    expect(html).toContain(pipeline.coreStatementTitle);
    expect(html).toContain('= Nguồn quyết định nghiệp vụ');
    expect(html).toContain(pipeline.agentStatementTitle);
    expect(html).toContain('= Lớp tương tác và điều phối');
    for (const stage of pipeline.stages) {
      expect(html).toContain(stage.title);
    }
  });

  it('represents the six decision layers', () => {
    expect(html).toContain(ruleLayers.title);
    for (const layer of ['Chính sách bắt buộc (HARD POLICY)', 'Tuyến xử lý (ROUTING)', 'Chặn bắt buộc (HARD SUPPRESSION)', 'Cam kết / hành động tiếp theo (PTP / NEXT ACTION)', 'Cơ Hội Thu Hồi (Recovery Opportunity)', 'Hành động đề xuất (NEXT BEST ACTION)']) {
      expect(html).toContain(layer);
    }
    expect(html).toContain('CALL');
    expect(html).toContain('CBS');
    expect(html).toContain('Mức cảnh báo = ĐỎ');
    expect(html).toContain('Số ngày quá hạn từ 5 ngày');
    expect(html).toContain('Số ngày quá hạn dưới 5 ngày');
    expect(html).toContain(routingNote);
    for (const precedence of ptpPrecedence) {
      expect(html).toContain(precedence);
    }
    expect(html).toContain(scoring.disclaimer);
    expect(html).toContain('100');
    for (const component of scoring.components) {
      expect(html).toContain(component.name);
    }
    for (const action of nbaActions) {
      expect(html).toContain(action);
    }
    expect(html).not.toMatch(/NBA-\d{3}/);
  });

  it('explains the real Recovery Opportunity calculation for SYN002846', () => {
    expect(html).toContain('Các thanh dưới đây là điểm tối đa của từng nhóm, không phải điểm SYN002846 đã đạt.');
    expect(html).toContain('Xem Cách Tính Điểm');
    expect(html).toContain('Ví dụ từ dữ liệu mô phỏng — SYN002846');
    expect(html).toContain('Tổng điểm tối đa');
    expect(html).toContain('47 / 100');
    expect(html).toContain('Cam kết thanh toán (PTP)');
    expect(html).toContain('Có tín hiệu thu nhập từ lương');
    expect(html).toContain('Số lần không liên lạc được');
    expect(html).not.toContain('Có nguồn SALARY');
    expect(html).not.toContain('dữ liệu UTC');
    expect(html).not.toContain('phân vị 0,9697');
    expect(html).not.toContain('module msb_recovery');
    expect(html).not.toContain('RULE_BASE_V1');
    expect(recoveryExample.total).toBe(47);
    expect(recoveryExample.components.map((component) => component.score)).toEqual([8, 20, 4, 11, 4, 0]);
    expect(recoveryExample.components.reduce((sum, component) => sum + component.score, 0)).toBe(recoveryExample.total);
    expect(recoveryExample.components.map((component) => component.maxScore)).toEqual([20, 25, 20, 15, 15, 5]);
    for (const component of recoveryExample.components) {
      expect(html).toContain(`${component.score} / ${component.maxScore}`);
      for (const signal of component.signals) {
        expect(html).toContain(signal.value);
        expect(html).toContain(signal.points);
      }
    }
  });

  it('contains the architecture section with separated decision and knowledge paths', () => {
    expect(html).toContain(architecture.title);
    expect(html).toContain(architecture.intro);
    expect(html).toContain('Kiểm tra độ tin cậy, khả năng truy vết, kiểm thử và vận hành lâu dài');
    expect(html).toContain(architecture.coreLabel);
    expect(html).toContain('là nguồn quyết định nghiệp vụ.');
    expect(html).toContain(architecture.agentLabel);
    expect(html).toContain(pipeline.agentStatement);
    for (const layer of [architecture.frontend, architecture.api, architecture.customerPath, architecture.knowledgePath]) {
      expect(html).toContain(layer.title);
      for (const item of layer.items) {
        expect(html).toContain(item);
      }
    }
    expect(html).toContain(architecture.decisionPathLabel);
    expect(html).toContain(architecture.knowledgePathLabel);
    expect(html).toContain(architecture.pathNote);
    expect(html).toContain('GreenNode Vector Database');
    expect(html).toContain('Qwen Flash');
  });

  it('shows code module cards', () => {
    expect(html).toContain(modules.title);
    expect(moduleCards.length).toBeGreaterThanOrEqual(7);
    for (const card of moduleCards) {
      expect(html).toContain(card.name);
    }
    expect(html).toContain('msb_agent_eval');
    expect(html).toContain('Đánh giá độ tin cậy của Trợ lý');
    const evalCard = moduleCards.find((c) => c.name === 'msb_agent_eval');
    expect(evalCard?.checks).toBeTruthy();
    for (const check of evalCard?.checks ?? []) {
      expect(html).toContain(check);
    }
  });

  it('shows AI can and cannot columns', () => {
    expect(html).toContain(aiRole.title);
    expect(html).toContain('AI làm gì');
    expect(html).toContain('AI không làm gì');
    expect(html).toContain(aiRole.safetyNote);
    expect(html).toContain('Thiết kế giảm rủi ro AI tự suy diễn quyết định nghiệp vụ.');
    for (const item of aiRole.can) {
      expect(html).toContain(item);
    }
    for (const item of aiRole.cannot) {
      expect(html).toContain(item);
    }
  });

  it('shows trust badges without overclaiming AgentBase proof', () => {
    expect(html).toContain('Quyết định Deterministic');
    expect(html).toContain('Đã kiểm tra Prompt Injection');
    expect(html).toContain('Không lộ lý do suy luận');
    expect(html).not.toContain('Đã kiểm chứng AgentBase kết nối công cụ quyết định và giữ nguyên kết quả nghiệp vụ.');
    expect(html).toContain('Kho kiến thức có nguồn tham khảo đã được kiểm tra trong bản demo.');
    expect(html).toContain('Lý do suy luận nội bộ không được tiết lộ.');
    expect(html).toContain('Trả lời kiến thức có nguồn (RAG)');
    expect(html).not.toMatch(/AgentBase[\s\S]{0,40}PASS/i);
    expect(html).not.toContain('Đang hoàn thiện kiểm chứng AgentBase');
  });

  it('shows the knowledge-assistant section with two separated lanes', () => {
    expect(html).toContain(knowledgeAssistant.title);
    expect(html).toContain(knowledgeAssistant.intro);
    expect(html).toContain(knowledgeAssistant.trustMessage);
    expect(html).toContain(knowledgeAssistant.decision.title);
    expect(html).toContain(knowledgeAssistant.knowledge.title);
    expect(html).toContain(knowledgeAssistant.sources);
    for (const example of [...knowledgeAssistant.decision.examples, ...knowledgeAssistant.knowledge.examples]) {
      expect(html.replace(/&quot;/g, '')).toContain(example.replace(/"/g, ''));
    }
  });

  it('makes GreenNode AI, Qwen Flash, vDB and local embedding visible', () => {
    for (const component of greenNodeStory.components) {
      expect(html).toContain(component.title);
      expect(html).toContain(component.detail);
    }
    expect(html).toContain('Qwen Flash');
    expect(html).toContain('GreenNode Vector Database');
    expect(html).toContain('Nhúng đa ngôn ngữ cục bộ');
    expect(html).toContain('Nền Tảng AI GreenNode');
  });

  it('keeps the 14 shared sample questions incl. knowledge suggestions', () => {
    expect(sampleQuestions.questions).toHaveLength(14);
    expect(html).toContain('CALL và CBS khác nhau thế nào?');
    expect(html).toContain('GreenNode AI đóng vai trò gì trong hệ thống?');
    expect(html).toContain('Điểm Cơ hội thu hồi được tính như thế nào?');
    expect(html).toContain('Trợ lý có tự quyết định phương án xử lý không?');
  });

  it('shows operator questions and FAQ', () => {
    expect(html).toContain('Bạn có thể hỏi Trợ lý điều gì?');
    expect(html).toContain('Tại sao hôm nay chưa nên gọi khách hàng này?');
    expect(faqs).toHaveLength(9);
    const plain = html.replace(/&quot;/g, '');
    for (const faq of faqs) {
      expect(plain).toContain(faq.question.replace(/"/g, ''));
      expect(plain).toContain(faq.answer.length > 3 ? faq.answer.replace(/"/g, '') : faq.question);
    }
  });

  it('shows a roadmap clearly marked as future', () => {
    expect(html).toContain('Lộ trình sản phẩm');
    expect(html).toContain('Đã có trong bản demo');
    expect(html).toContain('Giai đoạn 1 — Kết nối dữ liệu');
    expect(html).toContain('Giai đoạn 2 — AI hỗ trợ tác nghiệp');
    expect(html).toContain('Giai đoạn 3 — Tối ưu liên tục');
    expect(html).toContain('HƯỚNG PHÁT TRIỂN TƯƠNG LAI');
    expect(html).toContain('Cả ba giai đoạn đều là Hướng phát triển tương lai');
    expect(html).toContain('T24 / Temenos Transact');
    expect(html).toContain('DigiLenO');
    expect(html).toContain('Mô phỏng tình huống');
    expect(html).not.toContain('FUTURE / ROADMAP');
  });

  it('shows exactly three team members with the leader labelled', () => {
    expect(html).toContain('Debt Radar');
    expect(html).toContain('MSB AI Hackathon 2026');
    expect(team.members).toHaveLength(3);
    for (const member of team.members) {
      expect(html).toContain(member.name);
    }
    expect(html).toContain('Hà Đức Quyết');
    expect(html).toContain('DigiLenO — Trưởng nhóm');
  });

  it('does not make unsupported operational or recovery claims', () => {
    const banned = [
      'tăng tỷ lệ thu hồi',
      'tỷ lệ thu hồi',
      'giảm %',
      '% cuộc gọi',
      'cuộc gọi thực tế',
      'chắc chắn sẽ trả',
      'chắc chắn trả',
      'sẽ thanh toán chắc chắn',
    ];
    for (const phrase of banned) {
      expect(html).not.toContain(phrase);
    }
    expect(html).toContain('không phải xác suất khách hàng chắc chắn thanh toán');
  });
});

describe('TASK-011F interactive behaviour', () => {
  let container: HTMLDivElement;
  let root: Root;

  beforeEach(() => {
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);
  });

  afterEach(() => {
    act(() => root.unmount());
    container.remove();
  });

  it('toggles the FAQ via the keyboard-accessible button', () => {
    act(() => {
      root.render(<SystemOverviewPage onOpenOverview={() => undefined} onOpenCustomer={() => undefined} />);
    });
    const firstButton = container.querySelector('.so-faq-toggle') as HTMLButtonElement | null;
    expect(firstButton).not.toBeNull();
    expect(firstButton!.getAttribute('aria-expanded')).toBe('true');

    act(() => {
      firstButton!.click();
    });
    expect(firstButton!.getAttribute('aria-expanded')).toBe('false');

    act(() => {
      firstButton!.click();
    });
    expect(firstButton!.getAttribute('aria-expanded')).toBe('true');
  });

  it('invokes callback props from the final CTA', () => {
    let overviewCalls = 0;
    let customerCalls = 0;
    act(() => {
      root.render(
        <SystemOverviewPage
          onOpenOverview={() => {
            overviewCalls += 1;
          }}
          onOpenCustomer={(cif) => {
            customerCalls += 1;
            expect(cif).toBe('SYN002846');
          }}
        />,
      );
    });
    const buttons = Array.from(container.querySelectorAll('.so-final-buttons button')) as HTMLButtonElement[];
    expect(buttons).toHaveLength(2);
    act(() => {
      buttons[0].click();
      buttons[1].click();
    });
    expect(overviewCalls).toBe(1);
    expect(customerCalls).toBe(1);
  });
});

describe('TASK-011F source hygiene', () => {
  const sourceDir = resolve(__dirname);
  const files = ['SystemOverviewPage.tsx', 'content.ts'].map((name) => readFileSync(resolve(sourceDir, name), 'utf8'));

  it('does not embed credentials or secret names in the page source', () => {
    for (const source of files) {
      expect(source).not.toMatch(/COLLECTION_TOOL_API_KEY|GREENNODE_CLIENT_SECRET|LLM_API_KEY|CLIENT_SECRET|Bearer [A-Za-z0-9]/);
    }
  });

  it('does not leak internal decision enum codes in page source', () => {
    for (const source of files) {
      expect(source).not.toMatch(/NBA-\d{3}|WAIT_SELF_CURE|SCORE-|ROUTE-001/);
    }
  });
});

describe('TASK-011F content contract', () => {
  it('keeps accepted SYN002846 numbers literal', () => {
    expect(heroExample.rows.filter((r) => r.label === 'Tiền vào 7 ngày')[0].value).toBe('48 triệu đồng');
    expect(heroExample.rows.filter((r) => r.label === 'Dòng tiền ròng 30 ngày')[0].value).toBe('168 triệu đồng');
    expect(heroExample.rows.filter((r) => r.label.includes('DPD'))[0].value).toBe('11 ngày');
    expect(whatIf.rows[0].before).toBe('48 triệu');
    expect(whatIf.rows[1].before).toBe('168 triệu');
  });
});
