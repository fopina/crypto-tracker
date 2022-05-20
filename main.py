#!/usr/bin/env python

import time
import argparse
import requests

from pycoingecko import CoinGeckoAPI

CHART_DOWN = '📉'
CHART_UP = '📈'
SOON = '🔜'


class Combo:
    def __init__(self, combo_string):
        data = combo_string.split(',')
        assert len(data) == 3
        self.coin_id = data[0]
        self.pct_up = float(data[1]) / 100 if data[1] else None
        self.pct_down = float(data[2]) * -1 / 100 if data[2] else None
        self.last_value = None
        self.last_value_at = None

    def update(self, new_value):
        if self.last_value is None:
            self.last_value = new_value
            self.last_value_at = time.time()
            return True, None
        change = (new_value - self.last_value) / self.last_value
        if change > self.pct_up or change < self.pct_down:
            self.last_value = new_value
            self.last_value_at = time.time()
            return True, change
        return False, change

    def __str__(self):
        return self.coin_id


class ComboPack:
    def __init__(self, combos, token=None):
        self._cg = CoinGeckoAPI()
        self._combos = {
            c.coin_id: c
            for c in [
                combo if isinstance(combo, Combo) else Combo(combo)
                for combo in combos
            ]
        }
        self._query = ','.join(c.coin_id for c in self._combos.values())
        self._token = token

    def tick(self):
        prices = self._cg.get_price(ids=self._query, vs_currencies='usd')
        notification = []
        for k, v in prices.items():
            usd = v['usd']
            chg, pct = self._combos[k].update(v['usd'])
            if pct is None:
                pct_text = SOON
            else:
                pct_text = f'{pct * 100:-.2f} %'
            print(f'{k} at ${usd} | {pct_text} | {chg}')
            if chg:
                if pct:
                    if pct > 0:
                        pct_text = f'{pct_text} {CHART_UP}'
                    else:
                        pct_text = f'{pct_text} {CHART_DOWN}'
                notification.append(f'{k} at ${usd} | {pct_text}')
        if notification:
            self.notify('\n'.join(notification))

    def notify(self, message):
        r = requests.post(
        f'https://tgbots.skmobi.com/pushit/{self._token}',
        data={
            'msg': message,
            'format': 'Markdown'
        }
        )
        return r.json()['ok'] == True


def build_parser():
    parser = argparse.ArgumentParser('crypto-tracker')
    parser.add_argument(
        'combo', type=str, nargs='*',
        help='each COMBO should be <COIN ID>,<PERCENTAGE UP>,<PERCENTAGE DOWN>.Set a percentage to 0 or blank to not watch in that direction.'
    )
    parser.add_argument('--list', action='store_true', help='List supported coins')
    parser.add_argument('--token', type=str, help='@PushitBot token for notifications')
    return parser


def main(args):
    cg = CoinGeckoAPI()

    if args.list:
        for x in cg.get_coins_list():
            print(f'{x["id"]} - {x["name"]} ({x["symbol"]})')
        return

    if not args.combo:
        print('Nothing to watch...')
        return 1

    pack = ComboPack(args.combo, token=args.token)
    while True:
        pack.tick()
        time.sleep(15)


if __name__ == '__main__':
    exit(main(build_parser().parse_args()) or 0)
