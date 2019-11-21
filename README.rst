Prerequisite
============

* `tendermint <https://tendermint.com/downloads>`_
* `docker <https://docs.docker.com/install/>`_ with `integration-tests-chain-tx-enclave` image inside.
* binaries `dev-utils` `client-cli` `chain-abci` `client-rpc` in path.
* python3.7+

Install
=======

* ``pip3 install git+https://github.com/yihuang/crypto-chain-bot.git``

* ::

  $ git clone https://github.com/yihuang/crypto-chain-bot.git
  $ cd crypto-chain-bot
  $ pip3 install -e .

Usage
=====

::

    $ cd /path/to/data
    $ chainbot.py gen 4 > cluster.json
    $ cat cluster.json
    {
        "genesis_time": "2019-11-20T08:56:48.618137Z",
        "rewards_pool": 10000000000,
        "nodes": [
            {
                "name": "node0",
                "mnemonic": "eyebrow acoustic early point cage student robot garment usual medal author craft hungry split buffalo",
                "validator_seed": "478cd6c9ab502b58a09575c64d906be8229a7b5a0af6657e5d41fe7cd0915bc8",
                "node_seed": "8e28d882a20ecb0636871e1bd982d35bf430cee89a18a35cb5890ae0e172cc02",
                "bonded_coin": 1249999998750000128,
                "unbonded_coin": 1249999998750000128,
                "base_port": 26650
            },
            {
                "name": "node1",
                "mnemonic": "better slender doctor sand moon inherit diet child thrive unaware sound margin lonely inquiry blood",
                "validator_seed": "3bb00f28ea339e0004514c7a168c284abf4fd8d244e2ff23938d7ee6daba9e12",
                "node_seed": "9432c8888386b98400fa5072cf8b6b51fb25205e5255187e5591e8323f506285",
                "bonded_coin": 1249999998750000128,
                "unbonded_coin": 1249999998750000128,
                "base_port": 26660
            },
            {
                "name": "node2",
                "mnemonic": "kite gadget glare alter era alien spy powder female wild harvest amount raven disagree dawn",
                "validator_seed": "9252719b2993db7649ede3ab4865b25e6f572dabcf02c2c80145f57726dadd48",
                "node_seed": "388cfee4701c525139c7da1291f8bc217e0d09da303664386d71f05972f9703f",
                "bonded_coin": 1249999998750000128,
                "unbonded_coin": 1249999998750000128,
                "base_port": 26670
            },
            {
                "name": "node3",
                "mnemonic": "tail tennis shift nurse relief hobby quote endless sea anxiety across little order hero stomach",
                "validator_seed": "e1caea8e3aeedfc79fcc42f0e85408de9df12cddb968194033ff8ebe238e2ebb",
                "node_seed": "79259926b6797e30f3603567650e1c824da792db03bd4b451b6b730f5a42de8d",
                "bonded_coin": 1249999998750000128,
                "unbonded_coin": 1249999998750000128,
                "base_port": 26680
            }
        ]
    }
    $ chainbot.py prepare cluster.json
    $ ls -1 .
    node0
    node1
    node2
    node3
    tasks.ini
    cluster.json
    $ supervisord -n -c tasks.ini

Port Usage
==========

* base-port: 26650 + (node_index * 10)
* tendermint-p2p-port: base-port + 6
* tendermint-rpc-port: base-port + 7
* chain-abci: base-port + 8
* tx-enclave: base-port + 0
* client-rpc-port: base-port + 1
