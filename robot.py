#!/usr/bin/env python3
'''build robot CLI

Usage:
  robot.py build [--docker] [--enclave-mode <mode>] [--src <path>]
  robot.py init [-d,--data <path>] [--base-fee <fee>] [--per-byte-fee <fee>] [--tendermint <version>] [--docker] [-f, --force] [--src <path>]
  robot.py compose  [-d,--data <path>] [--src <path>] [--project-name <name] [--tendermint-rpc-port <port>] [--client-rpc-port <port>]
  robot.py runlocal [-d,--data <path>] [--src <path>] [--tendermint-rpc-port <port>] [--enclave-port <port>] [--chain-abci-port <port>]
  robot.py (-h | --help)
  robot.py --version

Options:
  -d,--data <path>               Set data root directory [default: .].
  --src <path>                   Set chain source directory [default: .].
  -f,--force                     Override existing data directory.
  --docker                       Use docker.
  --tendermint <version>         Version of terdermint [default: 0.32.0].
  --base-fee <fee>               Base fee [default: 0.0].
  --per-byte-fee <fee>           Per byte fee [default: 0.0].
  --enclave-mode <mode>          Envlave mode, SW|HW [default: SW].
  --tendermint-rpc-port <port>   Exported tendermint rpc port [default: 26657].
  --chain-abci-port <port>       chain-abci listen port when runlocal [default: 26658].
  --enclave-port <port>          tx-enclave listen port when runlocal [default: 25933].
  --chain-port <port>   Exported tendermint rpc port [default: 26657].
  --client-rpc-port <port>       Exported client rpc port [default: 26659].
  --project-name <name>          Docker project name [default: test].
  -h --help                      Show this screen.
  -v,--version                   Show version.
'''
import os
import re
import asyncio
import json
import shutil
import base64
import hashlib
from pathlib import Path
from docopt import docopt

opt = docopt(__doc__, version='Crypto-com build robot 0.1')
print(opt)

# constants
CHAIN_DOCKER_IMAGE = "integration-tests-chain"
CHAIN_TX_ENCLAVE_DOCKER_IMAGE = "integration-tests-chain-tx-enclave"
TENDERMINT_VERSION = '0.32.0'
WALLET_NAME = 'Default'
WALLET_PASSPHRASE = '123456'
CHAIN_ID = "test-chain-y3m1e6-AB"
CHAIN_HEX_ID = CHAIN_ID[-2:]

# paths
BASE_DIR = Path(__file__).parent
COMPOSE_FILE = BASE_DIR / 'docker-compose.yml'
ROOT_PATH = Path(opt['--data']).resolve()
SRC_PATH = Path(opt['--src']).resolve()
GENESIS_PATH = Path('config/genesis.json')
ENCLAVE_PATH = Path('enclave')
TENDERMINT_PATH = Path('tendermint')
WALLET_PATH = Path('wallet')
CHAIN_PATH = Path('chain')
DEVCONF_PATH = Path('dev_conf.json')
ADDRESS_STATE_PATH = Path('address-state.json')
CLIENT_CMD = Path('target/debug/client-cli')
CHAIN_CMD = Path('target/debug/chain-abci')
DEVUTIL_PATH = Path('target/debug/dev-utils')

DEV_CONF = '''{
    "rewards_pool": "6250000000000000000",
    "distribution": {
        "%(staking)s": "2500000000000000000",
        "0x3ae55c16800dc4bd0e3397a9d7806fb1f11639de": "1250000000000000000"
    },
    "unbonding_period": 15,
    "required_council_node_stake": "1250000000000000000",
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
        "base_fee": "%(base_fee)s",
        "per_byte_fee": "%(per_byte_fee)s"
    },
    "council_nodes": {
        "%(staking)s": [
            "integration test",
            "security@integration.test",
        {
            "consensus_pubkey_type": "Ed25519",
            "consensus_pubkey_b64": "%(validator_pub_key)s"
        }]
    },
    "genesis_time": "%(genesis_time)s"
}'''

ADDRESS_STATE = '''{
        "staking": "%(staking)s",
    "transfer": [
        "%(transfer1)s",
        "%(transfer2)s"
    ]
}'''


async def run(cmd, ignore_error=False, **kwargs):
    print('Execute:', cmd)
    proc = await asyncio.create_subprocess_shell(cmd, **kwargs)
    if not ignore_error:
        assert await proc.wait() == 0, cmd


async def interact(cmd, input=None, **kwargs):
    print(cmd)
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        **kwargs
    )
    (stdout, stderr) = await proc.communicate(input=input)
    assert proc.returncode == 0, f'{stdout.decode("utf-8")} ({cmd})'
    return stdout


async def build_chain_image():
    await run(f'cd "{SRC_PATH}" && docker build -t "{CHAIN_DOCKER_IMAGE}" -f ./docker/Dockerfile .')


async def build_chain_tx_enclave_image(mode):
    await run(f'''
cd "{SRC_PATH}" && \
docker build -t "{CHAIN_TX_ENCLAVE_DOCKER_IMAGE}" \
        -f ./chain-tx-enclave/tx-validation/Dockerfile . \
        --build-arg SGX_MODE={mode} \
        --build-arg NETWORK_ID={CHAIN_HEX_ID}
    ''')


async def init_tendermint(path):
    await run(f'''
docker run --rm -v "{path}:/tendermint" \
    --env TMHOME=/tendermint \
    --user "{os.getuid()}:{os.getgid()}" \
    "tendermint/tendermint:v{TENDERMINT_VERSION}" init \
    ''')
    await run(f'''
sed -i -e "s/index_all_tags = false/index_all_tags = true/g" \
"{path}/config/config.toml"
    ''')


async def run_wallet(
    args, input,
    storage=None,
):
    storage = storage or ROOT_PATH / WALLET_PATH
    if opt['--docker']:
        return await interact(f'''
docker run -i --rm -v "{storage}:/.storage" \
--env CRYPTO_CLIENT_STORAGE=/.storage \
--user "{os.getuid()}:{os.getgid()}" \
"${CHAIN_DOCKER_IMAGE}" \
client-cli {args} \
        ''', input)
    else:
        return await interact(
            f'{SRC_PATH / CLIENT_CMD} {args}',
            input,
            env=dict(os.environ,
                     CRYPTO_CLIENT_STORAGE=storage,
                     CRYPTO_CHAIN_ID=CHAIN_ID)
        )


async def create_wallet(name, **kwargs):
    args = f'wallet new --name "{name}" --type basic'
    return await run_wallet(args, f'{WALLET_PASSPHRASE}\n{WALLET_PASSPHRASE}\n'.encode(), **kwargs)


async def create_wallet_address(name, type='Staking', **kwargs):
    args = f'address new --name {name} --type {type}'
    result = await run_wallet(args, f'{WALLET_PASSPHRASE}\n'.encode(), **kwargs)
    prefix = {
        'Staking': '0x',
        'Transfer': 'dcro',
    }[type]
    return re.search(prefix + r'[0-9a-zA-Z]+', result.decode('utf-8')).group()


async def save_wallet_addresses(path, staking_addr, transfer_addrs):
    json.dump({
        'staking': staking_addr,
        'transfer': transfer_addrs,
    }, open(path, 'w'))


async def write_wallet_addresses(path, staking, transfer1, transfer2):
    open(path, 'w').write(ADDRESS_STATE % locals())


async def write_dev_conf(path, **kwargs):
    open(path, 'w').write(DEV_CONF % kwargs)


def validator_address(pubkey):
    return hashlib.sha256(base64.b64decode(pubkey)).hexdigest()[:40].upper()


async def update_genesis(dev_conf_path, genesis_path):
    if opt['--docker']:
        result = await interact(f'''
docker run -i --rm \
    -v "{dev_conf_path}:/dev-conf.conf" \
    "{CHAIN_DOCKER_IMAGE}" \
    dev-utils genesis generate -g /dev-conf.conf
        ''')
    else:
        result = await interact(f'{SRC_PATH / DEVUTIL_PATH} genesis generate -g "{dev_conf_path}"')

    genesis = json.load(open(genesis_path))
    genesis['chain_id'] = CHAIN_ID

    app = json.loads('{%s}' % result.decode('utf-8'))
    genesis.update(app)

    # update validators in genesis
    genesis['validators'] = [
        {
            'address': validator_address(node[2]['consensus_pubkey_b64']),
            'pub_key': {
                'type': 'tendermint/PubKeyEd25519',
                'value': node[2]['consensus_pubkey_b64'],
            },
            'power': str(int(int(genesis['app_state']['distribution'][addr][1]) / 10 ** 8)),
        }
        for addr, node in genesis['app_state']['council_nodes'].items()
    ]

    json.dump(genesis, open(genesis_path, 'w'), indent=4)


async def build():
    print('Build chain')
    if opt['--docker']:
        await build_chain_image()
    else:
        await run(f'cd "{SRC_PATH}" && cargo build')

    print('Build tx enclave image')
    await build_chain_tx_enclave_image(opt['--enclave-mode'])


async def init():
    if ROOT_PATH.exists():
        if opt['--force']:
            print('Root path already exists, delete it')
            shutil.rmtree(ROOT_PATH)
        else:
            print('Root path already exists, quit')
            return
    ROOT_PATH.mkdir()
    print('Init tendermint')
    await init_tendermint(ROOT_PATH / TENDERMINT_PATH)

    print('Init wallet')
    await create_wallet(WALLET_NAME,
                        storage=ROOT_PATH / WALLET_PATH)

    print('Create test addresses')
    staking = await create_wallet_address(
        WALLET_NAME, type='Staking')
    print('staking address:', staking)
    transfer1 = await create_wallet_address(
        WALLET_NAME, type='Transfer')
    print('transfer address1:', transfer1)
    transfer2 = await create_wallet_address(
        WALLET_NAME, type='Transfer')
    print('transfer address2:', transfer2)

    await save_wallet_addresses(ROOT_PATH / ADDRESS_STATE_PATH, staking, [transfer1, transfer2])

    genesis = json.load(open(ROOT_PATH / TENDERMINT_PATH / GENESIS_PATH))
    validator_pub_key = genesis['validators'][0]['pub_key']['value']
    genesis_time = genesis['genesis_time']
    print('Write dev-conf.conf')
    await write_dev_conf(ROOT_PATH / DEVCONF_PATH,
                         base_fee=opt['--base-fee'], per_byte_fee=opt['--per-byte-fee'],
                         staking=staking, genesis_time=genesis_time,
                         validator_pub_key=validator_pub_key)
    print('Update genesis config')
    await update_genesis(ROOT_PATH / DEVCONF_PATH,
                         ROOT_PATH / TENDERMINT_PATH / GENESIS_PATH)


async def compose():
    genesis = json.load(open(ROOT_PATH / TENDERMINT_PATH / GENESIS_PATH))
    app_hash = genesis['app_hash']
    await run(f'docker-compose -f {COMPOSE_FILE} -p {opt["--project-name"]} up',
              env=dict(os.environ,
                       ENCLAVE_DIRECTORY=ROOT_PATH / ENCLAVE_PATH,
                       TENDERMINT_DIRECTORY=ROOT_PATH / TENDERMINT_PATH,
                       WALLET_STORAGE_DIRECTORY=ROOT_PATH / WALLET_PATH,
                       CHAIN_ABCI_DIRECTORY=ROOT_PATH / CHAIN_PATH,
                       CHAIN_ID=CHAIN_ID,
                       APP_HASH=app_hash,
                       TENDERMINT_VERSION=opt['--tendermint'],
                       TENDERMINT_RPC_PORT=opt['--tendermint-rpc-port'],
                       CLIENT_RPC_PORT=opt['--client-rpc-port'],
                       ))


async def runlocal():
    genesis = json.load(open(ROOT_PATH / TENDERMINT_PATH / GENESIS_PATH))
    app_hash = genesis['app_hash']
    enclave_container_name = opt['--project-name'] + '-tx-enclave'
    enclave_port = opt['--enclave-port']
    chain_port = opt['--chain-abci-port']
    tendermint_port = opt['--tendermint-rpc-port']
    await run(f'docker rm -f {enclave_container_name}', ignore_error=True)
    await asyncio.sleep(.5)
    await run(f'''
docker run -d \
-p {enclave_port}:25933 \
--env RUST_BACKTRACE=1 \
--env RUST_LOG=info \
--name {enclave_container_name} \
-v {ROOT_PATH / ENCLAVE_PATH}:/enclave-storage \
chain-tx-validation \
    ''')
    await asyncio.sleep(1)
    await run(f'''
{SRC_PATH / CHAIN_CMD} -g {app_hash} -c {CHAIN_ID} \
--enclave_server tcp://127.0.0.1:{enclave_port} \
--data {ROOT_PATH / CHAIN_PATH} \
-p {chain_port} > {ROOT_PATH / Path('chain-stdout.log')} &
    ''')
    await asyncio.sleep(1)
    await run(f'''
tendermint node --proxy_app=tcp://127.0.0.1:{chain_port} \
--home={ROOT_PATH / TENDERMINT_PATH} \
--rpc.laddr=tcp://127.0.0.1:{tendermint_port} \
--consensus.create_empty_blocks=true
    ''')


async def main():
    if opt['build']:
        await build()
    elif opt['init']:
        await init()
    elif opt['compose']:
        await compose()
    elif opt['runlocal']:
        await runlocal()

if __name__ == '__main__':
    asyncio.run(main())
