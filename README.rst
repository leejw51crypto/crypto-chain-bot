Prerequisite
============

* python3
* ``pip3 install docopt``
* ``pip3 install supervisor``

Run
===

..code-block:: bash

    $ ./robot.py --help
    test robot CLI

    Usage:
      robot.py build [--docker] [--enclave-mode <mode>]
      robot.py init [-d,--data <path>] [--base-fee <fee>] [--per-byte-fee <fee>] [--tendermint <version>] [--docker] [-f, --force]
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
    build bot for crypto-com-chain

Examples
========

* Build chain binary in local::

    $ ./robot.py build --src ../chain

* Build chain docker image::

    $ ./robot.py build --docker --src ../chain

* Init tendermint genesis, basic staking and transfer wallet addresses, chain storage::

    $ ./robot.py init --src ../chain -d./zerofee
    $ ./robot.py init --src ../chain -d./withfee --base-fee 1.1 --per-byte-fee 1.25

* Run services with native binaries::

    $ ./robot.py start-native -d./zerofee --src ../chain
    $ ./robot.py start-native -d./withfee --src ../chain

* Stop native services::

    $ ./robot.py stop-native -d./zerofee

* Monitor native services::

    $ supervisorctl -c ./zerofee/supervisor/tasks.ini

* Run services in docker::

    $ ./robot.py compose --src ../chain -d./zerofee --docker
