Prerequisite
============

* `tendermint <https://tendermint.com/downloads>`_ binary in path.
* `docker <https://docs.docker.com/install/>`_
* python3
* ``pip3 install docopt``
* ``pip3 install supervisor``

Port Usage
==========

* base-port: 26650
* tx-enclave: base-port + 0
* chain-abci: base-port + 1
* tendermint-p2p-port: base-port + 2
* tendermint-rpc-port: base-port + 3
* client-rpc-port: base-port + 4

Run
===

* Root data directory is ``opt[--data] / opt[--project-name]``

::

    $ ./robot.py --help
    build robot CLI

    Usage:
      robot.py build [--docker] [--enclave-mode <mode>] [-s,--src <path>]
      robot.py init [-d,--data <path>] [-p,--project-name <name>] [-s,--src <path>] [--docker] [-f,--force] [-P,--base-port <port>] [--base-fee <fee>] [--per-byte-fee <fee>]
      robot.py compose  [-d,--data <path>] [-p,--project-name <name>] [-s,--src <path>] [-P,--base-port <port>]
      robot.py start-native [-d,--data <path>] [-p,--project-name <name>] [-s,--src <path>]
      robot.py stop-native [-d,--data <path>] [-p,--project-name <name>]
      robot.py (-h | --help)
      robot.py --version

    Options:
      -d,--data <path>               Set data root directory [default: .].
      -p,--project-name <name>       Used as data directory name and prefix of docker container name [default: default].
      -s,--src <path>                Set chain source directory [default: .].
      -P,--base-port <port>          Base port number when running in local [default: 26650].
      --docker                       Use docker.
      --base-fee <fee>               Base fee [default: 0.0].
      --per-byte-fee <fee>           Per byte fee [default: 0.0].
      --enclave-mode <mode>          Envlave mode, SW|HW [default: SW].
      -f,--force                     Override existing data directory.
      -h --help                      Show this screen.
      -v,--version                   Show version.

Examples
========

* Build chain binary in local::

    $ ./robot.py build --src ../chain

* Build chain docker image::

    $ ./robot.py build --docker --src ../chain

* Init tendermint genesis, basic staking and transfer wallet addresses, chain storage::

    $ ./robot.py init --src ../chain -p zerofee
    $ ./robot.py init --src ../chain -p withfee --base-fee 1.1 --per-byte-fee 1.25 -P 26660

* Run services with native binaries::

    $ ./robot.py start-native --src ../chain -p zerofee
    $ ./robot.py start-native --src ../chain -p withfee

* Stop native services::

    $ ./robot.py stop-native -p zerofee
    $ ./robot.py stop-native -p withfee

* Monitor native services::

    $ supervisorctl -c ./zerofee/supervisor/tasks.ini

* Run services in docker::

    $ ./robot.py compose --src ../chain -p zerofee --docker
