#!/bin/bash

source .env
#TODO - check if .env variables are defined

function rocket_user_login() {
	user=$1; shift
	password=$1

	curl \
		$ROCKETCHAT_BASE_URL/api/v1/login \
		-d "user=$user&password=$password"
}

function rocket_user_create_bot_user() {
	username=$1; shift
	password=$1; shift
	email=$1; shift
	name=$1; shift

	curl \
		-H "X-Auth-Token: $ROCKETCHAT_AUTH_TOKEN" \
		-H "X-User-Id: $ROCKETCHAT_USER_ID" \
		-H "Content-type:application/json" \
		$ROCKETCHAT_BASE_URL/api/v1/users.create \
		-d "{\"username\": \"$username\", \"password\": \"$password\", \"email\": \"$email\", \"name\": \"$name\", \"active\": true, \"roles\": [\"bot\"], \"joinDefaultChannels\": false, \"requirePasswordChange\": false, \"sendWelcomeEmail\": false, \"verified\": true}"
}

function rocket_msg_send() {
	channel=$1; shift
	message=$@

	curl \
		-H "X-Auth-Token: $ROCKETCHAT_AUTH_TOKEN" \
		-H "X-User-Id: $ROCKETCHAT_USER_ID" \
		-H "Content-type:application/json" \
		$ROCKETCHAT_BASE_URL/api/v1/chat.postMessage \
		-d "{\"channel\": \"$channel\", \"text\": \"$message\"}"
}

function rocket_get_userid() {
	username=$1; shift

	userid=$(curl -s \
		-H "X-Auth-Token: $ROCKETCHAT_AUTH_TOKEN" \
		-H "X-User-Id: $ROCKETCHAT_USER_ID" \
		-H "Content-type:application/json" \
		"$ROCKETCHAT_BASE_URL/api/v1/users.info?username=$username" | jq -r .user._id)
	echo $userid
}

function rocket_get_channelid() {
	roomname=$1; shift
	roomid=$(
		curl -s \
		-H "X-Auth-Token: $ROCKETCHAT_AUTH_TOKEN" \
		-H "X-User-Id: $ROCKETCHAT_USER_ID" \
		-H "Content-type:application/json" \
		"$ROCKETCHAT_BASE_URL/api/v1/channels.info?roomName=$roomname" | jq -r .channel._id )
	echo $roomid
}

function rocket_get_groupid() {
	roomname=$1; shift
	roomid=$(curl -s \
		-H "X-Auth-Token: $ROCKETCHAT_AUTH_TOKEN" \
		-H "X-User-Id: $ROCKETCHAT_USER_ID" \
		-H "Content-type:application/json" \
		"$ROCKETCHAT_BASE_URL/api/v1/rooms.info?roomName=$roomname" | jq -r .room._id)
	echo $roomid
}

function rocket_invite_to_channel() {
	channel=$1; shift
	username=$1; shift

	roomid=$(rocket_get_channelid "$channel")
	userid=$(rocket_get_userid "$username")

	curl \
		-H "X-Auth-Token: $ROCKETCHAT_AUTH_TOKEN" \
		-H "X-User-Id: $ROCKETCHAT_USER_ID" \
		-H "Content-type:application/json" \
		$ROCKETCHAT_BASE_URL/api/v1/channels.invite \
		-d "{\"roomId\": \"$roomid\", \"userId\": \"$userid\"}"
}

function rocket_invite_to_group() {
	group=$1; shift
	username=$1; shift

	roomid=$(rocket_get_groupid "$group")
	userid=$(rocket_get_userid "$username")

	curl \
		-H "X-Auth-Token: $ROCKETCHAT_AUTH_TOKEN" \
		-H "X-User-Id: $ROCKETCHAT_USER_ID" \
		-H "Content-type:application/json" \
		$ROCKETCHAT_BASE_URL/api/v1/groups.invite \
		-d "{\"roomId\": \"$roomid\", \"userId\": \"$userid\"}"
	set +o xtrace
}
