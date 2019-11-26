#!/usr/bin/env python3
import getpass

import fire
from jsonrpcclient import request
from decouple import config

CLIENT_RPC_URL = config('CLIENT_RPC_URL', 'http://127.0.0.1:26651')
CHAIN_RPC_URL = config('CHAIN_RPC_URL', 'http://127.0.0.1:26657')
DEFAULT_WALLET = config('DEFAULT_WALLET', 'Default')


def get_passphrase():
    phrase = config('PASSPHRASE', None)
    if phrase is None:
        phrase = getpass.getpass('Input passphrase:')
    return phrase


def call(method, *args):
    rsp = request(CLIENT_RPC_URL, method, *args)
    return rsp.data.result


def call_chain(method, *args):
    rsp = request(CHAIN_RPC_URL, method, *args)
    return rsp.data.result


class Address:
    def list(self, name=DEFAULT_WALLET, type='staking'):
        '''list addresses
        :param name: Name of the wallet. [default: Default]
        :params type: [staking|transfer]'''
        return call('wallet_listStakingAddresses' if type == 'staking' else 'wallet_listTransferAddresses', [name, get_passphrase()])

    def create(self, name=DEFAULT_WALLET, type='staking'):
        '''Create address
        :param name: Name of the wallet
        :param type: Type of address. [staking|transfer]'''
        return call(
            'wallet_createStakingAddress'
            if type == 'staking'
            else 'wallet_createTransferAddress',
            [name, get_passphrase()])


class Wallet:
    def balance(self, name=DEFAULT_WALLET):
        '''Get balance of wallet
        :param name: Name of the wallet. [default: Default]'''
        return call('wallet_balance', [name, get_passphrase()])

    def list(self):
        return call('wallet_list')

    def create(self, name=DEFAULT_WALLET, type='Basic'):
        '''create wallet
        :param name: Name of the wallet. [defualt: Default]
        :param type: Type of the wallet. [Basic|HD] [default: Basic]
        '''
        return call('wallet_create', [name, get_passphrase()], type)

    def restore(self, mnemonics, name=DEFAULT_WALLET):
        '''restore wallet
        :param name: Name of the wallet. [defualt: Default]
        :param mnemonics: mnemonics words
        '''
        return call('wallet_restore', [name, get_passphrase()])

    def view_key(self, name=DEFAULT_WALLET):
        return call(
            'wallet_getViewKey'
            [name, get_passphrase()]
        )

    def list_pubkey(self, name=DEFAULT_WALLET):
        return call('wallet_listPublicKeys', [name, get_passphrase()])

    def transactions(self, name=DEFAULT_WALLET):
        return call('wallet_transactions', [name, get_passphrase()])

    def send(self, to_address, amount, name=DEFAULT_WALLET, view_keys=None):
        return call(
            'wallet_sendToAddress',
            [name, get_passphrase()],
            to_address, amount, view_keys or [])


class Staking:
    def deposit_stake(self, to_address, inputs, name=DEFAULT_WALLET):
        return call('staking_depositStake', [name, get_passphrase()], hex(to_address), inputs)

    def state(self, address, name=DEFAULT_WALLET):
        return call('staking_state', [name, get_passphrase()], hex(address))

    def unbond_stake(self, address, amount, name=DEFAULT_WALLET):
        return call('staking_unbondStake', [name, get_passphrase()], hex(address), amount)

    def withdraw_all_unbonded_stake(self, from_address, to_address, name=DEFAULT_WALLET):
        return call(
            'staking_withdrawAllUnbondedStake',
            [name, get_passphrase()],
            hex(from_address), to_address, []
        )

    def unjail(self, address, name=DEFAULT_WALLET):
        return call('staking_unjail', [name, get_passphrase()], hex(address))


class MultiSig:
    def create_address(self, public_keys, self_public_key, required_signatures, name=DEFAULT_WALLET):
        return call('multiSig_createAddress',
                   [name, get_passphrase()],
                   public_keys,
                   self_public_key,
                   required_signatures)

    def new_session(self, message, signer_public_keys, self_public_key, name=DEFAULT_WALLET):
        return call('multiSig_newSession',
                   [name, get_passphrase()],
                   message,
                   signer_public_keys,
                   self_public_key)

    def nonce_commitment(self, session_id, passphrase):
        return call('multiSig_nonceCommitment', session_id, passphrase)

    def add_nonce_commitment(self, session_id, passphrase, nonce_commitment, public_key):
        return call('multiSig_addNonceCommitment', session_id, passphrase, nonce_commitment, public_key)

    def nonce(self, session_id, passphrase):
        return call('multiSig_nonce', session_id, passphrase)

    def add_nonce(self, session_id, passphrase, nonce, public_key):
        return call('multiSig_addNonce', session_id, passphrase, nonce, public_key)

    def partial_signature(self, session_id, passphrase):
        return call('multiSig_partialSign', session_id, passphrase)

    def add_partial_signature(self, session_id, passphrase, partial_signature, public_key):
        return call('multiSig_addPartialSignature', session_id, passphrase, partial_signature, public_key)

    def signature(self, session_id, passphrase):
        return call('multiSig_signature', session_id, passphrase)

    def broadcast_with_signature(self, session_id, unsigned_transaction, name=DEFAULT_WALLET):
        return call('multiSig_broadcastWithSignature',
                   [name, get_passphrase()],
                   session_id,
                   unsigned_transaction)


class Blockchain:
    def status(self):
        return call_chain('status')

    def info(self):
        return call_chain('info')

    def genesis(self):
        return call_chain('genesis')

    def unconfirmed_txs(self):
        return call_chain('unconfirmed_txs')

    def latest_height(self):
        return self.status()['latest_block_height']

    def validators(self, height='latest'):
        height = height if height != 'latest' else self.latest_height()
        return call_chain('validators', height)

    def block(self, height='latest'):
        height = height if height != 'latest' else self.latest_height()
        return call_chain('block', height)

    def block_results(self, height='latest'):
        height = height if height != 'latest' else self.latest_height()
        return call_chain('block_results', height)

    def chain(self, min_height, max_height='latest'):
        max_height = max_height if max_height != 'latest' else self.latest_height()
        return call_chain('blockchain', min_height, max_height)

    def commit(self, height='latest'):
        height = height if height != 'latest' else self.latest_height()
        return call_chain('commit', height)

    def query(self, path, data, proof=False):
        return call_chain('abci_query', path, data, proof)

    def broadcast_tx_commit(self, tx):
        return call_chain('broadcast_tx_commit', tx)

    def broadcast_tx_sync(self, tx):
        return call_chain('broadcast_tx_sync', tx)

    def broadcast_tx_async(self, tx):
        return call_chain('broadcast_tx_async', tx)

    def tx(self, txid):
        return call_chain('tx', txid)


class CLI:
    def __init__(self):
        self.wallet = Wallet()
        self.staking = Staking()
        self.address = Address()
        self.multisig = MultiSig()
        self.chain = Blockchain()

    def raw_tx(self, inputs, outputs, view_keys):
        return call('transaction_createRaw', inputs, outputs, view_keys)

    def sync(self, name=DEFAULT_WALLET):
        return call('sync', [name, get_passphrase()])

    def sync_all(self, name=DEFAULT_WALLET):
        return call('sync_all', [name, get_passphrase()])

    def sync_unlock(self, name=DEFAULT_WALLET):
        return call('sync_unlockWallet', [name, get_passphrase()])

    def sync_stop(self, name=DEFAULT_WALLET):
        return call('sync_stop', [name, get_passphrase()])


if __name__ == '__main__':
    fire.Fire(CLI())
