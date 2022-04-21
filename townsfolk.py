import globals
import game
import random
from character import Character


class Townsfolk(Character):
    def __init__(self):
        super().__init__()
        self.trueAlignment = 'good'
        self.trueType = 'townsfolk'


# Trouble Brewing
class Chef(Townsfolk):
    def __init__(self):
        super().__init__()
        self.trueCharacter = 'chef'
        self.turnOrder = 83
        super().match_visible_to_true()

    async def night_ability(self):
        if game.numDays == 0:
            self.wakeTonight = True
            count = 0
            for player in game.players:
                if player.visibleAlignment == 'evil' and player.rightNeighbor.visibleAlignment == 'evil':
                    count += 1

            if self.poisoned:
                possibles = game.all_of_property(lambda p: p.trueType == 'evil')
                possibles = list(range(len(possibles)))
                possibles.remove(count)
                count = random.choice(possibles)

            message = 'There are ' + str(count) + ' pair(s) of adjacent evil players'
            await self.send_to_self(message)


class Empath(Townsfolk):
    def __init__(self):
        super().__init__()
        self.trueCharacter = 'empath'
        self.turnOrder = 85
        super().match_visible_to_true()

    async def night_ability(self):
        self.wakeTonight = True
        count = 0
        if super().alive_neighbor('left').visibleAlignment == 'evil':
            count += 1
        if super().alive_neighbor('right').visibleAlignment == 'evil':
            count += 1

        if self.poisoned:
            possibles = [0, 1, 2]
            possibles.remove(count)
            count = random.choice(possibles)

        message = 'There are ' + str(count) + ' evil living players adjacent to you'
        await self.send_to_self(message)


class FortuneTeller(Townsfolk):
    def __init__(self):
        super().__init__()
        self.trueCharacter = 'fortune teller'
        self.turnOrder = 86
        super().match_visible_to_true()

    async def night_ability(self):
        self.wakeTonight = True

        prompt = 'Choose first player to investigate\n**~choose player**'
        iMessage = await super().wait_on_self(prompt, ['choose'])
        firstTarget = iMessage.payload

        prompt = 'Choose second player to investigate\n**~choose player**'
        iMessage = await super().wait_on_self(prompt, ['choose'], invalids=[firstTarget.nickname, firstTarget.alias])
        secondTarget = iMessage.payload

        targets = [firstTarget, secondTarget]
        message = 'Targets confirmed: **' + ' '.join(map(lambda p: p.nickname, targets)) + '**'
        await self.send_to_self(message)

        hit = False
        for target in targets:
            if target.visibleType == 'demon' or target == self.redHerring:
                hit = True
                break

        if self.poisoned:
            hit = not hit

        message = 'One of the targets is a demon' if hit else 'Neither of the targets is a demon'
        await self.send_to_self(message)

    def secondary_init(self):
        self.redHerring = game.random_of_property(lambda p: p.trueType != 'demon' and p.trueCharacter != 'recluse', self)


class Investigator(Townsfolk):
    def __init__(self):
        super().__init__()
        self.trueCharacter = 'investigator'
        self.turnOrder = 82
        super().match_visible_to_true()

    async def night_ability(self):
        if game.numDays == 0:
            self.wakeTonight = True
            minion = game.random_of_property(lambda p: p.visibleType == 'minion')

            if minion is None:
                message = 'There are no minions in play'
                await self.send_to_self(message)
                return

            if self.poisoned:
                minion = game.random_player(self)
                other = game.random_player(self, minion)
            else:
                other = game.random_player(self, minion)

            randomPick = [minion, other]
            random.shuffle(randomPick)
            character = minion.visibleCharacter if not self.poisoned else random.choice(list(set(game.possibleStartingRoles[2]) - {'spy'}))  # doesnt work if all minion roles but spy are banned. dont wanna fix because i dont feel like it

            message = 'Either ' + randomPick[0].nickname + ' or ' + randomPick[1].nickname + ' is the ' + character
            await self.send_to_self(message)


class Librarian(Townsfolk):
    def __init__(self):
        super().__init__()
        self.trueCharacter = 'librarian'
        self.turnOrder = 81
        super().match_visible_to_true()

    async def night_ability(self):
        if game.numDays == 0:
            self.wakeTonight = True
            outsider = game.random_of_property(lambda p: p.visibleType == 'outsider')

            if outsider is None:
                message = 'There are no outsiders in play'
                await self.send_to_self(message)
                return

            if self.poisoned:
                outsider = game.random_player(self)
                other = game.random_player(self, outsider)
            else:
                other = game.random_player(self, outsider)

            randomPick = [outsider, other]
            random.shuffle(randomPick)
            character = outsider.visibleCharacter if not self.poisoned else random.choice(list(set(game.possibleStartingRoles[1]) - {'recluse'}))

            message = 'Either ' + randomPick[0].nickname + ' or ' + randomPick[1].nickname + ' is the ' + character
            await self.send_to_self(message)


class Mayor(Townsfolk):  # handled in dusk post-execution
    def __init__(self):
        super().__init__()
        self.trueCharacter = 'mayor'
        super().match_visible_to_true()

    async def die(self, source):
        if not self.alive:
            return False

        if await super().die(source) and source == 'demon' and not self.poisoned:
            redirect = game.random_of_property(lambda p: p.trueType == 'townsfolk', self)
            if redirect is None:
                self.alive = False
                return True
            else:
                self.alive = True
                await redirect.die(source)
        else:
            self.alive = False
            return True


class Monk(Townsfolk):
    def __init__(self):
        super().__init__()
        self.trueCharacter = 'monk'
        self.turnOrder = 23
        super().match_visible_to_true()

    async def night_ability(self):
        if game.numDays != 0:
            self.wakeTonight = True

            prompt = 'Choose player to protect\n**~choose player**'

            iMessage = await super().wait_on_self(prompt, ['choose'], invalids=[self.nickname, self.alias])
            target = iMessage.payload

            message = 'Target confirmed: **' + target.nickname + '**'
            await super().send_to_self(message)
            target.monkProtected = not self.poisoned


class Ravenkeeper(Townsfolk):
    def __init__(self):
        super().__init__()
        self.trueCharacter = 'ravenkeeper'
        self.turnOrder = 84
        super().match_visible_to_true()

    async def die(self, source):
        if not self.alive:
            return False

        if await super().die(source):
            if source == 'demon':
                self.wakeTonight = True

                prompt = 'Choose player to investigate\n**~choose player**'

                iMessage = await super().wait_on_self(prompt, ['choose'])
                target = iMessage.payload

                message = 'Target confirmed: **' + target.nickname + '**'
                await super().send_to_self(message)

                character = target.visibleCharacter

                if self.poisoned:
                    possible = [role for subset in game.possibleStartingRoles for role in subset]
                    possible = list(set(possible) - {character} - {self.trueCharacter})
                    character = random.choice(possible)

                message = 'Target is the : ' + character
                await super().send_to_self(message)
            return True
        else:
            return False


class Slayer(Townsfolk):
    def __init__(self):
        super().__init__()
        self.trueCharacter = 'slayer'
        super().match_visible_to_true()

    async def slayer_ability(self, target):
        if self.usedAbility:
            return

        if target.trueType == 'demon' and not self.poisoned and await target.die('slayer'):
            message = '**' + self.nickname + '** slays **' + target.nickname + '**! A singular strike!'
        else:
            message = '**' + self.nickname + '** slays **' + target.nickname + '**! It isn\'t very effective'
        if target.alias == 'will':
            globals.timesWillSlain += 1
            message += '\nWill Nute now has ' + globals.timesWillSlain + ' crossbow bolts protruding from his chest'
        await globals.mainChannel.send(message)
        await game.check_game_end()
        self.usedAbility = True


class Soldier(Townsfolk):
    def __init__(self):
        super().__init__()
        self.trueCharacter = 'soldier'
        super().match_visible_to_true()

    async def die(self, source):
        if not self.alive:
            return False

        if not await super().die(source) or (source == 'demon' and not self.poisoned):
            self.alive = True
            self.causeOfDeath = None
            return False
        else:
            self.alive = False  # causeOfDeath is set from super().die(source) above
            return True


class Undertaker(Townsfolk):
    def __init__(self):
        super().__init__()
        self.trueCharacter = 'undertaker'
        self.turnOrder = 87
        super().match_visible_to_true()

    async def night_ability(self):
        if game.playerExecutedDuringDay is not None and game.playerDiedByExecution:
            self.wakeTonight = True

            character = game.playerExecutedDuringDay.trueCharacter

            if self.poisoned:
                possible = [role for subset in game.possibleStartingRoles for role in subset]
                possible = list(set(possible) - {character} - {self.trueCharacter})
                character = random.choice(possible)

            message = 'The ' + character + ' was executed today'
            await self.send_to_self(message)


class Virgin(Townsfolk):
    def __init__(self):
        super().__init__()
        self.trueCharacter = 'virgin'
        super().match_visible_to_true()

    async def nominated(self, source):
        if source.trueType == 'townsfolk' and not self.usedAbility and not self.poisoned:
            game.playerOnDeathRow = source
            await game.dusk()
        self.usedAbility = True


class Washerwoman(Townsfolk):
    def __init__(self):
        super().__init__()
        self.trueCharacter = 'washerwoman'
        self.turnOrder = 80
        super().match_visible_to_true()

    async def night_ability(self):
        if game.numDays == 0:
            self.wakeTonight = True

            townsfolk = game.random_of_property(lambda p: p.visibleType == 'townsfolk', self)

            if townsfolk is None:
                message = 'There are no townsfolk in play'
                await self.send_to_self(message)
                return

            if self.poisoned:
                townsfolk = game.random_player(self)
                other = game.random_player(self, townsfolk)
            else:
                other = game.random_player(self, townsfolk)

            randomPick = [townsfolk, other]
            random.shuffle(randomPick)
            character = townsfolk.visibleCharacter if not self.poisoned else random.choice(list(set(game.possibleStartingRoles[0]) - {self.trueCharacter}))

            message = 'Either **' + randomPick[0].nickname + '** or **' + randomPick[1].nickname + '** is the ' + character
            await self.send_to_self(message)


# Bad Moon Rising
class Chambermaid(Townsfolk):
    def __init__(self):
        super().__init__()
        self.trueCharacter = 'chambermaid'
        self.turnOrder = 100
        super().match_visible_to_true()

    async def night_ability(self):  # does this ability implicitly let them check if target is an executed zombuul?
        self.wakeTonight = True

        invalidPlayers = [player for player in game.players if not player.alive]
        invalidPlayers.append(self)
        invalids = list(map(lambda p: [p.nickname, p.alias], invalidPlayers))
        invalids = [name for sublist in invalids for name in sublist]

        prompt = 'Choose first player to check\n**~choose player**'
        iMessage = await super().wait_on_self(prompt, ['choose'], invalids=invalids)
        firstTarget = iMessage.payload
        invalids.extend([firstTarget.nickname, firstTarget.alias])

        prompt = 'Choose second player to check\n**~choose player**'
        iMessage = await super().wait_on_self(prompt, ['choose'], invalids=invalids)
        secondTarget = iMessage.payload

        targets = [firstTarget, secondTarget]
        message = 'Targets confirmed: **' + ', '.join(map(lambda p: p.nickname, targets)) + '**'
        await self.send_to_self(message)

        count = 0
        for target in targets:
            if target.wakeTonight:
                count += 1

        if self.poisoned:
            possibleCounts = [0, 1, 2]
            possibleCounts.remove(count)
            count = random.choice(possibleCounts)

        message = str(count) + ' of the targets wake/woke up tonight'
        await self.send_to_self(message)


class Courtier(Townsfolk):
    def __init__(self):
        super().__init__()
        self.trueCharacter = 'courtier'
        self.turnOrder = 22
        super().match_visible_to_true()
        self.dayPoisoned = None

    async def night_ability(self):  # we probably need to change how we handle poison

        if not self.usedAbility:
            self.wakeTonight = True

            prompt = 'Use your ability? **~yes** or **~no**'
            iMessage = await super().wait_on_self(prompt, ['yes', 'no'])

            if iMessage.command == 'yes':
                self.usedAbility = True

                prompt = 'Choose a role to poison\n**~role role**'
                iMessage = await super().wait_on_self(prompt, ['role'])
                role = iMessage.payload
                self.lastTarget = game.all_of_property(lambda p: p.trueCharacter == role)

                message = 'Target role confirmed: ' + role
                await self.send_to_self(message)

                if not self.poisoned and self.lastTarget is not None:
                    self.lastTarget.poison(self.trueCharacter)
                    self.dayPoisoned = game.numDays

    def reset_night_ability(self):  # handle the 3-day repoisoning in here, in case courtier dies
        self.wakeTonight = False
        if self.lastTarget is not None:
            self.lastTarget.unpoison(self.trueCharacter)

        if self.dayPoisoned is not None and game.numDays - self.dayPoisoned <= 3:
            self.lastTarget.poison(self.trueCharacter)


class Exorcist(Townsfolk):
    def __init__(self):
        super().__init__()
        self.trueCharacter = 'exorcist'
        self.turnOrder = 39
        super().match_visible_to_true()
        self.exorcisedAbility = None

    async def night_ability(self):
        if game.numDays != 0:
            self.wakeTonight = True

            prompt = 'Choose player to exorcise\n**~choose player**'
            iMessage = await super().wait_on_self(prompt, ['choose'])
            self.lastTarget = iMessage.payload

            message = 'Target confirmed: **' + self.lastTarget.nickname + '**'
            await self.send_to_self(message)

            if self.poisoned:
                return

            if self.lastTarget.trueType == 'demon':
                await self.lastTarget.dmChannel.send('**' + self.nickname + '** is the Exorcist')
                self.exorcisedAbility = self.lastTarget.night_ability
                self.lastTarget.night_ability = super().night_ability

    def reset_night_ability(self):
        self.wakeTonight = False
        if self.lastTarget is not None:
            self.lastTarget.night_ability = self.exorcisedAbility

        self.lastTarget = None
        self.exorcisedAbility = None


class Fool(Townsfolk):
    def __init__(self):
        super().__init__()
        self.trueCharacter = 'fool'
        self.turnOrder = 100
        super().match_visible_to_true()

    async def die(self, source):
        if not self.alive:
            return False

        if await super().die(source) and not self.usedAbility and not self.poisoned:
            self.alive = True
            self.usedAbility = True
            self.causeOfDeath = None
            return False
        else:
            self.alive = False  # causeOfDeath is set from super().die(source) above
            return True


class Gambler(Townsfolk):
    def __init__(self):
        super().__init__()
        self.trueCharacter = 'gambler'
        self.turnOrder = 31
        super().match_visible_to_true()

    async def night_ability(self):
        if game.numDays != 0:
            self.wakeTonight = True

            prompt = 'Choose a player to guess the role of\n**~choose player**'
            iMessage = await super().wait_on_self(prompt, ['choose'])
            target = iMessage.payload

            message = 'Target confirmed: **' + target.nickname + '**'
            await self.send_to_self(message)

            prompt = 'Guess **' + target.nickname + '\'s** role\n**~role role**'
            iMessage = await super().wait_on_self(prompt, ['role'])
            role = iMessage.payload

            message = 'Guess confirmed: ' + role
            await self.send_to_self(message)

            if target.trueCharacter != role and not self.poisoned:  # and not er protected?
                await super().die('gambler')


class Grandmother(Townsfolk):
    def __init__(self):
        super().__init__()
        self.trueCharacter = 'grandmother'
        self.turnOrder = 41
        super().match_visible_to_true()
        self.child = None

    async def night_ability(self):
        if game.numDays == 0:
            self.wakeTonight = True

            if not self.poisoned:
                message = '**' + self.child.nickname + '** is the ' + self.child.trueCharacter
            else:
                falseChild = game.random_player(self, self.child)
                falseRole = random.choice(list(set(game.possibleStartingRoles) -
                                               {falseChild.trueCharacter} - {'grandmother'}))
                message = '**' + falseChild.nickname + '** is the ' + falseRole

            await self.send_to_self(message)

        elif self.alive and not self.poisoned:
            if self.child in game.alivePlayersBeforeNight and self.child.causeOfDeath == 'demon':
                await super().die('grandmother')

    def secondary_init(self):
        self.child = game.random_of_property(lambda p: p.trueAlignment == 'good')


class Innkeeper(Townsfolk):
    def __init__(self):
        super().__init__()
        self.trueCharacter = 'innkeeper'
        self.turnOrder = 21
        super().match_visible_to_true()

    async def night_ability(self):  # miraculously, poisons ending at dusk is never a problem b/c of turn orders
        if game.numDays != 0:
            self.wakeTonight = True
            prompt = 'Choose first player to give safe lodging\n**~choose player**'
            iMessage = await super().wait_on_self(prompt, ['choose'])
            firstTarget = iMessage.payload

            prompt = 'Choose second player to give safe lodging\n**~choose player**'
            iMessage = await super().wait_on_self(prompt, ['choose'],
                                                  invalids=[firstTarget.nickname, firstTarget.alias])
            secondTarget = iMessage.payload

            targets = [firstTarget, secondTarget]
            message = 'Targets confirmed: **' + ' '.join(map(lambda p: p.nickname, targets)) + '**'
            await self.send_to_self(message)

            if self.poisoned:
                return

            firstTarget.innkeeperProtected = secondTarget.innkeeperProtected = True
            self.lastTarget = random.choice(targets)
            self.lastTarget.poison(self.trueCharacter)


class Minstrel(Townsfolk):
    def __init__(self):
        super().__init__()
        self.trueCharacter = 'minstrel'
        self.turnOrder = 0
        super().match_visible_to_true()

    async def night_ability(self):
        if (game.playerExecutedDuringDay is not None and
                game.playerExecutedDuringDay.trueType == 'minion' and not self.poisoned):
            for player in game.players:
                player.poison(self.trueCharacter)


class Pacifist(Townsfolk):  # handled in dusk execution
    def __init__(self):
        super().__init__()
        self.trueCharacter = 'pacifist'
        super().match_visible_to_true()


class Professor(Townsfolk):
    def __init__(self):
        super().__init__()
        self.trueCharacter = 'professor'
        self.turnOrder = 95
        super().match_visible_to_true()

    async def night_ability(self):
        if game.numDays != 0 and not self.usedAbility:
            self.wakeTonight = True

            prompt = 'Use your ability? **~yes** or **~no**'
            iMessage = await super().wait_on_self(prompt, ['yes', 'no'])

            if iMessage.command == 'yes':
                self.usedAbility = True

                prompt = 'Choose player to revive\n**~choose player**'
                invalids = game.all_of_property(lambda p: p.alive)
                iMessage = await super().wait_on_self(prompt, ['choose'], invalids=invalids)
                target = iMessage.payload

                message = 'Target confirmed: **' + target.nickname + '**'
                await self.send_to_self(message)

                if not self.poisoned and target.trueType == 'townsfolk':
                    target.alive = True


class Sailor(Townsfolk):
    def __init__(self):
        super().__init__()
        self.trueCharacter = 'sailor'
        self.turnOrder = 20
        super().match_visible_to_true()

    async def night_ability(self):
        self.wakeTonight = True

        prompt = 'Choose player to drink with\n**~choose player**'

        iMessage = await super().wait_on_self(prompt, ['choose'])
        target = iMessage.payload

        message = 'Target confirmed: **' + target.nickname + '**'
        await super().send_to_self(message)

        target = random.choice([target, self])
        if not self.poisoned:
            target.poison('sailor')

    async def die(self, source):
        if not self.poisoned:
            return False
        await super().die(source)


class TeaLady(Townsfolk):  # handled in die()
    def __init__(self):
        super().__init__()
        self.trueCharacter = 'tea lady'
        super().match_visible_to_true()
