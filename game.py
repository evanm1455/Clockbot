import globals
import random
import databases
from interpreter import wait_for_message
import math
import datetime
import time
import sys
import table
import asyncio

# players
joiningPlayers = []  # discord.Member objects
joiningPlayersNicknames = []
nicknamesDictionary = {}
players = []  # character objects. NEVER PERMUTE THIS, needs to stay in original order

# roles
bannedRoles = []
setsRawInput = []
possibleRoles = [[], [], [], []]
possibleStartingRoles = [[], [], [], []]  # set to value of possibleRoles when game starts
rolesInPlay = []

# game state
numDays = 0
nominatedPlayer = None
playerOnDeathRow = None
votesForDeathRow = 0
playerExecutedDuringDay = None
playerDiedByExecution = False
alivePlayersBeforeNight = []
nightList = []


async def add_player(player):

    if player not in joiningPlayers:
        joiningPlayers.append(player)
        tempNick = player.display_name
        joiningPlayersNicknames.append(tempNick)
        response = '**' + tempNick + '** has joined. ' + 'Number of players: ' + str(len(joiningPlayers)) + '\n­'
        await globals.mainChannel.send(response)
    else:
        await globals.mainChannel.send('You are already in the game' + '\n­')


async def ban(role):
    if role in bannedRoles:
        bannedRoles.remove(role)
        message = role + ' has been unbanned' + '\n­'
    else:
        bannedRoles.append(role)
        message = role + ' has been banned' + '\n­'
    await globals.mainChannel.send(message)


async def start_game():
    global joiningPlayers, players, possibleRoles, possibleStartingRoles, rolesInPlay
    numberOfPlayers = len(joiningPlayers)

    roles = []
    playerCounts = [[1, 0, 0, 0],
                    [1, 0, 0, 1],
                    [1, 1, 0, 1],
                    [1, 1, 1, 1],
                    [2, 1, 1, 1],
                    [2, 2, 1, 1],
                    [3, 2, 1, 1],
                    [3, 2, 2, 1],
                    [4, 2, 2, 1],
                    [4, 3, 2, 1],
                    [4, 3, 3, 1]
                    ]  # good, outsider, minion, demon

    for i in range(4):  # bans roles
        possibleRoles[i] = list(set(possibleRoles[i]) - set(bannedRoles))

    def invalid_roleset():
        if len(possibleRoles[0]) - 3 < playerCounts[numberOfPlayers - 1][0]:  # demon needs 2-3 unused townsfolk roles
            return 'Not enough townsfolk roles available'
        if len(possibleRoles[1]) < playerCounts[numberOfPlayers - 1][1]:
            return 'Not enough outsider roles available'
        if len(possibleRoles[2]) < playerCounts[numberOfPlayers - 1][2]:
            return 'Not enough minion roles available'
        if len(possibleRoles[3]) < playerCounts[numberOfPlayers - 1][3]:
            return 'Not enough demon roles available'
        return None

    if numberOfPlayers < 2:
        await globals.mainChannel.send('Player count = ' + str(numberOfPlayers) + ' is not enough to start game')
        return
    elif invalid_roleset() is not None:
        await globals.mainChannel.send(invalid_roleset())
        return
    else:
        message = 'Starting game with ' + str(numberOfPlayers) + ' players\nActive sets:\n' + sets_in_play()
        await globals.mainChannel.send(message)

    # hard code roles here, comment out random.shuffle
    possibleStartingRoles = possibleRoles
    for i in range(4):  # randomly pick roles that will be in game
        random.shuffle(possibleRoles[i])
        for j in range(playerCounts[numberOfPlayers - 1][i]):
            tempRole = possibleRoles[i].pop()
            roles.append(tempRole)

    rolesInPlay = roles
    random.shuffle(joiningPlayers)  # randomize order of user objects

    for role in roles:  # assignment of users & user params into the character objects corresponding to allowed roles
        # role is a string
        charObject = databases.characterDatabase[role]
        # charObject = make_character(role)
        charObject.position = roles.index(role)
        charObject.clientUser = joiningPlayers.pop()
        charObject.nickname = nicknamesDictionary[charObject.clientUser.id] if charObject.clientUser.id in nicknamesDictionary else charObject.clientUser.display_name
        charObject.alias = databases.aliasDatabase[charObject.clientUser.id]
        await charObject.clientUser.create_dm()
        charObject.dmChannel = charObject.clientUser.dm_channel
        players.append(charObject)

    for player in players:
        player.secondary_init()

    # table setup and show table before first night info & activations. don't show table on first dawn
    table.table_setup(players)
    table.draw_table('new picture')
    await table.show_table([globals.mainChannel, globals.clockbotSpam])

    for i in range(numberOfPlayers):  # set L/R neighbors
        if i == 0:
            players[i].leftNeighbor = players[numberOfPlayers - 1]
            players[i].rightNeighbor = players[1]
        elif i == numberOfPlayers - 1:
            players[i].leftNeighbor = players[numberOfPlayers - 2]
            players[i].rightNeighbor = players[0]
        else:
            players[i].leftNeighbor = players[i - 1]
            players[i].rightNeighbor = players[i + 1]

    for player in players:  # message players their roles
        await player.send_to_self('Your role: ' + player.trueCharacter if player.imitating is None else player.imitating)

    # give out the evil info
    evildoers = 'Evil Team: **' + '**, **'.join(map(lambda p: p.nickname, all_of_property(lambda p: p.trueAlignment == 'evil'))) + '**'
    evildoers += '\nDemon: **' + random_of_property(lambda p: p.trueType == 'demon').nickname + '**'
    for evildoer in all_of_property(lambda p: p.trueAlignment == 'evil'):
        await evildoer.send_to_self(evildoers)
        if evildoer.trueType == 'demon':
            if len(possibleRoles[1]) > 1:
                goodRolesNotInPlay = 'Good roles not in play: ' + ', '.join(possibleRoles[0][0:2]) + ', ' + possibleRoles[1][0]
            else:
                goodRolesNotInPlay = 'Good roles not in play: ' + ', '.join(possibleRoles[0][0:3])
            await evildoer.send_to_self(goodRolesNotInPlay)

    globals.phase = 'no_phase'
    await night()  # start first night


async def voting():
    global votesForDeathRow, nominatedPlayer, playerOnDeathRow
    globals.logger.phase_change_minor('Voting has begun on ' + nominatedPlayer.nickname)

    await table.show_table([globals.mainChannel])
    message = '­\nVoting has begun on **' + nominatedPlayer.nickname + '**\nVote with **~yes** or **~no**\n'
    minVotes = 0
    if playerOnDeathRow is not None:
        minVotes = votesForDeathRow
        message += '**' + playerOnDeathRow.nickname + '**' + ' is currently on death row. ' + str(minVotes) + \
                   ' votes are needed to tie\n­'
    else:
        minVotes = math.ceil(count_alive() / 2)  # do we require half or >half to kill?
        message += str(minVotes) + ' votes are needed to kill\n­'
    await globals.mainChannel.send(message)
    voterList = []
    for player in players:
        player.wantsVote = False

    def voting_order(playerList):  # sorts list by voting order (starting at right of nominee)
        nominatedPlayerIndex = playerList.index(nominatedPlayer)
        tempList1 = playerList[nominatedPlayerIndex:]
        tempList2 = playerList[0:nominatedPlayerIndex]

        def rotate(l, n):
            return l[n:] + l[:n]

        return rotate(tempList1 + tempList2, 1)

    for player in voting_order(players):
        if player.canVote:
            voterList.append(player)
    message = 'These players can vote (in this order):\n**' + ', '.join(map(lambda p: p.nickname, voterList)) + '**\n­'
    await globals.mainChannel.send(message + '\nVoting starts in 10 seconds, players each have 10 seconds to vote')
    time.sleep(10)

    async def get_votes(voterList):
        votes = 0
        time = 10

        for player in voterList:

            def check(m):
                return m.channel == globals.mainChannel and m.author == player.clientUser

            count = 0
            voteString = 'vote' if player.alive else 'deadvote'
            promptMessage = '**' + player.nickname + '\'s** ' + voteString + '? **~yes** or **~no** to vote\nCurrent ' \
                            'votes: ' + str(votes) + '/' + str(minVotes) + '\n'
            reply = None
            error = None

            while reply is None and count < time:
                if count == 0:
                    prompt = await globals.mainChannel.send(promptMessage + str(time - count) + 's remaining')

                try:
                    reply = await globals.client.wait_for('message', check=check, timeout=1)
                except asyncio.TimeoutError:
                    pass

                count += 1
                await prompt.edit(content=promptMessage + str(time - count) + 's remaining')

                if reply is not None and reply.content not in ['~yes', '~no']:
                    print('error: ' + reply.content)  # debug
                    error = await globals.mainChannel.send('command not recognized')
                    reply = None

            if reply is not None and reply.content == '~yes':
                votes += 1
                if not player.alive:  # deadvote expended
                    player.canVote = False

            if error is not None:
                await error.delete()
            await prompt.delete()

        return votes

    # async def get_votes(voterList):
    #     votes = 0
    #     for player in voterList:
    #         voteString = 'vote' if player.alive else 'deadvote'
    #         prompt = '**' + player.nickname + '\'s** ' + voteString + '? **~yes** or **~no** to vote. ' + \
    #                  'Current votes: ' + str(votes) + '/' + str(minVotes)
    #         iMessage = await wait_for_message(globals.mainChannel, prompt,
    #                                           player.clientUser, ['yes', 'no'], time=10)
    #         if iMessage.command == 'yes':
    #             votes += 1
    #             if not player.alive:  # deadvote expended
    #                 player.canVote = False
    #     return votes

    votes = await get_votes(voterList)
    await globals.mainChannel.send(str(votes) + '/' + str(minVotes) + ' votes to kill **' +
                                   nominatedPlayer.nickname + '**')
    if votes / count_alive() >= 0.5 and votes > votesForDeathRow:
        message = '**' + nominatedPlayer.nickname + '** is on death row'
        playerOnDeathRow = nominatedPlayer
        votesForDeathRow = votes
    elif votes == votesForDeathRow and votesForDeathRow > 0:
        message = 'Votes tied. Nobody is on death row'
        votesForDeathRow = 0
        playerOnDeathRow = None
    else:
        message = 'Not enough votes'
        if playerOnDeathRow is not None:
            message += '\n**' + playerOnDeathRow.nickname + '** is still on death row'
    await globals.mainChannel.send(message)

    globals.phase = 'day'


async def dusk():
    global nominatedPlayer, playerOnDeathRow, playerExecutedDuringDay, alivePlayersBeforeNight, \
        votesForDeathRow, playerDiedByExecution
    globals.logger.save()

    if playerOnDeathRow is not None:
        message = '**' + playerOnDeathRow.nickname + '** has been executed'

        pacifist = random_of_property(lambda p: p.trueCharacter == 'pacifist')  # pacifist stuff
        pacifistBlock = False
        if pacifist is not None and pacifist.alive and not pacifist.poison and playerOnDeathRow.trueAlignment == 'good':
            pacifistBlock = random.choice([False, True])

        if not pacifistBlock and await playerOnDeathRow.die('execution'):
            playerDiedByExecution = True
            message = message + '\nThey are now dead'
        else:
            message = message + '\nNothing happens'
        await globals.mainChannel.send(message)

        playerExecutedDuringDay = playerOnDeathRow

    # check mayor game end
    mayor = random_of_property(lambda p: p.trueCharacter == 'mayor')
    if mayor is not None and mayor.alive and not mayor.poisoned:
        if count_alive() == 3 and playerExecutedDuringDay is None:
            await game_end('good')
    await check_game_end()

    if playerDiedByExecution:
        table.draw_table()  # update table b/c they're dead
    await table.show_table([globals.mainChannel])

    await globals.mainChannel.send('Good Night' + '\n­')
    nominatedPlayer = None
    playerOnDeathRow = None
    votesForDeathRow = 0
    alivePlayersBeforeNight = []
    for player in players:
        player.dusk_reset()
        if player.alive:
            alivePlayersBeforeNight.append(player.nickname)

    globals.phase = 'no_phase'
    await night()


async def night():
    global nightList
    globals.logger.reset_grimoire()
    globals.logger.phase_change_major('Night ' + str(numDays))
    nightList = sorted(players)
    nightStartTime = datetime.datetime.now()

    time.sleep(5 * random.uniform(0.6, 1.2))  # wait a bit before starting night abilities to shroud info for first
    # activating player, don't want it to be obvious that there are no roles before them
    demonActivatedThisNight = False
    for player in nightList:
        player.reset_night_ability()
        if player.alive and not (demonActivatedThisNight and player.trueType == 'demon'):
            await player.night_ability()
            time.sleep(3 * random.uniform(1, 3))
            if player.trueType == 'demon':
                demonActivatedThisNight = True  # avoid imp-style double-activation of demon

    if numDays == 0:  # semi random minimum length of nights to mask number of night roles activating
        minimumNightLength = 15 * random.uniform(0.8, 1.4)
    else:
        minimumNightLength = 40 * random.uniform(0.8, 1.25)

    nightLength = (datetime.datetime.now() - nightStartTime).total_seconds()
    if nightLength < minimumNightLength:
        time.sleep(minimumNightLength - nightLength)

    await dawn()


async def dawn():
    global numDays, playerExecutedDuringDay, playerDiedByExecution
    globals.logger.save()
    numDays += 1
    globals.logger.phase_change_major('Day ' + str(numDays))
    playerExecutedDuringDay = None
    playerDiedByExecution = False

    if numDays != 1:
        table.draw_table('new picture')
        await table.show_table([globals.mainChannel, globals.clockbotSpam])

    for player in players:
        player.dawn_reset()

    def night_deaths():
        alivePlayersAfterNight = []
        for player in players:
            if player.alive:
                alivePlayersAfterNight.append(player.nickname)

        difference = list(set(alivePlayersBeforeNight) - set(alivePlayersAfterNight))
        if not difference:  # this doesn't work for night 0 because never enter dusk, but nobody should die night 0
            message = 'Good morning. Everyone is healthy. ' + '\n­'
        else:
            message = 'Good morning. RIP: ' + ', '.join(difference) + '\n­'
        return message

    await globals.mainChannel.send(night_deaths())
    if numDays == 1:
        message = '**~nominate player** to nominate\n**~sleep** to vote to sleep\n**~table** to show table'
        await globals.mainChannel.send(message)
    globals.phase = 'day'
    await check_game_end()


# builds set from [roleset] [subset] inputs. [set] is handled by validate_set()
def build_set(input):
    tempSet = []
    roleSetName = input[0]
    subsets = input[1:]

    troubleBrewing = [
        ['chef', 'empath', 'fortune teller', 'investigator', 'librarian', 'mayor', 'monk', 'ravenkeeper',
         'slayer', 'soldier', 'undertaker', 'virgin', 'washerwoman'],
        ['drunk', 'recluse', 'saint'],
        ['poisoner', 'scarlet woman', 'spy'],
        ['imp']]
    badMoon = [
        ['chambermaid', 'courtier', 'exorcist', 'fool', 'gambler', 'grandmother', 'innkeeper', 'minstrel',
         'pacifist', 'professor', 'sailor', 'tea lady'],
        ['goon', 'gypsy', 'lunatic', 'tinker'],
        ['assassin', 'devil\'s advocate', 'godfather', 'tinker'],
        ['pukka', 'zombuul']]

    if roleSetName == 'tb':
        tempSet = troubleBrewing
    elif roleSetName == 'bm':
        tempSet = badMoon

    setsRawInput.append(input)

    def add_subset_into_roleset(subset):
        if subset == 'townsfolk':
            possibleRoles[0].extend(tempSet[0])
        if subset == 'outsiders':
            possibleRoles[1].extend(tempSet[1])
        if subset == 'minions':
            possibleRoles[2].extend(tempSet[2])
        if subset == 'demons':
            possibleRoles[3].extend(tempSet[3])

    if len(subsets) == 0:
        for i in range(4):
            possibleRoles[i].extend(tempSet[i])
    else:
        for subset in subsets:
            add_subset_into_roleset(subset)

    for i in range(4):  # cleans up duplicates (if someone does ~create tb, ~create tb, ~create tb townsfolk, etc)
        possibleRoles[i] = remove_duplicates_from_list(possibleRoles[i])


def sets_in_play():
    tb = []
    bm = []
    tbSubsets = ''
    bmSubsets = ''
    bans = ''
    comparator = {'townsfolk', 'outsiders', 'minions', 'demons'}
    for x in setsRawInput:
        if x[0] == 'tb':
            tb.append(x[1:])
        elif x[0] == 'bm':
            bm.append(x[1:])

    flatTB = remove_duplicates_from_list([subset for sublist in tb for subset in sublist])
    flatTB = list(set(flatTB) & comparator)
    if set(flatTB) == comparator or [] in tb:
        tbSubsets += 'tb ALL\n'
    elif len(flatTB) > 0:
        tbSubsets += 'tb ' + ' '.join(flatTB) + '\n'

    flatBM = remove_duplicates_from_list([subset for sublist in bm for subset in sublist])
    flatBM = list(set(flatBM) & comparator)
    if flatBM == comparator or [] in bm:
        bmSubsets += 'bm ALL\n'
    elif len(flatBM) > 0:
        bmSubsets += 'bm ' + ' '.join(flatBM) + '\n'

    if len(bannedRoles) > 0:
        bans += ', '.join(bannedRoles) + ' banned\n'

    return tbSubsets + bmSubsets + bans


def get_nickname(player):
    return player.nickname


def remove_duplicates_from_list(list):
    newList = []
    for el in list:
        if el not in newList:
            newList.append(el)
    return newList


def check_vote():
    return count_vote() / count_can_vote() >= 0.75


async def check_sleep():
    if count_sleep() / count_can_vote() >= 0.75:
        await dusk()
    else:
        return


async def check_game_end():
    gameEnd = False
    goodWin = True
    for player in players:
        if player.trueType == 'demon' and player.alive:
            goodWin = False
    if count_alive() <= 2:
        gameEnd = True

    if goodWin:
        globals.phase = 'end'
        await game_end('good')
    elif gameEnd and not goodWin:
        globals.phase = 'end'
        await game_end('evil')


async def game_end(win):
    roles = ''
    for player in players:
        roles += ('***' if player.trueAlignment == win else '') + str(player) + ('***' if player.trueAlignment == win else '') + '\n'

    message = 'The ' + win + ' team has won!\n' + roles
    await globals.mainChannel.send(message)
    await globals.logger.shutdown()
    await globals.client.logout()
    sys.exit('Game is over')


def get_player_from_user(user):
    for player in players:
        if player.clientUser == user:
            return player
    return None


def get_player_from_name(name):
    for player in players:
        if player.alias.lower() == name.lower() or player.nickname.lower() == name.lower():
            return player
    return None


def count_can_vote():
    return count_property(lambda p: p.canVote)


def count_vote():
    return count_property(lambda p: p.wantVote)


def count_sleep():
    return count_property(lambda p: p.wantSleep)


def count_alive():
    return count_property(lambda p: p.alive)


def random_player(notPlayerOne=None, notPlayerTwo=None, notPlayerThree=None):
    getAlias = lambda p: None if p is None else p.alias
    valids = list(set(map(getAlias, players)) - {getAlias(notPlayerOne)} - {getAlias(notPlayerTwo)} - {getAlias(notPlayerThree)})

    if not valids:
        return None
    else:
        return get_player_from_name(random.choice(valids))


def count_property(func, notPlayerOne=None, notPlayerTwo=None):
    allOf = all_of_property(func, notPlayerOne, notPlayerTwo)
    if allOf:
        return len(allOf)
    else:
        return 0


def all_of_property(func, notPlayerOne=None, notPlayerTwo=None):
    getAlias = lambda p: None if p is None else p.alias
    withProperty = filter(func, players)
    valids = list(set(map(getAlias, withProperty)) - {getAlias(notPlayerOne)} - {getAlias(notPlayerTwo)})
    if not valids:
        return None
    else:
        valids = list(map(lambda n: get_player_from_name(n), valids))
        return valids


def random_of_property(func, notPlayerOne=None, notPlayerTwo=None):
    valids = all_of_property(func, notPlayerOne, notPlayerTwo)
    if not valids:
        return None
    else:
        return random.choice(valids)


def print_roles():
    roles = ''
    for player in players:
        if player.imitating is not None:
            roles += str(player) + ' (' + player.imitating + ')\n'
        else:
            roles += str(player) + '\n'
    return roles + '\n'
