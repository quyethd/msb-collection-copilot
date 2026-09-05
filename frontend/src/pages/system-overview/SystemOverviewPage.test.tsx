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
  hero,
  heroExample,
  moduleCards,
  modules,
  nbaActions,
  pains,
  pipeline,
  ptpPrecedence,
  routingNote,
  ruleLayers,
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
    expect(html).toContain('Trợ lý quyết định thu hồi nợ');
    expect(html).toContain('cho tác nghiệp CALL/CBS');
    expect(html).toContain('Không tìm khách hàng nợ nhiều nhất.');
    expect(html).toContain('Tìm cơ hội thu hồi tốt nhất tiếp theo.');
    for (const chip of ['Đúng khách hàng', 'Đúng hành động', 'Đúng thời điểm', 'Lý do rõ ràng']) {
      expect(html).toContain(chip);
    }
    for (const cta of [hero.ctaPrimary, hero.ctaSecondary]) {
      expect(html).toContain(cta);
    }
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
    expect(html).toContain('DPD cao');
    expect(html).toContain('Dư nợ cao');
    expect(html).toContain('cơ hội thu hồi tốt nhất');
    expect(html).toContain('cần gọi ngay');
    expect(html).toContain('Thuộc tuyến CALL không có nghĩa hôm nay nhất thiết phải gọi.');
    expect(html).toContain('Tại sao hệ thống lại đề xuất hành động này?');
    for (const signal of ['DPD', 'Dòng tiền', 'Cam kết thanh toán', 'Tuyến CALL / CBS']) {
      expect(html).toContain(signal);
    }
  });

  it('covers CALL and CBS audiences', () => {
    expect(benefitCards.some((c) => c.title.includes('CALL'))).toBe(true);
    expect(benefitCards.some((c) => c.title.includes('CBS'))).toBe(true);
    expect(html).toContain('Tác nghiệp CALL');
    expect(html).toContain('Tác nghiệp CBS');
    expect(html).toContain('Team Leader / Collection Manager');
    expect(html).toContain('Architecture / Technology');
  });

  it('maps WHO / WHY / WHAT / WHEN to actual system stages', () => {
    expect(html).toContain('WHO');
    expect(html).toContain('WHY');
    expect(html).toContain('WHAT');
    expect(html).toContain('WHEN');
    expect(steps).toHaveLength(4);
    expect(html).toContain('Recovery Opportunity + Ranking');
    expect(html).toContain('Evidence + GreenNode Agent');
    expect(html).toContain('Next Best Action');
    expect(html).toContain('Cashflow + PTP + callback + suppression + next action');
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
    expect(html).toContain('là nguồn quyết định nghiệp vụ.');
    expect(html).toContain(pipeline.agentStatementTitle);
    expect(html).toContain('là lớp tương tác, điều phối tool và giải thích.');
    for (const stage of pipeline.stages) {
      expect(html).toContain(stage.title);
    }
  });

  it('represents the six decision layers', () => {
    expect(html).toContain(ruleLayers.title);
    for (const layer of ['HARD POLICY', 'ROUTING', 'HARD SUPPRESSION', 'PTP / NEXT ACTION', 'RECOVERY OPPORTUNITY', 'NEXT BEST ACTION']) {
      expect(html).toContain(layer);
    }
    expect(html).toContain('CALL');
    expect(html).toContain('CBS');
    expect(html).toContain('Heatmap = RED');
    expect(html).toContain('DPD ≥ 5');
    expect(html).toContain('DPD &lt; 5');
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

  it('contains the architecture section with layer labels', () => {
    expect(html).toContain(architecture.title);
    expect(html).toContain(architecture.intro);
    expect(html).toContain('GreenNode không phải yếu tố trang trí');
    expect(html).toContain(architecture.coreLabel);
    expect(html).toContain('= Source of Truth');
    expect(html).toContain(architecture.agentLabel);
    expect(html).toContain('= Interaction &amp; Orchestration Layer');
    for (const layer of [architecture.frontend, architecture.api, architecture.core, architecture.agent, architecture.data]) {
      expect(html).toContain(layer.title);
      for (const item of layer.items) {
        expect(html).toContain(item);
      }
    }
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
    expect(html).toContain('Đã kiểm chứng AgentBase kết nối công cụ quyết định và giữ nguyên kết quả nghiệp vụ.');
    expect(html).toContain('Lý do suy luận nội bộ không được tiết lộ.');
    expect(html).not.toMatch(/AgentBase[\s\S]{0,40}PASS/i);
    expect(html).not.toContain('Đang hoàn thiện kiểm chứng AgentBase');
  });

  it('shows operator questions and FAQ', () => {
    expect(html).toContain('Bạn có thể hỏi Trợ lý điều gì?');
    expect(html).toContain('Tại sao hôm nay chưa nên gọi khách hàng này?');
    expect(faqs).toHaveLength(7);
    for (const faq of faqs) {
      expect(html).toContain(faq.question);
      expect(html).toContain(faq.answer.length > 3 ? faq.answer : faq.question);
    }
  });

  it('shows a roadmap clearly marked as future', () => {
    expect(html).toContain('Lộ trình sản phẩm');
    expect(html).toContain('Đã có trong bản demo');
    expect(html).toContain('Hướng phát triển tiếp theo');
    expect(html).toContain('Learning-to-rank');
    expect(html).toContain('Outcome feedback');
    expect(html).toContain('Những mục trong nhóm Hướng phát triển tiếp theo chưa phải tính năng đã triển khai.');
    expect(html).toContain('What-if Simulation');
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
    expect(heroExample.rows.filter((r) => r.label === 'DPD')[0].value).toBe('11 ngày');
    expect(whatIf.rows[0].before).toBe('48 triệu');
    expect(whatIf.rows[1].before).toBe('168 triệu');
  });
});