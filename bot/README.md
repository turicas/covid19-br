# Bot RocketChat (chat.brasil.io)

## Python

`rocketchat.py`: pode ser usado como biblioteca Python ou script que envia
mensagem pela linha de comando. Funções implementadas: login, criação de
usuário de bot e envio de mensagem.

Script:

```shell
python rocketchat.py --base_url=<base_url> --username=<username> --password=<password> "#channel" "message"
python rocketchat.py --base_url=<base_url> --user_id=<user_id> --auth_token=<auth_token> "#channel" "message"
```

Biblioteca: veja o `if __name__ == "__main__"` do `rocketchat.py`.


## Bash

`rocketchat.sh`: funções Bash para login, criação de usuário de bot e
envio de mensagem

Funções disponíveis:

```shell
source rocketchat.sh

rocket_user_login <base_url> <username> <password>
rocket_user_create_bot_user <base_url> <user_id> <auth_token> <username> <password> <email> <name>
rocket_msg_send <base_url> <user_id> <auth_token> <channel> <message>
```
