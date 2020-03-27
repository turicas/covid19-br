#!/usr/bin/env bash

# command dispacther
# -----------------------------------------------------------------------------
# Changes zsh globbing patterns
unsetopt NO_MATCH >/dev/null 2>&1 || :

# Dispatches calls of commands and arguments
dispatch ()
{
	namespace="$1"     # Namespace to be dispatched
	arg="${2:-}"       # First argument
	short="${arg#*-}"  # First argument without trailing -
	long="${short#*-}" # First argument without trailing --

	# Exit and warn if no first argument is found
	if [ -z "$arg" ]; then
		"${namespace}_" # Call empty call placeholder
		return 1
	fi

	shift 2 # Remove namespace and first argument from $@

	# Detects if a command, --long or -short option was called
	if [ "$arg" = "--$long" ];then
		longname="${long%%=*}" # Long argument before the first = sign

		# Detects if the --long=option has = sign
		if [ "$long" != "$longname" ]; then
			longval="${long#*=}"
			long="$longname"
			set -- "$longval" "${@:-}"
		fi

		main_call=${namespace}_option_${long}


	elif [ "$arg" = "-$short" ];then
		main_call=${namespace}_option_${short}
	else
		main_call=${namespace}_command_${long}
	fi

	$main_call "${@:-}" && dispatch_returned=$? || dispatch_returned=$?

	if [ $dispatch_returned = 127 ]; then
		"${namespace}_call_" "$namespace" "$arg" # Empty placeholder
		return 1
	fi

	return $dispatch_returned
}
# end command dispatcher
# -----------------------------------------------------------------------------

source ./rocketchat.sh

export BASE_URL=https://chat.brasil.io

onboarding.sh_command_welcome(){
    channel=$1; shift
    user=$1; shift

	ONBOARDING_MESSAGE="
Bem vindo ${user} .\\n
\\n
Para iniciar a colaboração em nosso projeto, me informe via mensagem privada 
o seu nome, e-mail, o Estado que você deseja colaborar com as coletas e checagens, 
e qual seu Estado de residência.\\n
\\n
Preciso que você leia as [instrunções](https://github.com/turicas/covid19-br/blob/master/CONTRIBUTING.md)\\n
\\n
Enquanto isso irei fazer seu cadastro na planilha de colaboradores, e lhe adicionar nos canais #covid19, #covid19-anuncios e no grupo da dua região.
"

    rocket_msg_send $channel $ONBOARDING_MESSAGE
}

# ./onboarding.sh invite "@username" "#channel"
onboarding.sh_command_invite(){
    #TODO - implement invite https://rocket.chat/docs/developer-guides/rest-api/channels/invite/
    # will need to get user_id from username, and then call an invite to each channel
    echo "adding user to channels"
}

# ./onboarding.sh sheets "#channel" "@username" "nome-da-região"
onboarding.sh_command_sheets(){
    channel=$1; shift
    user=$1; shift
    regiao=$1; shift

	SHEETS_MESSAGE="@turicas , libera o acesso para o ${user} nas planilhas da região ${regiao}"

    rocket_msg_send $channel $SHEETS_MESSAGE
}

dispatch onboarding.sh "$@"