#!/usr/bin/env python3
import getpass

import fire
from jsonrpcclient import request
from decouple import config

RPC_URL = config('RPC_URL', 'http://127.0.0.1:26651')
DEFAULT_WALLET = config('DEFAULT_WALLET', 'Default')


def get_passphrase():
    phrase = config('PASSPHRASE', None)
    if phrase is None:
        phrase = getpass.getpass('Input passphrase:')
    return phrase


def req(method, *args):
    rsp = request(RPC_URL, method, *args)
    return rsp.data.result


class Address:
    def list(self, name=DEFAULT_WALLET, type='staking'):
        '''list addresses
        :param name: Name of the wallet. [default: Default]
        :params type: [staking|transfer]'''
        return req('wallet_listStakingAddresses' if type == 'staking' else 'wallet_listTransferAddresses', [name, get_passphrase()])

    def create(self, name=DEFAULT_WALLET, type='staking'):
        '''Create address
        :param name: Name of the wallet
        :param type: Type of address. [staking|transfer]'''
        return req(
            'wallet_createStakingAddress'
            if type == 'staking'
            else 'wallet_createTransferAddress',
            [name, get_passphrase()])


class Wallet:
    def balance(self, name=DEFAULT_WALLET):
        '''Get balance of wallet
        :param name: Name of the wallet. [default: Default]'''
        return req('wallet_balance', [name, get_passphrase()])

    def list(self):
        return req('wallet_list')

    def create(self, name=DEFAULT_WALLET, type='Basic'):
        '''create wallet
        :param name: Name of the wallet. [defualt: Default]
        :param type: Type of the wallet. [Basic|HD] [default: Basic]
        '''
        return req('wallet_create', [name, get_passphrase()], type)

    def restore(self, mnemonics, name=DEFAULT_WALLET):
        '''restore wallet
        :param name: Name of the wallet. [defualt: Default]
        :param mnemonics: mnemonics words
        '''
        return req('wallet_restore', [name, get_passphrase()])

    def view_key(self, name=DEFAULT_WALLET):
        return req(
            'wallet_getViewKey'
            [name, get_passphrase()]
        )

    def list_pubkey(self, name=DEFAULT_WALLET):
        return req('wallet_listPublicKeys', [name, get_passphrase()])

    def transactions(self, name=DEFAULT_WALLET):
        return req('wallet_transactions', [name, get_passphrase()])

    def send(self, to_address, amount, name=DEFAULT_WALLET, view_keys=None):
        return req(
            'wallet_sendToAddress',
            [name, get_passphrase()],
            to_address, amount, view_keys or [])


class Staking:
    def deposit_stake(self, to_address, inputs, name=DEFAULT_WALLET):
        return req('staking_depositStake', [name, get_passphrase()], hex(to_address), inputs)

    def state(self, address, name=DEFAULT_WALLET):
        return req('staking_state', [name, get_passphrase()], hex(address))

    def unbond_stake(self, address, amount, name=DEFAULT_WALLET):
        return req('staking_unbondStake', [name, get_passphrase()], hex(address), amount)

    def withdraw_all_unbonded_stake(self, from_address, to_address, name=DEFAULT_WALLET):
        return req(
            'staking_withdrawAllUnbondedStake',
            [name, get_passphrase()],
            hex(from_address), to_address, []
        )

    def unjail(self, address, name=DEFAULT_WALLET):
        return req('staking_unjail', [name, get_passphrase()], hex(address))


class CLI:
    def __init__(self):
        self.wallet = Wallet()
        self.staking = Staking()
        self.address = Address()

    def raw_tx(self, inputs, outputs, view_keys):
        return req('transaction_createRaw', inputs, outputs, view_keys)

    def sync(self, name=DEFAULT_WALLET):
        return req('sync', [name, get_passphrase()])

    def sync_all(self, name=DEFAULT_WALLET):
        return req('sync_all', [name, get_passphrase()])

    def sync_unlock(self, name=DEFAULT_WALLET):
        return req('sync_unlockWallet', [name, get_passphrase()])

    def sync_stop(self, name=DEFAULT_WALLET):
        return req('sync_stop', [name, get_passphrase()])


if __name__ == '__main__':
    fire.Fire(CLI())
