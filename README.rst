Prerequisite
============

* `tendermint <https://tendermint.com/downloads>`_ in PATH.
* `docker <https://docs.docker.com/install/>`_ with ``integration-tests-chain-tx-enclave`` image inside.
* binaries ``dev-utils`` ``client-cli`` ``chain-abci`` ``client-rpc`` in PATH.
* python3.7+

Install
=======

::

  $ pip3 install git+https://github.com/yihuang/crypto-chain-bot.git

OR: ::

  $ git clone https://github.com/yihuang/crypto-chain-bot.git
  $ cd crypto-chain-bot
  $ pip3 install -e .

Usage
=====

::

    $ cd /path/to/testnet
    $ chainbot.py gen 2 > cluster.json
    $ cat cluster.json
    {
        "genesis_time": "2019-11-20T08:56:48.618137Z",
        "rewards_pool": 0,
        "nodes": [
            {
                "name": "node0",
                "mnemonic": "sea hurdle public diesel family mushroom situate nasty act young smoke fantasy olive paddle talent",
                "validator_seed": "da65e6e809413a217b03f77bb00800e9c36d8a2f11ff00669c412ec34e077225",
                "node_seed": "dbbdd0c1e8ca293cd90ce9f417224bdfafdccb70e43cb2ed1732b2884c553773",
                "bonded_coin": 2500000000000000000,
                "unbonded_coin": 2500000000000000000,
                "base_port": 26650
            },
            {
                "name": "node1",
                "mnemonic": "absent noble used scout unfair cannon attack brass review scrap soap legal sugar carpet warrior",
                "validator_seed": "60ab92ba36ab4222ea4f986ea060399bb550ae6f7b7f885e69c9b0bbe88be39d",
                "node_seed": "e2fc20e58511b7e313488cc953dc09ebae4fb50145170ffdd0fe159627d5f5d3",
                "bonded_coin": 2500000000000000000,
                "unbonded_coin": 2500000000000000000,
                "base_port": 26660
            }
        ],
        "config_patch": [
            {
                "op": "replace",
                "path": "/initial_fee_policy/base_fee",
                "value": "0.0"
            },
            {
                "op": "replace",
                "path": "/initial_fee_policy/per_byte_fee",
                "value": "0.0"
            }
        ]
    }
    $ chainbot.py prepare cluster.json
    $ ls -1 .
    node0
    node1
    tasks.ini
    cluster.json
    $ supervisord -n -c tasks.ini
    
Manage the running processes: ::

    $ supervisorctl -c tasks.ini
    node0:chain-abci-node0           RUNNING   pid 12080, uptime 0:00:13
    node0:client-rpc-node0           RUNNING   pid 12096, uptime 0:00:10
    node0:tendermint-node0           RUNNING   pid 12065, uptime 0:00:14
    node0:tx-enclave-node0           RUNNING   pid 12064, uptime 0:00:14
    node1:chain-abci-node1           RUNNING   pid 12081, uptime 0:00:13
    node1:client-rpc-node1           RUNNING   pid 12097, uptime 0:00:10
    node1:tendermint-node1           RUNNING   pid 12068, uptime 0:00:14
    node1:tx-enclave-node1           RUNNING   pid 12067, uptime 0:00:14

Port Usage
==========

* base-port: 26650 + (node_index * 10)
* tendermint-p2p-port: base-port + 6
* tendermint-rpc-port: base-port + 7
* chain-abci: base-port + 8
* tx-enclave: base-port + 0
* client-rpc-port: base-port + 1
