import base64
import hashlib
import json
import asyncio
import tempfile
from pathlib import Path
import re
import os

import nacl.signing

SRC_PATH = Path('../chain').resolve()
DEVUTIL_CMD = Path('target/debug/dev-utils')
CLIENT_CMD = Path('target/debug/client-cli')


class SigningKey:
    def __init__(self, seed):
        self._seed = seed
        self._sk = nacl.signing.SigningKey(seed)

    def priv_key_base64(self):
        return base64.b64encode(self._sk._signing_key).decode()

    def pub_key_base64(self):
        vk = self._sk.verify_key
        return base64.b64encode(bytes(vk)).decode()

    def validator_address(self):
        vk = self._sk.verify_key
        return hashlib.sha256(bytes(vk)).hexdigest()[:40].upper()


def tendermint_cfg():
    return {
        'proxy_app': 'tcp://127.0.0.1:26658',
        'moniker': 'CNMAC0019.local',
        'fast_sync': True, 'db_backend': 'goleveldb',
        'db_dir': 'data',
        'log_level': 'main:info,state:info,*:error',
        'log_format': 'plain',
        'genesis_file': 'config/genesis.json',
        'priv_validator_key_file': 'config/priv_validator_key.json',
        'priv_validator_state_file': 'data/priv_validator_state.json',
        'priv_validator_laddr': '',
        'node_key_file': 'config/node_key.json',
        'abci': 'socket',
        'prof_laddr': '',
        'filter_peers': False,
        'rpc': {
            'laddr': 'tcp://127.0.0.1:26657',
            'cors_allowed_origins': [],
            'cors_allowed_methods': [
                'HEAD',
                'GET',
                'POST'
            ],
            'cors_allowed_headers': [
                'Origin',
                'Accept',
                'Content-Type',
                'X-Requested-With',
                'X-Server-Time'
            ],
            'grpc_laddr': '',
            'grpc_max_open_connections': 900,
            'unsafe': False,
            'max_open_connections': 900,
            'max_subscription_clients': 100,
            'max_subscriptions_per_client': 5,
            'timeout_broadcast_tx_commit': '10s',
            'max_body_bytes': 1000000,
            'max_header_bytes': 1048576,
            'tls_cert_file': '',
            'tls_key_file': ''
        },
        'p2p': {
            'laddr': 'tcp://0.0.0.0:26656',
            'external_address': '',
            'seeds': '',
            'persistent_peers': '',
            'upnp': False, 'addr_book_file': 'config/addrbook.json',
            'addr_book_strict': True,
            'max_num_inbound_peers': 40,
            'max_num_outbound_peers': 10,
            'flush_throttle_timeout': '100ms',
            'max_packet_msg_payload_size': 1024,
            'send_rate': 5120000,
            'recv_rate': 5120000,
            'pex': True,
            'seed_mode': False,
            'private_peer_ids': '',
            'allow_duplicate_ip': False,
            'handshake_timeout': '20s',
            'dial_timeout': '3s'
        },
        'mempool': {
            'recheck': True,
            'broadcast': True,
            'wal_dir': '',
            'size': 5000,
            'max_txs_bytes': 1073741824,
            'cache_size': 10000,
            'max_tx_bytes': 1048576
        },
        'fastsync': {'version': 'v0'},
        'consensus': {
            'wal_file': 'data/cs.wal/wal',
            'timeout_propose': '3s',
            'timeout_propose_delta': '500ms',
            'timeout_prevote': '1s',
            'timeout_prevote_delta': '500ms',
            'timeout_precommit': '1s',
            'timeout_precommit_delta': '500ms',
            'timeout_commit': '1s',
            'skip_timeout_commit': False,
            'create_empty_blocks': True,
            'create_empty_blocks_interval': '0s',
            'peer_gossip_sleep_duration': '100ms',
            'peer_query_maj23_sleep_duration': '2s'
        },
        'tx_index': {
            'indexer': 'kv',
            'index_tags': '',
            'index_all_tags': True
        },
        'instrumentation': {
            'prometheus': False,
            'prometheus_listen_addr': ':26660',
            'max_open_connections': 3,
            'namespace': 'tendermint'
        }
    }


def priv_validator_key(seed):
    sk = SigningKey(seed)
    return {
        'address': sk.validator_address(),
        'pub_key': {
            'type': 'tendermint/PubKeyEd25519',
            'value': sk.pub_key_base64(),
        },
        'priv_key': {
            'type': 'tendermint/PrivKeyEd25519',
            'value': sk.priv_key_base64(),
        },
    }


def node_key(seed):
    sk = SigningKey(seed)
    return {
        'priv_key':{
            'type':'tendermint/PrivKeyEd25519',
            'value': sk.priv_key_base64(),
        }
    }


def app_state_cfg(validators, share, genesis_time, rewards_pool=0):
    return {
        "rewards_pool": str(rewards_pool),
        "distribution": {
            addr: str(share)
            for addr in validators
        },
        "unbonding_period": 60,
        "required_council_node_stake": "1",
        "jailing_config": {
            "jail_duration": 86400,
            "block_signing_window": 100,
            "missed_block_threshold": 50
        },
        "slashing_config": {
            "liveness_slash_percent": "0.1",
            "byzantine_slash_percent": "0.2",
            "slash_wait_period": 10800
        },
        "initial_fee_policy": {
            "base_fee": "1.1",
            "per_byte_fee": "1.25"
        },
        "council_nodes": {
            addr: [
                'test%d' % i,
                'test%d@example.com' % i,
                {
                    'consensus_pubkey_type': 'Ed25519',
                    'consensus_pubkey_b64': sk.pub_key_base64(),
                }
            ]
            for i, (addr, sk) in enumerate(validators.items())
        },
        "genesis_time": genesis_time,
    }


def tasks_ini(n, app_hash):
    base = {
        'supervisord': {
            'pidfile': '%(here)s/supervisord.pid',
        },
        'rpcinterface:supervisor': {
            'supervisor.rpcinterface_factory': 'supervisor.rpcinterface:make_main_rpcinterface',
        },
        'unix_http_server': {
            'file': '%(here)s/supervisor.sock',
        },
        'supervisorctl': {
            'serverurl': 'unix://%(here)s/supervisor.sock',
        },
    }

    commands = {
        'tx-enclave': f'''docker run --rm -p {ENCLAVE_PORT}:25933 --env RUST_BACKTRACE=1 --env RUST_LOG=info --name {opt['--project-name'] + '-tx-enclave'} -v {ROOT_PATH / ENCLAVE_PATH}:/enclave-storage {'--device' + SGX_DEVICE if SGX_DEVICE else ''} {CHAIN_TX_ENCLAVE_DOCKER_IMAGE}-{SGX_MODE.lower()}''',
        'chain-abci': f'{SRC_PATH / CHAIN_CMD} -g {app_hash} -c {CHAIN_ID} --enclave_server tcp://127.0.0.1:{ENCLAVE_PORT} --data {ROOT_PATH / CHAIN_PATH} -p {CHAIN_ABCI_PORT}',
        'tendermint': f'''tendermint node --proxy_app=tcp://127.0.0.1:{CHAIN_ABCI_PORT} --home={ROOT_PATH / TENDERMINT_PATH} --rpc.laddr=tcp://127.0.0.1:{TENDERMINT_RPC_PORT} --p2p.laddr=tcp://127.0.0.1:{TENDERMINT_P2P_PORT} {'--consensus.create_empty_blocks=true' if opt['--create-empty-block'] else '--consensus.create_empty_blocks=false'} --p2p.seeds=%(ENV_P2P_PEERS)s''',
        'client-rpc': f'''{SRC_PATH / CLIENT_RPC_CMD} --port={CLIENT_RPC_PORT} --chain-id={CHAIN_ID} --storage-dir={ROOT_PATH / WALLET_PATH} --websocket-url=ws://127.0.0.1:{TENDERMINT_RPC_PORT}/websocket''',
    }
    programs = {
        name: {
            'command': cmd,
            'stdout_logfile': f'%(here)s/{name}-%(group_name)s.log',
            'autostart': True,
            'autorestart': True,
            'redirect_stderr': True,
        }
        for name, cmd in commands.items()
    }

    groups = {}
    for node_cfgs

async def write_tasks_ini(path, app_hash):
    open(path, 'w').write(f'''
[supervisord]
pidfile=%(here)s/supervisord.pid

[]
supervisor.rpcinterface_factory = 

[unix_http_server]
file=%(here)s/supervisor.sock

[]


[program:tx-enclave]
command=
stdout_logfile=%(here)s/tx-enclave.log
autostart=true
autorestart=true
redirect_stderr=true

[program:chain-abci]
command=

[program:tendermint]
command=tendermint node --proxy_app=tcp://127.0.0.1:{CHAIN_ABCI_PORT} --home={ROOT_PATH / TENDERMINT_PATH} --rpc.laddr=tcp://127.0.0.1:{TENDERMINT_RPC_PORT} --p2p.laddr=tcp://127.0.0.1:{TENDERMINT_P2P_PORT} {'--consensus.create_empty_blocks=true' if opt['--create-empty-block'] else '--consensus.create_empty_blocks=false'} --p2p.seeds=%(ENV_P2P_PEERS)s
stdout_logfile=%(here)s/tendermint.log
autostart=true
autorestart=true
redirect_stderr=true

[program:client-rpc]
''')


def coin_to_voting_power(coin):
    return str(int(int(coin) / (10 ** 8)))


async def run(cmd, ignore_error=False, **kwargs):
    proc = await asyncio.create_subprocess_shell(cmd, **kwargs)
    retcode = await proc.wait()
    if not ignore_error:
        assert retcode == 0, cmd


async def interact(cmd, input=None, **kwargs):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        **kwargs
    )
    (stdout, stderr) = await proc.communicate(input=input)
    assert proc.returncode == 0, f'{stdout.decode("utf-8")} ({cmd})'
    return stdout


async def gen_app_state(cfg):
    with tempfile.NamedTemporaryFile('w') as fp:
        json.dump(cfg, fp)
        fp.flush()
        result = await interact(f'{SRC_PATH / DEVUTIL_CMD} genesis generate -g "{fp.name}"')
        return json.loads('{%s}' % result.decode('utf-8'))


async def gen_wallet_addr(mnemonic, type='Staking'):
    prefix = {
        'Staking': '0x',
        'Transfer': 'dcro',
    }[type]
    with tempfile.TemporaryDirectory() as dirname:
        await interact(
            f'{SRC_PATH / CLIENT_CMD} wallet restore --name Default',
            ('123456\n123456\n%s\n%s\n' % (mnemonic, mnemonic)).encode(),
            env=dict(os.environ,
                CRYPTO_CLIENT_STORAGE=dirname,
            ),
        )
        result = (await interact(
            f'{SRC_PATH / CLIENT_CMD} address new --name Default --type {type}',
            b'123456\n',
            env=dict(os.environ,
                CRYPTO_CLIENT_STORAGE=dirname,
            ),
        )).decode()
        return re.search(prefix + r'[0-9a-zA-Z]+', result).group()


async def gen_genesis(validators, rewards_pool=0, chain_id="test-chain-y3m1e6-AB"):
    genesis_time = "2019-11-20T08:56:48.618137Z"
    max_coin = 10000000000000000000
    share = int((max_coin - rewards_pool) / len(validators))
    genesis = {
        "genesis_time": genesis_time,
        "chain_id": chain_id,
        "consensus_params": {
            "block": {
                "max_bytes": "22020096",
                "max_gas": "-1",
                "time_iota_ms": "1000"
            },
            "evidence": {
                "max_age": "100000"
            },
            "validator": {
                "pub_key_types": [
                    "ed25519"
                ]
            }
        },
        'validators': [
            {
                'address': sk.validator_address(),
                'pub_key': {
                    'type': 'tendermint/PubKeyEd25519',
                    'value': sk.pub_key_base64(),
                },
                'power': coin_to_voting_power(share),
            }
            for addr, sk in validators.items()
        ],
    }

    state = await gen_app_state(app_state_cfg(validators, share, genesis_time, rewards_pool))
    genesis.update(state)
    return genesis


async def gen_validator(mnemonic, seed):
    return (
        await gen_wallet_addr(mnemonic),
        SigningKey(seed)
    )


async def gen_validators(cfgs):
    return dict([await gen_validator(mnemonic, seed) for (mnemonic, seed, _) in cfgs])

async def init_cluster(path, node_cfgs):
    vals = await gen_validators(node_cfgs)
    genesis = await gen_genesis(vals)
    app_hash = genesis['app_hash']

    for i, (_, val_seed, node_seed) in enumerate(node_cfgs):
        name = 'node%d' % i
        cfg_path = path / Path(name) / Path('tendermint') / Path('config')
        if not cfg_path.exists():
            os.makedirs(cfg_path)

        json.dump(genesis, open(cfg_path / Path('genesis.json'), 'w'), indent=4)
        json.dump(node_key(node_seed), open(cfg_path / Path('node_key.json'), 'w'), indent=4)
        json.dump(node_key(val_seed), open(cfg_path / Path('priv_validator_key.json'), 'w'), indent=4)
        json.dump(tendermint_cfg(), open(cfg_path / Path('config.toml'), 'w'), indent=4)

        data_path = path / Path(name) / Path('tendermint') / Path('config')
        if not data_path.exists():
            data_path.mkdir()
        json.dump({
            "height": "0",
            "round": "0",
            "step": 0
        }, open(data_path / Path('priv_validator_state.json'), 'w'))


node_cfg = [(
    'ripple scissors kick mammal hire column oak again sun offer wealth tomorrow wagon turn fatal',
    b'\xab' * 32,
    b'\xcd' * 32
)]

if __name__ == '__main__':
    print(asyncio.run(init_cluster('/tmp/nodes', node_cfg)))
