import { useMemo, useState } from 'react';
import {
  Activity,
  AlertTriangle,
  ArrowDown,
  ArrowRight,
  BadgeCheck,
  Ban,
  BookOpen,
  Bot,
  Box,
  CalendarDays,
  CheckCircle2,
  ChevronDown,
  ClipboardList,
  Cpu,
  Database,
  GitBranch,
  ListChecks,
  MessagesSquare,
  Monitor,
  PhoneCall,
  PieChart,
  Rocket,
  Scale,
  Search,
  Server,
  ShieldCheck,
  Sparkles,
  Wallet,
  Workflow,
  XCircle,
} from 'lucide-react';
import {
  aiRole,
  architecture,
  audienceNav,
  benefitCards,
  benefitChips,
  benefitSection,
  brand,
  dayTimeline,
  faqs,
  finalCta,
  greenNodeStory,
  knowledgeAssistant,
  hero,
  heroExample,
  moduleCards,
  modules,
  nbaActions,
  pains,
  pipeline,
  problemSection,
  ptpPrecedence,
  roadmap,
  routeCall,
  routeCbs,
  routingNote,
  ruleLayers,
  sampleQuestions,
  scoring,
  steps,
  team,
  trust,
  whatIf,
  whoWhyWhatWhen,
} from './content';

export interface SystemOverviewPageProps {
  onOpenOverview?: () => void;
  onOpenCustomer?: (cif: string) => void;
  ctaOverviewLabel?: string;
  ctaCustomerLabel?: string;
  heroPrimaryHref?: string;
  heroPrimaryLabel?: string;
}

const noop = () => undefined;

export function SystemOverviewPage({
  onOpenOverview,
  onOpenCustomer,
  ctaOverviewLabel = 'Mở Tổng quan',
  ctaCustomerLabel = 'Xem khách hàng mẫu SYN002846',
  heroPrimaryHref = '#pipeline',
  heroPrimaryLabel = hero.ctaPrimary,
}: SystemOverviewPageProps) {
  const overview = useMemo(() => onOpenOverview ?? noop, [onOpenOverview]);
  const openCustomer = useMemo(() => onOpenCustomer ?? noop, [onOpenCustomer]);
  const [openFaq, setOpenFaq] = useState<number | null>(0);

  return (
    <div className="system-overview-page">
      <a className="so-skip" href="#so-main">
        Chuyển tới nội dung chính
      </a>
      <div className="so-hero">
        <div className="so-hero-inner">
          <div className="so-brand">
            <div className="so-brand-logo">{brand.bank}</div>
            <div className="so-brand-name">
              <b>{brand.product}</b>
              <span>{brand.poweredBy}</span>
            </div>
          </div>
          <h1 className="so-headline">{hero.headline}</h1>
          <p className="so-value">{hero.value}</p>
          <p className="so-strong">
            <Sparkles size={16} aria-hidden="true" />
            {hero.strong}
          </p>
          <ul className="so-benefit-chips" aria-label="Lợi ích cốt lõi">
            {benefitChips.map((chip) => (
              <li key={chip}>
                <CheckCircle2 size={15} aria-hidden="true" />
                {chip}
              </li>
            ))}
          </ul>
          <div className="so-hero-cta">
            <a className="so-btn so-btn-primary" href={heroPrimaryHref}>
              {heroPrimaryLabel}
              <ArrowRight size={16} />
            </a>
            <a className="so-btn so-btn-outline" href="#architecture">
              {hero.ctaSecondary}
            </a>
          </div>
          <p className="so-disclaimer">{hero.disclaimer}</p>
        </div>
      </div>

      <nav className="so-audience-nav" aria-label="Chọn đối tượng xem nhanh">
        <span className="so-audience-label">Xem nhanh</span>
        {audienceNav.map((item) => (
          <a key={item.href} href={item.href} className="so-audience-link">
            {item.label}
            <ArrowRight size={14} />
          </a>
        ))}
      </nav>

      <main id="so-main" className="so-body">
        <section className="so-section" id="problem">
          <div className="so-section-head">
            <span className="so-eyebrow">BÀI TOÁN</span>
            <h2>{problemSection.title}</h2>
            <p>{problemSection.intro}</p>
          </div>
          <div className="so-pain-grid">
            {pains.map((pain, index) => (
              <article className="so-pain" key={pain.title}>
                <div className="so-pain-num">0{index + 1}</div>
                <AlertTriangle size={18} className="so-pain-icon" aria-hidden="true" />
                <h3>{pain.title}</h3>
                <p>{pain.body}</p>
                {pain.notes && (
                  <div className="so-pain-notes">
                    {pain.notes.map((note) => (
                      <div className="so-pain-note" key={note.left}>
                        <b>{note.left}</b>
                        <XCircle size={14} className="so-neq" aria-label="không phải là" />
                        <span>{note.right}</span>
                      </div>
                    ))}
                  </div>
                )}
                {pain.title === 'Một quyết định cần tổng hợp nhiều tín hiệu.' && (
                  <ul className="so-signal-list">
                    {['Số ngày quá hạn (DPD)', 'Dư nợ', 'Dòng tiền', 'Cam kết thanh toán', 'Lịch sử liên hệ', 'Khả năng liên hệ', 'Hành động tiếp theo', 'Tuyến CALL / CBS'].map(
                      (signal) => (
                        <li key={signal}>{signal}</li>
                      ),
                    )}
                  </ul>
                )}
              </article>
            ))}
            </div>
        </section>

        <section className="so-section" id="benefits">
          <div className="so-section-head">
            <span className="so-eyebrow">GIÁ TRỊ</span>
            <h2>{benefitSection.title}</h2>
            <p>{benefitSection.intro}</p>
          </div>
          <div className="so-benefit-grid">
            {benefitCards.map((card) => (
              <article
                className={`so-benefit-card so-benefit-${card.group}`}
                key={card.id}
                id={card.group === 'management' ? 'audience-management' : card.group === 'operations' ? 'audience-operations' : undefined}
              >
                <div className="so-benefit-icon">{benefitIcon(card.id)}</div>
                <span className="so-kicker">{card.kicker}</span>
                <h3>{card.title}</h3>
                <ul>
                  {card.points.map((point) => (
                    <li key={point}>
                      <CheckCircle2 size={14} aria-hidden="true" />
                      {point}
                    </li>
                  ))}
                </ul>
              </article>
            ))}
          </div>
        </section>

        <section className="so-section" id="whww">
          <div className="so-section-head">
            <span className="so-eyebrow">LUỒNG QUYẾT ĐỊNH</span>
            <h2>{whoWhyWhatWhen.title}</h2>
            <p>Mỗi câu hỏi vận hành được nối tới đúng lớp xử lý trong hệ thống.</p>
          </div>
          <div className="so-whww">
            {steps.map((step, index) => (
              <div className="so-whww-step" key={step.step}>
                <div className="so-whww-body">
                  <span className="so-whww-tag">{step.step}</span>
                  <h3>{step.label}</h3>
                  <p>{step.question}</p>
                  <div className="so-whww-system">
                    <span>Hệ thống</span>
                    <b>{step.system}</b>
                  </div>
                </div>
                {index < steps.length - 1 && (
                  <div className="so-whww-arrow" aria-hidden="true">
                    <ArrowDown size={20} />
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>

        <section className="so-section" id="hero-example">
          <div className="so-section-head">
            <span className="so-eyebrow">VÍ DỤ TÁC NGHIỆP</span>
            <h2>{heroExample.title}</h2>
            <p>{heroExample.disclaimer}</p>
          </div>
          <div className="so-example-grid">
            <div className="so-example-data">
              <div className="so-example-cif">
                <span>Khách hàng</span>
                <b className="so-mono">{heroExample.cif}</b>
              </div>
              <dl className="so-example-rows">
                {heroExample.rows.map((row) => (
                  <div className="so-example-row" key={row.label}>
                    <dt>{row.label}</dt>
                    <dd>{row.value}</dd>
                  </div>
                ))}
              </dl>
            </div>
            <div className="so-example-decision">
              <div className="so-decision-label">
                <span className="so-pulse" aria-hidden="true" />
                ĐỀ XUẤT HIỆN TẠI
              </div>
              <h3>{heroExample.recommendation}</h3>
              <p className="so-secondary">{heroExample.secondary}</p>
              <p className="so-explain">{heroExample.explanation}</p>
              <div className="so-route-tag">Tuyến xử lý: <b>{heroExample.rows[4].value}</b></div>
            </div>
          </div>
        </section>

        <section className="so-section" id="what-if">
          <div className="so-section-head">
            <span className="so-eyebrow">TÌNH HUỐNG THỬ</span>
            <h2>{whatIf.title}</h2>
            <p>{whatIf.disclaimer}</p>
          </div>
          <div className="so-whatif">
            <div className="so-whatif-rows">
              {whatIf.rows.map((rowMove) => (
                <div className="so-whatif-row" key={rowMove.label}>
                  <span>{rowMove.label}</span>
                  <div className="so-whatif-move">
                    <b>{rowMove.before}</b>
                    <ArrowRight size={16} />
                    <b className="so-after">{rowMove.after}</b>
                  </div>
                </div>
              ))}
              <div className="so-whatif-row so-whatif-decision-row">
                <span>Hành động đề xuất</span>
                <div className="so-whatif-move">
                  <b>{whatIf.before}</b>
                  <ArrowRight size={16} />
                  <b className="so-after">{whatIf.after}</b>
                </div>
              </div>
            </div>
            <p className="so-whatif-note">{whatIf.note}</p>
          </div>
        </section>

        <section className="so-section" id="pipeline">
          <div className="so-section-head">
            <span className="so-eyebrow">ĐƯỜNG ỐNG QUYẾT ĐỊNH</span>
            <h2>{pipeline.title}</h2>
          </div>
          <ol className="so-pipeline">
            {pipeline.stages.map((stage, index) => (
              <li className="so-pipeline-step" key={stage.title}>
                <div className="so-pipeline-node">
                  <span className="so-pipeline-num">{index + 1}</span>
                  {pipelineIcon(index)}
                </div>
                <h3>{stage.title}</h3>
                <p className="so-pipeline-detail">{stage.detail}</p>
                {index < pipeline.stages.length - 1 && (
                  <div className="so-pipeline-arrow" aria-hidden="true">
                    <ArrowDown size={16} />
                  </div>
                )}
              </li>
            ))}
          </ol>
          <div className="so-pipeline-statements">
            <div className="so-statement">
              <ShieldCheck size={18} aria-hidden="true" />
              <p>
                <b>{pipeline.coreStatementTitle}</b> {pipeline.coreStatement}
              </p>
            </div>
            <div className="so-statement so-statement-green">
              <Bot size={18} aria-hidden="true" />
              <p>
                <b>{pipeline.agentStatementTitle}</b> {pipeline.agentStatement}
              </p>
            </div>
          </div>
        </section>

        <section className="so-section" id="rules">
          <div className="so-section-head">
            <span className="so-eyebrow">VẬN HÀNH QUY TẮC</span>
            <h2>{ruleLayers.title}</h2>
            <p>{ruleLayers.intro}</p>
          </div>
          <div className="so-rules">
            <RuleLayer
              number={1}
              title="Chính sách bắt buộc (HARD POLICY)"
              icon={<ShieldCheck size={20} />}
              description="Các ràng buộc nghiệp vụ không được AI thay đổi."
            />
            <RuleLayer
              number={2}
              title="Tuyến xử lý (ROUTING)"
              icon={<GitBranch size={20} />}
              description={routingNote}
              content={
                <div className="so-route-cols">
                  <div className="so-route-col">
                    <b>CALL</b>
                    {routeCall.map((rule) => <li key={rule}>{rule}</li>)}
                  </div>
                  <div className="so-route-col">
                    <b>CBS</b>
                    {routeCbs.map((rule) => <li key={rule}>{rule}</li>)}
                  </div>
                </div>
              }
            />
            <RuleLayer
              number={3}
              title="Chặn bắt buộc (HARD SUPPRESSION)"
              icon={<Ban size={20} />}
              description="Các điều kiện cần chặn / tạm hoãn hành động được ưu tiên trước hành động đề xuất tiếp theo."
            />
            <RuleLayer
              number={4}
              title="Cam kết / hành động tiếp theo (PTP / NEXT ACTION)"
              icon={<CalendarDays size={20} />}
              description="Thứ tự ưu tiên các cam kết thanh toán và trạng thái liên hệ."
              content={
                <ol className="so-precedence">
                  {ptpPrecedence.map((item, index) => (
                    <li key={item}>
                      <span>{index + 1}</span>
                      {item}
                    </li>
                  ))}
                </ol>
              }
            />
            <RuleLayer
              number={5}
              title="Cơ hội thu hồi (RECOVERY OPPORTUNITY)"
              icon={<PieChart size={20} />}
              description={scoring.disclaimer}
              content={
                <div className="so-scoring">
                  <div className="so-scoring-bars">
                    {scoring.components.map((component) => (
                      <div className="so-scoring-row" key={component.name}>
                        <span className="so-scoring-name">{component.name}</span>
                        <div className="so-scoring-track">
                          <div
                            className="so-scoring-fill"
                            style={{ width: `${(component.weight / scoring.total) * 100}%` }}
                            aria-label={`${component.name}: ${component.weight} điểm`}
                          />
                        </div>
                        <b>{component.weight}</b>
                      </div>
                    ))}
                  </div>
                  <div className="so-scoring-total">
                    Tổng <strong>{scoring.total}</strong>
                  </div>
                </div>
              }
            />
            <RuleLayer
              number={6}
              title="Hành động đề xuất (NEXT BEST ACTION)"
              icon={<ListChecks size={20} />}
              description="Hành động thân thiện với nghiệp vụ, không hiển thị mã nội bộ."
              content={
                <ul className="so-action-chips">
                  {nbaActions.map((action) => (
                    <li key={action}>{action}</li>
                  ))}
                </ul>
              }
            />
          </div>
        </section>

        <section className="so-section" id="architecture">
          <div className="so-section-head">
            <span className="so-eyebrow">KIẾN TRÚC</span>
            <h2>{architecture.title}</h2>
            <p>{architecture.intro}</p>
            <p>
              <b className="so-arch-core-label">{architecture.coreLabel}</b> {architecture.coreState} ·{' '}
              <b className="so-arch-agent-label">{architecture.agentLabel}</b> {architecture.agentState}
            </p>
          </div>
          <div className="so-arch">
            <div className="so-arch-layer" role="group" aria-label="Frontend">
              <div className="so-arch-layer-title"><Monitor size={16} /> {architecture.frontend.title}</div>
              <ul className="so-arch-items">
                {architecture.frontend.items.map((item) => <li key={item}>{item}</li>)}
              </ul>
            </div>
            <div className="so-arch-arrow" aria-hidden="true"><ArrowDown size={18} /></div>
            <div className="so-arch-layer" role="group" aria-label="Lớp API và bản demo">
              <div className="so-arch-layer-title"><Workflow size={16} /> {architecture.api.title}</div>
              <ul className="so-arch-items">
                {architecture.api.items.map((item) => <li key={item}>{item}</li>)}
              </ul>
            </div>
            <div className="so-arch-arrow" aria-hidden="true"><ArrowDown size={18} /></div>
            <div className="so-arch-paths">
              <div className="so-arch-path so-arch-path-decision" role="group" aria-label={architecture.customerPath.title}>
                <div className="so-arch-path-head"><Cpu size={16} /><span><b>{architecture.decisionPathLabel}</b><small>{architecture.customerPath.title}</small></span></div>
                <p className="so-arch-path-intro">{architecture.customerPath.intro}</p>
                <ul className="so-arch-items">
                  {architecture.customerPath.items.map((item) => <li key={item}>{item}</li>)}
                </ul>
              </div>
              <div className="so-arch-path so-arch-path-knowledge" role="group" aria-label={architecture.knowledgePath.title}>
                <div className="so-arch-path-head"><BookOpen size={16} /><span><b>{architecture.knowledgePathLabel}</b><small>{architecture.knowledgePath.title}</small></span></div>
                <p className="so-arch-path-intro">{architecture.knowledgePath.intro}</p>
                <ul className="so-arch-items">
                  {architecture.knowledgePath.items.map((item) => <li key={item}>{item}</li>)}
                </ul>
              </div>
            </div>
            <p className="so-arch-path-note"><ShieldCheck size={14} /> {architecture.pathNote}</p>
          </div>
        </section>

        <section className="so-section so-greennode-section" id="greennode">
          <div className="so-section-head">
            <span className="so-eyebrow">NỀN TẢNG AI</span>
            <h2>{greenNodeStory.title}</h2>
            <p>{greenNodeStory.intro}</p>
          </div>
          <div className="so-greennode-grid">
            {greenNodeStory.components.map((component) => <article className="so-greennode-card" key={component.title}><Bot size={20}/><h3>{component.title}</h3><p>{component.detail}</p></article>)}
          </div>
        </section>

        <section className="so-section" id="modules">
          <div className="so-section-head">
            <span className="so-eyebrow">CẤU TRÚC CODE</span>
            <h2>{modules.title}</h2>
            <p>{modules.intro}</p>
          </div>
          <div className="so-module-grid">
            {moduleCards.map((card) => (
              <article className="so-module" key={card.name}>
                <div className="so-module-icon"><Box size={17} /></div>
                <h3 className="so-mono">{card.name}</h3>
                <p>{card.role}</p>
                {card.checks && (
                  <ul className="so-module-checks">
                    {card.checks.map((check) => (
                      <li key={check}>{check}</li>
                    ))}
                  </ul>
                )}
              </article>
            ))}
          </div>
        </section>

        <section className="so-section" id="ai-role">
          <div className="so-section-head">
            <span className="so-eyebrow">VAI TRÒ AI</span>
            <h2>{aiRole.title}</h2>
          </div>
          <div className="so-ai-cols">
            <div className="so-ai-col so-ai-can">
              <div className="so-ai-col-title"><CheckCircle2 size={18} /> AI làm gì</div>
              <ul>
                {aiRole.can.map((item) => <li key={item}><CheckCircle2 size={14} />{item}</li>)}
              </ul>
            </div>
            <div className="so-ai-col so-ai-cannot">
              <div className="so-ai-col-title"><XCircle size={18} /> AI không làm gì</div>
              <ul>
                {aiRole.cannot.map((item) => <li key={item}><XCircle size={14} />{item}</li>)}
              </ul>
            </div>
          </div>
          <p className="so-ai-note">
            <ShieldCheck size={15} />
            {aiRole.safetyNote}
          </p>
        </section>

        <section className="so-section so-knowledge-section" id="knowledge-assistant">
          <div className="so-section-head">
            <span className="so-eyebrow">TRỢ LÝ · QUYẾT ĐỊNH VÀ KIẾN THỨC</span>
            <h2>{knowledgeAssistant.title}</h2>
            <p>{knowledgeAssistant.intro}</p>
          </div>
          <div className="so-knowledge-cols">
            <article className="so-knowledge-card so-knowledge-decision">
              <div className="so-knowledge-card-head"><Cpu size={18} /> {knowledgeAssistant.decision.title}</div>
              <p>{knowledgeAssistant.decision.body}</p>
              <ul className="so-knowledge-examples">{knowledgeAssistant.decision.examples.map((e) => <li key={e}><MessagesSquare size={13} />{e}</li>)}</ul>
            </article>
            <article className="so-knowledge-card so-knowledge-rag">
              <div className="so-knowledge-card-head"><BookOpen size={18} /> {knowledgeAssistant.knowledge.title}</div>
              <p>{knowledgeAssistant.knowledge.body}</p>
              <ul className="so-knowledge-examples">{knowledgeAssistant.knowledge.examples.map((e) => <li key={e}><MessagesSquare size={13} />{e}</li>)}</ul>
            </article>
          </div>
          <p className="so-knowledge-trust"><ShieldCheck size={15} /> {knowledgeAssistant.trustMessage}</p>
          <p className="so-knowledge-source-note">{knowledgeAssistant.sources}</p>
        </section>

        <section className="so-section" id="trust">
          <div className="so-section-head">
            <span className="so-eyebrow">KIỂM CHỨNG</span>
            <h2>{trust.title}</h2>
          </div>
          <div className="so-trust-grid">
            {trust.badges.map((badge) => (
              <div className="so-trust-badge" key={badge}>
                <BadgeCheck size={18} />
                <span>{badge}</span>
              </div>
            ))}
          </div>
          <ul className="so-trust-points">
            {trust.points.map((point) => (
              <li key={point}>
                <BadgeCheck size={14} />
                {point}
              </li>
            ))}
          </ul>
          <p className="so-trust-status">
            <Activity size={15} />
            {trust.status}
          </p>
        </section>

        <section className="so-section" id="day">
          <div className="so-section-head">
            <span className="so-eyebrow">TÁC NGHIỆP</span>
            <h2>{dayTimeline.title}</h2>
          </div>
          <ol className="so-day">
            {dayTimeline.entries.map((entry) => (
              <li className="so-day-item" key={entry.time}>
                <time>{entry.time}</time>
                <div className="so-day-body">
                  <h3>{entry.action}</h3>
                  <p>{entry.note}</p>
                </div>
              </li>
            ))}
          </ol>
        </section>

        <section className="so-section" id="questions">
          <div className="so-section-head">
            <span className="so-eyebrow">HỎI TRỢ LÝ</span>
            <h2>{sampleQuestions.title}</h2>
            <p>{sampleQuestions.note}</p>
          </div>
          <ul className="so-question-grid">
            {sampleQuestions.questions.map((question) => (
              <li className="so-question-chip" key={question}>
                <MessagesSquare size={15} />
                <span>{question}</span>
              </li>
            ))}
          </ul>
        </section>

        <section className="so-section" id="faq">
          <div className="so-section-head">
            <span className="so-eyebrow">HỎI ĐÁP</span>
            <h2>Câu hỏi thường gặp</h2>
          </div>
          <div className="so-faq">
            {faqs.map((faq, index) => {
              const panelId = `faq-panel-${index}`;
              const open = openFaq === index;
              return (
                <div className={`so-faq-item${open ? ' so-faq-open' : ''}`} key={faq.question}>
                  <h3>
                    <button
                      className="so-faq-toggle"
                      aria-expanded={open}
                      aria-controls={panelId}
                      onClick={() => setOpenFaq(open ? null : index)}
                    >
                      <span>{faq.question}</span>
                      <ChevronDown size={18} />
                    </button>
                  </h3>
                  <div id={panelId} className="so-faq-panel" role="region" hidden={!open}>
                    <p>{faq.answer}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        <section className="so-section" id="roadmap">
          <div className="so-section-head">
            <span className="so-eyebrow">LỘ TRÌNH</span>
            <h2>{roadmap.title}</h2>
          </div>
          <div className="so-roadmap">
            <div className="so-roadmap-col so-roadmap-current">
              <h3>{roadmap.current.label}</h3>
              <ul>
                {roadmap.current.items.map((item) => <li key={item}><CheckCircle2 size={15} />{item}</li>)}
              </ul>
            </div>
            <div className="so-roadmap-col so-roadmap-future">
              <h3>{roadmap.future.label}</h3>
              <ul>
                {roadmap.future.items.map((item) => <li key={item}><Rocket size={15} />{item}</li>)}
              </ul>
            </div>
          </div>
          <p className="so-roadmap-note">{roadmap.disclaimer}</p>
        </section>
      </main>

      <section className="so-final-cta">
        <div className="so-final-inner">
          <h2>{finalCta.title}</h2>
          <div className="so-final-buttons">
            <button type="button" className="so-btn so-btn-primary" onClick={() => overview()}>
              {ctaOverviewLabel}
              <ArrowRight size={16} />
            </button>
            <button type="button" className="so-btn so-btn-outline" onClick={() => openCustomer(heroExample.cif)}>
              {ctaCustomerLabel}
            </button>
          </div>
        </div>
      </section>

      <footer className="so-footer">
        <div className="so-footer-brand">
          <b>{team.title}</b>
          <span>{team.subtitle}</span>
        </div>
        <ul className="so-team">
          {team.members.map((member) => (
            <li className="so-team-member" key={member.name}>
              <b>{member.name}</b>
              <span>
                {member.org}
                {member.role ? ` — ${member.role}` : ''}
              </span>
            </li>
          ))}
        </ul>
        <div className="so-footer-product">
          <b>{brand.product}</b>
          <span>{brand.poweredBy}</span>
        </div>
      </footer>
    </div>
  );
}

function benefitIcon(cardId: string) {
  switch (cardId) {
    case 'benefit-call':
      return <PhoneCall size={22} />;
    case 'benefit-cbs':
      return <Wallet size={22} />;
    case 'benefit-management':
      return <ClipboardList size={22} />;
    default:
      return <Server size={22} />;
  }
}

function pipelineIcon(index: number) {
  const icons = [Search, Scale, GitBranch, PieChart, ListChecks, CalendarDays, Bot] as const;
  const Icon = icons[index] ?? Activity;
  return <Icon size={18} />;
}

function RuleLayer({
  number,
  title,
  icon,
  description,
  content,
}: {
  number: number;
  title: string;
  icon: React.ReactNode;
  description: string;
  content?: React.ReactNode;
}) {
  return (
    <article className="so-rule">
      <div className="so-rule-head">
        <span className="so-rule-num">{number}</span>
        <div className="so-rule-icon">{icon}</div>
        <h3>{title}</h3>
      </div>
      <p className="so-rule-desc">{description}</p>
      {content && <div className="so-rule-content">{content}</div>}
    </article>
  );
}

export default SystemOverviewPage;
