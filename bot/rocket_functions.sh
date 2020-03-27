#!/bin/bash

function rocket_user_login() {
	base_url=$1; shift
	user=$1; shift
	password=$1

	curl \
		$base_url/api/v1/login \
		-d "user=$user&password=$password"
}

function rocket_user_create_bot_user() {
	base_url=$1; shift
	user_id=$1; shift
	auth_token=$1; shift
	username=$1; shift
	password=$1; shift
	email=$1; shift
	name=$1; shift

	curl \
		-H "X-Auth-Token: $auth_token" \
		-H "X-User-Id: $user_id" \
		-H "Content-type:application/json" \
		$base_url/api/v1/users.create \
		-d "{\"username\": \"$username\", \"password\": \"$password\", \"email\": \"$email\", \"name\": \"$name\", \"active\": true, \"roles\": [\"bot\"], \"joinDefaultChannels\": false, \"requirePasswordChange\": false, \"sendWelcomeEmail\": false, \"verified\": true}"
}

function rocket_msg_send() {
	base_url=$1; shift
	user_id=$1; shift
	auth_token=$1; shift
	channel=$1; shift
	message=$@

	curl \
		-H "X-Auth-Token: $auth_token" \
		-H "X-User-Id: $user_id" \
		-H "Content-type:application/json" \
		$base_url/api/v1/chat.postMessage \
		-d "{\"channel\": \"$channel\", \"text\": \"$message\"}"
}
