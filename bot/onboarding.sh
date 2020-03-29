#!/usr/bin/env bash

# command dispacther
# https://github.com/Mosai/workshop/blob/master/doc/dispatch.md
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

ONBOARDING_CHANNEL=covid19-onboarding

# ./onboarding.sh welcome "username"
onboarding.sh_command_welcome(){
	if [ -z ${1+x} ]; then 
		echo "ERRO - faltou informar usuario"
		echo "Ex.: ./onboarding.sh welcome fulano"
		exit 1
	fi

    user=$1; shift

	ONBOARDING_MESSAGE="
Bem vindo @${user} .\\n
\\n
Para iniciar a colaboração em nosso projeto, me informe via mensagem privada :\\n
\\n
- Nome completo;\\n
- e-mail;\\n
- Estado que pretende colaborar;\\n
- Estado de residência.\\n
\\n
Preciso que você leia as [instrunções](https://github.com/turicas/covid19-br/blob/master/CONTRIBUTING.md)\\n
\\n
Assim que você me fornecer estes dados, irei concluir seu cadatro na planilha de voluntários, e prosseguir com o processo, 
liberando acesso aos canais necessários, às planilhas, e lhe enviando uma série de orientaçãoes, e um vídeo.
"

    rocket_msg_send $ONBOARDING_CHANNEL $ONBOARDING_MESSAGE
}

# ./onboarding.sh guide "username"
onboarding.sh_command_guide(){
	if [ -z ${1+x} ]; then 
		echo "ERRO - faltou informar usuario"
		echo "Ex.: ./onboarding.sh guide fulano"
		exit 1
	fi

    user=$1; shift

	ONBOARDING_MESSAGE="
Oi, tudo bem?\\n
\\n
Temos agora um vídeo com o tutorial de como as planilhas devem ser preenchidas.\\n
\\n
Precisamos de 1 minutinho seu [para assistir 📹](https://drive.google.com/open?id=1EqmmPaUtN-OVNqt5hukRzO_afBAjpPQc).\\n
\\n
Também fizemos uma lista de *pontos de atenção* que devemos ter nas horas de preenchimento e checagem:\\n
\\n
1. *NUNCA* crie linhas novas nas planilhas ou altere a ordem das linhas. Se você não encontrar alguma cidade para preencher, limpe os filtros, ela está lá. Qualquer dúvida, leve para o canal.\\n
2. os filtros são traiçoeiros, apesar de úteis: ao acessar a planilha, você deve desabilitá-los e habilitá-los novamente (para fazer sua filtragem), já que não sabe o que foi filtrado/escondido por quem mexeu antes.\\n
3. os filtros são traiçoeiros, apesar de úteis 2: remova-os antes de fazer a transferência dos dados para a planilha final (copiar e colar).\\n
4. para transferir os dados do rascunho para a aba final, *SEMPRE* copie e cole as novas colunas inteiras. *NUNCA* copie e cole linhas ou células específicas.\\n
5. não esqueça de preencher os zeros nas colunas em que a sua par (casos < > mortes) tenha número preenchido, *ATENÇÃO* especialmente nas cidades que passam a entrar nas estatísticas.\\n
6. se por algum motivo você precisou atualizar dias anteriores, avise quem vai checar para que a atualização seja completa.\\n
7. cuidado extra nos estados que soltam mais de um boletim por dia: muitas vezes não será o caso de criar uma nova coluna para [hoje], mas apenas de atualizar os dados já preenchidos mais cedo\\n
8. *ATENÇÃO* com os headers das colunas (especialmente das novas): confiram se as datas e o formato padrão do estão corretos.\\n
9. não esqueça de preencher as abas dos links dos boletins (rascunho e final) - elas devem ficar sempre iguais\\n
10. nas abas dos boletins, *NUNCA* escreva as datas: para preencher um dia novo, arraste a célula da data da véspera para a linha de baixo. se for necessário repetir o mesmo dia, copie e cole a célula com a data.\\n
11. O programa sempre pega o dado mais atual para cada município. Se o município ou Importados/Indefinidos passou a não ser mais reportado, os dias seguintes devem ser preenchidos com 0; não deixar em branco.\\n
12. *NUNCA* use fórmulas nas planilhas (isso irá fazer com que o script não consiga extrair os dados de seu estado). Vamos sempre digitar os dados que estamos coletando.\\n
13. *SEMPRE* confira se o somatório de casos/mortes de todos os municípios é igual ao total por estado. Caso não sejam iguais, pode ser que tenha acontecido algum erro na escrita dos dados na planilha (mas também pode significar que a secretaria reportou o número errado - nesse caso, coloque o valor reportado pela secretaria).\\n
14. *SOMENTE COLOQUE NA PLANILHA FINAL SE VOCÊ TIVER CERTEZA DE QUE A INFORMAÇÃO ESTÁ CORRETA. NÃO FAÇA TESTES NESSA ABA*\\n
\\n
Obrigada pela sua contribuição! 🙂\\n
\\n
Fique à vontade para fazer sugestões.\\n
"
    rocket_msg_send "@$user" $ONBOARDING_MESSAGE
}

# ./onboarding.sh invite "username"
onboarding.sh_command_invite(){
	if [ -z ${1+x} ]; then 
		echo "ERRO - faltou informar o usuario usuario"
		echo "Ex.: ./onboarding.sh invite fulano"
		exit 1
	fi

    user=$1; shift
	regiao=$1; shift
	
	rocket_invite_to_channel "covid19-anuncios" "$user"
	rocket_invite_to_group "covid19" "$user"
	rocket_msg_send "@$user" "Acabei de lhe adicionar nos canais #covid19-anuncios e #covid19."
}

# ./onboarding.sh sheets "username" "<região>"
#TODO - validar regiao informada
onboarding.sh_command_sheets(){
	if [ -z ${2+x} ]; then 
		echo "ERRO - faltou informar usuario ou região"
		echo "Ex.: ./onboarding.sh sheets fulano nordeste"
		exit 1
	fi

    user=$1; shift
    regiao=$1; shift

    rocket_msg_send "@turicas" "olá, libera o acesso para o usuário @$user às planilhas da região $regiao"
	rocket_invite_to_group "covid19-$regiao" "$user"
}

dispatch onboarding.sh "$@"