# pg-listener

Simple script for listening and printing PostgreSQL notifications. The connection to the database and channels that will be listened to are stored in a config file. Output may be formatted, raw, or JSON.

## How to use

    Usage: python3 pg-listener.py [options]

    Options
    -c, --config <value>            Path to config file
    -j, --json                      Try to parse payload as JSON and show it formatted
    -r, --raw                       Print raw message to stdout

## Examples of usage

```
python3 pg-listener.py -c conf/demo.conf
```

```
python3 pg-listener.py -c conf/demo.conf -j
```

```
python3 pg-listener.py -c conf/demo.conf -r
```

## Config file structure

### .conf or .ini
```
[database]
dsn = postgres://user:password@host:5432/dbname

[listen]

channel_name_enabled = true
channel_name_disabled = false
```

### .yaml
```
database:
  dsn: postgres://user:password@host:5432/dbname

listen:
  channel_name_enabled: True
  channel_name_disabled: False
```

|key|description|
|---|---|
|database / dsn|connection to database|
|listen|list of channels that will be listened|

### Warning !!!
Only channels with true value will be listened to

## Examples of output
First terminal
```
python3 pg-listener.py -c conf/demo.conf
```

Second terminal
```
# run psql
psql -U postgres dbname

# send notifications
notify channel_name_enabled, '{"key1": "value1", "hello": "world"}';
notify channel_name_enabled, 'hello world';
```

First terminal output
```
LISTEN: channel_name_enabled
2022-07-23 09:36:13 [13239] channel_name_enabled: {"key1": "value1", "hello": "world"}
2022-07-23 09:36:26 [13239] channel_name_enabled: hello world
```

## Requirements
Python3 and python libraries

```
sudo pip3 install psycopg2
# or
sudo pip3 install psycopg2-binary

sudo pip3 install PyYAML
```