# Bot RocketChat (chat.brasil.io)

Nesse diretório estão os comandos relativos [ao nosso
robô](https://chat.brasil.io/direct/robo). Você pode usar parte da estrutura de
scripts Bash e Python para criar suas próprias notificações no RocketChat.

## Scripts Relevantes

- [`check-urls.sh`](check-urls.sh): verifica se as páginas das SES foram
  alteradas e envia nofiticações nos canais regionais.

## Biblioteca/CLI em Python

[`rocketchat.py`](rocketchat.py): pode ser usado como biblioteca Python ou
script que envia mensagem pela linha de comando. Funções implementadas: login,
criação de usuário de bot e envio de mensagem.

Script:

```shell
python rocketchat.py --base_url=<base_url> --username=<username> --password=<password> "#channel" "message"
python rocketchat.py --base_url=<base_url> --user_id=<user_id> --auth_token=<auth_token> "#channel" "message"
```

Biblioteca: veja o `if __name__ == "__main__"` do `rocketchat.py`.

## Bash

[`rocketchat.sh`](rocketchat.sh): funções Bash para login, criação de usuário
de bot e envio de mensagem.

Defina as configurações de autenticação no arquivo `.env`, usando o exemplo
`env-sample`:

```shell
cp env-sample .env
cat .env
# https://chat.brasil.io/account/tokens
export ROCKETCHAT_BASE_URL="https://chat.brasil.io"
export ROCKETCHAT_USER_ID="<user_id>"
export ROCKETCHAT_AUTH_TOKEN="<auth_token>"
...
```

Funções disponíveis:

```shell
source rocketchat.sh

rocket_user_login <username> <password>
rocket_user_create_bot_user <username> <password> <email> <name>
rocket_msg_send <channel> <message>
```

### onboarding.sh

Para automatizar o processo de onboarding de novos voluntários.

```shell
./onboarding.sh welcome <username>
./onboarding.sh invite <username>
./onboarding.sh sheets <username> <regiao>
```
