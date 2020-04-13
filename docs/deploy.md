# Deploy

Server:

```shell
APP_NAME="covid19-br"

dokku apps:create $APP_NAME
# copy `bot/covid19-br.cron` contents to dokku's crontab on server
dokku ps:scale $APP_NAME web=0
dokku ps:scale $APP_NAME cron=1

# For each var inside `.env`, do:
dokku config:set $APP_NAME VARIABLE=VALUE
```

Local:

```shell
git remote add dokku dokku@SERVER
git push dokku master
```
