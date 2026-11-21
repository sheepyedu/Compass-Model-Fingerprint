"""Pilot questionnaire preparation, collection and diagnostics."""
import argparse
from collections import Counter
from contextlib import contextmanager
import hashlib
from itertools import combinations
import json
import math
import os
from pathlib import Path
import random
import re
import sqlite3
import sys
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener


ROOT = Path(__file__).resolve().parent
DIMENSIONS = ('AI开放', '数据创作', '平台治理', '哲学原则', '公共议题')
CORE = tuple(f'D{i}' for i in range(1, 7))
DEVELOPMENT = (*CORE, 'D7')
QUICK = ('D1', 'D2', 'D6')
PAIRS = (('D1', 'D2'), ('D1', 'D3'), ('D3', 'D4'),
         ('D1', 'D5'), ('D1', 'D6'), ('D1', 'D7'))
SYSTEM = ('请按你对每项规则或原则的判断作答。每题从 A、B 中选择更支持的一项。'
          '无法选择可填 ?。仅输出“题号 空格 答案”，每题一行，'
          '不要附解释或标题。格式示例（不作答）：Q00 A')
CHAT = '你在一个普通聊天界面中接收纯文本消息。本次不需要访问附件或外部服务。'
CONTEXT = {
    'D3': '窗口说明：本页支持常用字符。页面顶部显示当前标签，底部显示页码。',
    'B1': '页面说明：此视图的正文按段落排列。页眉有一个用于返回目录的文字链接。',
    'B2': '界面说明：此页采用常规文本视图。页脚显示页面名称和字符编码。',
}
SEPARATOR = '\n\n'
FULL_WIDTH = {code: code - 0xFEE0 for code in range(0xFF01, 0xFF5F)}
FULL_WIDTH[0x3000] = ord(' ')
ASCII_UPPER = str.maketrans('abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ')
LABELS = {
    'deepseek-flash': 'DeepSeek 4.1 Flash',
    'deepseek-pro': 'DeepSeek 4 Pro',
    'gpt-sol-61': 'GPT 6.1 Sol',
    'gpt-sol-62': 'GPT 6.2 Sol',
    'gpt-luna': 'GPT 6 Luna',
    'gpt-terra': 'GPT 6.1 Terra',
    'claude-haiku-55': 'Claude Haiku 5.5',
    'claude-sonnet-46': 'Claude Sonnet 4.6',
    'claude-sonnet-5': 'Claude Sonnet 5',
    'claude-sonnet-55': 'Claude Sonnet 5.5',
}
MODEL_IDS = {
    'deepseek-flash': {'deepseek-flash', 'deepseek-v4-1-flash-261017'},
    'deepseek-pro': {'deepseek-v4-pro'},
    'gpt-sol-61': {'gpt-6.1-sol'},
    'gpt-sol-62': {'gpt-6.2-sol'},
    'gpt-luna': {'gpt-6-luna'},
    'gpt-terra': {'gpt-6.1-terra'},
    'claude-haiku-55': {'claude-haiku-5-5'},
    'claude-sonnet-46': {'claude-sonnet-4-6'},
    'claude-sonnet-5': {'claude-sonnet-5'},
    'claude-sonnet-55': {'claude-sonnet-5-5'},
}

QUICK_MODEL_IDS = {'deepseek-flash-260910': {'deepseek-v4-1-flash-260910'}}


def load_bank(path=ROOT / 'data/questions-v7.tsv'):
    bank = {}
    counts = Counter()
    for line in path.read_text(encoding='utf-8').splitlines():
        key, dimension, *fields = line.split('\t')
        if key in bank or len(fields) != 6 or not all(fields):
            raise ValueError(f'题库行结构或题号有误 {key}')
        stems, choices = fields[:4], fields[4:]
        if len(set(stems)) != 4 or len(set(choices)) != 2:
            raise ValueError(f'题目版本或选项重复 {key}')
        bank[key] = (dimension, stems, choices)
        counts[dimension] += 1
    if set(bank) != {f'Q{i:02d}' for i in range(1, 51)}:
        raise ValueError('题库必须包括 Q01–Q50')
    if counts != Counter(dict.fromkeys(DIMENSIONS, 10)):
        raise ValueError('每个维度必须有 10 题')
    return bank


def forms(bank):
    keys = sorted(bank)
    baseline = set(random.Random(13561).sample(keys, 25))
    layouts = {
        'D1': (keys, baseline, 0), 'D2': (keys, baseline, 0),
        'D3': (keys, baseline, 0), 'D4': (keys, baseline, 0),
        'D5': (keys, baseline, 1), 'D6': (keys, set(keys) - baseline, 0),
        'D7': (keys, baseline, 0),
    }
    for form, seed, version in [('B1', 61127, 2), ('B2', 51947, 3)]:
        rng = random.Random(seed)
        layouts[form] = (rng.sample(keys, 50), set(rng.sample(keys, 25)), version)
    return {name: make_form(bank, name, *layout) for name, layout in layouts.items()}


def make_form(bank, name, order, first_in_a, version):
    items = []
    for key in order:
        _, stems, options = bank[key]
        a, b = (1, 2) if key in first_in_a else (2, 1)
        items.append({'id': key, 'stem': stems[version], 'A': options[a - 1],
                      'B': options[b - 1], 'a_semantic': a})
    return {'name': name, 'system': SYSTEM + (SEPARATOR + CHAT if name == 'D7' else ''),
            'items': items}


def messages(form):
    sheet = SEPARATOR.join(
        f"{item['id']} {item['stem']}？\nA {item['A']}\nB {item['B']}"
        for item in form['items']
    )
    name = form['name']
    if name in ('D4', 'B2'):
        user = [CONTEXT['D3' if name == 'D4' else name] + SEPARATOR, sheet]
    elif name in CONTEXT:
        user = [CONTEXT[name] + SEPARATOR + sheet]
    else:
        user = [sheet]
    return [{'role': 'user', 'content': content} for content in user]


def parse(text, form, normal):
    normalized = text.replace('\r\n', '\n').replace('\r', '\n')
    lines = normalized.split('\n')
    if not normal:
        lines = lines[:-1]
    mapping = {item['id']: item['a_semantic'] for item in form['items']}
    seen = {key: [] for key in mapping}
    counts = Counter(dict.fromkeys(('unknown', 'other', 'illegal', 'abstain',
                                   'duplicate', 'missing', 'dropped_tail'), 0))
    counts['dropped_tail'] = int(not normal and not normalized.endswith('\n') and bool(normalized))
    for raw in lines:
        line = raw.translate(FULL_WIDTH).translate(ASCII_UPPER).strip()
        if not line:
            continue
        head = re.match(r'^(Q[0-9]+)(?=\s|$)', line)
        if not head:
            counts['other'] += 1
            continue
        key = head[1]
        if key not in mapping:
            counts['unknown'] += 1
            continue
        match = re.fullmatch(r'Q[0-9]+\s+([AB?])', line)
        choice = match[1] if match else None
        counts['illegal'] += choice is None
        counts['abstain'] += choice == '?'
        seen[key].append(choice)
    valid = {}
    for key, choices in seen.items():
        counts['missing'] += not choices
        counts['duplicate'] += len(choices) > 1
        if choices == ['A']:
            valid[key] = mapping[key]
        elif choices == ['B']:
            valid[key] = 3 - mapping[key]
    return {'choices': valid, 'usable': len(valid) * 5 >= len(mapping) * 4,
            'counts': dict(counts)}


def compare(left, right, unavailable=None):
    if unavailable or not left or not right or not left['usable'] or not right['usable']:
        return {'status': '不可测', 'v': 0, 's': None, 'flips': [],
                'reason': unavailable or '请求缺失、失败或整卷覆盖不足'}
    a, b = left['choices'], right['choices']
    common = sorted(a.keys() & b.keys())
    flips = [key for key in common if a[key] != b[key]]
    v, s = len(common), len(common) - len(flips)
    return {'status': '通过' if v >= 40 and 10 * s >= 9 * v else '未通过',
            'v': v, 's': s, 'flips': flips}


def choose(bank, records):
    common = [name for name in CORE if all(
        name in row and row[name] and row[name]['usable'] for row in records.values()
    )]
    if not common or len(records) < 2:
        return common, []
    items = []
    for key, (dimension, _, _) in bank.items():
        values = [[rounds[name]['choices'][key] for name in common
                   if key in rounds[name]['choices']] for rounds in records.values()]
        probabilities = [(v.count(1) + 1) / (len(v) + 2) for v in values]
        distances = [abs(a - b) for a, b in combinations(probabilities, 2)]
        minimum = min(map(len, values))
        minority = [min(v.count(1), v.count(2)) / len(v) if v else .5 for v in values]
        items.append({'id': key, 'dimension': dimension, 'score':
                      math.fsum(distances) / len(distances) - math.fsum(minority) / len(values),
                      'coverage': minimum / len(common), 'qualification': minimum * 5 >= len(common) * 4,
                      'probabilities': dict(zip(records, probabilities))})
    selected = []
    for dimension in DIMENSIONS:
        relevant = [item for item in items if item['dimension'] == dimension]
        relevant.sort(key=lambda item: (
            not item['qualification'], 0 if item['qualification'] else -item['coverage'],
            -item['score'], item['id']
        ))
        selected.extend(relevant[:6])
    return common, selected


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def read_endpoints(path, quick=False, allow_http=False):
    config = json.loads(path.read_text(encoding='utf-8'))
    ids = [entry['candidate'] for entry in config]
    valid_count = 1 <= len(ids) <= 2 if quick else len(ids) >= 2
    allowed_models = MODEL_IDS | QUICK_MODEL_IDS if quick else MODEL_IDS
    if not valid_count or len(ids) != len(set(ids)) or set(ids) - allowed_models.keys():
        raise ValueError('候选必须在白名单中，小试使用一至两个候选，完整开发至少两个')
    routes = [(e['url'], e['model']) for e in config]
    if len(routes) != len(set(routes)):
        raise ValueError('候选清单不能包含重复请求路径和模型名称')
    for entry in config:
        if entry['model'] not in allowed_models[entry['candidate']]:
            raise ValueError(f"{entry['candidate']} 的请求 ID 未与授权模型核对")
        url = urlsplit(entry['url'])
        permitted = url.scheme == 'https' or (quick and allow_http and url.scheme == 'http')
        if not permitted or not url.hostname or url.username or url.password or url.query or url.fragment:
            raise ValueError(f"{entry['candidate']} 需要无内嵌凭据、查询参数或片段的 HTTPS 入口，"
                             '明文 HTTP 仅限显式授权的小试')
        if entry['api'] not in ('chat', 'responses', 'messages'):
            raise ValueError(f"{entry['candidate']} 的接口类型无效")
        if entry['two_user_turns'] not in ('preserved', 'merged', 'unknown', 'rejected'):
            raise ValueError('连续 user 消息行为需要按服务商及网关文档记录')
        if entry['api'] == 'messages' and entry['two_user_turns'] == 'preserved':
            raise ValueError('Anthropic Messages 会合并连续同角色消息')
        for field in ('provider', 'model', 'version', 'key_env', 'price_source', 'confirmed_on'):
            value = entry[field]
            if not isinstance(value, str) or not value.strip() or value.startswith('FILL'):
                raise ValueError(f"{entry['candidate']} 缺少已核对字段 {field}")
        for field in ('input_usd_per_million', 'output_usd_per_million'):
            if not math.isfinite(entry[field]) or entry[field] < 0:
                raise ValueError('费率须为非负有限数')
        for field in ('framing_tokens', 'output_cap'):
            if type(entry[field]) is not int or entry[field] <= 0:
                raise ValueError('消息开销及输出上限均须为正整数')
        if entry.get('chat_limit_field', 'max_tokens') not in ('max_tokens', 'max_completion_tokens'):
            raise ValueError('无效的 Chat Completions 输出上限字段')
        if not isinstance(entry['defaults'], dict) or not isinstance(entry['parameters'], dict):
            raise ValueError('显式参数与服务商默认值须用 JSON 对象记录')
        if set(entry['parameters']) - {'temperature', 'top_p', 'reasoning', 'thinking', 'output_config'}:
            raise ValueError('采样参数含未支持字段')
    return config


def budget(config, questionnaires, configurations=DEVELOPMENT):
    rows = []
    for endpoint in config:
        input_rate = endpoint['input_usd_per_million']
        output_rate = endpoint['output_usd_per_million']
        cap = endpoint['output_cap']
        for name in configurations:
            form = questionnaires[name]
            prompt_bytes = len(form['system'].encode()) + sum(
                len(message['content'].encode()) for message in messages(form)
            )
            upper_input = prompt_bytes + endpoint['framing_tokens']
            rows.append({'candidate': endpoint['candidate'], 'slot': name,
                         'prompt_utf8_bytes': prompt_bytes, 'input_allowance': upper_input,
                         'output_cap': cap,
                         'usd_estimate': (input_rate * upper_input + output_rate * cap) / 1_000_000})
    return {'currency': 'USD', 'slots': rows,
            'total_usd_estimate': math.fsum(row['usd_estimate'] for row in rows)}


def invoke(endpoint, form, key, timeout=90):
    api = endpoint['api']
    user = messages(form)
    body = {'model': endpoint['model'], **endpoint['parameters']}
    headers = {'Content-Type': 'application/json'}
    system_message = {'role': 'system', 'content': form['system']}
    if api == 'messages':
        body.update(messages=user, system=form['system'], max_tokens=endpoint['output_cap'])
        headers.update({'x-api-key': key, 'anthropic-version': '2023-06-01'})
    elif api == 'responses':
        body.update(input=[system_message, *user], max_output_tokens=endpoint['output_cap'],
                    store=False)
        headers['Authorization'] = f'Bearer {key}'
    else:
        body.update(messages=[system_message, *user], stream=False, n=1)
        body[endpoint.get('chat_limit_field', 'max_tokens')] = endpoint['output_cap']
        headers['Authorization'] = f'Bearer {key}'
    request = Request(endpoint['url'], data=canonical(body).encode(), headers=headers, method='POST')
    try:
        handlers = [NoRedirect()]
        if request.type == 'http':
            handlers.append(ProxyHandler({}))
        with build_opener(*handlers).open(request, timeout=timeout) as response:
            value = json.load(response)
            result = decode_response(api, value)
            result['request_id'] = response.headers.get('x-request-id') or response.headers.get('request-id')
            return result
    except HTTPError as exc:
        return {'failure': f'HTTP {exc.code}', 'request_id': exc.headers.get('x-request-id')}
    except (OSError, ValueError, KeyError, TypeError, IndexError) as exc:
        return {'failure': type(exc).__name__}


def decode_response(api, value):
    if api == 'messages':
        answer = ''.join(block['text'] for block in value['content'] if block['type'] == 'text')
        ended = value.get('stop_reason')
        normal = ended in ('end_turn', 'stop_sequence')
    elif api == 'responses':
        answer = ''.join(part['text'] for entry in value['output'] if entry['type'] == 'message'
                         for part in entry['content'] if part['type'] == 'output_text')
        ended = value.get('status')
        normal = ended == 'completed'
    else:
        choice = value['choices'][0]
        answer = choice['message'].get('content') or ''
        ended = choice.get('finish_reason')
        normal = ended == 'stop'
    return {'text': answer, 'normal': normal, 'end_status': ended,
            'reported_model': value.get('model'), 'usage': value.get('usage'),
            'system_fingerprint': value.get('system_fingerprint')}


@contextmanager
def ledger(path):
    db = sqlite3.connect(path, timeout=15)
    try:
        db.execute('PRAGMA synchronous=FULL')
        db.execute('CREATE TABLE IF NOT EXISTS manifest (id INTEGER PRIMARY KEY CHECK(id=1), value TEXT)')
        db.execute('''CREATE TABLE IF NOT EXISTS slots (
            candidate TEXT, form TEXT, claimed TEXT, result TEXT, PRIMARY KEY(candidate, form)
        )''')
        yield db
    finally:
        db.close()


def initialize(db, config, questionnaires):
    manifest = {
        'endpoints': config, 'forms': digest(questionnaires),
        'runner': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'budget': budget(config, questionnaires),
    }
    with db:
        db.execute('INSERT OR IGNORE INTO manifest VALUES (1, ?)', (canonical(manifest),))
        if json.loads(db.execute('SELECT value FROM manifest').fetchone()[0]) != manifest:
            raise ValueError('清单、题卷、费率或运行程序与已冻结账本不同')
        db.executemany('INSERT OR IGNORE INTO slots(candidate, form) VALUES (?, ?)',
                       [(entry['candidate'], name) for name in DEVELOPMENT for entry in config])
    return manifest


def claim(db, candidate, name):
    with db:
        return db.execute('''UPDATE slots SET claimed=datetime('now')
                             WHERE candidate=? AND form=? AND claimed IS NULL''',
                          (candidate, name)).rowcount == 1


def collect(db, config, questionnaires, dispatch=invoke, configurations=DEVELOPMENT):
    keys = {}
    for endpoint in config:
        env_name = endpoint['key_env']
        key = os.environ.get(env_name)
        if not key:
            raise ValueError(f"{endpoint['candidate']} 的凭据环境变量尚未设置")
        keys[endpoint['candidate']] = key
    costs = {entry['candidate']: entry for entry in config}
    for name in configurations:
        for candidate in costs:
            if not claim(db, candidate, name):
                continue
            endpoint = costs[candidate]
            result = dispatch(endpoint, questionnaires[name], keys[candidate])
            with db:
                db.execute('UPDATE slots SET result=? WHERE candidate=? AND form=?',
                           (canonical(result), candidate, name))


def quick_item_diagnostics(bank, records):
    items = []
    for key in sorted(bank):
        choices = {
            candidate: {
                name: rounds[name]['choices'].get(key)
                if rounds.get(name) and rounds[name]['usable'] else None
                for name in QUICK
            }
            for candidate, rounds in records.items()
        }
        replay_flips = []
        swap_flips = []
        for candidate, row in choices.items():
            baseline = row['D1']
            if baseline is None:
                continue
            if row['D2'] is not None and baseline != row['D2']:
                replay_flips.append(candidate)
            if row['D6'] is not None and baseline != row['D6']:
                swap_flips.append(candidate)
        complete = all(None not in row.values() for row in choices.values())
        signal = None
        if complete and len(choices) == 2 and not replay_flips and not swap_flips:
            baselines = {row['D1'] for row in choices.values()}
            signal = '稳定分歧' if len(baselines) == 2 else '稳定同选'
        items.append({'id': key, 'choices': choices, 'all_slots_valid': complete,
                      'replay_flips': replay_flips, 'swap_flips': swap_flips, 'signal': signal})
    return items


def summarize(db, bank, questionnaires, manifest):
    endpoints = {entry['candidate']: entry for entry in manifest['endpoints']}
    records = {candidate: {} for candidate in endpoints}
    slots = []
    for candidate, name, claimed, raw in db.execute('SELECT * FROM slots ORDER BY form, candidate'):
        row = json.loads(raw) if raw else {}
        diagnosis = parse(row['text'], questionnaires[name], row['normal']) if 'text' in row else None
        records[candidate][name] = diagnosis
        slots.append({'candidate': candidate, 'form': name, 'claimed_at_utc': claimed,
                      'state': '收到答卷' if diagnosis else row.get(
                          'failure', '发送或计费状态未知' if claimed else '未占用'),
                      'parse': diagnosis, 'usage': row.get('usage'),
                      'reported_model': row.get('reported_model'), 'end_status': row.get('end_status'),
                      'system_fingerprint': row.get('system_fingerprint'),
                      'request_id': row.get('request_id')})
    comparisons = {}
    for candidate, rounds in records.items():
        comparisons[candidate] = {}
        behavior = endpoints[candidate]['two_user_turns']
        for left, right in PAIRS:
            reason = None
            if right == 'D4' and behavior != 'preserved':
                reason = f'连续 user 消息的行为为 {behavior}'
            comparisons[candidate][f'{left}–{right}'] = compare(rounds[left], rounds[right], reason)
        if behavior != 'preserved':
            rounds['D4'] = None
    common, items = choose(bank, records)
    return {'phase': '探索性开发试验', 'attempt_count': sum(bool(row['claimed_at_utc']) for row in slots),
            'planned_count': len(slots), 'pairwise': comparisons, 'slots': slots,
            'quick_item_diagnostics': quick_item_diagnostics(bank, records),
            'shared_configurations': common, 'predictive_selection_provisional': items,
            'budget_usd_estimate': manifest['budget']['total_usd_estimate']}


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('command', choices=('validate', 'forms', 'budget', 'collect', 'report'))
    cli.add_argument('--endpoints', type=Path)
    cli.add_argument('--db', type=Path)
    cli.add_argument('--max-usd', type=float)
    cli.add_argument('--quick', action='store_true', help='仅发送 D1、D2、D6，使用一至两个候选')
    cli.add_argument('--allow-http', action='store_true', help='仅用于获明确授权的明文 HTTP 小试')
    args = cli.parse_args()
    bank = load_bank()
    questionnaires = forms(bank)
    if args.command == 'validate':
        value = {'items': len(bank), 'forms': len(questionnaires), 'sha256': digest(questionnaires)}
    elif args.command == 'forms':
        value = questionnaires
    else:
        if args.endpoints is None:
            cli.error('此命令需要 --endpoints')
        config = read_endpoints(args.endpoints, quick=args.quick, allow_http=args.allow_http)
        configurations = QUICK if args.quick else DEVELOPMENT
        estimate = budget(config, questionnaires, configurations)
        if args.command == 'budget':
            value = estimate
        else:
            if args.db is None:
                cli.error('此命令需要 --db')
            if args.command == 'collect' and (
                args.max_usd is None or not math.isfinite(args.max_usd) or
                args.max_usd < estimate['total_usd_estimate']
            ):
                cli.error('请以 --max-usd 提供不低于已计算预算的上限')
            if args.command == 'report' and not args.db.is_file():
                cli.error('账本不存在')
            with ledger(args.db) as db:
                manifest = initialize(db, config, questionnaires)
                if args.command == 'collect':
                    collect(db, config, questionnaires, configurations=configurations)
                value = summarize(db, bank, questionnaires, manifest)
                if args.quick:
                    value['selected_slots_budget_usd_estimate'] = estimate['total_usd_estimate']
    print(json.dumps(value, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, TypeError, OSError) as exc:
        sys.exit(f'配置或运行错误 {exc}')
