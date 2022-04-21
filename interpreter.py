import globals
import game
import asyncio


# gambler will do ~guess character
# i changed my mind i dont think that is a good idea ^


class InterpretedMessage:
    def __init__(self, channel, user, command, payload, error=False):
        self.channel = channel
        self.user = user
        self.command = command
        self.payload = payload
        self.error = error


class PayloadPlus:
    def __init__(self, payload=None, error=False):
        self.payload = payload
        self.error = error


async def wait_for_message(channel, prompt, user, commands, invalids=None, time=None):
    if invalids is None:
        invalids = []

    def check(m):
        return m.channel == channel and m.author == user

    while True:
        await channel.send(prompt)
        try:
            reply = await globals.client.wait_for('message', check=check, timeout=time)
        except asyncio.TimeoutError:
            if 'vote?' in prompt:
                iMessage = InterpretedMessage(channel, user, 'no', None)
        else:
            iMessage = interpret_general(reply, commands, invalids)
        if iMessage is not None and not iMessage.error:
            break
        elif iMessage is not None:
            await channel.send(iMessage.payload)
    return iMessage


def interpret_general(message, commands, invalids=None):
    if invalids is None:
        invalids = []

    if message.content[0] != '~':
        return None
    if game.get_player_from_user(message.author) is None and (globals.phase != 'create' and globals.phase != 'no_game'):
        return None

    text = message.content[1:].split()
    for argument in text[1:]:
        for invalid in invalids:
            if argument == invalid:
                return InterpretedMessage(message.channel, message.author, 'N/A', 'Invalid argument given', error=True)

    for command in commands:
        if text[0] == command:
            globals.logger.log(globals.phase, message)
            payloadPlus = commandsDatabase[command](text[1:])
            if not payloadPlus.error:
                return InterpretedMessage(message.channel, message.author, command, payloadPlus.payload)
            else:
                return InterpretedMessage(message.channel, message.author, command, payloadPlus.payload, error=True)
    return InterpretedMessage(message.channel, message.author, text[0], 'Unrecognized or inappropriate command **~' + text[0] + '**', error=True)


def interpret_create(arguments):
    if not arguments:
        return PayloadPlus()
    else:
        return PayloadPlus(payload='Unexpected arguments. Usage: **~create**', error=True)


def interpret_join(arguments):
    if not arguments:
        return PayloadPlus()
    else:
        return PayloadPlus(payload='Unexpected arguments. Usage: **~join**', error=True)


def interpret_count(arguments):
    if not arguments:
        return PayloadPlus()
    else:
        return PayloadPlus(payload='Unexpected arguments. Usage: **~count**', error=True)


def interpret_set(arguments):
    if not arguments:
        return PayloadPlus(payload='Lacking arguments. Usage: **~set set [subset]**', error=True)
    if arguments[0] not in ['tb', 'bm']:
        return PayloadPlus(payload='Set not recognized. Usage: **~set set [subset]**', error=True)
    if len(arguments) == 1:
        return PayloadPlus(payload=arguments)
    for argument in arguments[1:]:
        if argument not in ['townsfolk', 'outsiders', 'minions', 'demons']:
            return PayloadPlus(payload='Type not recognized. Usage: **~set set [subset]**', error=True)
    return PayloadPlus(payload=arguments)


def interpret_start(arguments):
    if not arguments:
        return PayloadPlus()
    else:
        return PayloadPlus(payload='Unexpected arguments. Usage: **~start**', error=True)


def interpret_nominate(arguments):
    target = game.get_player_from_name(' '.join(arguments))
    if target is None:
        return PayloadPlus(payload=' '.join(arguments) + ' does not resolve to a player. Usage: **~nominate player**', error=True)
    else:
        return PayloadPlus(payload=target)


def interpret_sleep(arguments):
    if not arguments:
        return PayloadPlus()
    else:
        return PayloadPlus(payload='Unexpected arguments. Usage: **~sleep**', error=True)


def interpret_slay(arguments):
    target = game.get_player_from_name(' '.join(arguments))
    if target is None:
        return PayloadPlus(payload=' '.join(arguments) + ' does not resolve to a player. Usage: **~slay player**', error=True)
    else:
        return PayloadPlus(payload=target)


def interpret_vote(arguments):
    if not arguments:
        return PayloadPlus()
    else:
        return PayloadPlus(payload='Unexpected arguments. Usage: **~vote**', error=True)


def interpret_yes(arguments):
    if not arguments:
        return PayloadPlus()
    else:
        return PayloadPlus(payload='Unexpected arguments. Usage: **~yes**', error=True)


def interpret_no(arguments):
    if not arguments:
        return PayloadPlus()
    else:
        return PayloadPlus(payload='Unexpected arguments. Usage: **~no**', error=True)


def interpret_choose(arguments):
    target = game.get_player_from_name(' '.join(arguments))
    if target is None:
        return PayloadPlus(payload=' '.join(arguments) + ' does not resolve to a player. Usage: **~choose player**', error=True)
    else:
        return PayloadPlus(payload=target)


def interpret_note(arguments):
    return PayloadPlus()


def interpret_shutdown(arguments):
    return PayloadPlus()


def interpret_nick(arguments):
    if not arguments:
        return PayloadPlus(payload='Lacking arguments. Usage: **~nick nickname**', error=True)
    return PayloadPlus(payload=' '.join(arguments))


def interpret_ban(arguments):
    if not arguments:
        return PayloadPlus(payload='Lacking arguments. Usage: **~ban role**', error=True)
    if len(arguments) > 1:
        return PayloadPlus(payload='Too many arguments. Usage: **~ban role**', error=True)
    if arguments[0].lower() not in characterList:
        return PayloadPlus(payload='Argument did not resolve to an existing role', error=True)
    return PayloadPlus(payload=arguments[0].lower())


def interpret_table(arguments):
    return PayloadPlus()


def interpret_role(arguments):
    if not arguments:
        return PayloadPlus(payload='Lacking arguments. Usage: **~role role**', error=True)
    if len(arguments) > 1:
        return PayloadPlus(payload='Too many arguments. Usage: **~role role**', error=True)
    if arguments[0].lower() not in game.possibleStartingRoles:
        return PayloadPlus(payload='Argument did not resolve to a role that could be in play', error=True)
    else:
        return PayloadPlus(payload=arguments[0].lower())


commandsDatabase = {'create': interpret_create,
                    'join': interpret_join,
                    'count': interpret_count,
                    'set': interpret_set,
                    'start': interpret_start,
                    'nominate': interpret_nominate,
                    'sleep': interpret_sleep,
                    'slay': interpret_slay,
                    'vote': interpret_vote,
                    'yes': interpret_yes,
                    'no': interpret_no,
                    'choose': interpret_choose,
                    'note': interpret_note,
                    'shutdown': interpret_shutdown,
                    'nick': interpret_nick,
                    'ban': interpret_ban,
                    'table': interpret_table,
                    'role': interpret_role}

characterList = [
                 # trouble brewing
                 'chef',
                 'empath',
                 'fortune teller',
                 'investigator',
                 'librarian',
                 'mayor',
                 'monk',
                 'ravenkeeper',
                 'slayer',
                 'soldier',
                 'undertaker',
                 'virgin',
                 'washerwoman',
                 'drunk',
                 'recluse',
                 'saint',
                 'baron',
                 'poisoner',
                 'scarlet woman',
                 'spy',
                 'imp',
                 # bad moon rising
                 'chambermaid',
                 'courtier',
                 'exorcist',
                 'fool',
                 'gambler',
                 'grandmother',
                 'innkeeper',
                 'minstrel',
                 'pacifist',
                 'professor',
                 'sailor',
                 'tea lady',
                 'goon',
                 'gypsy',
                 'lunatic',
                 'tinker',
                 'assassin',
                 'devils advocate',
                 'godfather',
                 'mastermind',
                 'pukka',
                 'zombuul'
                 ]
