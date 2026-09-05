from __future__ import annotations

import argparse
import json
import sys

from .config import KNOWLEDGE_VERSION, SOURCE_COMMIT, KnowledgeRagConfig
from .corpus import load_corpus
from .evaluation import GOLDEN_QUESTIONS, evaluate, secret_audit
from .latency import latency_report
from .probe import run_probe
from .service import KnowledgeRagService, build_live_rag_service, build_service


def _print_help(parser: argparse.ArgumentParser) -> None:
    parser.print_help()


def cmd_version(service: KnowledgeRagService) -> None:
    print(
        json.dumps(
            {
                "task": "TASK-011H",
                "module": "msb_knowledge_rag",
                "knowledge_version": KNOWLEDGE_VERSION,
                "source_commit": SOURCE_COMMIT,
                "corpus_dir": str(service.config.corpus_dir),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def cmd_status(service: KnowledgeRagService) -> None:
    status = service.gate_status()
    print(json.dumps(status, ensure_ascii=False, indent=2))


def cmd_ingest(service: KnowledgeRagService, dry_run: bool = False) -> None:
    documents = load_corpus(service.config.corpus_dir)
    chunks = service.all_chunks
    if dry_run:
        print(
            json.dumps(
                {
                    "mode": "dry-run",
                    "documents": len(documents),
                    "chunks": len(chunks),
                    "document_ids": [document.document_id for document in documents],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return
    count = service.index_all()
    print(
        json.dumps(
            {
                "mode": "ingest",
                "store": getattr(service.posstore, "name", "unknown"),
                "inference_anchor": "LIVE_GREENNODE_VDB"
                if service.posstore.is_live()
                else "LOCAL_MOCKED_VDB",
                "indexed_chunks": count,
                "documents": len(documents),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def cmd_answer(service: KnowledgeRagService, question: str) -> None:
    answer = service.answer(question)
    print(json.dumps(vars(answer), ensure_ascii=False, indent=2))


def cmd_evaluate(service: KnowledgeRagService, as_json: bool = False) -> None:
    report = evaluate(service)
    anchor = (
        "LIVE_GREENNODE_VDB" if service.posstore.is_live() else "LOCAL_MOCKED_VDB"
    )
    if not as_json:
        summary = report.summary()
        print(f"TASK-011H RAG evaluation (anchor={anchor})")
        for key, value in summary.items():
            print(f"  {key:<28} {value}")
        print("--- per-question ---")
        for row in report.rows:
            flags = []
            if row.group in ("A", "B", "C", "D"):
                flags.append("R@3" if row.recall_3 else "miss")
                flags.append(f"mrr={row.mrr}")
                flags.append("grounded" if row.grounded else "!grounded")
                flags.append("cited" if row.cited else "!cited")
            if row.group in ("BOUNDARY", "SECURITY"):
                flags.append("boundary-ok" if row.boundary_ok else "boundary-FAIL")
            print(
                f"  {row.question_id:<6} {row.group:<9} {row.classification:<28} "
                f"{row.question[:64]} {' '.join(flags)}"
            )
        return
    print(json.dumps(report.summary(), ensure_ascii=False, indent=2))
    print(json.dumps([vars(row) for row in report.rows], ensure_ascii=False, indent=2))


def cmd_latency(service: KnowledgeRagService, limit: int) -> None:
    questions = [
        question.question
        for question in GOLDEN_QUESTIONS
        if question.group in ("A", "B", "C", "D")
    ][:limit]
    report = latency_report(service, questions)
    print(json.dumps(report, ensure_ascii=False, indent=2))


def cmd_secret_audit(service: KnowledgeRagService) -> None:
    report = secret_audit(service)
    for key, value in report.items():
        print(f"  {key:<28} {value}")


def cmd_probe(config: KnowledgeRagConfig) -> None:
    from .probe import run_probe

    result = run_probe(config)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="msb_knowledge_rag",
        description="MSB Collection Copilot — Project Knowledge RAG (TASK-011H)",
    )
    parser.add_argument(
        "--provider",
        choices=("deterministic", "local-multilingual", "local-e5", "greennode-maas"),
        default=None,
        help="embedding provider override (RAG_EMBEDDING_PROVIDER)",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="use the Qwen Flash grounded answerer (build_live_rag_service)",
    )
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("version", help="print version metadata")
    subparsers.add_parser("status", help="print gate status")
    ingest_parser = subparsers.add_parser("ingest", help="index the knowledge corpus")
    ingest_parser.add_argument("--dry-run", action="store_true")
    answer_parser = subparsers.add_parser("answer", help="answer a knowledge question")
    answer_parser.add_argument("question", nargs="+")
    eval_parser = subparsers.add_parser("evaluate", help="evaluate RAG on golden set")
    eval_parser.add_argument("--json", action="store_true")
    latency_parser = subparsers.add_parser("latency", help="per-phase latency report")
    latency_parser.add_argument("--questions", type=int, default=10)
    subparsers.add_parser("secret-audit", help="SECRET_AUDIT / PRIVATE_REASONING / SECRET_QUERY_SAFE")
    subparsers.add_parser("probe", help="read-only live MaaS/vDB probe")
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        _print_help(parser)
        return 2
    config = KnowledgeRagConfig()
    if args.provider:
        config.embedding_provider = args.provider
    if args.live:
        service = build_live_rag_service(config)
    else:
        service = build_service(config)
    if args.command == "version":
        cmd_version(service)
    elif args.command == "status":
        cmd_status(service)
    elif args.command == "ingest":
        cmd_ingest(service, dry_run=bool(args.dry_run))
    elif args.command == "answer":
        cmd_answer(service, " ".join(args.question))
    elif args.command == "evaluate":
        cmd_evaluate(service, as_json=bool(args.json))
    elif args.command == "latency":
        cmd_latency(service, limit=args.questions)
    elif args.command == "secret-audit":
        cmd_secret_audit(service)
    elif args.command == "probe":
        cmd_probe(config)
    else:
        _print_help(parser)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())