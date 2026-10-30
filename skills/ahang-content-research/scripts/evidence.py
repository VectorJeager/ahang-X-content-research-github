#!/usr/bin/env python3
"""Read and validate the packaged evidence index; no network or write actions."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date, datetime, timedelta, timezone
import ipaddress
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlparse

DEFAULT_DATASET=Path(__file__).resolve().parents[1]/'references'/'evidence.json'
STATUSES={'visible_text','detail_text','preview_only','article_card_only','author_website_edited'}
SOURCE_KINDS={'x_post','author_website'}

def load_dataset(path: Path) -> dict:
    with path.open(encoding='utf-8') as stream:
        data=json.load(stream)
    if not isinstance(data,dict):
        raise ValueError('Dataset must be a JSON object')
    return data

def conservative_quote_units(text: str) -> int:
    han=len(re.findall(r'[\u3400-\u9fff]',text))
    other_words=len(re.findall(r'[^\W_\u3400-\u9fff]+',text,flags=re.UNICODE))
    return han+other_words

def url_error(value: object) -> str | None:
    if not isinstance(value,str):return 'must be a URL string'
    parsed=urlparse(value)
    if parsed.scheme!='https' or not parsed.hostname:return 'must be an absolute HTTPS URL'
    if parsed.username or parsed.password:return 'must not contain credentials'
    host=parsed.hostname.lower()
    if host=='localhost' or host.endswith(('.localhost','.local')):return 'must not reference a local host'
    try:
        address=ipaddress.ip_address(host)
    except ValueError:
        return None
    return None if address.is_global else 'must not reference a private network address'

def validate_dataset(data: dict) -> list[str]:
    errors=[]
    if data.get('schema_version')!=1:errors.append('schema_version must be 1')
    if data.get('dataset_kind')!='selected_evidence_index':errors.append('dataset_kind must be selected_evidence_index')
    research_date=data.get('research_date')
    try:date.fromisoformat(research_date)
    except (ValueError,TypeError):errors.append('research_date must use YYYY-MM-DD')
    account=data.get('account',{})
    if not isinstance(account,dict) or account.get('handle')!='Astronaut_1216':
        errors.append('account.handle must be Astronaut_1216')
    coverage=data.get('coverage',{})
    if not isinstance(coverage,dict):
        errors.append('coverage must be an object');coverage={}
    rows=data.get('records')
    if not isinstance(rows,list):return errors+['records must be an array']
    if coverage.get('packaged_record_count')!=len(rows):
        errors.append('coverage.packaged_record_count does not match records')
    if coverage.get('full_raw_observation_ledger_included') is not False:
        errors.append('This selected index does not include the complete raw observation ledger')
    for flag in ['historical_first_post_verified','first_1500_fulltext_verified']:
        if not isinstance(coverage.get(flag),bool):errors.append(f'coverage.{flag} must be boolean')
    target=coverage.get('requested_authored_post_count')
    if not isinstance(target,int) or isinstance(target,bool) or target<1:
        errors.append('requested_authored_post_count must be a positive integer');target=1500
    if coverage.get('first_1500_fulltext_verified'):
        qualified=[r for r in rows if isinstance(r,dict) and r.get('observed_post_type')!='reply' and r.get('full_post_text_included') is True and r.get('read_status') in {'visible_text','detail_text'}]
        if len(qualified)<target or coverage.get('historical_first_post_verified') is not True:
            errors.append('Insufficient eligible fulltext records and earliest-boundary evidence for complete target coverage')
        audit=coverage.get('sequence_audit')
        if not isinstance(audit,dict) or audit.get('continuous') is not True or not audit.get('source'):
            errors.append('Complete coverage requires a documented sequence_audit; record count alone is insufficient')
    ids=set();canonical_urls=set();valid_dates=[]
    required=['evidence_id','date','title','account_handle','source_url','canonical_post_url','source_kind','observed_post_type','read_status','read_status_note','excerpt','summary','analysis']
    for position,row in enumerate(rows,1):
        if not isinstance(row,dict):errors.append(f'record {position} must be an object');continue
        label=row.get('evidence_id',f'record {position}')
        for key in required:
            if not isinstance(row.get(key),str) or not row[key].strip():errors.append(f'{label}: {key} must be a non-empty string')
        ident=row.get('evidence_id')
        if not isinstance(ident,str) or not re.fullmatch(r'E\d{2,}',ident):errors.append(f'{label}: invalid evidence_id')
        elif ident in ids:errors.append(f'{label}: duplicate evidence_id')
        else:ids.add(ident)
        if row.get('account_handle')!='Astronaut_1216':errors.append(f'{label}: different account handle')
        if row.get('read_status') not in STATUSES:errors.append(f'{label}: unsupported read_status')
        if row.get('source_kind') not in SOURCE_KINDS:errors.append(f'{label}: unsupported source_kind')
        if row.get('observed_post_type') not in {'reply','authored_post_or_quote'}:errors.append(f'{label}: unsupported observed_post_type')
        if row.get('timezone')!='Asia/Shanghai':errors.append(f'{label}: timezone must be Asia/Shanghai')
        for key in ['source_url','canonical_post_url']:
            problem=url_error(row.get(key))
            if problem:errors.append(f'{label}: {key} {problem}')
        canonical=row.get('canonical_post_url')
        if isinstance(canonical,str):
            normalized=canonical.rstrip('/').casefold()
            if normalized in canonical_urls:errors.append(f'{label}: duplicate canonical_post_url')
            canonical_urls.add(normalized)
            parsed=urlparse(canonical)
            match=re.fullmatch(r'/Astronaut_1216/status/(\d+)',parsed.path,flags=re.I)
            if parsed.hostname not in {'x.com','www.x.com','twitter.com','www.twitter.com'} or not match:
                errors.append(f'{label}: canonical_post_url must point to this account status')
            else:
                try:
                    milliseconds=(int(match.group(1))>>22)+1288834974657
                    actual=datetime.fromtimestamp(milliseconds/1000,timezone(timedelta(hours=8))).date().isoformat()
                    if actual!=row.get('date'):errors.append(f'{label}: date differs from post ID in Asia/Shanghai')
                except (ValueError,OverflowError,OSError):errors.append(f'{label}: invalid post ID timestamp')
        try:
            date.fromisoformat(row.get('date'));valid_dates.append(row['date'])
            if isinstance(research_date,str) and row['date']>research_date:errors.append(f'{label}: date is later than research_date')
        except (ValueError,TypeError):errors.append(f'{label}: date must use YYYY-MM-DD')
        excerpt=row.get('excerpt')
        if isinstance(excerpt,str) and conservative_quote_units(excerpt)>25:
            errors.append(f'{label}: excerpt exceeds the package short-quotation budget')
        provenance=row.get('excerpt_provenance')
        if not isinstance(provenance,dict):errors.append(f'{label}: missing excerpt_provenance')
        else:
            if url_error(provenance.get('read_source_url')):errors.append(f'{label}: invalid excerpt read_source_url')
            if not isinstance(provenance.get('raw_page_snapshot_included'),bool):errors.append(f'{label}: snapshot flag must be boolean')
            if not isinstance(provenance.get('independently_rechecked_for_package'),bool):errors.append(f'{label}: recheck flag must be boolean')
        if not isinstance(row.get('full_post_text_included'),bool):errors.append(f'{label}: full_post_text_included must be boolean')
        topics=row.get('topics')
        if not isinstance(topics,list) or not topics or not all(isinstance(t,str) and t.strip() for t in topics):errors.append(f'{label}: topics must contain non-empty strings')
        if row.get('source_kind')=='author_website' and row.get('read_status')!='author_website_edited':
            errors.append(f'{label}: author website source must preserve edited-version status')
    if valid_dates and coverage.get('earliest_visible_record')>min(valid_dates):
        errors.append('earliest_visible_record cannot be later than the oldest selected record')
    return errors

def sorted_records(data: dict) -> list[dict]:
    return sorted(data['records'],key=lambda r:(r['date'],r['canonical_post_url'].rsplit('/',1)[-1]))

def summary(data: dict) -> dict:
    rows=data['records'];c=data['coverage']
    return {
        'dataset_kind':data['dataset_kind'],'research_date':data['research_date'],
        'packaged_evidence_entries':len(rows),
        'read_status_counts':dict(sorted(Counter(r['read_status'] for r in rows).items())),
        'source_kind_counts':dict(sorted(Counter(r['source_kind'] for r in rows).items())),
        'reply_entries':sum(r['observed_post_type']=='reply' for r in rows),
        'full_post_text_entries':sum(r['full_post_text_included'] for r in rows),
        'selected_date_range':{'earliest':min((r['date'] for r in rows),default=None),'latest':max((r['date'] for r in rows),default=None)},
        'requested_authored_post_count':c['requested_authored_post_count'],
        'first_1500_fulltext_verified':c['first_1500_fulltext_verified'],
        'historical_first_post_verified':c['historical_first_post_verified'],
        'reported_session_observations':c.get('reported_session_observations'),
        'reported_session_authored_scan':c.get('reported_session_authored_scan'),
        'scope_note':c.get('prior_counts_note')
    }

def emit(value: object) -> None:
    print(json.dumps(value,ensure_ascii=False,indent=2))

def positive_int(value: str) -> int:
    result=int(value)
    if result<1:raise argparse.ArgumentTypeError('must be positive')
    return result

def nonnegative_int(value: str) -> int:
    result=int(value)
    if result<0:raise argparse.ArgumentTypeError('must not be negative')
    return result

def main(argv: list[str] | None=None) -> int:
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset',type=Path,default=DEFAULT_DATASET,help='alternate JSON path; place before subcommand')
    commands=parser.add_subparsers(dest='command',required=True)
    commands.add_parser('stats');commands.add_parser('validate')
    show=commands.add_parser('show');show.add_argument('evidence_ids',nargs='+')
    for name in ['search','list']:
        command=commands.add_parser(name)
        if name=='search':command.add_argument('query',nargs='+')
        command.add_argument('--status',choices=sorted(STATUSES))
        command.add_argument('--kind',choices=sorted(SOURCE_KINDS))
        command.add_argument('--topic')
        command.add_argument('--limit',type=positive_int,default=10 if name=='search' else None)
        command.add_argument('--offset',type=nonnegative_int,default=0)
    args=parser.parse_args(argv)
    try:
        data=load_dataset(args.dataset)
        errors=validate_dataset(data)
    except (OSError,ValueError,TypeError,KeyError) as exc:
        emit({'valid':False,'errors':[str(exc)]});return 2
    if args.command=='validate':
        emit({'valid':not errors,'record_count':len(data.get('records',[])),'errors':errors,'verification_scope':'structure, source URLs, dates, and coverage consistency; not live quotation authenticity'})
        return 2 if errors else 0
    if errors:
        emit({'valid':False,'errors':errors});return 2
    if args.command=='stats':emit(summary(data));return 0
    if args.command=='show':
        by_id={r['evidence_id']:r for r in data['records']}
        wanted=[s.upper() for s in args.evidence_ids]
        unknown=[s for s in wanted if s not in by_id]
        if unknown:emit({'error':'Unknown evidence IDs','ids':unknown});return 2
        emit({'records':[by_id[s] for s in wanted],'scope':summary(data)});return 0
    rows=sorted_records(data)
    if args.status:rows=[r for r in rows if r['read_status']==args.status]
    if args.kind:rows=[r for r in rows if r['source_kind']==args.kind]
    if args.topic:rows=[r for r in rows if args.topic.casefold() in ' '.join(r['topics']).casefold()]
    if args.command=='search':
        terms=' '.join(args.query).casefold().split()
        def matches(row):
            haystack=' '.join([row['title'],row['excerpt'],row['summary'],row['analysis'],*row['topics']]).casefold()
            return all(t in haystack for t in terms)
        rows=[r for r in rows if matches(r)]
    total=len(rows);end=None if args.limit is None else args.offset+args.limit
    page=rows[args.offset:end]
    next_offset=args.offset+len(page)
    emit({'match_count':total,'returned_count':len(page),'next_offset':next_offset if next_offset<total else None,'records':page,'scope_note':'Matches are within the selected local index, not the account full history.'})
    return 0

if __name__=='__main__':
    raise SystemExit(main())
