import discord
import tokenFile
import globals
import game
import databases
from interpreter import interpret_general, wait_for_message
from logger import Logger
import table
import math
import sys

token = tokenFile.token
globals.client = discord.Client()
globals.phase = 'no_game'
globals.logger = Logger()


# handler for messages while in no_game phase
async def phase_no_game(message):
    iMessage = interpret_general(message, ['create'])
    if iMessage is not None and not iMessage.error:
        globals.mainChannel = iMessage.channel
        response = 'Game created\n**~set tb [subset]** to add sets, leave subset empty for full set\n' \
                   '**~join** to join the game\n**~count** to check who has joined\n**~start** to start the game\n' \
                   '**~nick nickname** to set a nickname\n**~ban role** to ban a role'
        await iMessage.channel.send(response)
        globals.phase = 'create'
    elif iMessage is not None:
        await iMessage.channel.send(iMessage.payload)


# handler for messages while in create phase
async def phase_create(message):
    iMessage = interpret_general(message, ['join', 'count', 'set', 'start', 'nick', 'ban'])
    if iMessage is not None and not iMessage.error:
        if iMessage.command == 'join':
            nick = iMessage.user.display_name
            if iMessage.user in game.joiningPlayers:
                await globals.mainChannel.send('You are already in the game')
            elif (nick in databases.aliasDatabase.values() and not databases.aliasDatabase[iMessage.user] == nick) or nick in game.nicknamesDictionary.values() or nick in game.joiningPlayersNicknames:
                await globals.mainChannel.send('Player with same name is already in the game')
            else:
                await game.add_player(iMessage.user)
        elif iMessage.command == 'count':
            response = str(len(game.joiningPlayers)) + ' players\nList of players: ' + \
                      ', '.join(game.joiningPlayersNicknames)
            await globals.mainChannel.send(response)
        elif iMessage.command == 'nick':
            nick = iMessage.payload
            if nick in databases.aliasDatabase.values() or nick in game.nicknamesDictionary.values() or nick in game.joiningPlayersNicknames:
                await globals.mainChannel.send('Nickname is already in use')
            else:
                game.nicknamesDictionary[iMessage.user.id] = iMessage.payload
                await globals.mainChannel.send('Name confirmed')
        elif iMessage.command == 'set':
            game.build_set(iMessage.payload)
            await globals.mainChannel.send('Sets in play:\n' + game.sets_in_play())
        elif iMessage.command == 'start':
            globals.phase = 'night'
            await game.start_game()  # starts phase if successful #globals.phase = 'night'
        elif iMessage.command == 'ban':
            await game.ban(iMessage.payload)
    elif iMessage is not None:
        await iMessage.channel.send(iMessage.payload)


# lots of gross stuff here, should clean up at some point
async def phase_day(message):
    iMessage = interpret_general(message, ['nominate', 'sleep', 'table', 'slay'])
    if iMessage is not None and not iMessage.error:
        user = game.get_player_from_user(iMessage.user)

        if iMessage.command == 'nominate':
            target = iMessage.payload
            if target.canBeNominated and (user.canNominate and user.alive):
                await target.nominated(user)
                game.nominatedPlayer = target
                target.canBeNominated = False
                user.canNominate = False
                response = '**' + target.nickname + '** has been nominated by **' + user.nickname + '**' \
                           + '\n**~vote** to move to voting phase' + '\n­'
                await globals.mainChannel.send(response)
                globals.logger.phase_change_minor(game.nominatedPlayer.nickname + ' has been nominated')
                globals.phase = 'nomination'
            elif target.canBeNominated and not (user.canNominate and user.alive):
                response = 'You cannot nominate' + '\n­'
                await globals.mainChannel.send(response)
            elif not target.canBeNominated and (user.canNominate and user.alive):
                response = '**' + target.nickname + '** cannot be nominated' + '\n­'
                await globals.mainChannel.send(response)
            else:
                response = '**' + target.nickname + '** cannot be nominated and you cannot nominate\n­'
                await globals.mainChannel.send(response)
        elif iMessage.command == 'sleep':
            if user.wantSleep:
                user.wantSleep = False
                response = '**' + user.nickname + '** no longer wants to sleep\n' + str(game.count_sleep()) + '/' + str(
                    math.ceil(0.75 * game.count_can_vote())) + ' players want to sleep\n­'
            else:
                user.wantSleep = True
                response = '**' + user.nickname + '** wants to sleep\n' + str(game.count_sleep()) + '/' + str(
                    math.ceil(0.75 * game.count_can_vote())) + ' players want to sleep\n­'
            await globals.mainChannel.send(response)
            await game.check_sleep()  # if time to sleep, send to dusk Interim. execute, resets table, moves to night
        elif iMessage.command == 'table':
            await table.show_table([iMessage.channel])
        elif iMessage.command == 'slay':
            target = iMessage.payload
            await user.slayer_ability(target)
    elif iMessage is not None:
        await iMessage.channel.send(iMessage.payload)


async def phase_nomination(message):
    iMessage = interpret_general(message, ['vote', 'table', 'slay'])
    if iMessage is not None and not iMessage.error:
        user = game.get_player_from_user(iMessage.user)
        if iMessage.command == 'vote':
            if user.canVote:
                if user.wantVote:
                    user.wantVote = False
                    message = '**' + user.nickname + '** no longer wants to vote\n' + str(game.count_vote()) + \
                              '/' + str(math.ceil(0.75 * game.count_can_vote())) + ' players want to vote on **' + \
                              game.nominatedPlayer.nickname + '**'
                else:
                    user.wantVote = True
                    message = '**' + user.nickname + '** wants to vote\n' + str(game.count_vote()) + '/' + str(
                        math.ceil(0.75 * game.count_can_vote())) + ' players want to vote on **' + \
                        game.nominatedPlayer.nickname + '**'
            else:
                message = 'You cannot vote'
            await globals.mainChannel.send(message)
            if game.check_vote():
                for player in game.players:
                    player.wantVote = False
                globals.phase = 'voting'
                await game.voting()  # starts voting
        elif iMessage.command == 'table':
            await table.show_table([iMessage.channel])
        elif iMessage.command == 'slay':
            target = iMessage.payload
            await user.slayer_ability(target)
    elif iMessage is not None:
        await iMessage.channel.send(iMessage.payload)


@globals.client.event
async def on_message(message):
    if message.author == globals.client.user and globals.logger.file is not None:
        globals.logger.log(globals.phase, message)
        return
    if message.author.bot:
        return
    if message.channel is not globals.mainChannel and globals.phase != 'no_game':
        return
    if message.content == "" or message.content is None:
        return
    if message.content[0] != '~':
        return
    is_private = isinstance(message.channel, discord.abc.PrivateChannel)

    iMessage = interpret_general(message, ['note', 'shutdown'])
    if iMessage is not None and globals.logger is not None:
        if iMessage.command == 'note':
            return
        elif iMessage.command == 'shutdown':
            await globals.logger.shutdown()
            globals.logger = None
            sys.exit('Manual shutdown')

    if globals.phase == 'no_game' and not is_private:
        await phase_no_game(message)
    elif globals.phase == 'create' and not is_private:
        await phase_create(message)
    elif globals.phase == 'day' and not is_private:
        await phase_day(message)
    elif globals.phase == 'nomination' and not is_private:
        await phase_nomination(message)


@globals.client.event
async def on_ready():
    print(f'{globals.client.user.name} connected!')
    globals.clockbotSpam = globals.client.get_channel(741022184033746984)


globals.client.run(token)
