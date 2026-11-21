from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pilot


BANK = pilot.load_bank()
FORMS = pilot.forms(BANK)


def response(n, start=1):
    return '\n'.join(f'Q{i:02d} A' for i in range(start, start + n)) + '\n'


def endpoint(candidate):
    return {
        'candidate': candidate, 'provider': 'test', 'model': candidate,
        'version': 'test', 'url': 'https://example.test/completions', 'api': 'chat',
        'two_user_turns': 'preserved', 'key_env': 'COMPASS_PILOT_TEST_KEY',
        'output_cap': 1024, 'framing_tokens': 200, 'parameters': {},
        'input_usd_per_million': 1, 'output_usd_per_million': 2,
        'price_source': 'synthetic', 'confirmed_on': '2026-11-21',
    }


class PilotTest(unittest.TestCase):
    def test_claude_allowlist_omits_legacy_haiku(self):
        expected = {
            'claude-haiku-55': 'claude-haiku-5-5',
            'claude-sonnet-46': 'claude-sonnet-4-6',
            'claude-sonnet-5': 'claude-sonnet-5',
            'claude-sonnet-55': 'claude-sonnet-5-5',
        }
        self.assertEqual(set(expected), {key for key in pilot.MODEL_IDS if key.startswith('claude-')})
        config = [dict(endpoint(key), model=model, defaults={})
                  for key, model in expected.items()]
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'endpoints.json'
            path.write_text(json.dumps(config))
            self.assertEqual(config, pilot.read_endpoints(path))
            config[0].update(candidate='claude-haiku-45', model='claude-haiku-4-5-20251001')
            path.write_text(json.dumps(config))
            with self.assertRaisesRegex(ValueError, '白名单'):
                pilot.read_endpoints(path)

    def test_default_questionnaire_covers_technology_and_philosophy(self):
        self.assertEqual(('AI开放', '数据创作', '平台治理', '哲学原则', '公共议题'),
                         pilot.DIMENSIONS)
        form = FORMS['D1']
        self.assertIn('模型权重', form['items'][0]['stem'])
        self.assertIn('训练', next(item for item in form['items'] if item['id'] == 'Q11')['stem'])
        self.assertIn('动机', next(item for item in form['items'] if item['id'] == 'Q31')['stem'])
        self.assertIn('规则', form['system'])

    def test_config_controls(self):
        for form in FORMS.values():
            self.assertEqual(25, sum(item['a_semantic'] == 1 for item in form['items']))
        self.assertEqual(pilot.messages(FORMS['D1']), pilot.messages(FORMS['D2']))
        d4 = pilot.messages(FORMS['D4'])
        self.assertEqual(2, len(d4))
        self.assertEqual(pilot.messages(FORMS['D3'])[0]['content'],
                         ''.join(message['content'] for message in d4))
        self.assertEqual(pilot.messages(FORMS['D1']), pilot.messages(FORMS['D7']))
        self.assertNotEqual(FORMS['D1']['system'], FORMS['D7']['system'])
        self.assertEqual(1, len(pilot.messages(FORMS['B1'])))
        self.assertEqual(2, len(pilot.messages(FORMS['B2'])))

    def test_truncation(self):
        form = FORMS['D1']
        self.assertIn('Q07', pilot.parse('Q07 A', form, True)['choices'])
        self.assertNotIn('Q07', pilot.parse('Q07 A', form, False)['choices'])
        self.assertIn('Q07', pilot.parse('Q07 A\nQ08 B', form, False)['choices'])

    def test_diagnostics(self):
        blocks = ['Q07 A\nQ07 B text', 'Q07 B text\nQ07 A',
                  'Q07 A\nQ07 A', 'Q07 A\nQ07 B']
        for text in blocks:
            with self.subTest(text=text):
                parsed = pilot.parse(text, FORMS['D1'], True)
                self.assertNotIn('Q07', parsed['choices'])
                self.assertEqual(1, parsed['counts']['duplicate'])
        parsed = pilot.parse('ｑ０７　ａ\nQ08 ?\nQ99 B\n备注\nQ09', FORMS['D1'], True)
        self.assertIn('Q07', parsed['choices'])
        for name in ('abstain', 'unknown', 'other', 'illegal'):
            self.assertEqual(1, parsed['counts'][name])
        self.assertEqual(47, parsed['counts']['missing'])
        self.assertFalse(pilot.parse('我无法作答。', FORMS['D1'], True)['usable'])

    def test_coverage(self):
        for size in (30, 50):
            form = {**FORMS['D1'], 'items': FORMS['D1']['items'][:size]}
            cutoff = size * 4 // 5
            for count in (cutoff - 1, cutoff):
                self.assertEqual(count == cutoff, pilot.parse(response(count), form, True)['usable'])

    def test_flip_remapping_and_pair_boundaries(self):
        a = pilot.parse(response(50), FORMS['D1'], True)
        b = pilot.parse(response(50).replace(' A', ' B'), FORMS['D6'], True)
        self.assertEqual(50, pilot.compare(a, b)['s'])
        v39 = pilot.parse(response(40, 2), FORMS['D1'], True)
        v40 = pilot.parse(response(40), FORMS['D1'], True)
        self.assertEqual('未通过', pilot.compare(v39, v40)['status'])
        for flips, expected in [(4, '通过'), (5, '未通过')]:
            right = {'choices': dict(v40['choices']), 'usable': True}
            for index in range(1, flips + 1):
                key = f'Q{index:02d}'
                right['choices'][key] = 3 - right['choices'][key]
            outcome = pilot.compare(v40, right)
            self.assertEqual(expected, outcome['status'])
            self.assertEqual(40 - flips, outcome['s'])
        unusable = pilot.parse(response(39), FORMS['D1'], True)
        self.assertEqual(0, pilot.compare(a, unusable)['v'])
        self.assertIsNone(pilot.compare(a, b, 'merged')['s'])

    def test_selection_uses_common_core_only(self):
        a = pilot.parse(response(50), FORMS['D1'], True)
        b = pilot.parse(response(50).replace(' A', ' B'), FORMS['D1'], True)
        excluded = pilot.parse(response(39), FORMS['D1'], True)
        configs, items = pilot.choose(BANK, {
            'a': {'D1': a, 'D2': excluded, 'D7': b},
            'b': {'D1': b, 'D2': b, 'D7': a},
        })
        self.assertEqual(['D1'], configs)
        self.assertEqual(30, len(items))
        self.assertAlmostEqual(1 / 3, items[0]['score'])
        self.assertEqual(([], []), pilot.choose(BANK, {'a': {'D1': a}, 'b': {}}))

    def test_concurrent_claims_and_interrupted_slot(self):
        config = [endpoint('deepseek-flash'), endpoint('deepseek-pro')]
        config[1]['two_user_turns'] = 'merged'
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'ledger.sqlite3'
            with pilot.ledger(path) as db:
                manifest = pilot.initialize(db, config, FORMS)

            def occupy(_):
                with pilot.ledger(path) as db:
                    return pilot.claim(db, 'deepseek-flash', 'D1')

            with ThreadPoolExecutor(max_workers=8) as pool:
                self.assertEqual(1, sum(pool.map(occupy, range(24))))

            attempts = []
            def fake_send(item, form, _key):
                attempts.append((item['candidate'], form['name']))
                return {'text': response(50), 'normal': True}

            with pilot.ledger(path) as db, patch.dict(os.environ, {'COMPASS_PILOT_TEST_KEY': 'mock'}):
                pilot.collect(db, config, FORMS, fake_send)
                pilot.collect(db, config, FORMS, fake_send)
                report = pilot.summarize(db, BANK, FORMS, manifest)
            self.assertEqual(13, len(attempts))
            self.assertEqual(13, len(set(attempts)))
            self.assertEqual(14, report['attempt_count'])
            self.assertEqual('不可测', report['pairwise']['deepseek-pro']['D3–D4']['status'])
            self.assertTrue(any(row['state'] == '发送或计费状态未知' for row in report['slots']))

    def test_small_pilot_limits_dispatch_and_reports_item_signals(self):
        config = [endpoint('deepseek-flash'), endpoint('deepseek-pro')]
        names = {row['candidate'] for row in config}
        attempts = []

        def fake_send(entry, form, _key):
            candidate, name = entry['candidate'], form['name']
            attempts.append((candidate, name))
            letter = 'A' if (candidate == 'deepseek-flash') != (name == 'D6') else 'B'
            data = response(50).replace(' A', f' {letter}')
            if candidate == 'deepseek-flash' and name == 'D2':
                data = data.replace('Q02 A', 'Q02 B')
            if candidate == 'deepseek-flash' and name == 'D6':
                data = data.replace('Q03 B', 'Q03 A')
            return {'text': data, 'normal': True}

        with tempfile.TemporaryDirectory() as directory:
            with pilot.ledger(Path(directory) / 'quick.sqlite3') as db, patch.dict(
                os.environ, {'COMPASS_PILOT_TEST_KEY': 'mock'}
            ):
                manifest = pilot.initialize(db, config, FORMS)
                for _ in range(2):
                    pilot.collect(db, config, FORMS, fake_send, configurations=pilot.QUICK)
                report = pilot.summarize(db, BANK, FORMS, manifest)
        self.assertEqual([(candidate['candidate'], form) for form in pilot.QUICK
                          for candidate in config], attempts)
        self.assertEqual(6, report['attempt_count'])
        self.assertEqual(14, report['planned_count'])
        self.assertEqual(6, len(pilot.budget(config, FORMS, pilot.QUICK)['slots']))
        items = {item['id']: item for item in report['quick_item_diagnostics']}
        self.assertEqual('稳定分歧', items['Q01']['signal'])
        self.assertEqual(['deepseek-flash'], items['Q02']['replay_flips'])
        self.assertEqual(['deepseek-flash'], items['Q03']['swap_flips'])
        self.assertEqual(names, items['Q01']['choices'].keys())

    def test_single_endpoint_quick_mode_skips_cross_model_selection(self):
        config = [dict(endpoint('deepseek-flash'), model='deepseek-flash', defaults={})]
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'endpoints.json'
            path.write_text(json.dumps(config))
            with self.assertRaises(ValueError):
                pilot.read_endpoints(path)
            self.assertEqual(config, pilot.read_endpoints(path, quick=True))
        usable = pilot.parse(response(50), FORMS['D1'], True)
        common, selected = pilot.choose(BANK, {'deepseek-flash': {'D1': usable}})
        self.assertEqual(['D1'], common)
        self.assertFalse(selected)

    def test_plain_http_requires_explicit_quick_opt_in(self):
        config = [dict(endpoint('deepseek-flash'), model='deepseek-v4-1-flash-261017', defaults={}),
                  dict(endpoint('deepseek-flash-260910'), model='deepseek-v4-1-flash-260910',
                       url='http://example.test/chat/completions', defaults={})]
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'endpoints.json'
            path.write_text(json.dumps(config))
            with self.assertRaisesRegex(ValueError, 'HTTPS'):
                pilot.read_endpoints(path, quick=True)
            self.assertEqual(config, pilot.read_endpoints(path, quick=True, allow_http=True))
            with self.assertRaisesRegex(ValueError, '白名单'):
                pilot.read_endpoints(path, allow_http=True)

    def test_wire_response_shapes(self):
        chat = {'choices': [{'message': {'content': 'Q01 A'}, 'finish_reason': 'length'}]}
        self.assertFalse(pilot.decode_response('chat', chat)['normal'])
        msg = {'content': [{'type': 'text', 'text': 'Q01 A'}], 'stop_reason': 'end_turn'}
        self.assertTrue(pilot.decode_response('messages', msg)['normal'])
        responses = {'output': [{'type': 'message',
                                 'content': [{'type': 'output_text', 'text': 'Q01 A'}]}],
                     'status': 'completed'}
        self.assertEqual('Q01 A', pilot.decode_response('responses', responses)['text'])
